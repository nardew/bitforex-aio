import asyncio
import logging
import os
from datetime import datetime

from bitforex import enums
from bitforex.BitforexClient import BitforexClient
from bitforex.Pair import Pair
from bitforex.subscriptions import OrderBookSubscription, TradeSubscription, Ticker24hSubscription, TickerSubscription

LOG = logging.getLogger("bitforex")
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler())

print(f"Available loggers: {[name for name in logging.root.manager.loggerDict]}\n")

async def trade_update(response : dict) -> None:
	print(f"Callback trade_update: [{response}]")

async def order_book_update(response : dict) -> None:
	print(f"Callback order_book_update: [{response}]")

async def ticker_update(response : dict) -> None:
	print(f"Callback ticker_update: [{response}]")

async def run():
	print("STARTING BITFOREX CLIENT\n")

	# to retrieve your API/SEC key go to your bitforex account, create the keys and store them in APIKEY/SECKEY
	# environment variables
	api_key = os.environ['BITFOREXAPIKEY']
	sec_key = os.environ['BITFOREXSECKEY']

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

	# Websockets
	print("\nWEBSOCKETS\n")

	# Bundle several subscriptions into a single websocket
	client.compose_subscriptions([
		OrderBookSubscription(pair = Pair('ETH', 'BTC'), depth = "0", callbacks = [order_book_update]),
		TradeSubscription(pair = Pair('ETH', 'BTC'), size = "20", callbacks = [trade_update]),
	])

	# Execute all websockets asynchronously
	await client.start_subscriptions()

	await client.close()

if __name__ == "__main__":
	asyncio.run(run())
