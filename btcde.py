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
import http.client
http.client.HTTPConnection.debuglevel = 1


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

__version__ = '0.1'


class Connection:
    """To provide connection credentials to the trading API"""
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

# Bitcoin.de API URI
apihost = 'https://api.bitcoin.de'
apiversion = 'v1'
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
    if r.status_code != 200 and r.status_code != 201 and r.status_code != 204:
        reader = codecs.getreader("utf-8")
        content = json.load(reader(r.raw))
        errors = content.get('errors')
        print('Code:     ' + str(errors[0]['code']))
        print('Message:  ' + errors[0]['message'])
        print('With URL: ' + r.url)
        return False
    else:
        return True


def APIConnect(conn, method, params, uri):
    """Transform Parameters to URL"""
    global nonce
    # set header
    header = {'content-type':
              'application/x-www-form-urlencoded; charset=utf-8'}
    encoded_string = ''
    if params:
        for key, value in sorted(params.items()):
            encoded_string += str(key) + '=' + str(value) + '&'
        encoded_string = encoded_string[:-1]
        url = uri + '?' + encoded_string
    else:
        url = uri
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
    # set values for header
    header.update({'X-API-KEY': conn.api_key,
                   'X-API-NONCE': str(nonce),
                   'X-API-SIGNATURE': hmac_signed})
    try:
        if method == 'GET':
            r = requests.get(url, headers=(header),
                             stream=True, verify=False)
        elif method == 'POST':
            r = requests.post(url, headers=(header), data=encoded_string,
                              stream=True, verify=False)
        elif method == 'DELETE':
            r = requests.delete(url, headers=(header),
                                stream=True, verify=False)
        # Handle API Errors
        if HandleAPIErrors(r):
            # get results
            result = r.json()
        else:
            result = {}
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)
    return result


def showOrderbook(conn, OrderType, **args):
    """Search Orderbook for offers."""
    # Build parameters
    if OrderType == 'buy' or OrderType == 'sell':
        params = {'type': OrderType}
    else:
        print('problem')
    params.update(args)
    return APIConnect(conn, 'GET', params, orderuri)


def createOrder(conn, OrderType, max_amount, price, **args):
    """Create a new Order."""
    # Build parameters
    params = {'type': OrderType, 'max_amount': max_amount, 'price': price}
    params.update(args)
    return APIConnect(conn, 'POST', params, orderuri)


def deleteOrder(conn, order_id):
    """Delete an Order."""
    newuri = orderuri + ":" + order_id
    return APIConnect(conn, 'DELETE', order_id, newuri)


def showMyOrders(conn, **args):
    """Query and Filter own Orders."""
    newuri = orderuri + '/my_own'
    return APIConnect(conn, 'GET', args, newuri)


def showMyOrderDetails(conn, order_id):
    """Details to an own Order."""
    newuri = orderuri + '/:' + order_id
    params = {'order_id': order_id}
    return APIConnect(conn, 'GET', params, newuri)


def executeTrade(conn, order_id, OrderType, amount):
    """Buy/Sell on a specific Order."""
    newuri = tradeuri + '/:' + order_id
    params = {'order_id': order_id, 'type': OrderType, 'amount': amount}
    return APIConnect(conn, 'POST', params, newuri)


def showMyTrades(conn, **args):
    """Query and Filter on past Trades."""
    return APIConnect(conn, 'GET', args, tradeuri)


def showMyTradeDetails(conn, trade_id):
    """Details to a specific Trade."""
    newuri = tradeuri + '/:' + trade_id
    params = {'trade_id': trade_id}
    return APIConnect(conn, 'GET', params, newuri)


def showAccountInfo(conn):
    """Query on Account Infos."""
    params = {}
    return APIConnect(conn, 'GET', params, accounturi)


def showOrderbookCompact(conn):
    """Bids and Asks in compact format."""
    params = {}
    return APIConnect(conn, 'GET', params, orderuri + '/compact')


def showPublicTradeHistory(conn, since_tid=None):
    """All successful trades of the las 7 days."""
    if since_tid is not None:
        params = {'since_tid': since_tid}
    else:
        params = {}
    return APIConnect(conn, 'GET', params, tradeuri + '/history')


def showRates(conn):
    """Query of the average rate last 3 and 12 hours."""
    newuri = apihost + '/' + apiversion + '/rates'
    params = {}
    return APIConnect(conn, 'GET', params, newuri)


def showAccountLedger(conn, **args):
    """Query on Account statement."""
    return APIConnect(conn, 'GET', args, accounturi + '/ledger')
