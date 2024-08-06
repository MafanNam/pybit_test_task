import argparse
import decimal
import inspect
import os
import time
from typing import Optional

from pybit import exceptions
from pybit.unified_trading import HTTP

import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("BYBIT_API_KEY")
SECRET_KEY = os.getenv("BYBIT_API_SECRET")


class FuturesOrders:
    def __init__(self, symbol: str, category: str = "linear"):
        """
        Конструктор класса и инициализация
        - клиента pybit
        - получение параметров и фильтров Инструмента
        """
        self.cl = HTTP(api_key=API_KEY, api_secret=SECRET_KEY, recv_window=60000, testnet=True)
        self.category = category
        self.symbol = symbol
        self.qty_decimals, self.min_qty = self.get_filters()

    def get_filters(self):
        """
        Фильтры заданного инструмента
        - мин размер ордера в Базовой Валюте,
        - макс размер ордера в БВ
        """
        r = self.cl.get_instruments_info(symbol=self.symbol, category=self.category)
        c = r.get('result', {}).get('list', [])[0]
        print(c)
        min_qty = c.get('lotSizeFilter', {}).get('minOrderQty', '0.0')
        qty_decimals = abs(decimal.Decimal(min_qty).as_tuple().exponent)
        min_qty = float(min_qty)

        self.log(qty_decimals, min_qty)
        return qty_decimals, min_qty

    def get_price(self):
        """
        Один из способов получения текущей цены
        """
        r = float(self.cl.get_tickers(category=self.category, symbol=self.symbol).get('result').get('list')[0].get(
            'ask1Price'))
        self.log(r)
        return r

    def get_position(self, key: Optional[str] = None):
        """
        Получаю текущую позицию
        :param key:
        :return:
        """
        r = self.cl.get_positions(category=self.category, symbol=self.symbol)
        p = r.get('result', {}).get('list', [])[0]
        qty = float(p.get('size', '0.0'))
        if qty <= 0.0: raise Exception("empty position")

        ret = dict(
            avg_price=float(p.get('avgPrice', '0.0')),
            side=p.get('side'),
            leverage=p.get("leverage"),
            unrel_pnl=float(p.get('unrealisedPnl', '0.0')),
            qty=qty
        )
        ret['rev_side'] = ("Sell", "Buy")[ret['side'] == 'Sell']
        self.log(ret)

        return ret.get(key) if key else ret

    def place_market_order_by_base(self, qty: float, side: str):
        """
        Размещение рыночного ордера с указанием размера ордера в Базовой Валюте (BTC, XRP, etc)
        :param qty:
        :param side:
        :return:
        """
        args = dict(
            category=self.category,
            symbol=self.symbol,
            side=side.capitalize(),
            orderType="Market",
            qty=self.floor_qty(qty),
            marketUnit="quoteCoin",
            timeInForce='GoodTillCancel',
            reduceOnly=False,
            closeOnTrigger=False,
            orderLinkId=f"{self.symbol}_{time.time()}"
        )
        self.log("args", args)

        r = self.cl.place_order(**args)
        self.log("result", r)

        return r

    def place_market_order_by_quote(self, quote: float, side: str):
        """
        Отправка ордера с размером позиции в Котируемой Валюте (USDT напр)
        имеет смысл только для контрактов
        """
        curr_price = self.get_price()
        qty = self.floor_qty(quote / curr_price)
        print(qty)
        if qty < self.min_qty: raise Exception(f"{qty} is to small")

        print(qty)

        self.place_market_order_by_base(qty, side)

    def set_leverage(self, leverage: float):
        """

        :param leverage:
        :return:
        """

        position = self.get_position()
        logger.info(f"TEST: {position}")
        current_leverage = position['leverage']

        logger.info(f"Current leverage: {current_leverage}, Requested leverage: {leverage}")

        if float(current_leverage) == float(leverage):
            logger.info(f"Leverage is already set to {leverage}x. No need to modify.")
            return

        # Set new leverage
        args = dict(
            category=self.category,
            symbol=self.symbol,
            buyLeverage=str(leverage),
            sellLeverage=str(leverage),
        )

        self.log("args", args)

        r = self.cl.set_leverage(**args)
        self.log("result", r)

        return r

    def log(self, *args):
        """
        Для удобного вывода из методов класса
        """
        caller = inspect.stack()[1].function
        print(f"* {caller}", self.symbol, "\n\t", args, "\n")

    def _floor(self, value, decimals: int):
        """
        Для аргументов цены нужно отбросить (округлить вниз)
        до колва знаков заданных в фильтрах цены
        """
        factor = 1 / (10 ** decimals)
        return (value // factor) * factor

    def floor_qty(self, value):
        return self._floor(value, self.qty_decimals)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Open a market order on Bybit USDT perpetual market.')
    parser.add_argument('coin', type=str, help='Cryptocurrency symbol (e.g., BTC, ETH).')
    parser.add_argument('side', type=str, choices=['buy', 'sell'], help='Type of order (buy for long, sell for short).')
    parser.add_argument('order_value', type=float, help='Order value in USDT.')
    parser.add_argument('leverage', type=float, help='Leverage for the order.')

    return parser.parse_args()


def main():
    args = parse_arguments()
    symbol = args.coin + 'USDT'
    order_value = args.order_value
    leverage = args.leverage
    side = 'Buy' if args.side == 'buy' else 'Sell'

    # logger.info(f"{type(order_value)}, {order_value}")

    try:
        f = FuturesOrders(symbol=symbol, category='linear')

        f.set_leverage(leverage)
        f.place_market_order_by_quote(order_value, side)
        f.get_position()
        pass

    except exceptions.InvalidRequestError as e:
        print("ByBit API Request Error", e.status_code, e.message, sep=" | ")
    except exceptions.FailedRequestError as e:
        print("HTTP Request Failed", e.status_code, e.message, sep=" | ")
    except Exception as e:
        raise e
        # print(e)


if __name__ == '__main__':
    main()
