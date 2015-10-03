#! /usr/bin/env python
"""This Module provides the functions from bitcoin.de Trading API"""

import requests
import time
import json
import hmac
import hashlib

__version__ = '0.1'


class Connection:
    """To provide connection credentials to the trading API"""
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

# Bitcoin.de API URI
uri = 'https://api.bitcoin.de/v1/orders'
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
        content = json.load(r.raw)
        errors = content.get('errors')
        print('Code:     ' + str(errors[0]['code']))
        print('Message:  ' + errors[0]['message'])
        print('With URL: ' + r.url)
        return False
    else:
        return True


def getQuery(conn, params):
    """Transform Parameters to URL"""
    global uri
    global nonce
    # set header
    header = {'content-type': 'application/json; charset=utf-8'}
    encoded_string = ''
    for key, value in sorted(params.iteritems()):
        encoded_string += str(key) + '=' + str(value) + '&'
    encoded_string = encoded_string[:-1]
    url = uri + '?' + encoded_string
    md5_encoded_query_string = hashlib.md5("").hexdigest()
    # raise nonce before using
    nonce += 1
    # build the signature
    hmac_data = 'GET' + '#' \
                + url + '#' + conn.api_key \
                + '#' + str(nonce) + '#' + md5_encoded_query_string
    hmac_signed = hmac.new(conn.api_secret,
                           digestmod=hashlib.sha256, msg=hmac_data).hexdigest()
    # set values for header
    header.update({'X-API-KEY': conn.api_key,
                   'X-API-NONCE': nonce,
                   'X-API-SIGNATURE': hmac_signed})
    # try to connect and handle errors
    try:
        r = requests.get(url, headers=(header), stream=True, verify=False)
        # Handle API Errors
        if HandleAPIErrors(r):
            # get results
            result = r.json()
        else:
            result = {}
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)
    return result


def postQuery(conn, params):
    """Transform Parameters to URL"""
    global uri
    global nonce
    # set header
    header = {'content-type': 'application/json; charset=utf-8'}
    encoded_string = ''
    for key, value in sorted(params.iteritems()):
        encoded_string += str(key) + '=' + str(value) + '&'
    encoded_string = encoded_string[:-1]
    print (encoded_string)
    url = uri + '?' + encoded_string
    print (url)
    md5_encoded_query_string = hashlib.md5(encoded_string).hexdigest()
    print (md5_encoded_query_string)
    # raise nonce before using
    nonce += 1
    print (nonce)
    # build the signature
    hmac_data = 'POST' + '#' \
                + uri + '#' + conn.api_key \
                + '#' + str(nonce) + '#' + md5_encoded_query_string
    print (hmac_data)
    hmac_signed = hmac.new(conn.api_secret,
                           digestmod=hashlib.sha256, msg=hmac_data).hexdigest()
    print (hmac_signed)
    # set values for header
    header.update({'X-API-KEY': conn.api_key,
                   'X-API-NONCE': nonce,
                   'X-API-SIGNATURE': hmac_signed})
    print (header)
    # transform params to json
    DATA = json.dumps(params)
    print (DATA)
    # try to connect and handle errors
    try:
        r = requests.post(url, data=DATA, headers=(header),
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
