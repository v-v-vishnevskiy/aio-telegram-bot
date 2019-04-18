import aiohttp
import logging

from typing import Any, Dict, Optional


try:
    from ujson import dumps, loads
except ModuleNotFoundError:
    from json import dumps, loads

logger = logging.getLogger(__name__)


class TelegramBot:
    base_url = "https://api.telegram.org/bot"

    def __init__(self, token: str, **kwargs):
        self._url = self.base_url + f"{token}/"

        self._session_kwargs = self._default_kwargs
        self._session_kwargs.update(kwargs)

        self._session: aiohttp.ClientSession = None

    async def start(self):
        self._session = await self._make_session()

    async def stop(self):
        await self._session.close()

    @property
    def _default_kwargs(self) -> Dict[str, Any]:
        return {
            "timeout": aiohttp.ClientTimeout(total=1),
            "json_serialize": dumps
        }

    async def _make_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(**self._session_kwargs)

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
                logger.error(f"Status: {response.status}", extra=data)
                if response.status >= 500:
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=response.status,
                        message=response.reason,
                        headers=response.headers
                    )
