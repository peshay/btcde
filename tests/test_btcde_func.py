from unittest import TestCase
import hashlib
import hmac
import requests_mock
import json
import btcde


@requests_mock.Mocker()
class TestBtcdeAPIDocu(TestCase):
    '''Tests are as in bitcoin.de API documentation.
    https://www.bitcoin.de/de/api/tapi/v2/docu'''
    
    def sampleData(self, file):
        '''Retrieve sample data from json files.'''
        filepath = 'tests/resources/{}.json'.format(file)
        data = json.load(open(filepath))
        return data

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
        response = self.sampleData('createOrder')
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
        response = self.sampleData('showOrderbook_buy')
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
        response = self.sampleData('showOrderbook_buy')
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
        response = self.sampleData('createOrder')
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
        response = self.sampleData('deleteOrder')
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
        response = self.sampleData('showMyOrders')
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
        response = self.sampleData('showMyOrderDetails')
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
        response = self.sampleData('executeTrade')
        m.get(requests_mock.ANY, json=response, status_code=200)
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
        response = self.sampleData('showMyTrades')
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
        response = self.sampleData('showMyTrades')
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
        response = self.sampleData('showMyTradeDetails')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyTradeDetails(params.get('trade_id'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)

    def test_showAccountInfo(self, m):
        '''Test the function showAccountInfo.'''
        base_url = 'https://api.bitcoin.de/v2/account'
        url_args = ''
        response = self.sampleData('showAccountInfo')
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
        response = self.sampleData('showOrderbookCompact')
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
        response = self.sampleData('showPublicTradeHistory')
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
        response = self.sampleData('showRates')
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
        response = self.sampleData('showAccountLedger')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showAccountLedger(params.get('currency'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
