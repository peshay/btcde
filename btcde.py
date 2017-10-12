#! /usr/bin/env python
"""This Module provides the functions from bitcoin.de Trading API"""

import requests
import time
import json
import hmac
import hashlib
import logging
import codecs

# these two lines enable debugging at httplib level
# (requests->urllib3->httplib)
# you will see the REQUEST, including HEADERS and DATA, and RESPONSE with
# HEADERS but without DATA.
# the only thing missing will be the response.body which is not logged.
#import http.client
#http.client.HTTPConnection.debuglevel = 1


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

__version__ = '1.4'


class Connection:
    """To provide connection credentials to the trading API"""
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

# Bitcoin.de API URI
apihost = 'https://api.bitcoin.de'
apiversion = 'v2'
valid_trading_pair = ['btceur', 'bcheur', 'etheur']
valid_order_type = ['buy', 'sell']
orderuri = apihost + '/' + apiversion + '/' + 'orders'
tradeuri = apihost + '/' + apiversion + '/' + 'trades'
accounturi = apihost + '/' + apiversion + '/' + 'account'
# set initial nonce
nonce = int(time.time())
# disable unsecure SSL warning
requests.packages.urllib3.disable_warnings()


def HandleRequestsException(e):
    """Handle Exception from request."""
    print(e[0][0])
    print(e[0][1])


def HandleAPIErrors(r):
    """To handle Errors from BTCDE API."""
    valid_status_codes = [200, 201, 204]
    if r.status_code not in valid_status_codes:
        reader = codecs.getreader("utf-8")
        content = json.load(reader(r.raw))
        errors = content.get('errors')
        print('Code:     ' + str(errors[0]['code']))
        print('Message:  ' + errors[0]['message'])
        print('With URL: ' + r.url)
        return False
    else:
        return True


def params_url(params, uri):
    encoded_string = ''
    if params:
        for key, value in sorted(params.items()):
            encoded_string += str(key) + '=' + str(value) + '&'
        encoded_string = encoded_string[:-1]
        url = uri + '?' + encoded_string
    else:
        url = uri
    return url, encoded_string

def set_header(conn, url, method, encoded_string):
    global nonce
    # raise nonce before using
    nonce += 1
    if method == 'POST':
        md5_encoded_query_string = hashlib.md5(encoded_string.encode()).hexdigest()
    else:
        md5_encoded_query_string = hashlib.md5(b'').hexdigest()
    hmac_data = method + '#' + \
        url + '#' + conn.api_key + \
        '#' + str(nonce) + '#' + md5_encoded_query_string
    hmac_signed = hmac.new(bytearray(conn.api_secret.encode()), msg=hmac_data.encode(), digestmod=hashlib.sha256).hexdigest()
    # set header
    header = {'content-type':
              'application/x-www-form-urlencoded; charset=utf-8',
              'X-API-KEY': conn.api_key,
                   'X-API-NONCE': str(nonce),
                   'X-API-SIGNATURE': hmac_signed }
    return header
    
def send_request(url, method, header, encoded_string):
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
    
def APIConnect(conn, method, params, uri):
    """Transform Parameters to URL"""
    url, encoded_string = params_url(params, uri)
    header = set_header(conn, url, method, encoded_string)
    try:
        r = send_request(url, method, header, encoded_string)
        # Handle API Errors
        if HandleAPIErrors(r):
            # get results
            result = r.json()
        else:
            result = {}
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)
    return result


def showOrderbook(conn, OrderType, trading_pair, **args):
    """Search Orderbook for offers."""
    # Build parameters
    if OrderType in valid_order_type and trading_pair in valid_trading_pair:
        params = {'type': OrderType, 'trading_pair': trading_pair}
    else:
        print('problem')
    params.update(args)
    return APIConnect(conn, 'GET', params, orderuri)


def createOrder(conn, OrderType, trading_pair, max_amount, price, **args):
    """Create a new Order."""
    # Build parameters
    params = {'type': OrderType, 'max_amount': max_amount, 'price': price, 'trading_pair': trading_pair}
    params.update(args)
    return APIConnect(conn, 'POST', params, orderuri)


def deleteOrder(conn, order_id, trading_pair):
    """Delete an Order."""
    newuri = orderuri + "/" + order_id + "/" + trading_pair
    params = {'order_id': order_id, 'trading_pair': trading_pair}
    return APIConnect(conn, 'DELETE', params, newuri)


def showMyOrders(conn, **args):
    """Query and Filter own Orders."""
    newuri = orderuri + '/my_own'
    return APIConnect(conn, 'GET', args, newuri)


def showMyOrderDetails(conn, order_id):
    """Details to an own Order."""
    newuri = orderuri + '/' + order_id
    params = {'order_id': order_id}
    return APIConnect(conn, 'GET', params, newuri)


def executeTrade(conn, order_id, OrderType, trading_pair, amount):
    """Buy/Sell on a specific Order."""
    newuri = tradeuri + '/' + order_id
    params = {'order_id': order_id, 'type': OrderType, 'trading_pair': trading_pair, 'amount': amount}
    return APIConnect(conn, 'POST', params, newuri)


def showMyTrades(conn, **args):
    """Query and Filter on past Trades."""
    return APIConnect(conn, 'GET', args, tradeuri)


def showMyTradeDetails(conn, trade_id):
    """Details to a specific Trade."""
    newuri = tradeuri + '/' + trade_id
    params = {'trade_id': trade_id}
    return APIConnect(conn, 'GET', params, newuri)


def showAccountInfo(conn):
    """Query on Account Infos."""
    params = {}
    return APIConnect(conn, 'GET', params, accounturi)


def showOrderbookCompact(conn, trading_pair):
    """Bids and Asks in compact format."""
    params = {'trading_pair': trading_pair}
    return APIConnect(conn, 'GET', params, orderuri + '/compact')


def showPublicTradeHistory(conn, trading_pair, since_tid=None):
    """All successful trades of the las 7 days."""
    if since_tid is not None:
        params = {'trading_pair': trading_pair, 'since_tid': since_tid}
    else:
        params = {'trading_pair': trading_pair}
    return APIConnect(conn, 'GET', params, tradeuri + '/history')


def showRates(conn, trading_pair):
    """Query of the average rate last 3 and 12 hours."""
    newuri = apihost + '/' + apiversion + '/rates'
    params = {'trading_pair': trading_pair}
    return APIConnect(conn, 'GET', params, newuri)


def showAccountLedger(conn, **args):
    """Query on Account statement."""
    return APIConnect(conn, 'GET', args, accounturi + '/ledger')
