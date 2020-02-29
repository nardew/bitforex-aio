# bitforex-aio 1.0.0.

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
```

#### WEBSOCKETS
```python
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