# Bybit Order Script

A Python script to interact with the Bybit API for opening market orders on the Bybit USDT perpetual market. The script
allows you to place market orders with specified leverage and order value.

### Features

- Place market orders (buy/sell) on the Bybit USDT perpetual market.
- Set leverage for the order.
- Designed for the Bybit Testnet environment.

![run1](https://raw.githubusercontent.com/MafanNam/pybit_test_task/main/assets/run1.png)
![order1](https://raw.githubusercontent.com/MafanNam/pybit_test_task/main/assets/order1.png)

![run2](https://raw.githubusercontent.com/MafanNam/pybit_test_task/main/assets/run2.png)
![order2](https://raw.githubusercontent.com/MafanNam/pybit_test_task/main/assets/order2.png)

![run3](https://raw.githubusercontent.com/MafanNam/pybit_test_task/main/assets/run3.png)
![order3](https://raw.githubusercontent.com/MafanNam/pybit_test_task/main/assets/order3.png)

![all_orders](https://raw.githubusercontent.com/MafanNam/pybit_test_task/main/assets/all_orders.png)

### Requirements

- Python 3.10 or later
- `pybit` library for interacting with the Bybit API
- A Bybit Testnet account

### Setup

1. Register on Bybit Testnet:
    - Sign up for a Bybit Testnet account here.
    - Follow the instructions here to request test coins.

2. Clone repository:

```bash
$ git clone https://github.com/MafanNam/pybit_test_task.git
$ cd pybit_test_task
```

3. Create and activate virtual env:

```bash
$ pip install virtualenv
$ python -m virtualenv venv
$ .\venv\Scripts\activate
$ # or linux
$ source venv/bin/activate
```

2. Install Dependencies:
   Ensure you have `pybit` and `pytest` installed. You can install them using pip:

```bash
$ pip install -r requirements.txt
```

## Environment Variables

To run this project, you will need to add the following environment variables to your `.env` file.
`.env.example` only for example

`BYBIT_API_KEY`= <YOUR_BYBIT_API_KEY>

`BYBIT_API_SECRET`= <YOUR_BYBIT_API_SECRET>

## Script Usage

To use the script, run the following command:

```bash
$ python bybit_order.py <Coin> <Buy/Sell> <Order Value in USDT> <Leverage>
```

### Example

```bash
$ python bybit_order.py BTC buy 1000 10
```

This command will open a long position (buy) on BTC with a value of 1000 USDT and leverage of 10x.

## Script Details

`bybit_order.py`

The script performs the following actions:

1. Set Leverage:
    - Configures the leverage for the specified cryptocurrency pair.

2. Place Market Order:
    - Opens a market order with the given value and leverage.

3. Error Handling:
    - Includes error handling for API requests and responses.

### Arguments

- `Coin`: The cryptocurrency symbol (e.g., BTC, ETH).
- `Buy/Sell`: The type of order (buy for long, sell for short).
- `Order Value in USDT`: The total value of the order in USDT.
- `Leverage`: The leverage to be used for the order.

## Unit Tests

Unit tests are written using `pytest`. To run the tests, use the following command:

```bash
$ pytest bybit_order.py
```