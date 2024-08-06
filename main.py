import sys
import argparse
from pybit.unified_trading import HTTP
import logging
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Open a market order on Bybit USDT perpetual market.')
    parser.add_argument('coin', type=str, help='Cryptocurrency symbol (e.g., BTC, ETH).')
    parser.add_argument('side', type=str, choices=['buy', 'sell'], help='Type of order (buy for long, sell for short).')
    parser.add_argument('order_value', type=float, help='Order value in USDT.')
    parser.add_argument('leverage', type=float, help='Leverage for the order.')

    return parser.parse_args()


def set_leverage(client, symbol, leverage):
    try:
        # Get current leverage
        position = client.get_positions(category="linear", symbol=symbol)
        current_leverage = position['result']['list'][0]['leverage']

        logger.info(f"Current leverage: {current_leverage}, Requested leverage: {leverage}")

        if float(current_leverage) == float(leverage):
            logger.info(f"Leverage is already set to {leverage}x. No need to modify.")
            return

        # Set new leverage
        response = client.set_leverage(
            category='linear',
            symbol=symbol,
            buyLeverage=str(leverage),
            sellLeverage=str(leverage)
        )
        logger.info(f"Leverage set response: {response}")
    except Exception as e:
        logger.error(f"Failed to set leverage: {e}")
        sys.exit(1)


def place_market_order(client, symbol, side, qty):
    try:
        response = client.place_order(
            category='linear',
            symbol=symbol,
            side=side,
            orderType='Market',
            qty=str(qty),
            marketUnit="quoteCoin",
            timeInForce='GoodTillCancel',
            reduceOnly=False,
            closeOnTrigger=False
        )
        logger.info(f"Market order response: {response}")
    except Exception as e:
        logger.error(f"Failed to place market order: {e}")
        sys.exit(1)


def main():
    # Load environment variables from .env file
    load_dotenv()

    # Get API credentials from environment variables
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')

    if not api_key or not api_secret:
        logger.error('API key and secret must be set in the environment variables.')
        sys.exit(1)

    args = parse_arguments()
    symbol = args.coin + 'USDT'
    order_value = args.order_value
    leverage = args.leverage
    side = 'Buy' if args.side == 'buy' else 'Sell'

    # Initialize Bybit client
    client = HTTP(
        api_key=api_key,
        api_secret=api_secret,
        recv_window=60000,
        testnet=True,
    )

    # Set leverage
    set_leverage(client, symbol, leverage)

    # Place market order
    place_market_order(client, symbol, side, order_value)


if __name__ == "__main__":
    main()
