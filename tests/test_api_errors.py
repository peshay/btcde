from decimal import Decimal

import pytest
import requests
from requests_mock import ANY

import btcde

ERRORS = [
    {'code': 8, 'message': 'Insufficient API credits'},
    {'code': 9, 'message': 'Try again later'},
]


@pytest.mark.parametrize('method', ['GET', 'POST', 'DELETE'])
def test_api_errors_are_optional(requests_mock, method):
    params = btcde.ParameterBuilder({}, {}, 'https://example.test/v4/fixture')
    requests_mock.register_uri(method, params.url, status_code=429,
                               json={'errors': ERRORS})
    conn = btcde.Connection('fixture-key', 'fixture-secret', ssl_verify=True)

    assert conn.APIConnect(method, params) == {}


@pytest.mark.parametrize('method', ['GET', 'POST', 'DELETE'])
def test_raises_all_api_errors_with_response(requests_mock, method):
    params = btcde.ParameterBuilder({}, {}, 'https://example.test/v4/fixture')
    requests_mock.register_uri(method, params.url, status_code=429,
                               json={'errors': ERRORS},
                               headers={'Retry-After': '30'})
    conn = btcde.Connection('fixture-key', 'fixture-secret', ssl_verify=True,
                            raise_api_errors=True)

    with pytest.raises(btcde.APIError) as raised:
        conn.APIConnect(method, params)

    error = raised.value
    assert error.errors == ERRORS
    assert error.response.status_code == 429
    assert error.response.headers['Retry-After'] == '30'
    assert error.response.url == params.url
    assert '8: Insufficient API credits' in str(error)
    assert '9: Try again later' in str(error)
    assert requests_mock.call_count == 1


def test_public_method_propagates_api_error(requests_mock):
    requests_mock.get(ANY, status_code=400,
                      json={'errors': ERRORS})
    conn = btcde.Connection('fixture-key', 'fixture-secret', ssl_verify=True,
                            raise_api_errors=True)

    with pytest.raises(btcde.APIError) as raised:
        conn.showOrderbook('buy', 'btceur')

    assert raised.value.errors[0]['code'] == 8
    assert requests_mock.last_request.method == 'GET'


@pytest.mark.parametrize('status_code', [200, 201])
def test_successful_responses_keep_decimal_parsing(requests_mock, status_code):
    requests_mock.get(ANY, status_code=status_code,
                      text='{"credits": 42, "price": 0.1}')
    conn = btcde.Connection('fixture-key', 'fixture-secret', ssl_verify=True,
                            raise_api_errors=True)

    assert conn.showRates('btceur') == {'credits': 42, 'price': Decimal('0.1')}


def test_empty_success_response_does_not_raise_api_error(requests_mock):
    requests_mock.get(ANY, status_code=204)
    conn = btcde.Connection('fixture-key', 'fixture-secret', ssl_verify=True,
                            raise_api_errors=True)

    assert conn.showRates('btceur') == {}


@pytest.mark.parametrize('raise_api_errors', [False, True])
def test_transport_errors_keep_existing_handling(requests_mock, raise_api_errors):
    requests_mock.get(ANY, exc=requests.exceptions.ConnectionError)
    conn = btcde.Connection('fixture-key', 'fixture-secret', ssl_verify=True,
                            raise_api_errors=raise_api_errors)

    assert conn.showRates('btceur') == {}
