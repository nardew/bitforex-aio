import asyncio
import aiohttp
import hmac
import hashlib
import ssl
import logging
import datetime
import json
from typing import List, Optional

from bitforex.BitforexException import BitforexException
from bitforex import enums
from bitforex.subscriptions import SubscriptionMgr, Subscription
from bitforex.Timer import Timer

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

	async def get_listen_key(self):
		return await self._create_post("userDataStream", headers = self._get_header_api_key())

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
			# add signature into parameters
			if signed:
				params = {} if params is None else params
				params['signature'] = self._get_signature(params, data)

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

	def _get_header_api_key(self):
		header = {
			'Accept': 'application/json',
			"X-MBX-APIKEY": self.api_key
		}

		return header

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

	def _get_signature(self, params : dict, data : dict) -> str:
		params_string = ""
		data_string = ""

		if params is not None:
			params_string = '&'.join([f"{key}={val}" for key, val in params.items()])

		if data is not None:
			data_string = '&'.join(["{}={}".format(param[0], param[1]) for param in data])

		m = hmac.new(self.sec_key.encode('utf-8'), (params_string+data_string).encode('utf-8'), hashlib.sha256)
		return m.hexdigest()