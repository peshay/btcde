[![Build Status](https://travis-ci.org/peshay/btcde.svg?branch=master)](https://travis-ci.org/peshay/btcde)
[![Codecov](https://codecov.io/gh/peshay/btcde/branch/master/graph/badge.svg)](https://codecov.io/gh/peshay/btcde/branch/master)
[![Scrutinizer](https://scrutinizer-ci.com/g/peshay/btcde/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/peshay/btcde/?branch=master)
[![Python version](https://img.shields.io/pypi/pyversions/btcde.svg)](https://pypi.python.org/pypi/btcde)
[![license](https://img.shields.io/github/license/peshay/btcde.svg)](https://github.com/peshay/btcde/blob/master/LICENSE)
[![Beerpay](https://beerpay.io/peshay/btcde/badge.svg?style=beer)](https://beerpay.io/peshay/btcde)

# btcde.py

A Python Module for the [Bitcoin.de Trading API](https://www.bitcoin.de/de/api/marketplace)

Requires: requests

## Install btcde.py

You can (not yet) install the btcde module via pip

    pip install btcde

## How to Use

This is an example how you can use it in a python script
```python
#! /usr/bin/env python
import btcde
# create a object for the connection settings
api_key = <YourAPIKey>
api_secret = <YourAPISecret>
conn = btcde.Connection(api_key, api_secret)
orderbook = btcde.showOrderbook(conn, 'buy')
print('API Credits Left: ' + str(orderbook.get('credits')))
orders = orderbook.get('orders')
for order in orders:
    print('Order ID: ' + str(order.get('order_id')) + '\tPrice: ' + str(order.get('price')) + ' EUR')
```
---
## API Methods

For more Details on the API Methods, please read [bitcoin.de API Documentation](https://www.bitcoin.de/de/api/tapi/v2/docu)
All mandatory parameters have to be passed to a function, all optional are resolved via ```**args```

#### showOrderbook(conn, OrderType, **args)

*API Credits Cost: 2*

#### createOrder(conn, OrderType, max_amount, price, **args)

*API Credits Cost: 1*

#### deleteOrder(conn, order_id)

*API Credits Cost: 2*

#### showMyOrders(conn, **args)

*API Credits Cost: 2*

#### showMyOrderDetails(conn, order_id)

*API Credits Cost: 2*

#### executeTrade(conn, order_id, OrderType, amount)

*API Credits Cost: 1*

#### showMyTrades(conn, **args)

*API Credits Cost: 3*

#### showMyTradeDetails(conn, trade_id)

*API Credits Cost: 3*

#### showAccountInfo(conn)

*API Credits Cost: 2*

#### showOrderbookCompact(conn)

*API Credits Cost: 3*

#### showPublicTradeHistory(conn, since_tid=None)

*API Credits Cost: 3*

#### showRates(conn)

*API Credits Cost: 3*

#### showAccountLedger(conn, **args)

*API Credits Cost: 3*

## Support on Beerpay
Hey dude! Help me out for a couple of :beers:!

[![Beerpay](https://beerpay.io/peshay/btcde/badge.svg?style=beer-square)](https://beerpay.io/peshay/btcde)  [![Beerpay](https://beerpay.io/peshay/btcde/make-wish.svg?style=flat-square)](https://beerpay.io/peshay/btcde?focus=wish)
