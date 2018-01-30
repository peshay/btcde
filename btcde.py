#! /usr/bin/env python
"""API Wrapper for Bitcoin.de Trading API."""

import requests
import time
import json
import hmac
import hashlib
import logging
import codecs
import decimal

logging.basicConfig()
log = logging.getLogger(__name__)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.propagate = True

__version__ = '2.2'

# disable unsecure SSL warning
requests.packages.urllib3.disable_warnings()

class ParameterBuilder(object):
    '''To verify given parameters for API.'''
    def __init__(self, avail_params, given_params, uri):
        self.verify_keys_and_values(avail_params, given_params)
        self.params = given_params
        self.create_url(uri)

    def verify_keys_and_values(self, avail_params, given_params):
        for k, v in given_params.items():
            if k not in avail_params:
                list_string = ', '.join(avail_params)
                raise KeyError("{} is not any of {}".format(k, list_string))
            if k == 'trading_pair':
                self.error_on_invalid_value(v, self.TRADING_PAIRS)
            elif k == 'type':
                self.error_on_invalid_value(v, self.ORDER_TYPES)
            elif k == 'currency':
                self.error_on_invalid_value(v, self.CURRENCIES)
            elif k == 'seat_of_bank':
                self.error_on_invalid_value(v, self.BANK_SEATS)
            elif k in ['min_trust_level', 'trust_level']:
                self.error_on_invalid_value(v, self.TRUST_LEVELS)
            elif k == 'payment_option':
                self.error_on_invalid_value(v, self.PAYMENT_OPTIONS)
            elif k == 'state':
                self.error_on_invalid_value(v, self.STATES)

    def error_on_invalid_value(self, value, list):
        if value not in list:
            list_string = ', '.join(str(x) for x in list)
            raise ValueError("{} is not any of {}".format(value, list_string))

    def create_url(self, uri):
        if self.params:
            self.encoded_string = ''
            for key, value in sorted(self.params.items()):
                self.encoded_string += str(key) + '=' + str(value) + '&'
            self.encoded_string = self.encoded_string[:-1]
            self.url = uri + '?' + self.encoded_string
        else:
            self.encoded_string = ''
            self.url = uri


    TRADING_PAIRS = ['btceur', 'bcheur', 'etheur']
    ORDER_TYPES = ['buy', 'sell']
    CURRENCIES = ['btc', 'bch', 'eth']
    BANK_SEATS = ['AT', 'BE', 'BG', 'CH', 'CY', 'CZ',
                  'DE', 'DK', 'EE', 'ES', 'FI', 'FR',
                  'GB', 'GR', 'HR', 'HU', 'IE', 'IS',
                  'IT', 'LI', 'LT', 'LU', 'LV', 'MT',
                  'MQ', 'NL', 'NO', 'PL', 'PT', 'RO',
                  'SE', 'SI', 'SK']
    TRUST_LEVELS = ['bronze', 'silver', 'gold', 'platin']
    STATES = [-1, 0, 1]
    PAYMENT_OPTIONS = [1, 2, 3]
    TRADE_TYPES = ['all', 'buy', 'sell', 'inpayment',
                   'payout', 'affiliate', 'welcome_btc',
                   'buy_yubikey', 'buy_goldshop',
                   'buy_diamondshop', 'kickback',
                   'outgoing_fee_voluntary']

def HandleRequestsException(e):
    """Handle Exception from request."""
    log.warning(e)


def HandleAPIErrors(r):
    """To handle Errors from BTCDE API."""
    valid_status_codes = [200, 201, 204]
    if r.status_code not in valid_status_codes:
        content = r.json()
        errors = content.get('errors')
        log.warning('API Error Code: {}'.format(str(errors[0]['code'])))
        log.warning('API Error Message: {}'.format(errors[0]['message']))
        log.warning('API Error URL: {}'.format(r.url))
        return False
    else:
        return True


class Connection(object):
    """To provide connection credentials to the trading API"""
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        # set initial self.nonce
        self.nonce = int(time.time())
        # Bitcoin.de API URI
        self.apihost = 'https://api.bitcoin.de'
        self.apiversion = 'v2'
        self.orderuri = self.apihost + '/' + self.apiversion + '/' + 'orders'
        self.tradeuri = self.apihost + '/' + self.apiversion + '/' + 'trades'
        self.accounturi = self.apihost + '/' + self.apiversion + '/' + 'account'

    def build_hmac_sign(self, md5string, method, url):
        hmac_data = '{method}#{url}#{key}#{nonce}#{md5}'\
                    .format(method=method, url=url,
                            key=self.api_key, nonce=str(self.nonce),
                            md5=md5string)
        hmac_signed = hmac.new(bytearray(self.api_secret.encode()), msg=hmac_data.encode(), digestmod=hashlib.sha256).hexdigest()
        return hmac_signed

    def set_header(self, url, method, encoded_string):
        # raise self.nonce before using
        self.nonce += 1
        if method == 'POST':
            md5_encoded_query_string = hashlib.md5(encoded_string.encode()).hexdigest()
        else:
            md5_encoded_query_string = hashlib.md5(b'').hexdigest()
        hmac_signed = self.build_hmac_sign(md5_encoded_query_string,
                                           method, url)
        # set header
        header = {'content-type':
                  'application/x-www-form-urlencoded; charset=utf-8',
                  'X-API-KEY': self.api_key,
                  'X-API-NONCE': str(self.nonce),
                  'X-API-SIGNATURE': hmac_signed }
        return header

    def send_request(self, url, method, header, encoded_string):
        if method == 'GET':
            r = requests.get(url, headers=(header),
                             stream=True, verify=False)
        elif method == 'POST':
            r = requests.post(url, headers=(header), data=encoded_string,
                              stream=True, verify=False)
        elif method == 'DELETE':
            r = requests.delete(url, headers=(header),
                                stream=True, verify=False)
        return r

    def APIConnect(self, method, params):
        """Transform Parameters to URL"""
        header = self.set_header(params.url, method,
                                 params.encoded_string)
        log.debug('Set Header: {}'.format(header))
        try:
            r = self.send_request(params.url, method, header,
                                  params.encoded_string)
            # Handle API Errors
            if HandleAPIErrors(r):
                # get results
                result = r.json(parse_float=decimal.Decimal)
            else:
                result = {}
        except requests.exceptions.RequestException as e:
            HandleRequestsException(e)
            result = {}
        return result

    def showOrderbook(self, order_type, trading_pair, **args):
        """Search Orderbook for offers."""
        params = {'type': order_type,
                  'trading_pair': trading_pair}
        params.update(args)
        avail_params = ['type', 'trading_pair', 'amount', 'price',
                        'order_requirements_fullfilled',
                        'only_kyc_full', 'only_express_orders',
                        'only_same_bankgroup', 'only_same_bic',
                        'seat_of_bank']
        p = ParameterBuilder(avail_params, params, self.orderuri)
        return self.APIConnect('GET', p)


    def createOrder(self, order_type, trading_pair, max_amount, price, **args):
        """Create a new Order."""
        # Build parameters
        params = {'type': order_type,
                  'max_amount': max_amount,
                  'price': price,
                  'trading_pair': trading_pair}
        params.update(args)
        avail_params = ['type', 'trading_pair', 'max_amount', 'price',
                        'min_amount', 'new_order_for_remaining_amount',
                        'min_trust_level', 'only_kyc_full', 'payment_option',
                        'seat_of_bank']
        p = ParameterBuilder(avail_params, params, self.orderuri)
        return self.APIConnect('POST', p)


    def deleteOrder(self, order_id, trading_pair):
        """Delete an Order."""
        # Build parameters
        params = {'order_id': order_id,
                  'trading_pair': trading_pair}
        avail_params = ['order_id', 'trading_pair']
        newuri = self.orderuri + "/" + order_id + "/" + trading_pair
        p = ParameterBuilder(avail_params, params, newuri)
        p.encoded_string = ''
        p.url = newuri
        return self.APIConnect('DELETE', p)


    def showMyOrders(self, **args):
        """Query and Filter own Orders."""
        # Build parameters
        params = args
        avail_params = ['type', 'trading_pair', 'state',
                        'date_start', 'date_end', 'page']
        newuri = self.orderuri + '/my_own'
        p = ParameterBuilder(avail_params, params, newuri)
        return self.APIConnect('GET', p)


    def showMyOrderDetails(self, order_id):
        """Details to an own Order."""
        newuri = self.orderuri + '/' + order_id
        p = ParameterBuilder({}, {}, newuri)
        return self.APIConnect('GET', p)


    def executeTrade(self, order_id, order_type, trading_pair, amount):
        """Buy/Sell on a specific Order."""
        newuri = self.tradeuri + '/' + order_id
        params = {'order_id': order_id,
                  'type': order_type,
                  'trading_pair': trading_pair,
                  'amount': amount}
        avail_params = ['order_id', 'type', 'trading_pair',
                        'amount']
        p = ParameterBuilder(avail_params, params, newuri)
        return self.APIConnect('POST', p)


    def showMyTrades(self, **args):
        """Query and Filter on past Trades."""
        # Build parameters
        params = args
        avail_params = ['type', 'trading_pair', 'state',
                        'date_start', 'date_end', 'page']
        p = ParameterBuilder(avail_params, params, self.tradeuri)
        return self.APIConnect('GET', p)


    def showMyTradeDetails(self, trade_id):
        """Details to a specific Trade."""
        newuri = self.tradeuri + '/' + trade_id
        params = {}
        p = ParameterBuilder({}, {}, newuri)
        return self.APIConnect('GET', p)


    def showAccountInfo(self):
        """Query on Account Infos."""
        p = ParameterBuilder({}, {}, self.accounturi)
        return self.APIConnect('GET', p)


    def showOrderbookCompact(self, trading_pair):
        """Bids and Asks in compact format."""
        params = {'trading_pair': trading_pair}
        # Build parameters
        avail_params = ['trading_pair']
        p = ParameterBuilder(avail_params, params,
                             self.orderuri + '/compact')
        return self.APIConnect('GET', p)


    def showPublicTradeHistory(self, trading_pair, **args):
        """All successful trades of the las 7 days."""
        params = {'trading_pair': trading_pair}
        params.update(args)
        avail_params = ['trading_pair', 'since_tid']
        p = ParameterBuilder(avail_params, params,
                             self.tradeuri + '/history')
        return self.APIConnect('GET', p)


    def showRates(self, trading_pair):
        """Query of the average rate last 3 and 12 hours."""
        newuri = self.apihost + '/' + self.apiversion + '/rates'
        params = {'trading_pair': trading_pair}
        avail_params = ['trading_pair']
        p = ParameterBuilder(avail_params, params, newuri)
        return self.APIConnect('GET', p)


    def showAccountLedger(self, currency, **args):
        """Query on Account statement."""
        params = {'currency': currency}
        params.update(args)
        avail_params = ['currency', 'type',
                        'date_start', 'date_end', 'page']
        p = ParameterBuilder(avail_params, params,
                             self.accounturi + '/ledger')
        return self.APIConnect('GET', p)
