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
        expected_arguments = ('mock', 'GET', {'type': 'buy'}, btcde.orderuri)
        for callargs in mock_APIConnect.call_args[0]:
            print(callargs)
        self.assertEqual(mock_APIConnect.call_args[0], expected_arguments)