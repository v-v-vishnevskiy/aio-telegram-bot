import asyncio
import logging
from typing import Callable, Union

import aiohttp
import aiojobs

from aiotelegrambot.client import Client
from aiotelegrambot.errors import BotError, TelegramApiError
from aiotelegrambot.handler import Handlers
from aiotelegrambot.message import Message
from aiotelegrambot.middleware import Middlewares
from aiotelegrambot.types import recognize_type

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, client: Client, handlers: Handlers = None):
        self.client = client
        self.handlers = handlers or Handlers()
        self.middlewares = Middlewares()
        self._scheduler = None
        self._closed = True
        self._update_id = 0
        self.ctx = {}

    async def initialize(self, *, webhook: bool = False, interval: float = 0.1, **scheduler_options):
        if self._closed is False:
            return

        if not self.handlers:
            raise BotError("Can't initialize with no one handler")

        self._closed = False
        self._scheduler = await aiojobs.create_scheduler(**scheduler_options)
        if webhook is False:
            await self._scheduler.spawn(self._get_updates(interval))

    async def close(self):
        if self._closed:
            return

        self._closed = True

        for job in self._scheduler:
            await job.wait()

        await self._scheduler.close()
        self._scheduler = None

        self._update_id = 0

    def add_handler(self, handler: Callable, *args, **kwargs):
        self.handlers.add(*args, **kwargs)(handler)

    async def process_update(self, data: dict):
        if self._closed is True:
            raise RuntimeError("The bot isn't initialized")

        chat_type, incoming, content_type = recognize_type(data)
        handler = self.handlers.get(chat_type, incoming, content_type, data)
        await self._scheduler.spawn(
            self.middlewares(Message(self.client, data, self.ctx, chat_type, incoming, content_type), handler)
        )

    async def _get_updates(self, interval: float):
        while self._closed is False:
            try:
                data = await self.client.get_updates(self._update_id)
                await self._process_updates(data)
                await asyncio.sleep(interval)
            except TelegramApiError as e:
                self.client.process_error(str(e), e.response, e.data, False)
                if e.response.status >= 500:
                    await asyncio.sleep(30)
                else:
                    await asyncio.sleep(10)
            except asyncio.TimeoutError as e:
                logger.exception(str(e))
            except aiohttp.ClientError as e:
                logger.exception(str(e))
                await asyncio.sleep(10)

    async def _process_updates(self, data: Union[None, dict]):
        if data:
            for raw in data["result"]:
                await self.process_update(raw)
                self._update_id = max(raw["update_id"], self._update_id)
            self._update_id += 1 if data["result"] else 0
