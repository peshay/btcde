import unittest 
from unittest.mock import patch
import btcde

class TestBtcdeApi(unittest.TestCase):
    """Test Api Functions."""
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    patch('btcde.APIConnect')
    def test_showOrderbook_buy(self, mock_APIConnect):
        result = btcde.showOrderbook('mock', 'buy')
        expected_arguments = ['mock', 'GET', {'type': 'buy'}, btcde.orderuri]
        self.assertEqual(mock_APIConnect.call_args, expected_arguments)
