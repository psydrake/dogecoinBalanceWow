"""Main.py is the top level script.

Loads the Bottle framework and mounts controllers.  Also adds a custom error
handler.
"""

from google.appengine.api import memcache, urlfetch
# import the Bottle framework
from server.lib.bottle import Bottle, request, response, template
import json, logging, StringIO, urllib2
from decimal import *

# TODO: name and list your controllers here so their routes become accessible.
from server.controllers import RESOURCE_NAME_controller

BLOCKEXPLORER_URL = 'http://dogechain.info/chain/Dogecoin/q/addressbalance/'
BLOCKEXPLORER_URL_BACKUP = 'https://chain.so/api/v2/get_address_balance/doge/'
TRADING_PAIR_URL = 'http://api.cryptocoincharts.info/tradingPair/'
TRADING_PAIR_URL_BTC_BACKUP="https://api.mintpal.com/v1/market/stats/DOGE/"
TRADING_PAIR_URL_USD_BACKUP = 'https://coinbase.com/api/v1/prices/buy' 
# TRADING_PAIR_URL_FIAT_BACKUP = 'http://api.bitcoincharts.com/v1/markets.json'
BTCAVERAGE_URL = 'https://api.bitcoinaverage.com/ticker/' # used for BTC / (CNY, GBP, EUR, AUD)
BTER_LTC_BTC_URL = 'http://data.bter.com/api/1/ticker/ltc_btc'

TIMEOUT_DEADLINE = 12 # seconds

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
    except:
        logging.warn('Error retrieving ' + url)
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
    if (currency not in ['CNY', 'EUR', 'GBP', 'USD', 'LTC', 'AUD']):
        dogeCurrency = json.loads(memcache.get('trading_DOGE_' + currency))
        if (not dogeCurrency):
            logging.warn('No data found in memcache for trading_DOGE_' + currency)
            return mReturn
        else:
            mReturn = dogeCurrency['price']
    else:
        # For CNY, EUR, GBP, USD, AUD We have to convert from DOGE -> BTC -> FIAT
        # UPDATE: now also for LTC
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

def pullTradingPair(currency1='DOGE', currency2='BTC'):
    url = BTCAVERAGE_URL + currency2 + '/' if currency2 in ['CNY', 'EUR', 'GBP', 'USD', 'LTC', 'AUD'] else TRADING_PAIR_URL + currency1 + '_' + currency2
    data = None
    useBackupUrl = False

    try:
        data = urlfetch.fetch(url, deadline=TIMEOUT_DEADLINE)
        if (not data or not data.content or data.status_code != 200):
            logging.warn('No content returned from ' + url)
            useBackupUrl = True
    except:
        logging.warn('Error retrieving ' + url)
        useBackupUrl = True

    if (useBackupUrl):
        backupUrl = ''
        if (currency1 == 'DOGE' and currency2 == 'BTC'):
            backupUrl = TRADING_PAIR_URL_BTC_BACKUP + currency2
        elif (currency1 == 'BTC' and currency2 == 'LTC'):
            backupUrl = BTER_LTC_BTC_URL
        elif (currency1 == 'BTC' and currency2 == 'USD'):
            backupUrl = TRADING_PAIR_URL_USD_BACKUP
        else:
            logging.error('Cannot get trading pair for ' + currency1 + ' / ' + currency2)
            return

        logging.warn('Now trying ' + backupUrl)
        data = urlfetch.fetch(backupUrl, deadline=TIMEOUT_DEADLINE)

    dataDict = json.loads(data.content)
    if (currency1 == 'BTC' and currency2 in ['CNY', 'EUR', 'GBP', 'USD', 'AUD']):
        # standardize format of exchange rate data from different APIs (we will use 'price' as a key)
        dataDict['price'] = dataDict['last'] 

    if (useBackupUrl):
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
                logging.error('Unexpected JSON returned from URL ' + TRADING_PAIR_URL_USD_BACKUP)
        else:
            logging.error('Error loading trading pair from ' + url)

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
    #pullTradingPair('BTC', 'AUD')
    return "Done"

@bottle.error(404)
def error_404(error):
  """Return a custom 404 error."""
  return 'Sorry, Nothing at this URL.'
