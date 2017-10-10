from unittest import TestCase 
from mock import patch
import btcde


class TestBtcdeApi(TestCase):
    """Test Api Functions."""
    
    def setUp(self):
        self.patcher = patch('btcde.APIConnect')
        self.mock_APIConnect = self.patcher.start()
    
    def tearDown(self):
        self.patcher.stop()
    
    def assertArguments(self, expected_arguments, mock_APIConnect):
        for idx, expected in enumerate(expected_arguments):
            actual = mock_APIConnect.call_args[0][idx]
            self.assertEqual(actual, expected,
                             'Argument {} with value {} '
                             'does not match expected {}'.format(idx,
                                                                 actual,
                                                                 expected))
    
    def test_showOrderbook_buy_and_sell(self):
        methods = 'buy', 'sell'
        trading_pairs = ['btceur', 'bcheur', 'etheur']
        for trading_pair in trading_pairs:
            for method in methods:
                result = btcde.showOrderbook('mock', method, trading_pair)
                expected_arguments = ['mock', 'GET', {'type': method, 'trading_pair': trading_pair}, btcde.orderuri]
                self.assertArguments(expected_arguments, self.mock_APIConnect)
    
    def test_createOrder(self):
        OrderType = 'now'
        trading_pair = 'btceur'
        max_amount = 5
        price = 10
        result = btcde.createOrder('mock', OrderType, trading_pair, max_amount, price)
        params = {'type': OrderType, 'max_amount': max_amount, 'price': price, 'trading_pair': trading_pair}
        expected_arguments = ['mock', 'POST', params, btcde.orderuri]
        self.assertArguments(expected_arguments, self.mock_APIConnect)

    def test_deleteOrder(self):
        order_id = '42'
        trading_pair = 'btceur'
        result = btcde.deleteOrder('mock', order_id, trading_pair)
        params = {'order_id': order_id, 'trading_pair': trading_pair}
        expected_arguments = ['mock', 'DELETE', params, btcde.orderuri + "/" + order_id + "/" + trading_pair]
        self.assertArguments(expected_arguments, self.mock_APIConnect)
                                                             
    def test_showMyOrders(self):
        result = btcde.showMyOrders('mock')
        expected_arguments = ['mock', 'GET', {}, btcde.orderuri + '/my_own']
        self.assertArguments(expected_arguments, self.mock_APIConnect)

    def test_showMyOrderDetails(self):
        order_id = '42'
        result = btcde.showMyOrderDetails('mock', order_id)
        params = {'order_id': order_id}
        expected_arguments = ['mock', 'GET', params, btcde.orderuri + '/' + order_id]
        self.assertArguments(expected_arguments, self.mock_APIConnect)
                                                             
    def test_executeTrade(self):
        order_id = '42'
        OrderType = 'foobar'
        amount = '73'
        trading_pair = 'btceur'
        result = btcde.executeTrade('mock', order_id, OrderType, trading_pair, amount)
        params = {'order_id': order_id, 'type': OrderType, 'amount': amount, 'trading_pair': trading_pair}
        expected_arguments = ['mock', 'POST', params, btcde.tradeuri + '/' + order_id]
        self.assertArguments(expected_arguments, self.mock_APIConnect)

    def test_showMyTrades(self):
        result = btcde.showMyTrades('mock')
        expected_arguments = ['mock', 'GET', {}, btcde.tradeuri]
        self.assertArguments(expected_arguments, self.mock_APIConnect)
        
    def test_showMyTradeDetails(self):
        trade_id = '42'
        result = btcde.showMyTradeDetails('mock', trade_id)
        params = {'trade_id': trade_id}
        expected_arguments = ['mock', 'GET', params, btcde.tradeuri + '/' + trade_id]
        self.assertArguments(expected_arguments, self.mock_APIConnect)

    def test_showAccountInfo(self):
        result = btcde.showAccountInfo('mock')
        params = {}
        expected_arguments = ['mock', 'GET', params, btcde.accounturi]
        self.assertArguments(expected_arguments, self.mock_APIConnect)

    def test_showOrderbookCompact(self):
        trading_pair = 'btceur'
        result = btcde.showOrderbookCompact('mock', trading_pair)
        params = {'trading_pair': trading_pair}
        expected_arguments = ['mock', 'GET', params, btcde.orderuri + '/compact']
        self.assertArguments(expected_arguments, self.mock_APIConnect)

    def test_showPublicTradeHistory(self):
        trading_pair = 'btceur'
        result1 = btcde.showPublicTradeHistory('mock', trading_pair)
        params = {'trading_pair': trading_pair}
        expected_arguments = ['mock', 'GET', params, btcde.tradeuri + '/history']
        self.assertArguments(expected_arguments, self.mock_APIConnect)
        self.tearDown()
        self.setUp()
        since_tid = '3'
        params.update({'since_tid': since_tid})
        result2 = btcde.showPublicTradeHistory('mock', trading_pair, since_tid)
        expected_arguments = ['mock', 'GET', params, btcde.tradeuri + '/history']
        self.assertArguments(expected_arguments, self.mock_APIConnect) 

    def test_showRates(self):
        trading_pair = 'btceur'
        result = btcde.showRates('mock',trading_pair )
        params = {'trading_pair': trading_pair}
        expected_arguments = ['mock', 'GET', params, btcde.apihost + '/' + btcde.apiversion + '/rates']
        self.assertArguments(expected_arguments, self.mock_APIConnect)

    def test_showAccountLedger(self):
        result = btcde.showAccountLedger('mock')
        expected_arguments = ['mock', 'GET', {}, btcde.accounturi + '/ledger']
        self.assertArguments(expected_arguments, self.mock_APIConnect)

class TestSimpleFunctions(TestCase):
    
    def test_params_url(self):
        sample_params = { 'foo': 'bar', 'bar': 'foo'}
        result = btcde.params_url(sample_params, 'https://foo.bar')
        expected_result = 'https://foo.bar?bar=foo&foo=bar'
        self.assertEquals(result, expected_result)
    
    def test_params_url_wo_params(self):
        result = btcde.params_url({}, 'https://foo.bar')
        expected_result = 'https://foo.bar'
        self.assertEquals(result, expected_result)
        
        
class TestApiComm(TestCase):
    
    def setUp(self):
        self.fake_url = 'https://foo.bar/apiv2/'
        btcde.nonce = 9
        btcde.conn = btcde.Connection('foobar', 'barfoo')
   
    def tearDown(self):
        pass

    def test_api_signing_wout_post(self):
        '''Test API signing without POST.'''
        btcde.method = ''
        self.header = btcde.set_header(self.fake_url)
        self.assertEqual(self.header.get('X-API-KEY'),
                                         'foobar')
        self.assertEqual(self.header.get('X-API-NONCE'),
                                         '10')
        self.ApiSign = 'c494280b62451eeba87804c91dc2422a6f6f5b48d203d6cc94813c6103bc67ee'
        self.assertEqual(self.header.get('X-API-SIGNATURE'), self.ApiSign)
        
    def test_api_signing_with_post(self):
        '''Test API signing with POST.'''
        btcde.method = 'POST'
        btcde.encoded_string = 'foo&bar'
        self.header = btcde.set_header(self.fake_url)
        self.assertEqual(self.header.get('X-API-KEY'),
                                         'foobar')
        self.assertEqual(self.header.get('X-API-NONCE'),
                                         '10')
        self.ApiSign = 'f8f00da62fcabd247f94e488dd752a4f0aaad29506cf2c488ad8c1802b3ef0fe'
        self.assertEqual(self.header.get('X-API-SIGNATURE'), self.ApiSign)
        
#    def test_api_errors(self):
#        '''Test for valid API errors.'''
#        # TODO random return
#        patch('requests.status_code', return_value=201)
#        self.assertTrue(btcde.HandleAPIErrors(requests))
            
