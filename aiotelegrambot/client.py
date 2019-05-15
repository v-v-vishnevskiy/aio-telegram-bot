import logging
from json import dumps, loads
from typing import Callable, List, Optional, Union

import aiohttp

logger = logging.getLogger(__name__)


class Client:
    base_url = "https://api.telegram.org/bot"

    def __init__(self, token: str, json_loads: Callable = loads, **kwargs):
        self._url = "{}{}/".format(self.base_url, token)

        session_kwargs = {
            "timeout": aiohttp.ClientTimeout(total=1)
        }
        session_kwargs.update(kwargs)

        self._json_loads = json_loads
        self._session = aiohttp.ClientSession(**session_kwargs)

    async def close(self):
        await self._session.close()

    async def get_updates(
            self,
            offset: Optional[Union[int, str]] = None,
            limit: Optional[Union[int, str]] = None,
            timeout: Optional[Union[int, str]] = None
    ) -> Optional[dict]:
        params = {}
        if offset:
            params["offset"] = offset
        if limit:
            params["limit"] = limit
        if timeout:
            params["timeout"] = timeout
        return await self.request("get", "getUpdates", params=params)

    async def set_webhook(
            self,
            url: str,
            certificate: Optional[str] = None,
            max_connections: Optional[int] = None,
            allowed_updates: Optional[List[str]] = None
    ) -> Optional[dict]:
        kwargs = {
            "params": [("url", url)]
        }
        if certificate:
            kwargs["data"] = {"certificate": open(certificate, "r")}
        if max_connections is not None:
            kwargs["params"].append(("max_connections", max_connections))
        if allowed_updates is not None:
            kwargs["params"].append(("allowed_updates", dumps(allowed_updates)))
        return await self.request("post", "setWebhook", **kwargs)

    async def get_webhook_info(self) -> Optional[dict]:
        return await self.request("get", "getWebhookInfo")

    async def delete_webhook(self) -> Optional[dict]:
        return await self.request("get", "deleteWebhook")

    async def send_message(self, text: str, chat_id: Union[int, str]):
        await self.request("get", "sendMessage", params={"chat_id": chat_id, "text": text})

    async def request(self, method: str, api: str, **kwargs) -> Optional[dict]:
        url = self._url + api

        async with getattr(self._session, method)(url, **kwargs) as response:
            text = await response.text()
            if response.status == 200:
                data = self._json_loads(text)
                if data["ok"]:
                    return data
                else:
                    logger.error("Unsuccessful request", extra=data)
            else:
                logger.error("Status: {}".format(response.status), extra=text)
                if response.status >= 500:
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=response.status,
                        message=response.reason,
                        headers=response.headers
                    )
