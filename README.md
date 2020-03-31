# bitforex-aio 1.0.1

**Announcement:** `bitforex-aio` has been replaced by a new library [`cryptoxlib-aio`](https://github.com/nardew/cryptoxlib-aio). `cryptoxlib-aio` offers the very same functionality as `bitforex-aio` but on top it provides access to multiple cryptoexchanges and other (mostly technical) new features. You can keep using `bitforex-aio` but please note no new features/bugfixes will be implemented. We recommend to migrate to `cryptoxlib-aio`.

----

[![](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-365/) [![](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-374/)

`bitforex-aio` is a Python library providing access to [Bitforex crypto exchange](https://www.bitforex.com). Library implements Bitforex's REST API as well as websockets.

`bitforex-aio` is designed as an asynchronous library utilizing modern features of Python and of supporting asynchronous libraries (mainly [async websockets](https://websockets.readthedocs.io/en/stable/) and [aiohttp](https://aiohttp.readthedocs.io/en/stable/)).

For changes see [CHANGELOG](https://github.com/nardew/bitforex-aio/blob/master/CHANGELOG.md).

### Features
- access to full Bitforex's REST API (account details, market data, order management, ...) and websockets
- channels bundled in one or multiple websockets processed in parallel 
- transparent connection management (automated heartbeats, ...)
- lean architecture setting ground for the future extensions and customizations
- fully asynchronous design aiming for the best performance

### Installation
```bash
pip install bitforex-aio
```

### Prerequisites

Due to dependencies and Python features used by the library please make sure you use Python `3.6` or `3.7`.

Before starting using `bitforex-aio`, it is necessary to take care of downloading your Bitforex API and SECRET key from your Bitforex account.

### Examples
#### REST API
```python
client = BitforexClient(api_key, sec_key)

# REST api calls
print("REST API")

print("\nExchange info:")
await client.get_exchange_info()

print("\nOrder book:")
await client.get_order_book(pair = Pair('ETH', 'BTC'), depth = "1")

print("\nTicker:")
await client.get_ticker(pair = Pair('ETH', 'BTC'))

print("\nSingle fund:")
await client.get_single_fund(currency = "NOBS")

print("\nFunds:")
await client.get_funds()

print("\nTrades:")
await client.get_trades(pair = Pair('ETH', 'BTC'), size = "1")

print("\nCandelsticks:")
await client.get_candlesticks(pair = Pair('ETH', 'BTC'), interval = enums.CandelstickInterval.I_1W, size = "5")

print("\nCreate order:")
await client.create_order(Pair("ETH", "BTC"), side = enums.OrderSide.SELL, quantity = "1", price = "1")

print("\nCreate multiple orders:")
await client.create_multi_order(Pair("ETH", "BTC"),
                                orders = [("1", "1", enums.OrderSide.SELL), ("2", "1", enums.OrderSide.SELL)])

print("\nCancel order:")
await client.cancel_order(pair = Pair('ETH', 'BTC'), order_id = "10")

print("\nCancel multiple orders:")
await client.cancel_multi_order(pair = Pair('ETH', 'BTC'), order_ids = ["10", "20"])

print("\nCancel all orders:")
await client.cancel_all_orders(pair = Pair('ETH', 'BTC'))

print("\nGet order:")
await client.get_order(pair = Pair('ETH', 'BTC'), order_id = "1")

print("\nGet orders:")
await client.get_orders(pair = Pair('ETH', 'BTC'), order_ids = ["1", "2"])

print("\nFind orders:")
await client.find_order(pair = Pair('ETH', 'BTC'), state = enums.OrderState.PENDING)
```

#### WEBSOCKETS
```python
client = BitforexClient(api_key, sec_key)

client.compose_subscriptions([
    OrderBookSubscription(pair = Pair('ETH', 'BTC'), depth = "0", callbacks = [order_book_update]),
    TradeSubscription(pair = Pair('ETH', 'BTC'), size = "20", callbacks = [trade_update]),
])

# Execute all websockets asynchronously
await client.start_subscriptions()

await client.close()
```

All examples can be found in `client-example/client.py` in the GitHub repository.

### Support

If you like the library and you feel like you want to support its further development, enhancements and bugfixing, then it will be of great help and most appreciated if you:
- file bugs, proposals, pull requests, ...
- spread the word
- donate an arbitrary tip
  * BTC: 15JUgVq3YFoPedEj5wgQgvkZRx5HQoKJC4
  * ETH: 0xf29304b6af5831030ba99aceb290a3a2129b993d
  * ADA: DdzFFzCqrhshyLV3wktXFvConETEr9mCfrMo9V3dYz4pz6yNq9PjJusfnn4kzWKQR91pWecEbKoHodPaJzgBHdV2AKeDSfR4sckrEk79
  * XRP: rhVWrjB9EGDeK4zuJ1x2KXSjjSpsDQSaU6 **+ tag** 599790141

### Contact

If you feel you want to get in touch, then please

- preferably use Github Issues, or
- send an e-mail to <img src="http://safemail.justlikeed.net/e/8701dfa9bd62d1de196684aa746f9d32.png" border="0" align="absbottom">

### Affiliation

In case you are interested in an automated trading bot, check out our other project [creten](https://github.com/nardew/creten).
