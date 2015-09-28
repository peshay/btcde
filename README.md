# btcde.py

A Python Module for the [Bitcoin.de Trading API](https://www.bitcoin.de/de/api/marketplace)

Requires: requests

## Install btcde.py

You can install the btcde module via pip

    pip install btcde

## How to Use

This is an example how you can use it in a python script
```python
#! /usr/bin/env python
import btcde
# create a object for the connection settings
api_key = <YourAPIKey>
api_secret = <YourAPISecret>
conn = btcde.Connection(api_key, api_secret)
