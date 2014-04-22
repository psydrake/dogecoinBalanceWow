# Dogecoin Balance Wow

## About
Simple web / mobile app for checking the balance of your Dogecoin wallet address(es).

## Technical
Dogecoin Balance Wow consists of two parts:
* A pure HTML / CSS / JavaScript front end built with the [AngularJS](http://angularjs.org/) JavaScript framework.
* A [Google App Engine](https://developers.google.com/appengine/) back end, written in [Python](http://www.python.org/), that looks up wallet balance data from the [Dogecoin Blockchain](https://dogechain.info/chain/Dogecoin) and caches currency price data from the [cryptocoincharts.info](http://www.cryptocoincharts.info/) API.

The front end communicates with the back end via [JSONP](http://en.wikipedia.org/wiki/JSONP) calls. The backend polls cryptocoincharts.info every 10 minutes, and it stores this data in [memcache](https://developers.google.com/appengine/docs/python/memcache/) for all subsequent client requests, in order to reduce load on the CryptoCoinCharts server. Wallet balance lookups from the DogeChain [API](https://dogechain.info/chain/Dogecoin/q) occur on demand.

## Install On Your Device
* [Android](https://play.google.com/store/apps/details?id=net.edrake.dogecoinbalancewow)
* [Amazon Kindle Fire](http://www.amazon.com/Drake-Emko-Dogecoin-Balance-Wow/dp/B00ISNBWEY)
* [Windows Phone](http://www.windowsphone.com/en-us/store/app/dogecoin-balance-wow/9e343cb7-3552-4f7f-9d88-0a0d87c05848)
* [Blackberry 10](http://appworld.blackberry.com/webstore/content/53031888/)
* [FirefoxOS](https://marketplace.firefox.com/app/dogecoin-balance-wow)
* [Chrome Web Store](https://chrome.google.com/webstore/detail/dogecoin-balance-wow/mbldbbdmcmpelfakglhfafgiopeepnob)
* [Browse As A Web Site](http://d2kg4h6gsenx6a.cloudfront.net/main.html)

## Author
Drake Emko - drakee (a) gmail.com
* [@DrakeEmko](https://twitter.com/DrakeEmko)
* [Wolfgirl Band](http://wolfgirl.bandcamp.com/)
