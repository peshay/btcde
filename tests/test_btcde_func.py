from unittest import TestCase
import hashlib
import hmac
import requests_mock
from mock import patch
import json
import btcde
from decimal import Decimal


@patch('btcde.log')
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

    def verifySignature(self, url, method, nonce, params):
        '''To verify API Signature.'''
        self.XAPINONCE = nonce
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

    def test_signature_post(self, mock_logger, m):
        '''Test signature on a post request.'''
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
                                                  'POST', self.conn.nonce,
                                                  params)
        self.assertEqual(request_signature, verified_signature)
        self.assertTrue(mock_logger.debug.called)

    def test_signature_get(self, mock_logger, m):
        '''Test signature on a get request.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur'}
        response = self.sampleData('showOrderbook_buy')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showOrderbook(params.get('type'),
                                params.get('trading_pair'))
        history = m.request_history
        request_signature = history[0].headers.get('X-API-SIGNATURE')
        verified_signature = self.verifySignature(self.conn.orderuri,
                                                  'GET', self.conn.nonce,
                                                  params)
        self.assertEqual(request_signature, verified_signature)
        self.assertTrue(mock_logger.debug.called)

    def test_signature_delete(self, mock_logger, m):
        '''Test signature on a delete request.'''
        order_id = 'A1234BC'
        trading_pair = 'btceur'
        m.delete(requests_mock.ANY, json={}, status_code=200)
        self.conn.deleteOrder(order_id, trading_pair)
        history = m.request_history
        request_signature = history[0].headers.get('X-API-SIGNATURE')
        url = self.conn.orderuri + "/" + order_id + "/" + trading_pair
        verified_signature = self.verifySignature(url, 'DELETE', self.conn.nonce, {})
        self.assertEqual(request_signature, verified_signature)
        self.assertTrue(mock_logger.debug.called)

    def test_show_orderbook(self, mock_logger, m):
        '''Test function showOrderbook.'''
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
        self.assertTrue(mock_logger.debug.called)

    def test_createOrder(self, mock_logger, m):
        '''Test function createOrder.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur',
                  'max_amount': '10',
                  'price': '10'}
        base_url = 'https://api.bitcoin.de/v2/orders'
        url_args = '?max_amount={}&price={}&trading_pair={}&type={}'\
                   .format(params.get('max_amount'),
                           params.get('price'),
                           params.get('trading_pair'),
                           params.get('type'))
        response = self.sampleData('createOrder')
        m.post(requests_mock.ANY, json=response, status_code=201)
        self.conn.createOrder(params.get('type'),
                              params.get('trading_pair'),
                              params.get('max_amount'),
                              params.get('price'))
        history = m.request_history
        self.assertEqual(history[0].method, "POST")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_deleteOrder(self, mock_logger, m):
        '''Test function deleteOrder.'''
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
        self.assertTrue(mock_logger.debug.called)

    def test_showMyOrders(self, mock_logger, m):
        '''Test function showMyOrders.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur'}
        base_url = 'https://api.bitcoin.de/v2/orders/my_own'
        url_args = '?trading_pair={}&type={}'\
                   .format(params.get('trading_pair'),
                           params.get('type'))
        response = self.sampleData('showMyOrders')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyOrders(type=params.get('type'),
                               trading_pair=params.get('trading_pair'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showMyOrderDetails(self, mock_logger, m):
        '''Test function showMyOrderDetails.'''
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
        self.assertTrue(mock_logger.debug.called)

    def test_executeTrade(self, mock_logger, m):
        '''Test function executeTrade.'''
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
        self.assertTrue(mock_logger.debug.called)

    def test_showMyTrades(self, mock_logger, m):
        '''Test function showMyTrades.'''
        base_url = 'https://api.bitcoin.de/v2/trades'
        url_args = ''
        response = self.sampleData('showMyTrades')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyTrades()
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showMyTrades_with_params(self, mock_logger, m):
        '''Test function showMyTrades with parameters.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur'}
        base_url = 'https://api.bitcoin.de/v2/trades'
        url_args = '?trading_pair={}&type={}'\
                   .format(params.get('trading_pair'),
                           params.get('type'))
        response = self.sampleData('showMyTrades')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyTrades(type=params.get('type'),
                               trading_pair=params.get('trading_pair'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showMyTradeDetails(self, mock_logger, m):
        '''Test function showMyTradeDetails.'''
        params = {'trade_id': '1337'}
        base_url = 'https://api.bitcoin.de/v2/trades'
        url_args = '/{}'.format(params.get('trade_id'))
        response = self.sampleData('showMyTradeDetails')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyTradeDetails(params.get('trade_id'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showAccountInfo(self, mock_logger, m):
        '''Test function showAccountInfo.'''
        base_url = 'https://api.bitcoin.de/v2/account'
        url_args = ''
        response = self.sampleData('showAccountInfo')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showAccountInfo()
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showOrderbookCompact(self, mock_logger, m):
        '''Test function showOrderbookCompact.'''
        params = {'trading_pair': 'btceur'}
        base_url = 'https://api.bitcoin.de/v2/orders/compact'
        url_args = '?trading_pair={}'.format(params.get('trading_pair'))
        response = self.sampleData('showOrderbookCompact')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showOrderbookCompact(params.get('trading_pair'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showPublicTradeHistory(self, mock_logger, m):
        '''Test function showPublicTradeHistory.'''
        params = {'trading_pair': 'btceur'}
        base_url = 'https://api.bitcoin.de/v2/trades/history'
        url_args = '?trading_pair={}'.format(params.get('trading_pair'))
        response = self.sampleData('showPublicTradeHistory')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showPublicTradeHistory(params.get('trading_pair'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showPublicTradeHistory_since(self, mock_logger, m):
        '''Test function showPublicTradeHistory with since_tid.'''
        params = {'trading_pair': 'btceur', 'since_tid': '123'}
        base_url = 'https://api.bitcoin.de/v2/trades/history'
        url_args = '?since_tid={}&trading_pair={}'.format(params.get('since_tid'),
                                                          params.get('trading_pair'))
        response = self.sampleData('showPublicTradeHistory')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showPublicTradeHistory(params.get('trading_pair'),
                                         since_tid=params.get('since_tid'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showRates(self, mock_logger, m):
        '''Test function showRates.'''
        params = {'trading_pair': 'btceur'}
        base_url = 'https://api.bitcoin.de/v2/rates'
        url_args = '?trading_pair={}'.format(params.get('trading_pair'))
        response = self.sampleData('showRates')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showRates(params.get('trading_pair'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showAccountLedger(self, mock_logger, m):
        '''Test function showAccountLedger.'''
        params = {'currency': 'btc'}
        base_url = 'https://api.bitcoin.de/v2/account/ledger'
        url_args = '?currency={}'.format(params.get('currency'))
        response = self.sampleData('showAccountLedger')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showAccountLedger(params.get('currency'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_allowed_pairs(self, mock_logger, m):
        '''Test the allowed trading pairs.'''
        i = 0
        for pair in ['btceur', 'bcheur', 'etheur', 'btgeur', 'bsveur']:
            params = {'trading_pair': pair}
            base_url = 'https://api.bitcoin.de/v2/rates'
            url_args = '?trading_pair={}'.format(params.get('trading_pair'))
            response = self.sampleData('showRates')
            m.get(requests_mock.ANY, json=response, status_code=200)
            self.conn.showRates(params.get('trading_pair'))
            history = m.request_history
            self.assertEqual(history[i].method, "GET")
            self.assertEqual(history[i].url, base_url + url_args)
            self.assertTrue(mock_logger.debug.called)
            i += 1

    def test_allowed_currency(self, mock_logger, m):
        '''Test the allowed currencies.'''
        i = 0
        for curr in ['btc', 'bch', 'eth', 'btg', 'bsv']:
            params = {'currency': curr}
            base_url = 'https://api.bitcoin.de/v2/account/ledger'
            url_args = '?currency={}'.format(params.get('currency'))
            response = self.sampleData('showAccountLedger')
            m.get(requests_mock.ANY, json=response, status_code=200)
            self.conn.showAccountLedger(params.get('currency'))
            history = m.request_history
            self.assertEqual(history[i].method, "GET")
            self.assertEqual(history[i].url, base_url + url_args)
            self.assertTrue(mock_logger.debug.called)
            i += 1

    def test_decimal_parsing(self, mock_logger, m):
        '''Test if the decimal parsing calculates correctly.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur',
                  'max_amount': 10,
                  'price': 1337}
        response = self.sampleData('showOrderbook_buy')
        m.get(requests_mock.ANY, json=response, status_code=200)
        data = self.conn.showOrderbook(params.get('type'),
                                       params.get('trading_pair'),
                                       price=params.get('price'))
        price = data.get('orders')[0].get('price')
        self.assertIsInstance(price, Decimal)
        self.assertEqual(price + Decimal('22.3'), Decimal('2232.2'))
        self.assertNotEqual(float(price) + float('22.3'), float('2232.2'))


class TestBtcdeExceptions(TestCase):
    '''Test for Exception Handling.'''

    def sampleData(self, file):
        '''Retrieve sample data from json files.'''
        filepath = 'tests/resources/{}.json'.format(file)
        data = json.load(open(filepath))
        return data

    def setUp(self):
        self.XAPIKEY = 'f00b4r'
        self.XAPISECRET = 'b4rf00'
        self.conn = btcde.Connection(self.XAPIKEY, self.XAPISECRET)
        self.XAPINONCE = self.conn.nonce

    def tearDown(self):
        del self.XAPIKEY
        del self.XAPISECRET
        del self.conn

    @requests_mock.Mocker()
    def test_dont_fail_on_non_utf8(self, m):
        '''Test if no exception raises with a non-utf8 response.
        https://github.com/peshay/btcde/issues/12'''
        filepath = 'tests/resources/NonUTF8'
        with open(filepath, 'r') as f:
            m.post(requests_mock.ANY, content=f.read().encode('utf-16', 'replace'), status_code=403)
        try:
            self.conn.executeTrade('foobar', 'buy', 'btceur', '0')
            self.assertTrue(True)
        except UnicodeDecodeError:
            self.assertTrue(False)

    @requests_mock.Mocker()
    def test_APIException(self, m):
        '''Test API Exception.'''
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
        response = self.sampleData('error')
        m.post(requests_mock.ANY, json=response, status_code=400)
        self.conn.createOrder(params.get('type'),
                              params.get('trading_pair'), params.get('max_amount'),
                              price=params.get('price'))
        history = m.request_history
        self.assertEqual(history[0].method, "POST")
        self.assertEqual(history[0].url, base_url + url_args)

    @patch('btcde.log')
    def test_RequestException(self, mock_logger):
        '''Test Requests Exception.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur',
                  'max_amount': 10,
                  'price': 13}
        self.conn.orderuri = 'https://foo.bar'
        self.conn.createOrder(params.get('type'),
                              params.get('trading_pair'), params.get('max_amount'),
                              price=params.get('price'))
        self.assertTrue(mock_logger.warning.called)

    def test_TradingPairValueException(self):
        '''Test wrong traiding_pair Value Exception.'''
        with self.assertRaises(ValueError) as context:
            self.conn.deleteOrder('123', 'usdeur')
        self.assertTrue('usdeur is not any of' in str(context.exception))

    def test_OrderTypeValueException(self):
        '''Test wrong type Value Exception.'''
        with self.assertRaises(ValueError) as context:
            self.conn.createOrder('fail', 'btceur', '100', '100')
        self.assertTrue('fail is not any of' in str(context.exception))

    def test_CurrencyValueException(self):
        '''Test wrong currency Value Exception.'''
        with self.assertRaises(ValueError) as context:
            self.conn.showAccountLedger('usd')
        self.assertTrue('usd is not any of' in str(context.exception))

    def test_BankSeatValueException(self):
        '''Test wrong seat_of_bank Value Exception.'''
        with self.assertRaises(ValueError) as context:
            self.conn.showOrderbook('buy', 'btceur', seat_of_bank='SZ')
        self.assertTrue('SZ is not any of' in str(context.exception))

    def test_TrustLevelValueException(self):
        '''Test wrong trust_level Value Exception.'''
        with self.assertRaises(ValueError) as context:
            self.conn.createOrder('buy', 'btceur', '100', '100',
                                   min_trust_level='foo')
        self.assertTrue('foo is not any of' in str(context.exception))

    def test_PaymentOptionValueException(self):
        '''Test wrong payment_option Value Exception.'''
        with self.assertRaises(ValueError) as context:
            self.conn.createOrder('buy', 'btceur', '100', '100',
                                   payment_option=4)
        self.assertTrue('4 is not any of' in str(context.exception))

    def test_OrderStateValueException(self):
        '''Test wrong state Value Exception.'''
        with self.assertRaises(ValueError) as context:
            self.conn.showMyOrders(state=1)
        self.assertTrue('1 is not any of' in str(context.exception))

    def test_TradeStateValueException(self):
        '''Test wrong state Value Exception.'''
        with self.assertRaises(ValueError) as context:
            self.conn.showMyTrades(state=-2)
        self.assertTrue('-2 is not any of' in str(context.exception))

    def test_UnknownKeyException(self):
        '''Test wrong Key Exception.'''
        with self.assertRaises(KeyError) as context:
            self.conn.showMyOrders(foo=4)
        self.assertTrue('foo is not any of' in str(context.exception))
