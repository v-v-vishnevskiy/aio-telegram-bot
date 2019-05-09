import aiohttp
import logging

from typing import Dict, Optional


try:
    from ujson import dumps, loads
except ImportError:
    from json import dumps, loads

logger = logging.getLogger(__name__)


class Client:
    base_url = "https://api.telegram.org/bot"

    def __init__(self, token: str, **kwargs):
        self._url = "{}{}/".format(self.base_url, token)

        session_kwargs = {
            "timeout": aiohttp.ClientTimeout(total=1),
            "json_serialize": dumps
        }
        session_kwargs.update(kwargs)

        self._session = aiohttp.ClientSession(**session_kwargs)

    async def close(self):
        await self._session.close()

    async def request(self, method: str, api: str, **kwargs) -> Optional[Dict]:
        url = self._url + api

        async with getattr(self._session, method)(url, **kwargs) as response:
            data = loads(await response.text())
            if response.status == 200:
                if data["ok"]:
                    return data
                else:
                    logger.error("Unsuccessful request", extra=data)
            else:
                logger.error("Status: {}".format(response.status), extra=data)
                if response.status >= 500:
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=response.status,
                        message=response.reason,
                        headers=response.headers
                    )
