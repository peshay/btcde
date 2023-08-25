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
import inspect
import urllib

from urllib.parse import urlencode

logging.basicConfig()
log = logging.getLogger(__name__)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.propagate = True

__version__ = '4.0'

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
                self.error_on_invalid_value(v, self.TRADE_TYPES)
            elif k == 'currency':
                self.error_on_invalid_value(v, self.CURRENCIES)
            elif k == 'seat_of_bank':
                self.error_on_invalid_value(v, self.BANK_SEATS)
            elif k in ['min_trust_level', 'trust_level']:
                self.error_on_invalid_value(v, self.TRUST_LEVELS)
            elif k == 'payment_option':
                self.error_on_invalid_value(v, self.PAYMENT_OPTIONS)
            elif k == 'state':
                caller = inspect.stack()[2][3]
                if caller in ["showMyOrders", "showMyOrderDetails"]:
                    self.error_on_invalid_value(v, self.ORDER_STATES)
                elif caller in ["showMyTrades", "showMyTradesDetails"]:
                    self.error_on_invalid_value(v, self.TRADE_STATES)

    def error_on_invalid_value(self, value, list):
        if value not in list:
            list_string = ', '.join(str(x) for x in list)
            raise ValueError("{} is not any of {}".format(value, list_string))

    def create_url(self, uri):
        if self.params:
            self.encoded_string = urlencode(sorted(self.params.items()))
            self.url = uri + '?' + self.encoded_string
        else:
            self.encoded_string = ''
            self.url = uri


    TRADING_PAIRS = ['btceur', 'bcheur', 'etheur', 'btgeur', 'bsveur', 'ltceur',
                     'iotabtc', 'dashbtc', 'gntbtc', 'ltcbtc', 'xrpeur', 'usdteur', 'btcusdt', 'ethusdt']
    ORDER_TYPES = ['buy', 'sell']
    CURRENCIES = ['btc', 'bch', 'eth', 'btg', 'bsv', 'ltc',
                  'iota', 'dash', 'gnt', 'xrp', 'usdt']
    BANK_SEATS = ['AT', 'BE', 'BG', 'CH', 'CY', 'CZ',
                  'DE', 'DK', 'EE', 'ES', 'FI', 'FR',
                  'GB', 'GR', 'HR', 'HU', 'IE', 'IS',
                  'IT', 'LI', 'LT', 'LU', 'LV', 'MT',
                  'MQ', 'NL', 'NO', 'PL', 'PT', 'RO',
                  'SE', 'SI', 'SK']
    TRUST_LEVELS = ['bronze', 'silver', 'gold', 'platin']
    TRADE_STATES = [-1, 0, 1]
    ORDER_STATES = [-2, -1, 0]
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
        self.nonce = int(time.time() * 1000000)
        # Bitcoin.de API URI
        self.apihost = 'https://api.bitcoin.de'
        self.apiversion = 'v4'
        self.apibase = f'{self.apihost}/{self.apiversion}/'

    def build_hmac_sign(self, md5string, method, url):
        hmac_data = '#'.join([method, url, self.api_key, str(self.nonce), md5string])
        hmac_signed = hmac.new(bytearray(self.api_secret.encode()), msg=hmac_data.encode(), digestmod=hashlib.sha256).hexdigest()
        return hmac_signed

    def set_header(self, url, method, encoded_string):
        # raise self.nonce before using
        self.nonce = int(time.time() * 1000000)
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

    def addToAddressPool(self, currency, address, **args):
        """Add address to pool"""
        uri = f'{self.apibase}{currency}/address'
        params = {'address': address}
        params.update(args)
        avail_params = ['address', 'amount_usages', 'comment']
        p = ParameterBuilder(avail_params, params, uri)
        return self.APIConnect('POST', p)

    def removeFromAddressPool(self, currency, address):
        """Remove address from pool"""
        uri = f'{self.apibase}{currency}/address/{address}'
        params = {'currency': currency, 'address': address}
        avail_params = ['currency', 'address']
        p = ParameterBuilder({}, {}, uri)
        p.verify_keys_and_values(avail_params, params)
        return self.APIConnect('DELETE', p)

    def listAddressPool(self, currency, **args):
        """List address pool"""
        uri = f'{self.apibase}{currency}/address'
        params = args
        avail_params = ['usable', 'comment', 'page']
        p = ParameterBuilder(avail_params, params, uri)
        return self.APIConnect('GET', p)

    def showOrderbook(self, order_type, trading_pair, **args):
        """Search Orderbook for offers."""
        uri = f'{self.apibase}{trading_pair}/orderbook'
        params = {'type': order_type}
        params.update(args)
        avail_params = ['type', 'trading_pair', 'amount_currency_to_trade', 'price',
                        'order_requirements_fullfilled',
                        'only_kyc_full', 'only_express_orders', 'payment_option',
                        'sepa_option', 'only_same_bankgroup', 'only_same_bic',
                        'seat_of_bank', 'page_size']
        p = ParameterBuilder(avail_params, params, uri)
        return self.APIConnect('GET', p)

    def showOrderDetails(self, trading_pair, order_id):
        """Show details for an offer."""
        uri = f'{self.apibase}{trading_pair}/orders/public/details/{order_id}'
        params = {'trading_pair': trading_pair, 'order_id': order_id}
        avail_params = ['trading_pair', 'order_id']
        p = ParameterBuilder({}, {}, uri)
        p.verify_keys_and_values(avail_params, params)
        return self.APIConnect('GET', p)

    def createOrder(self, order_type, trading_pair, max_amount_currency_to_trade, price, **args):
        """Create a new Order."""
        uri = f'{self.apibase}{trading_pair}/orders'
        # Build parameters
        params = {'type': order_type,
                  'max_amount_currency_to_trade': max_amount_currency_to_trade,
                  'price': price}
        params.update(args)
        avail_params = ['type', 'max_amount_currency_to_trade', 'price',
                        'min_amount_currency_to_trade', 'end_datetime',
                        'new_order_for_remaining_amount', 'trading_pair',
                        'min_trust_level', 'only_kyc_full', 'payment_option',
                        'sepa_option', 'seat_of_bank']
        p = ParameterBuilder(avail_params, params, uri)
        p.verify_keys_and_values(avail_params, {'trading_pair': trading_pair})
        return self.APIConnect('POST', p)

    def deleteOrder(self, order_id, trading_pair):
        """Delete an Order."""
        # Build parameters
        uri = f'{self.apibase}{trading_pair}/orders/{order_id}'
        avail_params = ['order_id', 'trading_pair']
        params = { 'order_id': order_id, 'trading_pair': trading_pair}
        p = ParameterBuilder({}, {}, uri)
        p.verify_keys_and_values(avail_params, params)
        return self.APIConnect('DELETE', p)

    def showMyOrders(self, **args):
        """Query and Filter own Orders."""
        # Build parameters
        params = args
        avail_params = ['type', 'trading_pair', 'state',
                        'date_start', 'date_end', 'page']
        if params.get("trading_pair"):
            uri = f'{self.apibase}{params["trading_pair"]}/orders'
            del params["trading_pair"]
        else:
            uri = f'{self.apibase}orders'
        p = ParameterBuilder(avail_params, params, uri)
        return self.APIConnect('GET', p)

    def showMyOrderDetails(self, trading_pair, order_id):
        """Details to an own Order."""
        uri = f'{self.apibase}{trading_pair}/orders/{order_id}'
        p = ParameterBuilder({}, {}, uri)
        return self.APIConnect('GET', p)

    def executeTrade(self, trading_pair, order_id, order_type, amount):
        """Buy/Sell on a specific Order."""
        uri = f'{self.apibase}{trading_pair}/trades/{order_id}'
        params = { 'type': order_type,
                   'amount_currency_to_trade': amount}
        avail_params = ['type', 'amount_currency_to_trade']
        p = ParameterBuilder(avail_params, params, uri)
        return self.APIConnect('POST', p)

    def showMyTrades(self, **args):
        """Query and Filter on past Trades."""
        # Build parameters
        params = args
        avail_params = ['type', 'trading_pair', 'state',
                        'only_trades_with_action_for_payment_or_transfer_required',
                        'payment_method', 'date_start', 'date_end', 'page']
        if params.get("trading_pair"):
            uri = f'{self.apibase}{params["trading_pair"]}/trades'
            del params["trading_pair"]
        else:
            uri = f'{self.apibase}trades'
        p = ParameterBuilder(avail_params, params, uri)
        return self.APIConnect('GET', p)

    def showMyTradeDetails(self, trading_pair, trade_id):
        """Details to a specific Trade."""
        params = {'trading_pair': trading_pair, 'trade_id': trade_id}
        avail_params = [ 'trading_pair', 'trade_id' ]
        uri = f'{self.apibase}{trading_pair}/trades/{trade_id}'
        p = ParameterBuilder({}, {}, uri)
        p.verify_keys_and_values(avail_params, params)
        return self.APIConnect('GET', p)

    def markCoinsAsTransferred(self, trading_pair, trade_id, amount_currency_to_trade_after_fee):
        """Mark trade as transferred."""
        params = {'amount_currency_to_trade_after_fee': amount_currency_to_trade_after_fee,
                  'trading_pair': trading_pair, 'trade_id': trade_id}

        avail_params = [ 'trading_pair', 'trade_id', 'amount_currency_to_trade_after_fee' ]
        uri = f'{self.apibase}{trading_pair}/trades/{trade_id}/mark_coins_as_transferred'
        p = ParameterBuilder(avail_params,
            {'amount_currency_to_trade_after_fee': amount_currency_to_trade_after_fee}, uri)
        p.verify_keys_and_values(avail_params, params)
        return self.APIConnect('POST', p)

    def markTradeAsPaid(self, trading_pair, trade_id, volume_currency_to_pay_after_fee):
        """Mark traded as paid."""
        params = {'volume_currency_to_pay_after_fee': volume_currency_to_pay_after_fee,
                  'trading_pair': trading_pair, 'trade_id': trade_id}

        avail_params = [ 'trading_pair', 'trade_id', 'volume_currency_to_pay_after_fee' ]
        uri = f'{self.apibase}{trading_pair}/trades/{trade_id}/mark_trade_as_paid'
        p = ParameterBuilder(avail_params,
            {'volume_currency_to_pay_after_fee': volume_currency_to_pay_after_fee}, uri)
        p.verify_keys_and_values(avail_params, params)
        return self.APIConnect('POST', p)

    def markCoinsAsReceived(self, trading_pair, trade_id, amount_currency_to_trade_after_fee, rating):
        """Mark coins as received."""
        params = {'amount_currency_to_trade_after_fee': amount_currency_to_trade_after_fee,
                  'trading_pair': trading_pair, 'trade_id': trade_id, 'rating': rating}
        params_post = {'amount_currency_to_trade_after_fee': amount_currency_to_trade_after_fee,
                       'rating': rating}
        avail_params = [ 'trading_pair', 'trade_id', 'amount_currency_to_trade_after_fee', 'rating' ]
        uri = f'{self.apibase}{trading_pair}/trades/{trade_id}/mark_coins_as_received'
        p = ParameterBuilder(avail_params, params_post, uri)
        p.verify_keys_and_values(avail_params, params)
        return self.APIConnect('POST', p)

    def markTradeAsPaymentReceived(self, trading_pair, trade_id,
                                   volume_currency_to_pay_after_fee, rating,
                                   is_paid_from_correct_bank_account):
        """Mark coins as received."""
        params = {'volume_currency_to_pay_after_fee': volume_currency_to_pay_after_fee,
                  'trading_pair': trading_pair, 'trade_id': trade_id, 'rating': rating}
        params_post = {'volume_currency_to_pay_after_fee': volume_currency_to_pay_after_fee,
                       'rating': rating,
                       'is_paid_from_correct_bank_account': is_paid_from_correct_bank_account}
        avail_params = [ 'trading_pair', 'trade_id', 'volume_currency_to_pay_after_fee',
                         'rating', 'is_paid_from_correct_bank_account' ]
        uri = f'{self.apibase}{trading_pair}/trades/{trade_id}/mark_trade_as_payment_received'
        p = ParameterBuilder(avail_params, params_post, uri)
        p.verify_keys_and_values(avail_params, params)
        return self.APIConnect('POST', p)

    def addTradeRating(self, trading_pair, trade_id, rating):
        """Mark coins as received."""
        params = {'trading_pair': trading_pair, 'trade_id': trade_id, 'rating': rating}
        params_post = {'rating': rating}
        avail_params = [ 'trading_pair', 'trade_id', 'rating' ]
        uri = f'{self.apibase}{trading_pair}/trades/{trade_id}/add_trade_rating'
        p = ParameterBuilder(avail_params, params_post, uri)
        p.verify_keys_and_values(avail_params, params)
        return self.APIConnect('POST', p)

    def showAccountInfo(self):
        """Query on Account Infos."""
        uri = f'{self.apibase}account'
        p = ParameterBuilder({}, {}, uri)
        return self.APIConnect('GET', p)

    def showOrderbookCompact(self, trading_pair):
        """Bids and Asks in compact format."""
        params = {'trading_pair': trading_pair}
        avail_params = ['trading_pair']
        uri = f'{self.apibase}{trading_pair}/orderbook/compact'
        # Build parameters
        p = ParameterBuilder({}, {}, uri)
        p.verify_keys_and_values(avail_params, params)
        return self.APIConnect('GET', p)

    def showPublicTradeHistory(self, trading_pair, **args):
        """All successful trades of the last 24 hours."""
        params = { 'trading_pair': trading_pair }
        params.update(args)
        avail_params = ['trading_pair', 'since_tid']
        uri = f'{self.apibase}{trading_pair}/trades/history'
        if params.get('since_tid'):
            del params["trading_pair"]
            p = ParameterBuilder(avail_params, params, uri)
        else:
            p = ParameterBuilder({}, {}, uri)
        p.verify_keys_and_values(avail_params, params)
        return self.APIConnect('GET', p)

    def showRates(self, trading_pair):
        """Query of the average rate last 3 and 12 hours."""
        uri = f'{self.apibase}{trading_pair}/rates'
        params = {'trading_pair': trading_pair}
        avail_params = ['trading_pair']
        # Build parameters
        p = ParameterBuilder({}, {}, uri)
        p.verify_keys_and_values(avail_params, params)
        return self.APIConnect('GET', p)

    def showAccountLedger(self, currency, **args):
        """Query on Account statement."""
        params = {'currency': currency}
        params.update(args)
        uri = f'{self.apibase}{currency}/account/ledger'
        avail_params = ['currency', 'type',
                        'datetime_start', 'datetime_end', 'page']
        p = ParameterBuilder(avail_params, params, uri)
        del params['currency']
        p = ParameterBuilder(avail_params, params, uri)
        return self.APIConnect('GET', p)

    def showPermissions(self):
        """Show permissions that are allowed for used API key"""
        uri = f'{self.apibase}permissions'
        p = ParameterBuilder({}, {}, uri)
        return self.APIConnect('GET', p)