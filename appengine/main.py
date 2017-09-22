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
BTER_LTC_BTC_URL = 'http://data.bter.com/api/1/ticker/ltc_btc'
TIMEOUT_DEADLINE = 10 # seconds

def bitcoinaverage_ticker(currency):
  timestamp = int(time.time())
  payload = '{}.{}'.format(timestamp, config.bitcoinaverage_public_key)
  hex_hash = hmac.new(config.bitcoinaverage_secret_key.encode(), msg=payload.encode(), digestmod=hashlib.sha256).hexdigest()
  signature = '{}.{}'.format(payload, hex_hash)

  url = 'https://apiv2.bitcoinaverage.com/indices/global/ticker/BTC' + currency
  headers = {'X-Signature': signature}
  return urlfetch.fetch(url, headers=headers, deadline=TIMEOUT_DEADLINE)

def cryptopia_ticker(currency1, currency2):
  url = 'https://www.cryptopia.co.nz/api/GetMarket/' + currency1 + '_' + currency2
  return urlfetch.fetch(url, deadline=TIMEOUT_DEADLINE)

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
  data = None
  useBackupUrl = False

  url = BLOCKEXPLORER_URL + address
  try:
    data = urlfetch.fetch(url, deadline=TIMEOUT_DEADLINE)
    if (not data or not data.content or data.status_code != 200):
      logging.warn('No content returned from ' + url)
      useBackupUrl = True
    else:
      dataDict = json.loads(data.content)

  except Exception as e:
    logging.warn("Error: {0} retrieving data from {1}".format(e, url))
    useBackupUrl = True

  if (useBackupUrl):
    url = BLOCKEXPLORER_URL_BACKUP + address
    logging.warn('Now trying ' + url)
    data = urlfetch.fetch(url, deadline=TIMEOUT_DEADLINE)

    dataDict = json.loads(data.content)
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
  dataDict = None

  try:
    if currency2 in ['CNY', 'EUR', 'GBP', 'USD']:
      data = bitcoinaverage_ticker(currency2)
      if (not data or not data.content or data.status_code != 200):
        logging.error('No content returned for ' + currency1 + '_' + currency2)
        return None
      else:
        dataDict = json.loads(data.content)
        dataDict['price'] = dataDict['last']
    elif (currency1 == 'BTC' and currency2 == 'LTC'):
      data = urlfetch.fetch(BTER_LTC_BTC_URL, deadline=TIMEOUT_DEADLINE)
      if (not data or not data.content or data.status_code != 200):
        logging.error('No content returned from ' + BTER_LTC_BTC_URL)
        return None
      else:
        dataDict = json.loads(data.content)
        price = str(Decimal(1) / Decimal(dataDict['last']))
        dataDict['price'] = price
    else:
      data = cryptopia_ticker(currency1, currency2)
      if (not data or not data.content or data.status_code != 200):
        logging.error('No content returned for ' + currency1 + '_' + currency2)
        return None
      else:
        dataDict = json.loads(data.content)
        dataDict['price'] = dataDict['Data']['LastPrice']

  except Exception as e:
    logging.error("Error {0} retrieving data for trading pair {1}_{2}".format(e, currency1, currency2))
    return None

  return dataDict

def pullTradingPair(currency1='DOGE', currency2='BTC'):
  dataDict = trading_pair_data(currency1, currency2)
  if not dataDict:
    return

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
