from unittest import TestCase 
from mock import patch
import time
import hashlib
import hmac
import requests
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
            md5_encoded_query_string = hashlib.md5(self.encoded_string.encode()).hexdigest()
        else:
            md5_encoded_query_string = hashlib.md5(b'').hexdigest()
        hmac_data = method + '#' + \
                    self.url + '#' + self.XAPIKEY + \
                    '#' + str(self.XAPINONCE) + '#' + md5_encoded_query_string
        hmac_signed = hmac.new(bytearray(self.XAPISECRET.encode()), msg=hmac_data.encode(), digestmod=hashlib.sha256).hexdigest()
        return hmac_signed
        
    def setUp(self):
        self.XAPIKEY = 'f00b4r'
        self.XAPISECRET = 'b4rf00'
        self.XAPINONCE = int(time.time())
        btcde.nonce = self.XAPINONCE
        self.conn = btcde.Connection(self.XAPIKEY, self.XAPISECRET)
        
    def tearDown(self):
        del self.XAPIKEY
        del self.XAPISECRET
        del self.XAPINONCE
        del self.conn
     
    def test_signature_post(self, m):
        '''Test the signature on a post request.'''
        params = {'type': 'buy',
                  'trading_pair': 'btceur',
                  'max_amount': 10,
                  'price': 1337}
        response = {"order_id": "A1234BC",
                    "errors": [],
                    "credits": 8,}
        m.post(requests_mock.ANY, json = response, status_code=201)
        btcde.createOrder(self.conn, params.get('type'), params.get('trading_pair'), params.get('max_amount'), params.get('price'))
        history = m.request_history
        request_signature = history[0].headers.get('X-API-SIGNATURE')
        verified_signature = self.verifySignature(btcde.orderuri, 'POST', params)
        self.assertEqual(request_signature, verified_signature)
        
        
    def test_signature_get(self, m):
        '''Test the signature on a get request.'''
        pass
