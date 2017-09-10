"""Main.py is the top level script.

Loads the Bottle framework and mounts controllers.  Also adds a custom error
handler.
"""

from google.appengine.api import memcache, urlfetch
from server.lib.bottle import Bottle, request, response, template
import json, logging, StringIO, urllib2
from decimal import *

# TODO: name and list your controllers here so their routes become accessible.
from server.controllers import RESOURCE_NAME_controller

import hashlib, hmac, time # for bitcoinaverage API
import config # this file contains secret API key(s), and so it is in .gitignore

BLOCKEXPLORER_URL = 'http://dogechain.info/chain/Dogecoin/q/addressbalance/'
BLOCKEXPLORER_URL_BACKUP = 'https://chain.so/api/v2/get_address_balance/doge/'
CCC_TRADE_PAIR_URL = 'http://api.cryptocoincharts.info/tradingPair/'
BTER_LTC_BTC_URL = 'http://data.bter.com/api/1/ticker/ltc_btc'
TIMEOUT_DEADLINE = 10 # seconds

def bitcoinaverage_ticker(currency):
  #secret_key = '***REMOVED***'
  #public_key = '***REMOVED***'
  timestamp = int(time.time())
  payload = '{}.{}'.format(timestamp, config.bitcoinaverage_public_key)
  hex_hash = hmac.new(config.bitcoinaverage_secret_key.encode(), msg=payload.encode(), digestmod=hashlib.sha256).hexdigest()
  signature = '{}.{}'.format(payload, hex_hash)

  url = 'https://apiv2.bitcoinaverage.com/indices/global/ticker/BTC' + currency
  headers = {'X-Signature': signature}
  return urlfetch.fetch(url, headers=headers, deadline=TIMEOUT_DEADLINE)

# Run the Bottle wsgi application. We don't need to call run() since our
# application is embedded within an App Engine WSGI application server.
bottle = Bottle()

# Mount a new instance of bottle for each controller and URL prefix.
# TODO: Change 'RESOURCE_NAME' and add new controller references
bottle.mount("/RESOURCE_NAME", RESOURCE_NAME_controller.bottle)

@bottle.route('/')
def home():
  """Return project name at application root URL"""
  return "Dogecoin Balance Wow"

@bottle.route('/api/balance/<address:re:[a-zA-Z0-9]+>')
def getBalance(address=''):
  response.content_type = 'application/json; charset=utf-8'

  url = BLOCKEXPLORER_URL + address
  data = None
  useBackupUrl = False

  try:
    data = urlfetch.fetch(url, deadline=TIMEOUT_DEADLINE)
    if (not data or not data.content or data.status_code != 200):
      logging.warn('No content returned from ' + url)
      useBackupUrl = True
  except Exception as e:
    logging.warn("Error {0} retrieving data: {1}".format(e.errno, e.strerror))
    useBackupUrl = True

  if (useBackupUrl):
    backupUrl = BLOCKEXPLORER_URL_BACKUP + address
    logging.warn('Now trying ' + backupUrl)
    data = urlfetch.fetch(backupUrl, deadline=TIMEOUT_DEADLINE)

  dataDict = json.loads(data.content)
  if (useBackupUrl):
    # backupUrl uses a different format (JSON) to present data
    dataDict = dataDict['data']['confirmed_balance']
    logging.info('Parsed balance from backup url: ' + str(dataDict))

  balance = json.dumps(dataDict).strip('"')
  mReturn = balance

  query = request.query.decode()
  if (len(query) > 0):
    mReturn = query['callback'] + '({balance:' + balance + '})'

  logging.info("getBalance(" + address + "): " + mReturn)
  return mReturn

@bottle.route('/api/trading-doge')
@bottle.route('/api/trading-doge/')
@bottle.route('/api/trading-doge/<currency:re:[A-Z][A-Z][A-Z]>')
def tradingDOGE(currency='BTC'):
  response.content_type = 'application/json; charset=utf-8'

  mReturn = '{}'
  if (currency not in ['CNY', 'EUR', 'GBP', 'USD', 'LTC']):
    dogeCurrency = json.loads(memcache.get('trading_DOGE_' + currency))
    if (not dogeCurrency):
      logging.warn('No data found in memcache for trading_DOGE_' + currency)
      return mReturn
    else:
      mReturn = dogeCurrency['price']
  else:
    # For CNY, EUR, GBP, USD, LTC We have to convert from DOGE -> BTC -> FIAT
    dogeBtc = json.loads(memcache.get('trading_DOGE_BTC'))
    if (not dogeBtc):
      logging.warn("No data found in memcache for trading_DOGE_BTC")
      return mReturn

    btcCurrency = json.loads(memcache.get('trading_BTC_' + currency))
    if (not btcCurrency):
      logging.warn("No data found in memcache for trading_BTC_" + currency)
      return mReturn

    logging.info('dogeBtc: ' + str(dogeBtc) + ', btcCurrency: ' + str(btcCurrency))
    mReturn = Decimal(dogeBtc['price']) * Decimal(btcCurrency['price'])

  query = request.query.decode()
  if (len(query) > 0):
      mReturn = query['callback'] + '({price:' + str(mReturn) + '})'

  logging.info("tradingDOGE(" + currency + "): " + str(mReturn))
  return str(mReturn)

def trading_pair_data(currency1, currency2):
  data = None
  useBackupUrl = False

  try:
    if currency2 in ['CNY', 'EUR', 'GBP', 'USD', 'AUD']:
      data = bitcoinaverage_ticker(currency2)
    else:
      data = urlfetch.fetch(CCC_TRADE_PAIR_URL + currency1 + '_' + currency2, deadline=TIMEOUT_DEADLINE)
  except:
    logging.warn('Error retrieving ' + url)
    useBackupUrl = True
  finally:
    if (not useBackupUrl and (not data or not data.content or data.status_code != 200)):
      logging.warn('No content returned from ' + url)
      useBackupUrl = True

  return data, useBackupUrl

def trading_pair_data_fallback(currency1, currency2):
  data = None
  fallbackUrl = ''

  if (currency1 == 'BTC' and currency2 == 'LTC'):
    fallbackUrl = BTER_LTC_BTC_URL
  else:
    logging.error('Cannot get trading pair for ' + currency1 + ' / ' + currency2)
    return data, fallbackUrl, False

  logging.warn('Now trying ' + fallbackUrl + ' for trading pair for ' + currency1 + ' / ' + currency2)
  try:
    data = urlfetch.fetch(fallbackUrl, deadline=TIMEOUT_DEADLINE)
    if (not data or not data.content or data.status_code != 200):
      logging.error('No content returned from ' + fallbackUrl)
      return data, fallbackUrl, False
  except:
    logging.error('Error retrieving ' + fallbackUrl)
    return data, fallbackUrl, False

  return data, fallbackUrl, True

def load_data_dict(currency1, currency2, data, useFallbackUrl):
  dataDict = json.loads(data.content)

  if (currency1 == 'BTC' and currency2 in ['CNY', 'EUR', 'GBP', 'USD', 'AUD']):
    # standardize format of exchange rate data from different APIs (we will use 'price' as a key)
    dataDict['price'] = dataDict['last']
  elif (useFallbackUrl):
    if (currency1 == 'DOGE' and currency2 == 'BTC'):
      dataDict = {'price': dataDict[0]['last_price']}
    elif (currency1 == 'BTC' and currency2 == 'LTC'):
      price = str(Decimal(1) / Decimal(dataDict['last']))
      dataDict = {'price': price}
      logging.info('BTC_LTC: ' + price)
    elif (currency1 == 'BTC' and currency2 == 'USD'):
      if (dataDict['subtotal']['currency'] == 'USD'):
        dataDict = {'price': dataDict['subtotal']['amount']}
      else:
        logging.error('Unexpected JSON returned: ' + str(dataDict))
  else:
    logging.error('Error loading trading pair: ' + currency1 + '_' + currency2)

  return dataDict

def pullTradingPair(currency1='DOGE', currency2='BTC'):
  data, useFallbackUrl = trading_pair_data(currency1, currency2)

  if useFallbackUrl:
    data, fallbackUrl, success = trading_pair_data_fallback(currency1, currency2)
    if not success:
      return

  dataDict = load_data_dict(currency1, currency2, data, useFallbackUrl)

  tradingData = json.dumps(dataDict).strip('"')
  memcache.set('trading_' + currency1 + '_' + currency2, tradingData)
  logging.info('Stored in memcache for key trading_' + currency1 + '_' + currency2 + ': ' + tradingData)

@bottle.route('/tasks/pull-cryptocoincharts-data')
def pullCryptocoinchartsData():
  pullTradingPair('DOGE', 'BTC')
  pullTradingPair('BTC', 'USD')
  pullTradingPair('BTC', 'EUR')
  pullTradingPair('BTC', 'GBP')
  pullTradingPair('BTC', 'CNY')
  pullTradingPair('BTC', 'LTC')
  return "Done"

@bottle.error(404)
def error_404(error):
  """Return a custom 404 error."""
  return 'Sorry, Nothing at this URL.'
