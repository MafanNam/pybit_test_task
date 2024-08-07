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
        Class constructor and initialization
        - pybit client
        - Getting Tool parameters and filters
        """
        self.cl = HTTP(api_key=API_KEY, api_secret=SECRET_KEY, recv_window=60000, testnet=True)
        self.category = category
        self.symbol = symbol
        self.qty_decimals, self.min_qty = self.get_filters()

    def get_filters(self):
        """
        Filters of a given instrument
        - min order size in Base Currency,
        - max order size in BW
        """
        res = self.cl.get_instruments_info(symbol=self.symbol, category=self.category)
        rl = res.get('result', {}).get('list', [])[0]
        min_qty = rl.get('lotSizeFilter', {}).get('minOrderQty', '0.0')
        qty_decimals = abs(decimal.Decimal(min_qty).as_tuple().exponent)
        min_qty = float(min_qty)

        self.log(qty_decimals, min_qty)
        return qty_decimals, min_qty

    def get_price(self):
        """
        Method of obtaining the current price
        """
        res = float(self.cl.get_tickers(category=self.category, symbol=self.symbol).get('result').get('list')[0].get(
            'ask1Price'))
        self.log(res)
        return res

    def get_position(self, key: Optional[str] = None):
        """
        Getting the current position
        """
        res = self.cl.get_positions(category=self.category, symbol=self.symbol)
        if not res.get('result', {}).get('list'):
            return None
        rl = res.get('result', {}).get('list', [])[0]
        qty = float(res.get('size', '0.0'))

        if qty <= 0.0:
            return None

        ret = dict(
            avg_price=float(rl.get('avgPrice', '0.0')),
            side=rl.get('side'),
            leverage=rl.get("leverage"),
            unrel_pnl=float(rl.get('unrealisedPnl', '0.0')),
            qty=qty
        )
        ret['rev_side'] = ("Sell", "Buy")[ret['side'] == 'Sell']
        self.log(ret)

        return ret.get(key) if key else ret

    def place_market_order_by_base(self, qty: float, side: str):
        """
        Placing a market order specifying the order size in Base Currency (BTC, XRP, etc)
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

        res = self.cl.place_order(**args)
        self.log("result", res)

        return res

    def place_market_order_by_quote(self, quote: float, side: str):
        """
        Sending an order with position size in Quoted Currency (USDT e.g.)
        makes sense only for contracts
        """
        curr_price = self.get_price()
        qty = self.floor_qty(quote / curr_price)
        if qty < self.min_qty:
            raise Exception(f"{qty} is to small")

        self.place_market_order_by_base(qty, side)

    def set_leverage(self, leverage: float):
        """
        Sending an order with position size in Quoted Currency (USDT e.g.) for contracts only
        """

        position = self.cl.get_positions(category=self.category, symbol=self.symbol)

        try:
            current_leverage = position['result']['list'][0]['leverage']
            logger.info(f"Current leverage: {current_leverage}, Requested leverage: {leverage}")
        except Exception as e:
            logger.error(f"Failed to get leverage: {e}")
            return

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

        res = self.cl.set_leverage(**args)
        self.log("result", res)

        return res

    def log(self, *args):
        """
        For convenient derivation from the methods of the class
        """
        caller = inspect.stack()[1].function
        print(f"* {caller}", self.symbol, "\n\t", args, "\n")

    @staticmethod
    def _floor(value, decimals: int):
        """
        For the price arguments, you need to round down
        to the number of digits set in the price filters
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

    try:
        f = FuturesOrders(symbol=symbol, category='linear')

        f.set_leverage(leverage)
        f.place_market_order_by_quote(order_value, side)
        f.get_position()
        pass

    except exceptions.InvalidRequestError as e:
        logger.error(f"ByBit API Request Error | {e.status_code} | {e.message}")
    except exceptions.FailedRequestError as e:
        logger.error(f"HTTP Request Failed | {e.status_code} | {e.message}")
    except Exception as e:
        logger.error(f"Other Error | {e}")

    logger.info(f"Market order on {symbol} {side} for {order_value} USDT with leverage {leverage}x")


if __name__ == '__main__':
    main()
