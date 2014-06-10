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
TRADING_PAIR_URL = 'http://www.cryptocoincharts.info/v2/api/tradingPair/'
TIMEOUT_DEADLINE = 30 # seconds

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

    #data = urllib2.urlopen(BLOCKEXPLORER_URL + address)
    data = urlfetch.fetch(BLOCKEXPLORER_URL + address, deadline=TIMEOUT_DEADLINE)
    dataDict = json.loads(data.content)
    balance = json.dumps(dataDict)

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
    if (currency not in ['EUR', 'USD']):
        dogeCurrency = json.loads(memcache.get('trading_DOGE_' + currency))
        if (not dogeCurrency):
            logging.warn('No data found in memcache for trading_DOGE_' + currency)
            return mReturn
        else:
            mReturn = dogeCurrency['price']
    else:
        # For EUR, We have to convert from DOGE -> BTC -> EUR
        # Update: For USD, We now have to do the same, since the price isn't accurate from the API we're using
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
    #data = urllib2.urlopen(TRADING_PAIR_URL + currency1 + '_' + currency2)
    data = urlfetch.fetch(TRADING_PAIR_URL + currency1 + '_' + currency2, deadline=TIMEOUT_DEADLINE)
    dataDict = json.loads(data.content)

    tradingData = json.dumps(dataDict)
    memcache.set('trading_' + currency1 + '_' + currency2, tradingData)
    logging.info('Stored in memcache for key trading_' + currency1 + '_' + currency2 + ': ' + tradingData)

@bottle.route('/tasks/pull-cryptocoincharts-data')
def pullCryptocoinchartsData():
    pullTradingPair('DOGE', 'BTC')
    pullTradingPair('DOGE', 'LTC')
    pullTradingPair('DOGE', 'CNY')
    pullTradingPair('BTC', 'EUR')
    pullTradingPair('BTC', 'USD')
    return "Done"

@bottle.error(404)
def error_404(error):
  """Return a custom 404 error."""
  return 'Sorry, Nothing at this URL.'
