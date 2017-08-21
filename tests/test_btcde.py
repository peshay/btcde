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
    
    def test_showOrderbook_buy_and_sell(self):
        methods = 'buy', 'sell'
        for method in method:
            result = btcde.showOrderbook('mock', method)
            expected_arguments = ['mock', 'GET', {'type': method}, btcde.orderuri]
            for idx, expected in enumerate(expected_arguments):
                actual = self.mock_APIConnect.call_args[0][idx]
                self.assertEqual(actual, expected,
                                 'Argument {} with value {} '
                                 'does not match expected {}'.format(idx,
                                                                     actual,
                                                                     expected))
    
    def test_createOrder(self):
        OrderType = 'now'
        max_amount = 5
        price = 10
        result = btcde.createOrder('mock', OrderType, max_amount, price)
        params = {'type': OrderType, 'max_amount': max_amount, 'price': price}
        expected_arguments = ['mock', 'POST', params, btcde.orderuri]
        actual = self.mock_APIConnect.call_args[0][idx]
        self.assertEqual(actual, expected,
                         'Argument {} with value {} '
                         'does not match expected {}'.format(idx,
                                                             actual,
                                                             expected))

    def test_deleteOrder(self):
        order_id = 42
        result = btcde.deleteOrder('mock', order_id)
        params = {'order_id': order_id}
        expected_arguments = ['mock', 'DELETE', params, btcde.orderuri + "/" + order_id]
        actual = self.mock_APIConnect.call_args[0][idx]
        self.assertEqual(actual, expected,
                         'Argument {} with value {} '
                         'does not match expected {}'.format(idx,
                                                             actual,
                                                             expected))
