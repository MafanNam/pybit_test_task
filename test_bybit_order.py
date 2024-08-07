import time

import pytest
from pybit import exceptions
from bybit_order import FuturesOrders
from pybit.unified_trading import HTTP


@pytest.fixture
def mock_http(mocker):
    mock_http = mocker.patch.object(HTTP, 'get_instruments_info', return_value={
        'result': {
            'list': [{
                'lotSizeFilter': {'minOrderQty': '0.001'}
            }]
        }
    })
    mocker.patch.object(HTTP, 'get_tickers', return_value={
        'result': {'list': [{'ask1Price': '10000.0'}]}
    })
    mocker.patch.object(HTTP, 'get_positions', return_value={
        'result': {'list': [{
            'avgPrice': '10000.0',
            'side': 'Buy',
            'leverage': '10',
            'unrealisedPnl': '0.0',
            'size': '1.0'
        }]}
    })
    mocker.patch.object(HTTP, 'place_order', return_value={'result': 'success'})
    mocker.patch.object(HTTP, 'set_leverage', return_value={'result': 'success'})
    return mock_http


def test_get_filters(mock_http):
    f = FuturesOrders(symbol='BTCUSDT')
    assert f.qty_decimals == 3
    assert f.min_qty == 0.001


def test_get_price(mock_http):
    f = FuturesOrders(symbol='BTCUSDT')
    price = f.get_price()
    assert price == 10000.0


def test_place_market_order_by_base(mock_http):
    f = FuturesOrders(symbol='BTCUSDT')
    response = f.place_market_order_by_base(qty=0.01, side='Buy')
    assert response == {'result': 'success'}


def test_place_market_order_by_quote(mock_http):
    f = FuturesOrders(symbol='BTCUSDT')
    f.place_market_order_by_quote(quote=1000.0, side='Buy')
    mock_http.place_order(
        category='linear',
        symbol='BTCUSDT',
        side='Buy',
        orderType='Market',
        qty=0.1,  # 1000 / 10000 rounded down
        marketUnit='quoteCoin',
        timeInForce='GoodTillCancel',
        reduceOnly=False,
        closeOnTrigger=False,
        orderLinkId=f'BTCUSDT_{time.time()}'
    )


def test_set_leverage(mock_http):
    f = FuturesOrders(symbol='BTCUSDT')
    response = f.set_leverage(20)
    assert response == {'result': 'success'}


def test_floor_qty(mock_http):
    f = FuturesOrders(symbol='BTCUSDT')
    assert f.floor_qty(0.1234) == 0.123


def test_handle_invalid_request_error(mock_http, mocker):
    mocker.patch.object(HTTP, 'place_order', side_effect=exceptions.InvalidRequestError(
        status_code=400, message='Invalid request', time=time.time(), resp_headers={}, request={}))
    f = FuturesOrders(symbol='BTCUSDT')
    with pytest.raises(exceptions.InvalidRequestError):
        f.place_market_order_by_base(qty=0.01, side='Buy')


def test_handle_failed_request_error(mock_http, mocker):
    mocker.patch.object(HTTP, 'place_order', side_effect=exceptions.FailedRequestError(
        status_code=500, message='Request failed', time=time.time(), resp_headers={}, request={}))
    f = FuturesOrders(symbol='BTCUSDT')
    with pytest.raises(exceptions.FailedRequestError):
        f.place_market_order_by_base(qty=0.01, side='Buy')


def test_handle_general_exception(mock_http, mocker):
    mocker.patch.object(HTTP, 'place_order', side_effect=Exception('General error'))
    f = FuturesOrders(symbol='BTCUSDT')
    with pytest.raises(Exception):
        f.place_market_order_by_base(qty=0.01, side='Buy')
