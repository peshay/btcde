#! /usr/bin/env python
"""This Module provides the functions from bitcoin.de Trading API"""

import requests
import time
from colorama import Fore
import json

__version__ = '0.1'


class Connection:
    """To provide connection credentials to the trading API"""
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

# set header
header = {'content-type': 'application/json; charset=utf-8'}

# set initial nonce
nonce = int(time.time())


def HandleRequestsException(e):
    """Handle Exception from request."""
    print(Fore.RED + e[0][0])
    print(Fore.RED + e[0][1])


def HandleAPIErrors(r):
    """To handle Errors from BTCDE API."""
    if r.status_code != 200 and r.status_code != 201 and r.status_code != 204:
        content = json.load(r.raw)
