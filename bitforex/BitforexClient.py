import asyncio
import aiohttp
import hmac
import hashlib
import ssl
import logging
import datetime
import json
from typing import List, Optional, Tuple

from bitforex.BitforexException import BitforexException
from bitforex import enums
from bitforex.subscriptions import SubscriptionMgr, Subscription
from bitforex.Timer import Timer
from bitforex.Pair import Pair

LOG = logging.getLogger(__name__)

class BitforexClient(object):
	REST_API_URI = "https://api.bitforex.com/api/v1/"

	def __init__(self, api_key : str = None, sec_key : str = None,
	             api_trace_log : bool = False, ssl_context : ssl.SSLContext = None) -> None:
		self.api_key = api_key
		self.sec_key = sec_key
		self.api_trace_log = api_trace_log

		self.rest_session = None

		if ssl_context is not None:
			self.ssl_context = ssl_context
		else:
			self.ssl_context = ssl.create_default_context()

		self.subscription_sets = []

	async def get_exchange_info(self) -> dict:
		return await self._create_get("market/symbols")

	async def get_order_book(self, pair : Pair, depth : str = None) -> dict:
		params = BitforexClient._clean_request_params({
			"symbol": str(pair),
			"size": depth,
		})

		return await self._create_get("market/depth", params = params)

	async def get_ticker(self, pair : Pair) -> dict:
		params = BitforexClient._clean_request_params({
			"symbol": str(pair)
		})

		return await self._create_get("market/ticker", params = params, signed = True)

	async def get_candlesticks(self, pair : Pair, interval : enums.CandelstickInterval, size : str = None) -> dict:
		params = BitforexClient._clean_request_params({
			"symbol": str(pair),
			"ktype": interval.value,
			"size": size
		})

		return await self._create_get("market/kline", params = params, signed = True)

	async def get_trades(self, pair : Pair, size : str = None) -> dict:
		params = BitforexClient._clean_request_params({
			"symbol": str(pair),
			"size": size
		})

		return await self._create_get("market/trades", params = params, signed = True)

	async def get_single_fund(self, currency : str) -> dict:
		params = BitforexClient._clean_request_params({
			"currency": currency.lower(),
			"nonce": self._get_current_timestamp_ms()
		})

		return await self._create_post("fund/mainAccount", params = params, signed = True)

	async def get_funds(self) -> dict:
		params = BitforexClient._clean_request_params({
			"nonce": self._get_current_timestamp_ms()
		})

		return await self._create_post("fund/allAccount", params = params, signed = True)

	async def create_order(self, pair : Pair, price : str, quantity : str, side : enums.OrderSide) -> dict:
		params = BitforexClient._clean_request_params({
			"symbol": str(pair),
			"price": price,
			"amount": quantity,
			"tradeType": side.value,
			"nonce": self._get_current_timestamp_ms()
		})

		return await self._create_post("trade/placeOrder", params = params, signed = True)

	# orders is a list of tuples where each tuple represents an order. Members of the tuple represent following attributes:
	# (price, quantity, side)
	async def create_multi_order(self, pair : Pair, orders : List[Tuple[str, str, enums.OrderSide]]) -> dict:
		orders_data = []
		for order in orders:
			orders_data.append({
				"price": order[0],
				"amount": order[1],
				"tradeType": order[2].value,
			})

		params = BitforexClient._clean_request_params({
			"symbol": str(pair),
			"ordersData": orders_data,
			"nonce": self._get_current_timestamp_ms()
		})

		return await self._create_post("trade/placeMultiOrder", params = params, signed = True)

	async def cancel_order(self, pair : Pair, order_id : str) -> dict:
		params = BitforexClient._clean_request_params({
			"symbol": str(pair),
			"orderId": order_id,
			"nonce": self._get_current_timestamp_ms()
		})

		return await self._create_post("trade/cancelOrder", params = params, signed = True)

	async def cancel_multi_order(self, pair : Pair, order_ids : List[str]) -> dict:
		params = BitforexClient._clean_request_params({
			"symbol": str(pair),
			"orderIds": ",".join(order_ids),
			"nonce": self._get_current_timestamp_ms()
		})

		return await self._create_post("trade/cancelMultiOrder", params = params, signed = True)

	async def cancel_all_orders(self, pair : Pair) -> dict:
		params = BitforexClient._clean_request_params({
			"symbol": str(pair),
			"nonce": self._get_current_timestamp_ms()
		})

		return await self._create_post("trade/cancelAllOrder", params = params, signed = True)

	async def get_order(self, pair : Pair, order_id : str) -> dict:
		params = BitforexClient._clean_request_params({
			"symbol": str(pair),
			"orderId": order_id,
			"nonce": self._get_current_timestamp_ms()
		})

		return await self._create_post("trade/orderInfo", params = params, signed = True)

	async def find_order(self, pair : Pair, state : enums.OrderState, side : enums.OrderSide = None) -> dict:
		params = BitforexClient._clean_request_params({
			"symbol": str(pair),
			"state": state.value,
			"nonce": self._get_current_timestamp_ms()
		})

		if side:
			params["tradeType"] = side.value

		return await self._create_post("trade/orderInfos", params = params, signed = True)

	async def get_orders(self, pair : Pair, order_ids : List[str]) -> dict:
		params = BitforexClient._clean_request_params({
			"symbol": str(pair),
			"orderIds": ",".join(order_ids),
			"nonce": self._get_current_timestamp_ms()
		})

		return await self._create_post("trade/multiOrderInfo", params = params, signed = True)

	def compose_subscriptions(self, subscriptions : List[Subscription]) -> None:
		self.subscription_sets.append(subscriptions)

	async def start_subscriptions(self) -> None:
		if len(self.subscription_sets):
			done, pending = await asyncio.wait(
				[asyncio.create_task(SubscriptionMgr(subscriptions, self.api_key, self.ssl_context).run()) for subscriptions in self.subscription_sets],
				return_when = asyncio.FIRST_EXCEPTION
			)
			for task in done:
				try:
					task.result()
				except Exception as e:
					LOG.exception(f"Unrecoverable exception occurred while processing messages: {e}")
					LOG.info("All websockets scheduled for shutdown")
					for task in pending:
						if not task.cancelled():
							task.cancel()
		else:
			raise Exception("ERROR: There are no subscriptions to be started.")

	async def close(self) -> None:
		session = self._get_rest_session()
		if session is not None:
			await session.close()

	async def _create_get(self, resource : str, params : dict = None, headers : dict = None, signed : bool = False) -> dict:
		return await self._create_rest_call(enums.RestCallType.GET, resource, None, params, headers, signed)

	async def _create_post(self, resource : str, data : dict = None, params : dict = None, headers : dict = None, signed : bool = False) -> dict:
		return await self._create_rest_call(enums.RestCallType.POST, resource, data, params, headers, signed)

	async def _create_delete(self, resource : str, params : dict = None, headers : dict = None, signed : bool = False) -> dict:
		return await self._create_rest_call(enums.RestCallType.DELETE, resource, None, params, headers, signed)

	async def _create_put(self, resource : str, params : dict = None, headers : dict = None, signed : bool = False) -> dict:
		return await self._create_rest_call(enums.RestCallType.PUT, resource, None, params, headers, signed)

	async def _create_rest_call(self, rest_call_type : enums.RestCallType, resource : str, data : dict = None, params : dict = None, headers : dict = None, signed : bool = False) -> dict:
		with Timer('RestCall'):
			# add signature into the parameters
			if signed:
				params = {} if params is None else params
				params['accessKey'] = self.api_key
				params['signData'] = self._get_signature(resource, params, data)

			if rest_call_type == enums.RestCallType.GET:
				rest_call = self._get_rest_session().get(BitforexClient.REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
			elif rest_call_type == enums.RestCallType.POST:
				rest_call = self._get_rest_session().post(BitforexClient.REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
			elif rest_call_type == enums.RestCallType.DELETE:
				rest_call = self._get_rest_session().delete(BitforexClient.REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
			elif rest_call_type == enums.RestCallType.PUT:
				rest_call = self._get_rest_session().put(BitforexClient.REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
			else:
				raise Exception(f"Unsupported REST call type {rest_call_type}.")

			LOG.debug(f"> rest type [{rest_call_type.name}], resource [{resource}], params [{params}], headers [{headers}], data [{data}]")
			async with rest_call as response:
				status_code = response.status
				response_body = await response.text()

				LOG.debug(f"<: status [{status_code}], response [{response_body}]")

				if str(status_code)[0] != '2':
					raise BitforexException(f"<: status [{status_code}], response [{response_body}]")

				if len(response_body) > 0:
					response_body = json.loads(response_body)

				return {
					"status_code": status_code,
					"response": response_body
				}

	def _get_rest_session(self) -> aiohttp.ClientSession:
		if self.rest_session is not None:
			return self.rest_session

		if self.api_trace_log:
			trace_config = aiohttp.TraceConfig()
			trace_config.on_request_start.append(BitforexClient._on_request_start)
			trace_config.on_request_end.append(BitforexClient._on_request_end)
			trace_configs = [trace_config]
		else:
			trace_configs = None

		self.rest_session = aiohttp.ClientSession(trace_configs=trace_configs)

		return self.rest_session

	@staticmethod
	def _clean_request_params(params : dict) -> dict:
		res = {}
		for key, value in params.items():
			if value is not None:
				res[key] = str(value)

		return res

	async def _on_request_start(session, trace_config_ctx, params) -> None:
		LOG.debug(f"> Context: {trace_config_ctx}")
		LOG.debug(f"> Params: {params}")

	async def _on_request_end(session, trace_config_ctx, params) -> None:
		LOG.debug(f"< Context: {trace_config_ctx}")
		LOG.debug(f"< Params: {params}")

	@staticmethod
	def _get_current_timestamp_ms() -> int:
		return int(datetime.datetime.now(tz = datetime.timezone.utc).timestamp() * 1000)

	def _get_signature(self, resource : str, params : dict, data : dict) -> str:
		params_string = ""
		data_string = ""

		if params is not None:
			params_string = '/api/v1/' + resource + '?'
			params_string += '&'.join([f"{key}={val}" for key, val in sorted(params.items())])

		if data is not None:
			data_string = '&'.join(["{}={}".format(param[0], param[1]) for param in data])

		m = hmac.new(self.sec_key.encode('utf-8'), (params_string+data_string).encode('utf-8'), hashlib.sha256)
		return m.hexdigest()