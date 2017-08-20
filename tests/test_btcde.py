from unittest import TestCase 
from mock import patch
import btcde


class TestBtcdeApi(TestCase):
    """Test Api Functions."""
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    @patch('btcde.APIConnect')
    def test_showOrderbook_buy(self, mock_APIConnect):
        result = btcde.showOrderbook('mock', 'buy')
        expected_arguments = ['mock', 'GET', {'type': 'buy'}, btcde.orderuri]
        for idx, expected in enumerate(expected_arguments):
            actual = mock_APIConnect.call_args[0][idx]
            self.assertEqual(actual, expected,
                             'Argument {} with value {} '
                             'does not match expected {}'.format(idx,
                                                                 actual,
                                                                 expected))
