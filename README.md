[![Build Status](https://travis-ci.org/peshay/btcde.svg?branch=master)](https://travis-ci.org/peshay/btcde)
[![Codecov](https://codecov.io/gh/peshay/btcde/branch/master/graph/badge.svg)](https://codecov.io/gh/peshay/btcde/branch/master)
[![Scrutinizer](https://scrutinizer-ci.com/g/peshay/btcde/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/peshay/btcde/?branch=master)
[![Python version](https://img.shields.io/pypi/pyversions/btcde.svg)](https://pypi.python.org/pypi/btcde)
[![license](https://img.shields.io/github/license/peshay/btcde.svg)](https://github.com/peshay/btcde/blob/master/LICENSE)
[![Beerpay](https://beerpay.io/peshay/btcde/badge.svg?style=beer)](https://beerpay.io/peshay/btcde)

# btcde.py

API Wrapper for [Bitcoin.de Trading API](https://www.bitcoin.de/de/api/tapi/doc)

Requires: requests

## Install btcde.py

You can install the btcde module via pip

```bash
pip install btcde
```

## How to Use

This is an example how you can use it in a python script

```python
#! /usr/bin/env python
import btcde
# create a object for the connection settings
api_key = <YourAPIKey>
api_secret = <YourAPISecret>
conn = btcde.Connection(api_key, api_secret)
orderbook = conn.showOrderbook('buy', 'btceur')
print(f'API Credits Left: {orderbook["credits"]}')
orders = orderbook['orders']
for order in orders:
    print(f'Order ID: {order["order_id"]} \tPrice: {order["price"]} EUR')
```

---

## API Methods

For more Details on the API Methods, please read [bitcoin.de API Documentation](https://www.bitcoin.de/de/api/tapi/doc)

All mandatory parameters have to be passed to a function, all optional are resolved via ```**args```

Following Methodds are not yet implemented. If you like to get those implemented as well, please [join the development project for version 4.1](https://github.com/peshay/btcde/projects/5)

* Functions for Withdrawal
* Functions for Deposit
* Crypto-to-Crypto trades
* Websocket-API

### Addresspool

#### addToAddressPool(currency, address, **args)

* Required Parameters:
  * currency
  * address
* Optional Parameters:
  * amount_usages
  * comment

*API Credits Cost:* 2

#### removeFromAddressPool(currency, address)

* Required Parameters:
  * currency
  * address

*API Credits Cost:* 2

#### listAddressPool(currency)

* Required Parameters:
  * currency
  * address
* Optional Parameters:
  * usable
  * comment
  * page

*API Credits Cost:* 2

### Orders

#### showOrderbook(OrderType, trading_pair, **args)

* Required Parameters:
  * type
  * trading_pair
* Optional Parameters:
  * amount_currency_to_trade
  * price
  * order_requirements_fullfilled
  * only_kyc_full
  * only_express_orders
  * payment_option
  * sepa_option
  * only_same_bankgroup
  * only_same_bic
  * seat_of_bank
  * page_size

*API Credits Cost:* 2

#### showOrderDetails(trading_pair, order_id, **args)

* Required Parameters:
  * trading_pair
  * order_id

*API Credits Cost:* 2

#### createOrder(OrderType, trading_pair, max_amount_currency_to_trade, price, **args)

* Required Parameters:
  * type
  * trading_pair
  * max_amount_currency_to_trade
  * price
* Optional Parameters:
  * min_amount_currency_to_trade
  * end_datetime
  * new_order_for_remaining_amount
  * min_trust_level
  * only_kyc_full
  * payment_option
  * sepa_option
  * seat_of_bank

*API Credits Cost:* 1

#### deleteOrder(order_id, trading_pair)

* Required Parameters:
  * order_id
  * trading_pair

*API Credits Cost:* 2

#### showMyOrders(**args)

* Optional Parameters:
  * type
  * trading_pair
  * state
  * date_start
  * date_end
  * page

*API Credits Cost:* 2

#### showMyOrderDetails(trading_pair, order_id)

* Required Parameters:
  * trading_pair
  * order_id

*API Credits Cost:* 2

### Trades

#### executeTrade(order_id, OrderType, trading_pair, amount)

* Required Parameters:
  * order_id
  * type
  * trading_pair
  * amount_currency_to_trade
* Optional Parameters:
  * payment_option

*API Credits Cost:* 1

#### showMyTrades(**args)

* Optional Parameters:
  * type
  * trading_pair
  * state
  * only_trades_with_action_for_payment_or_transfer_required
  * payment_method
  * date_start
  * date_end
  * page

*API Credits Cost:* 3

#### showMyTradeDetails(trading_pair, trade_id)

* Required Parameters:
  * trade_id
  * trading_pair

*API Credits Cost:* 3

### miscellaneous

#### markCoinsAsTransferred(trading_pair, trade_id, amount_currency_to_trade_after_fee)

* Required Parameters:
  * trading_pair
  * trade_id
  * amount_currency_to_trade_after_fee

*API Credits Cost:* 1

#### markTradeAsPaid(trading_pair, trade_id, volume_currency_to_pay_after_fee)

* Required Parameters:
  * trading_pair
  * trade_id
  * volume_currency_to_pay_after_fee

*API Credits Cost:* 1

#### markCoinsAsReceived(trading_pair, trade_id, amount_currency_to_trade_after_fee, rating)

* Required Parameters:
  * trading_pair
  * trade_id
  * amount_currency_to_trade_after_fee
  * rating

*API Credits Cost:* 1

#### markTradeAsPaymentReceived(trading_pair, trade_id, volume_currency_to_pay_after_fee, rating, is_paid_from_correct_bank_account)

* Required Parameters:
  * trading_pair
  * trade_id
  * volume_currency_to_pay_after_fee
  * rating
  * is_paid_from_correct_bank_account

*API Credits Cost:* 1

#### addTradeRating(trading_pair, trade_id, rating)

* Required Parameters:
  * trading_pair
  * trade_id
  * rating

*API Credits Cost:* 1

#### showAccountInfo()

*API Credits Cost:* 2

#### showOrderbookCompact(trading_pair)

* Required Parameters:
  * trading_pair

*API Credits Cost:* 3

#### showPublicTradeHistory(trading_pair, **args)

* Required Parameters:
  * trading_pair
* Optional Parameters:
  * since_tid

*API Credits Cost:* 3

#### showRates(trading_pair)

* Required Parameters:
  * trading_pair

*API Credits Cost:* 3

#### showAccountLedger(currency, **args)

* Required Parameters:
  * currency
* Optional Parameters:
  * type
  * datetime_start
  * datetime_end
  * page

*API Credits Cost:* 3

#### showPermissions()

*API Credits Cost:* 2

### Deposit

#### requestDepositAddress

Not yet implemented!

#### showDeposit

Not yet implemented!

#### showDeposits

Not yet implemented!

### Withdrawal

#### createWithdrawal

Not yet implemented!

### deleteWithdrawal

Not yet implemented!

#### showWithdrawal

Not yet implemented!

#### showWithdrawalMinNetworkFee

Not yet implemented!

#### showWithdrawals

Not yet implemented!
