#! /usr/bin/env python
"""Just me testing."""
import btcde

buyparams = {'type': 'buy',
             'max_amount': 5,
             'price': 1000.50
             }

showparams = {'type': 'buy',
              'amount': 5.3,
              'price': 1000.50
              }
api_key = 'a3bbe3fffae97de589331513dee818db'
api_secret = '32c0f3e88632f2adaf385e77017e5ff7e7acc901'
conn = btcde.Connection(api_key, api_secret)
# MyTrades = btcde.showMyTrades(conn)
# print (MyTrades)
# AccountInfo = btcde.showAccountInfo(conn)
# print (AccountInfo)
# OrderbookCompact = btcde.showOrderbookCompact(conn)
# print (OrderbookCompact)
# PublicTradeHistory = btcde.showPublicTradeHistory(conn)
# print (PublicTradeHistory)
# Rates = btcde.showRates(conn)
# print (Rates)
# AccountLedger = btcde.showAccountLedger(conn)
# print (AccountLedger)
# Orderbook = btcde.showOrderbook(conn, 'buy')
# print ('API Credits Left: %s') % Orderbook.get('credits')
# Orders = Orderbook.get('orders')
# for Order in Orders:
#     print ('Order ID: %s\tPrice: %s EUR') % (Order.get('order_id'),
#                                            Order.get('price'))
NewOrder = btcde.createOrder(conn, 'buy', 5, 900)
print (NewOrder)
# Credits = NewOrder.get('credits')
# Orders = OrderBook.get('orders')
# print ('%s Credits left') % Credits
# for order in Orders:
#    trading_info = order.get('trading_partner_information')
#    if trading_info.get('bank_name') == 'FIDOR BANK AG':
#        print ('Order ID: %s') % order.get('order_id')
#        print ('    Price: %s') % order.get('price')
#        print ('    Max Amount: %s') % order.get('max_amount')
