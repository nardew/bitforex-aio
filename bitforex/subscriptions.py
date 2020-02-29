import websockets
import json
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import List, Callable, Any

from bitforex.Pair import Pair
from bitforex import enums
from bitforex.PeriodicChecker import PeriodicChecker

LOG = logging.getLogger(__name__)

class Subscription(ABC):
	def __init__(self, callbacks = None):
		self.callbacks = callbacks

	@abstractmethod
	def get_channel_name(self) -> str:
		pass

	@abstractmethod
	def get_params(self) -> dict:
		pass

	async def initialize(self) -> None:
		pass

	async def process_message(self, response : dict) -> None:
		await self.process_callbacks(response)

	async def process_callbacks(self, response : dict) -> None:
		if self.callbacks is not None:
			await asyncio.gather(*[asyncio.create_task(cb(response)) for cb in self.callbacks])


class SubscriptionMgr(object):
	WEB_SOCKET_URI = "wss://www.bitforex.com/mkapi/coinGroup1/ws"

	def __init__(self, subscriptions : List[Subscription], api_key : str, ssl_context = None):
		self.api_key = api_key
		self.ssl_context = ssl_context

		self.subscriptions = subscriptions

		self.ping_checker = PeriodicChecker(period_ms = 30 * 1000)

	async def run(self) -> None:
		for subscription in self.subscriptions:
			await subscription.initialize()

		try:
			# main loop ensuring proper reconnection after a graceful connection termination by the remote server
			while True:
				LOG.debug(f"Initiating websocket connection.")
				async with websockets.connect(SubscriptionMgr.WEB_SOCKET_URI, ping_interval = None, ssl = self.ssl_context) as websocket:
					subscription_message = self._create_subscription_message()
					LOG.debug(f"> {subscription_message}")
					await websocket.send(json.dumps(subscription_message))

					# start processing incoming messages
					while True:
						response = await websocket.recv()
						LOG.debug(f"< {response}")

						if response != "pong_p":
							await self.process_message(json.loads(await websocket.recv()))

						if self.ping_checker.check():
							LOG.debug(f"> ping_p")
							await websocket.send("ping_p")
		except asyncio.CancelledError:
			LOG.warning(f"Websocket requested to be shutdown.")
		except Exception:
			LOG.error(f"Exception occurred. Websocket will be closed.")
			raise

	def _create_subscription_message(self) -> List[dict]:
		subscription_message = []
		for subscription in self.subscriptions:
			subscription_message.append({
				"type": "subHq",
				"event": subscription.get_channel_name(),
				"param": subscription.get_params(),
			})

		return subscription_message

	async def process_message(self, response : dict) -> None:
		for subscription in self.subscriptions:
			if subscription.get_channel_name() == response["event"]:
				await subscription.process_message(response["data"])
				break

class OrderBookSubscription(Subscription):
	def __init__(self, pair : Pair, depth : str, callbacks : List[Callable[[dict], Any]] = None):
		super().__init__(callbacks)

		self.pair = pair
		self.depth = depth

	def get_channel_name(self):
		return "depth10"

	def get_params(self):
		return {
			"businessType": str(self.pair),
			"dType": self.depth
		}

class Ticker24hSubscription(Subscription):
	def __init__(self, pair : Pair, callbacks : List[Callable[[dict], Any]] = None):
		super().__init__(callbacks)

		self.pair = pair

	def get_channel_name(self):
		return "ticker"

	def get_params(self):
		return {
			"businessType": str(self.pair)
		}

class TickerSubscription(Subscription):
	def __init__(self, pair : Pair, size : str, interval = enums.CandelstickInterval, callbacks : List[Callable[[dict], Any]] = None):
		super().__init__(callbacks)

		self.pair = pair
		self.size = size
		self.interval = interval

	def get_channel_name(self):
		return "kline"

	def get_params(self):
		return {
			"businessType": str(self.pair),
			"size": self.size,
			"kType": self.interval.value
		}

class TradeSubscription(Subscription):
	def __init__(self, pair : Pair, size : str, callbacks: List[Callable[[dict], Any]] = None):
		super().__init__(callbacks)

		self.pair = pair
		self.size = size

	def get_channel_name(self):
		return "trade"

	def get_params(self):
		return {
			"businessType": str(self.pair),
			"size": self.size
		}