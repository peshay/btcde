from unittest import TestCase
import hashlib
import hmac
import requests_mock
import btcde


@requests_mock.Mocker()
class TestBtcdeAPIDocu(TestCase):
    '''Tests are as in bitcoin.de API documentation.
    https://www.bitcoin.de/de/api/tapi/v2/docu'''

    def sortParams(self, url, params={}):
        '''To sort params for url string.'''
        self.encoded_string = ''
        if len(params) > 0:
            for key, value in sorted(params.items()):
                self.encoded_string += str(key) + '=' + str(value) + '&'
            self.encoded_string = self.encoded_string[:-1]
            self.url = url + '?' + self.encoded_string
        else:
            self.url = url
        return self.url, self.encoded_string

    def verifySignature(self, url, method, params):
        '''To verify API Signature.'''
        self.XAPINONCE += 1
        self.url, self.encoded_string = self.sortParams(url, params)
        if method == 'POST':
            md5_encoded_query_string = hashlib.md5(self.encoded_string.encode()
                                                   ).hexdigest()
        else:
            md5_encoded_query_string = hashlib.md5(b'').hexdigest()
        hmac_data = '{method}#{url}#{key}#{nonce}#{md5}'\
                    .format(method=method,
                            url=self.url,
                            key=self.XAPIKEY,
                            nonce=str(self.XAPINONCE),
                            md5=md5_encoded_query_string)
        hmac_signed = hmac.new(bytearray(self.XAPISECRET.encode()),
                               msg=hmac_data.encode(),
                               digestmod=hashlib.sha256).hexdigest()
        return hmac_signed

    def setUp(self):
        self.XAPIKEY = 'f00b4r'
        self.XAPISECRET = 'b4rf00'
        self.conn = btcde.Connection(self.XAPIKEY, self.XAPISECRET)
        self.XAPINONCE = self.conn.nonce

    def tearDown(self):
        del self.XAPIKEY
        del self.XAPISECRET
        del self.conn

    def test_signature_post(self, m):
        '''Test the signature on a post request.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur',
                  'max_amount': 10,
                  'price': 1337}
        response = {"order_id": "A1234BC",
                    "errors": [],
                    "credits": 8}
        m.post(requests_mock.ANY, json=response, status_code=201)
        self.conn.createOrder(params.get('type'),
                              params.get('trading_pair'),
                              params.get('max_amount'),
                              params.get('price'))
        history = m.request_history
        request_signature = history[0].headers.get('X-API-SIGNATURE')
        verified_signature = self.verifySignature(self.conn.orderuri,
                                                  'POST',
                                                  params)
        self.assertEqual(request_signature, verified_signature)

    def test_signature_get(self, m):
        '''Test the signature on a get request.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur'}
        response = {"orders":
                    {"order_id": "A1B2D3",
                     "trading_pair": "btceur", "type": "buy",
                     "max_amount": 0.5, "min_amount": 0.1,
                     "price": 230.55, "max_volume": 115.28,
                     "min_volume": 23.06,
                     "order_requirements_fullfilled": True,
                     "trading_partner_information":
                     {"username": "bla", "is_kyc_full": True,
                      "trust_level": "gold", "bank_name": "Sparkasse",
                      "bic": "HASPDEHHXXX", "seat_of_bank": "DE", "rating": 99,
                      "amount_trades": 52},
                     "order_requirements":
                     {"min_trust_level": "gold",
                      "only_kyc_full": True,
                      "seat_of_bank": ["DE", "NL"],
                      "payment_option": 1, }
                     }, "errors": [],
                    "credits": 12}
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showOrderbook(params.get('type'),
                                params.get('trading_pair'))
        history = m.request_history
        request_signature = history[0].headers.get('X-API-SIGNATURE')
        verified_signature = self.verifySignature(self.conn.orderuri,
                                                  'GET',
                                                  params)
        self.assertEqual(request_signature, verified_signature)

    def test_signature_delete(self, m):
        '''Test the signature on a delete request.'''
        order_id = 'A1234BC'
        trading_pair = 'btceur'
        m.delete(requests_mock.ANY, json={}, status_code=200)
        self.conn.deleteOrder(order_id, trading_pair)
        history = m.request_history
        request_signature = history[0].headers.get('X-API-SIGNATURE')
        url = self.conn.orderuri + "/" + order_id + "/" + trading_pair
        verified_signature = self.verifySignature(url, 'DELETE', {})
        self.assertEqual(request_signature, verified_signature)

    def test_show_orderbook(self, m):
        '''Test the function showOrderbook.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur',
                  'max_amount': 10,
                  'price': 1337}
        base_url = 'https://api.bitcoin.de/v2/orders'
        url_args = '?price={}&trading_pair={}&type={}'\
                   .format(params.get('price'),
                           params.get('trading_pair'),
                           params.get('type'))
        response = {
           "orders": {
               "order_id": "A1B2D3",
               "trading_pair": "btceur",
               "type": "buy",
               "max_amount": 0.5,
               "min_amount": 0.1,
               "price": 230.55,
               "max_volume": 115.28,
               "min_volume": 23.06,
               "order_requirements_fullfilled": True,
               "trading_partner_information": {
                   "username": "bla",
                   "is_kyc_full": True,
                   "trust_level": "gold",
                   "bank_name": "Sparkasse",
                   "bic": "HASPDEHHXXX",
                   "seat_of_bank": "DE",
                   "rating": 99,
                   "amount_trades": 52
               },
               "order_requirements": {
                   "min_trust_level": "gold",
                   "only_kyc_full": True,
                   "seat_of_bank": [
                       "DE",
                       "NL"
                   ],
                   "payment_option": 1,
               }
           },
           "errors": [

           ],
           "credits": 12
        }
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showOrderbook(params.get('type'),
                                params.get('trading_pair'),
                                price=params.get('price'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_createOrder(self, m):
        '''Test the function createOrder.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur',
                  'max_amount': 10,
                  'price': 13}
        base_url = 'https://api.bitcoin.de/v2/orders'
        url_args = '?max_amount={}&price={}&trading_pair={}&type={}'\
                   .format(params.get('max_amount'),
                           params.get('price'),
                           params.get('trading_pair'),
                           params.get('type'))
        response = {"order_id": "A1234BC",
                    "errors": [],
                    "credits": 8}
        m.post(requests_mock.ANY, json=response, status_code=201)
        self.conn.createOrder(params.get('type'),
                              params.get('trading_pair'), params.get('max_amount'),
                              price=params.get('price'))
        history = m.request_history
        self.assertEqual(history[0].method, "POST")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_deleteOrder(self, m):
        '''Test the function deleteOrder.'''
        params = {'trading_pair': 'btceur',
                  'order_id': '1337'}
        base_url = 'https://api.bitcoin.de/v2/orders'
        url_args = '/{}/{}'.format(params.get('order_id'),
                                   params.get('trading_pair'))
        response = {"errors": [],
                    "credits": 5}
        m.delete(requests_mock.ANY, json=response, status_code=200)
        self.conn.deleteOrder(params.get('order_id'),
                              params.get('trading_pair'))
        history = m.request_history
        self.assertEqual(history[0].method, "DELETE")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_showMyOrders(self, m):
        '''Test the function showMyOrders.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur',
                  'price': '1337'}
        base_url = 'https://api.bitcoin.de/v2/orders/my_own'
        url_args = '?price={}&trading_pair={}&type={}'\
                   .format(params.get('price'),
                           params.get('trading_pair'),
                           params.get('type'))
        response = {"orders":
                    [
                     {
                       "order_id": "2EDYNS",
                       "trading_pair": "btceur",
                       "type": "sell",
                       "max_amount": 0.5,
                       "min_amount": 0.2,
                       "price": 250.55,
                       "max_volume": 125.28,
                       "min_volume": 50.11,
                       "end_datetime": "2015-01-20T15:00:00+02:00",
                       "new_order_for_remaining_amount": True,
                       "state": 0,
                       "order_requirements":
                       {
                          "min_trust_level": "silver",
                          "only_kyc_full": True,
                          "payment_option": 1,
                          "seat_of_bank": "NL"
                       },
                       "created_at": "2015-01-10T15:00:00+02:00",
                      },
                    ],
                    "page": {
                        "current": 1,
                        "last": 2
                    },
                    "errors": [],
                    "credits": 15
                    }
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyOrders(type=params.get('type'),
                               trading_pair=params.get('trading_pair'),
                               price=params.get('price'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_showMyOrderDetails(self, m):
        '''Test the function showMyOrderDetails.'''
        params = {'order_id': '1337'}
        base_url = 'https://api.bitcoin.de/v2/orders/{}'\
                   .format(params.get('order_id'))
        url_args = ''
        response = {"order":
                    {
                        "order_id": "2EDYNS",
                        "trading_pair": "btceur",
                        "type": "sell",
                        "max_amount": 0.5,
                        "min_amount": 0.2,
                        "price": 250.55,
                        "max_volume": 125.28,
                        "min_volume": 50.11,
                        "end_datetime": "2015-01-20T15:00:00+02:00",
                        "new_order_for_remaining_amount": True,
                        "state": 0,
                        "order_requirements":
                        {
                            "min_trust_level": "silver",
                            "only_kyc_full": True,
                            "payment_option": 1,
                            "seat_of_bank": "DE"
                        },
                        "created_at": "2015-01-10T15:00:00+02:00"
                     },
                    "errors": [],
                    "credits": 15
                    }
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyOrderDetails(params.get('order_id'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_executeTrade(self, m):
        '''Test the function executeTrade.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur',
                  'amount': '10',
                  'order_id': '1337'}
        base_url = 'https://api.bitcoin.de/v2/trades/{}'\
                   .format(params.get('order_id'))
        url_args = '?amount={}&order_id={}&trading_pair={}&type={}'\
                   .format(params.get('amount'),
                           params.get('order_id'),
                           params.get('trading_pair'),
                           params.get('type'))
        response = {"errors": [],
                    "credits": 8}
        m.post(requests_mock.ANY, json=response, status_code=201)
        self.conn.executeTrade(params.get('order_id'),
                               params.get('type'),
                               params.get('trading_pair'),
                               params.get('amount'))
        history = m.request_history
        self.assertEqual(history[0].method, "POST")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_showMyTrades(self, m):
        '''Test the function showMyTrades.'''
        base_url = 'https://api.bitcoin.de/v2/trades'
        url_args = ''
        response = {"order":
                    {
                        "order_id": "2EDYNS",
                        "trading_pair": "btceur",
                        "type": "sell",
                        "max_amount": 0.5,
                        "min_amount": 0.2,
                        "price": 250.55,
                        "max_volume": 125.28,
                        "min_volume": 50.11,
                        "end_datetime": "2015-01-20T15:00:00+02:00",
                        "new_order_for_remaining_amount": True,
                        "state": 0,
                        "order_requirements":
                        {
                           "min_trust_level": "silver",
                           "only_kyc_full": True,
                           "payment_option": 1,
                           "seat_of_bank": "DE"
                        },
                        "created_at": "2015-01-10T15:00:00+02:00"
                    },
                    "errors": [],
                    "credits": 15
                    }
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyTrades()
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_showMyTrades_with_params(self, m):
        '''Test the function showMyTrades with parameters.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur'}
        base_url = 'https://api.bitcoin.de/v2/trades'
        url_args = '?trading_pairs={}&type={}'\
                   .format(params.get('trading_pairs'),
                           params.get('type'))
        response = {"order":
                    {
                        "order_id": "2EDYNS",
                        "trading_pair": "btceur",
                        "type": "sell",
                        "max_amount": 0.5,
                        "min_amount": 0.2,
                        "price": 250.55,
                        "max_volume": 125.28,
                        "min_volume": 50.11,
                        "end_datetime": "2015-01-20T15:00:00+02:00",
                        "new_order_for_remaining_amount": True,
                        "state": 0,
                        "order_requirements":
                        {
                           "min_trust_level": "silver",
                           "only_kyc_full": True,
                           "payment_option": 1,
                           "seat_of_bank": "DE"
                        },
                        "created_at": "2015-01-10T15:00:00+02:00"
                    },
                    "errors": [],
                    "credits": 15
                    }
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyTrades(type=params.get('type'),
                               trading_pairs=params.get('trading_pairs'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_showMyTradeDetails(self, m):
        '''Test the function showMyTradeDetails.'''
        params = {'trade_id': '1337'}
        base_url = 'https://api.bitcoin.de/v2/trades'
        url_args = '/{}'.format(params.get('trade_id'))
        response = {"trade":
                    {
                        "trade_id": "2EDYNS",
                        "trading_pair": "btceur",
                        "type": "sell",
                        "amount": 0.5,
                        "price": 250.55,
                        "volume": 125.28,
                        "fee_eur": 0.6,
                        "fee_btc": 0.0025,
                        "fee_currency": 0.0025,
                        "new_trade_id_for_remaining_amount": "C4Y8HD",
                        "state": 1,
                        "my_rating_for_trading_partner": "positive",
                        "trading_partner_information":
                        {
                           "username": "testuser",
                           "is_kyc_full": True,
                           "bank_name": "sparkasse",
                           "bic": "HASPDEHHXXX",
                           "rating": 99,
                           "amount_trades": 42,
                           "trust_level": "gold",
                           "seat_of_bank": "DE",
                        },
                        "payment_method": 1,
                        "created_at": "2015-01-10T15:00:00+02:00",
                        "successfully_finished_at":
                        "2015-01-10T15:00:00+02:00",
                    },
                    "errors": [],
                    "credits": 15,
                    }
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyTradeDetails(params.get('trade_id'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_showAccountInfo(self, m):
        '''Test the function showAccountInfo.'''
        base_url = 'https://api.bitcoin.de/v2/account'
        url_args = ''
        response = {"errors": [],
                    "credits": 5}
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showAccountInfo()
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_showOrderbookCompact(self, m):
        '''Test the function showOrderbookCompact.'''
        params = {'trading_pair': 'btceur'}
        base_url = 'https://api.bitcoin.de/v2/orders/compact'
        url_args = '?trading_pair={}'.format(params.get('trading_pair'))
        response = {"errors": [],
                    "credits": 5}
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showOrderbookCompact(params.get('trading_pair'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_showPublicTradeHistory(self, m):
        '''Test the function showPublicTradeHistory.'''
        params = {'trading_pair': 'btceur'}
        base_url = 'https://api.bitcoin.de/v2/trades/history'
        url_args = '?trading_pair={}'.format(params.get('trading_pair'))
        response = {"trading_pair": "btceur",
                    "trades": [
                         {
                             "date": 1435922625,
                             "price": 230,
                             "amount": "2.50000000",
                             "tid": 1252020
                         },
                         {
                             "date": 1435922655,
                             "price": 200.1,
                             "amount": "0.60000000",
                             "tid": 1252023
                         }
                     ],
                    "errors": [],
                    "credits": 19
                    }
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showPublicTradeHistory(params.get('trading_pair'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_showRates(self, m):
        '''Test the function showRates.'''
        params = {'trading_pair': 'btceur'}
        base_url = 'https://api.bitcoin.de/v2/rates'
        url_args = '?trading_pair={}'.format(params.get('trading_pair'))
        response = {"trading_pair": "btceur",
                    "rates": {
                           "rate_weighted": "257.3999269",
                           "rate_weighted_3h": "258.93994247",
                           "rate_weighted_12h": "255.30363219"
                      },
                    "errors": [],
                    "credits": 19
                    }
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showRates(params.get('trading_pair'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_showAccountLedger(self, m):
        '''Test the function showAccountLedger.'''
        params = {'currency': 'btceur'}
        base_url = 'https://api.bitcoin.de/v2/account/ledger'
        url_args = '?currency={}'.format(params.get('currency'))
        response = {"trading_pair": "btceur",
                    "rates": {
                           "rate_weighted": "257.3999269",
                           "rate_weighted_3h": "258.93994247",
                           "rate_weighted_12h": "255.30363219"
                      },
                    "errors": [],
                    "credits": 19
                    }
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showAccountLedger(params.get('currency'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
