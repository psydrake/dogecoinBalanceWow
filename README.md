# Dogecoin Balance Wow

## About
Simple web / mobile app for checking the balance of your Dogecoin wallet address(es).

## Technical
Dogecoin Balance Wow consists of two parts:
* A pure HTML / CSS / JavaScript front end built with the [AngularJS](http://angularjs.org/) JavaScript framework.
* A [Google App Engine](https://developers.google.com/appengine/) back end, written in [Python](http://www.python.org/), that looks up wallet balance data from the [Dogecoin Blockchain](https://dogechain.info/chain/Dogecoin) and caches currency price data from the [cryptocoincharts.info](http://www.cryptocoincharts.info/) API.

The front end communicates with the back end via [JSONP](http://en.wikipedia.org/wiki/JSONP) calls. The backend polls cryptocoincharts.info every 10 minutes, and it stores this data in [memcache](https://developers.google.com/appengine/docs/python/memcache/) for all subsequent client requests, in order to reduce load on the CryptoCoinCharts server. Wallet balance lookups from the DogeChain [API](https://dogechain.info/chain/Dogecoin/q) occur on demand.

## Install On Your Device
* [Dogecoin Balance Wow for Android](https://play.google.com/store/apps/details?id=net.edrake.dogecoinbalancewow)
* [Dogecoin Balance Wow for Amazon Kindle Fire](http://www.amazon.com/Drake-Emko-KittehCoin-Balance/dp/B00IQN7P74)
* [Dogecoin Balance Wow for FirefoxOS](https://marketplace.firefox.com/app/dogecoin-balance-wow)
* [Dogecoin Balance Wow in the Chrome Web Store](https://chrome.google.com/webstore/detail/dogecoin-balance-wow/mbldbbdmcmpelfakglhfafgiopeepnob)
* [Dogecoin Balance Wow as a Web Site](http://d2kg4h6gsenx6a.cloudfront.net/main.html)

## Author
Drake Emko - drakee (a) gmail.com
* [@DrakeEmko](https://twitter.com/DrakeEmko)
* [Wolfgirl Band](http://wolfgirl.bandcamp.com/)
