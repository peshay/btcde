from unittest import TestCase
import hashlib
import hmac
import requests_mock
from mock import patch
import json
import btcde
from decimal import Decimal
from mock import patch
from unittest.mock import patch


from urllib.parse import urlencode

@patch('btcde.log')
@requests_mock.Mocker()
class TestBtcdeAPIDocu(TestCase):
    '''Tests are as in bitcoin.de API documentation.
    https://www.bitcoin.de/de/api/tapi/doc'''

    def sampleData(self, file):
        '''Retrieve sample data from json files.'''
        filepath = 'tests/resources/{}.json'.format(file)
        data = json.load(open(filepath))
        return data

    def sortParams(self, url, params={}):
        '''To sort params for url string.'''
        self.encoded_string = ''
        if len(params) > 0:
            self.encoded_string = urlencode(params)
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
        hmac_data = '#'.join([method, self.url, self.XAPIKEY,
                             str(self.XAPINONCE), md5_encoded_query_string])
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
        trading_pair = 'btceur'
        params = {'max_amount_currency_to_trade': 10,
                  'price': 1337,
                  'type': 'buy'}
        response = self.sampleData('createOrder')
        m.post(requests_mock.ANY, json=response, status_code=201)
        self.conn.createOrder(params['type'], trading_pair,
                              params['max_amount_currency_to_trade'], params['price'])
        history = m.request_history
        request_signature = history[0].headers.get('X-API-SIGNATURE')
        url = f'https://api.bitcoin.de/v4/{trading_pair}/orders'
        verified_signature = self.verifySignature(url, 'POST',
                                                  self.conn.nonce, params)
        self.assertEqual(request_signature, verified_signature)
        self.assertTrue(mock_logger.debug.called)

    def test_signature_get(self, mock_logger, m):
        '''Test signature on a get request.'''
        trading_pair = 'btceur'
        params = { 'type': 'buy' }
        response = self.sampleData('showOrderbook_buy')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showOrderbook(params.get('type'), trading_pair)
        history = m.request_history
        request_signature = history[0].headers.get('X-API-SIGNATURE')
        url = f'https://api.bitcoin.de/v4/{trading_pair}/orderbook'
        verified_signature = self.verifySignature(url, 'GET',
                                                  self.conn.nonce, params)
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
        url = f'https://api.bitcoin.de/v4/{trading_pair}/orders/{order_id}'
        verified_signature = self.verifySignature(url, 'DELETE', self.conn.nonce, {})
        self.assertEqual(request_signature, verified_signature)
        self.assertTrue(mock_logger.debug.called)

    def test_add_to_address_pool(self, mock_logger, m):
        '''Test function addToAddressPool.'''
        currency = 'dash'
        params = { 'address': '1337',
                   'amount_usages': 3,
                   'comment': 'foobar' }
        base_url = f'https://api.bitcoin.de/v4/{currency}/address'
        url_args = '?' + urlencode(params)
        response = self.sampleData('minimal')
        m.post(requests_mock.ANY, json=response, status_code=201)
        self.conn.addToAddressPool(currency, params['address'],
                                   amount_usages=params['amount_usages'],
                                   comment=params['comment'])
        history = m.request_history
        self.assertEqual(history[0].method, "POST")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_list_address_pool(self, mock_logger, m):
        '''Test function listAddressPool.'''
        currency = 'dash'
        params = { "comment": "foobar",
                   "page": 3,
                   "usable": 1 }
        base_url = f'https://api.bitcoin.de/v4/{currency}/address'
        url_args = '?' + urlencode(params)
        response = self.sampleData('listAddressPool')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.listAddressPool(currency, usable=params['usable'],
                                  comment=params['comment'], page=params['page'])
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_remove_from_address_pool(self, mock_logger, m):
        '''Test function removeFromAddressPool.'''
        currency = 'dash'
        address = '1337'
        base_url = f'https://api.bitcoin.de/v4/{currency}/address/{address}'
        response = self.sampleData('minimal')
        m.delete(requests_mock.ANY, json=response, status_code=200)
        self.conn.removeFromAddressPool(currency, address)
        history = m.request_history
        self.assertEqual(history[0].method, "DELETE")
        self.assertEqual(history[0].url, base_url)
        self.assertTrue(mock_logger.debug.called)

    def test_show_orderbook(self, mock_logger, m):
        '''Test function showOrderbook.'''
        trading_pair = 'btceur'
        params = {'price': 1337,
                  'type': 'buy'}
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/orderbook'
        url_args = '?' + urlencode(params)
        response = self.sampleData('showOrderbook_buy')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showOrderbook(params['type'],
                                trading_pair,
                                price=params['price'])
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showOrderDetails(self, mock_logger, m):
        '''Test function showOrderDetails.'''
        params = {'trading_pair': 'btceur',
                  'order_id': '1337'}
        base_url = (f'https://api.bitcoin.de/v4/{params["trading_pair"]}'
                   f'/orders/public/details/{params["order_id"]}')
        response = self.sampleData('showOrderDetails')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showOrderDetails(params['trading_pair'], params['order_id'])
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url)
        self.assertTrue(mock_logger.debug.called)

    def test_createOrder(self, mock_logger, m):
        '''Test function createOrder.'''
        trading_pair = 'btceur'
        params = {'max_amount_currency_to_trade': '10',
                  'price': '10',
                  'type': 'buy'
                  }
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/orders'
        url_args = '?' + urlencode(params)
        response = self.sampleData('createOrder')
        m.post(requests_mock.ANY, json=response, status_code=201)
        self.conn.createOrder(params['type'],
                              trading_pair,
                              params['max_amount_currency_to_trade'],
                              params['price'])
        history = m.request_history
        self.assertEqual(history[0].method, "POST")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_deleteOrder(self, mock_logger, m):
        '''Test function deleteOrder.'''
        trading_pair = 'btceur'
        order_id = '1337'
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/orders/{order_id}'
        response = self.sampleData('minimal')
        m.delete(requests_mock.ANY, json=response, status_code=200)
        self.conn.deleteOrder(order_id, trading_pair)
        history = m.request_history
        self.assertEqual(history[0].method, "DELETE")
        self.assertEqual(history[0].url, base_url)
        self.assertTrue(mock_logger.debug.called)

    def test_showMyOrders(self, mock_logger, m):
        '''Test function showMyOrders.'''
        trading_pair = 'btceur'
        params = { 'type': 'buy' }
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/orders'
        url_args = '?' + urlencode(params)
        response = self.sampleData('showMyOrders')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyOrders(type=params.get('type'),
                               trading_pair=trading_pair)
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showMyOrderDetails(self, mock_logger, m):
        '''Test function showMyOrderDetails.'''
        trading_pair = 'btceur'
        order_id = '1337'
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/orders/{order_id}'
        response = self.sampleData('showMyOrderDetails')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyOrderDetails(trading_pair, order_id)
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url)
        self.assertTrue(mock_logger.debug.called)

    def test_executeTrade(self, mock_logger, m):
        '''Test function executeTrade.'''
        trading_pair = 'btceur'
        order_id = '1337'
        params = {'amount_currency_to_trade': '10',
                  'type': 'buy'}
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/trades/{order_id}'
        url_args = '?' + urlencode(params)
        response = self.sampleData('minimal')
        m.post(requests_mock.ANY, json=response, status_code=201)
        self.conn.executeTrade(trading_pair,
                               order_id,
                               params['type'],
                               params['amount_currency_to_trade'])
        history = m.request_history
        self.assertEqual(history[0].method, "POST")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showMyTrades(self, mock_logger, m):
        '''Test function showMyTrades.'''
        base_url = 'https://api.bitcoin.de/v4/trades'
        response = self.sampleData('showMyTrades')
        m.get(requests_mock.ANY, json=response, status_code=200)
        history = m.request_history
        # Test with trading pair
        self.conn.showMyTrades()
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url)
        self.assertTrue(mock_logger.debug.called)

    def test_showMyTrades_with_params(self, mock_logger, m):
        '''Test function showMyTrades with parameters.'''
        trading_pair = 'btceur'
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/trades'
        response = self.sampleData('showMyTrades')
        m.get(requests_mock.ANY, json=response, status_code=200)
        history = m.request_history
        # Test again without trading pair, but parameter
        params = {'type': 'buy'}
        url_args = '?' + urlencode(params)
        self.conn.showMyTrades(type=params['type'], trading_pair=trading_pair)
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showMyTradeDetails(self, mock_logger, m):
        '''Test function showMyTradeDetails.'''
        trading_pair = 'btceur'
        trade_id = '1337'
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/trades/{trade_id}'
        response = self.sampleData('showMyTradeDetails')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showMyTradeDetails(trading_pair, trade_id)
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url)
        self.assertTrue(mock_logger.debug.called)

    def test_markCoinsAsTransferred(self, mock_logger, m):
        '''Test function markCoinsAsTransferred.'''
        trading_pair = 'btceur'
        trade_id = '1337'
        params = { 'amount_currency_to_trade_after_fee': 0.1337}
        url_args = '?' + urlencode(params)
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/trades/{trade_id}/mark_coins_as_transferred'
        response = self.sampleData('markCoinsAsTransferred')
        m.post(requests_mock.ANY, json=response, status_code=200)
        self.conn.markCoinsAsTransferred(trading_pair, trade_id, params['amount_currency_to_trade_after_fee'])
        history = m.request_history
        self.assertEqual(history[0].method, "POST")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_markTradeAsPaid(self, mock_logger, m):
        '''Test function markTradeAsPaid.'''
        trading_pair = 'btceur'
        trade_id = '1337'
        params = { 'volume_currency_to_pay_after_fee': 0.1337}
        url_args = '?' + urlencode(params)
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/trades/{trade_id}/mark_trade_as_paid'
        response = self.sampleData('markCoinsAsTransferred')
        m.post(requests_mock.ANY, json=response, status_code=200)
        self.conn.markTradeAsPaid(trading_pair, trade_id, params['volume_currency_to_pay_after_fee'])
        history = m.request_history
        self.assertEqual(history[0].method, "POST")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_markCoinsAsReceived(self, mock_logger, m):
        '''Test function markCoinsAsReceived.'''
        trading_pair = 'btceur'
        trade_id = '1337'
        params = { 'amount_currency_to_trade_after_fee': 0.1337, 'rating': 'positive'}
        url_args = '?' + urlencode(params)
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/trades/{trade_id}/mark_coins_as_received'
        response = self.sampleData('markCoinsAsTransferred')
        m.post(requests_mock.ANY, json=response, status_code=200)
        self.conn.markCoinsAsReceived(trading_pair, trade_id,
                                      params['amount_currency_to_trade_after_fee'],
                                      params['rating'])
        history = m.request_history
        self.assertEqual(history[0].method, "POST")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_markTradeAsPaymentReceived(self, mock_logger, m):
        '''Test function markTradeAsPaymentReceived.'''
        trading_pair = 'btceur'
        trade_id = '1337'
        params = { 'is_paid_from_correct_bank_account': True, 'rating': 'positive',
                   'volume_currency_to_pay_after_fee': 0.1337 }
        url_args = '?' + urlencode(params)
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/trades/{trade_id}/mark_trade_as_payment_received'
        response = self.sampleData('markCoinsAsTransferred')
        m.post(requests_mock.ANY, json=response, status_code=200)
        self.conn.markTradeAsPaymentReceived(trading_pair, trade_id,
                                      params['volume_currency_to_pay_after_fee'],
                                      params['rating'],
                                      params['is_paid_from_correct_bank_account'])
        history = m.request_history
        self.assertEqual(history[0].method, "POST")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_addTradeRating(self, mock_logger, m):
        '''Test function addTradeRating.'''
        trading_pair = 'btceur'
        trade_id = '1337'
        params = { 'rating': 'positive' }
        url_args = '?' + urlencode(params)
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/trades/{trade_id}/add_trade_rating'
        response = self.sampleData('markCoinsAsTransferred')
        m.post(requests_mock.ANY, json=response, status_code=200)
        self.conn.addTradeRating(trading_pair, trade_id, params['rating'])
        history = m.request_history
        self.assertEqual(history[0].method, "POST")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showAccountInfo(self, mock_logger, m):
        '''Test function showAccountInfo.'''
        base_url = 'https://api.bitcoin.de/v4/account'
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
        trading_pair = 'btceur'
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/orderbook/compact'
        response = self.sampleData('showOrderbookCompact')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showOrderbookCompact(trading_pair)
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url)
        self.assertTrue(mock_logger.debug.called)

    def test_showPublicTradeHistory(self, mock_logger, m):
        '''Test function showPublicTradeHistory.'''
        trading_pair = 'btceur'
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/trades/history'
        response = self.sampleData('showPublicTradeHistory')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showPublicTradeHistory(trading_pair)
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url)
        self.assertTrue(mock_logger.debug.called)

    def test_showPublicTradeHistory_since(self, mock_logger, m):
        '''Test function showPublicTradeHistory with since_tid.'''
        trading_pair = 'btceur'
        params = {'since_tid': '123'}
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/trades/history'
        url_args = '?' + urlencode(params)
        response = self.sampleData('showPublicTradeHistory')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showPublicTradeHistory(trading_pair, since_tid=params.get('since_tid'))
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showRates(self, mock_logger, m):
        '''Test function showRates.'''
        trading_pair = 'btceur'
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/rates'
        response = self.sampleData('showRates')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showRates(trading_pair)
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url)
        self.assertTrue(mock_logger.debug.called)

    def test_showAccountLedger(self, mock_logger, m):
        '''Test function showAccountLedger.'''
        currency = 'btc'
        params = {'type': 'all'}
        url_args = '?' + urlencode(params)
        base_url = f'https://api.bitcoin.de/v4/{currency}/account/ledger'
        response = self.sampleData('showAccountLedger')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showAccountLedger(currency, type=params['type'])
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_showPermissions(self, mock_logger, m):
        '''Test function showPermissions.'''
        base_url = f'https://api.bitcoin.de/v4/permissions'
        response = self.sampleData('showPermissions')
        m.get(requests_mock.ANY, json=response, status_code=200)
        self.conn.showPermissions()
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url)
        self.assertTrue(mock_logger.debug.called)

    def test_urlEncoding(self, mock_logger, m):
        '''Test URL encoding on parameters.'''
        currency = 'btc'
        params = {'datetime_start': '2018-01-01T01:00:00+01:00'}
        base_url = f'https://api.bitcoin.de/v4/{currency}/account/ledger'
        url_args = '?' + urlencode(params)
        response = self.sampleData('showAccountLedger')
        m.get(requests_mock.ANY, json=response, status_code=200)
        r = self.conn.showAccountLedger(currency, datetime_start="2018-01-01T01:00:00+01:00")
        history = m.request_history
        self.assertEqual(history[0].method, "GET")
        self.assertEqual(history[0].url, base_url + url_args)
        self.assertTrue(mock_logger.debug.called)

    def test_allowed_pairs(self, mock_logger, m):
        '''Test the allowed trading pairs.'''
        i = 0
        for pair in ['btceur', 'bcheur', 'etheur', 'btgeur', 'bsveur', 'ltceur',
                     'iotabtc', 'dashbtc', 'gntbtc', 'ltcbtc', 'xrpeur', 'usdteur', 'btcusdt', 'ethusdt' ]:
            params = {'trading_pair': pair}
            base_url = f'https://api.bitcoin.de/v4/{pair}/rates'
            response = self.sampleData('showRates')
            m.get(requests_mock.ANY, json=response, status_code=200)
            self.conn.showRates(params.get('trading_pair'))
            history = m.request_history
            self.assertEqual(history[i].method, "GET")
            self.assertEqual(history[i].url, base_url)
            self.assertTrue(mock_logger.debug.called)
            i += 1

    def test_allowed_currency(self, mock_logger, m):
        '''Test the allowed currencies.'''
        i = 0
        for curr in ['btc', 'bch', 'eth', 'btg', 'bsv', 'ltc',
                     'iota', 'dash', 'gnt', 'xrp', 'usdt']:
            base_url = f'https://api.bitcoin.de/v4/{curr}/account/ledger'
            url_args = '?currency={}'.format(curr)
            response = self.sampleData('showAccountLedger')
            m.get(requests_mock.ANY, json=response, status_code=200)
            self.conn.showAccountLedger(curr)
            history = m.request_history
            self.assertEqual(history[i].method, "GET")
            self.assertEqual(history[i].url, base_url)
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
        self.assertEqual(price + Decimal('22.3'), Decimal('252.85'))
        self.assertNotEqual(float(price) + float('22.3'), float('252.85'))


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
            self.conn.executeTrade('btceur', 'foobar', 'buy', 42)
            self.assertTrue(True)
        except UnicodeDecodeError:
            self.assertTrue(False)

    @requests_mock.Mocker()
    def test_APIException(self, m):
        '''Test API Exception.'''
        trading_pair = 'btceur'
        params = {'max_amount_currency_to_trade': 10,
                  'price': 13,
                  'type': 'buy' }
        base_url = f'https://api.bitcoin.de/v4/{trading_pair}/orders'
        url_args = '?' + urlencode(params)
        response = self.sampleData('error')
        m.post(requests_mock.ANY, json=response, status_code=400)
        self.conn.createOrder(params['type'], trading_pair,
                              params['max_amount_currency_to_trade'],
                              price=params['price'])
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
