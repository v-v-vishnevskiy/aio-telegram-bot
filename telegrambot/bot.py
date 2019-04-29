import asyncio
import contextvars
from dataclasses import dataclass
from typing import Callable, Optional, Union

import aiojobs

from telegrambot.client import Client
from telegrambot.errors import BotError
from telegrambot.handler import Handler, Handlers
from telegrambot.types import Incoming, MessageType, _recognize_type


@dataclass
class Message:
    bot: "Bot"
    raw: dict
    context: dict
    incoming: Optional[Incoming]
    message_type: Optional[MessageType]


class Bot:
    def __init__(self, client: Client, handlers: Handlers = None, context: dict = None):
        self.client = client
        self._handlers: Handlers = handlers or Handlers()
        self._context = context
        self._scheduler: Optional[aiojobs.Scheduler] = None
        self._closed = True
        self._update_id = 0
        self.__chat_id = contextvars.ContextVar("chat_id")

    async def initialize(self, *, webhooks: bool = False, **kwargs):
        if self._closed is False:
            return

        if len(self._handlers) == 0:
            raise BotError("Can't initialize with no one handler")

        self._closed = False
        self._scheduler = await aiojobs.create_scheduler(**kwargs)
        if webhooks is False:
            await self._scheduler.spawn(self._get_updates())

    async def close(self):
        if self._closed:
            return

        self._closed = True

        await self._scheduler.close()
        self._scheduler = None

        self._update_id = 0

    def add_handler(self, handler: Callable, *args, **kwargs):
        self._handlers.add(*args, **kwargs)(handler)

    async def send_text(self, text: str, chat_id: int = None):
        chat_id = chat_id or self.__chat_id.get()
        await self.client.request("get", "sendMessage", params={"chat_id": chat_id, "text": text})

    async def process_update(self, data: dict):
        if self._closed is True:
            raise RuntimeError("The bot isn't initialize")

        incoming, message_type = _recognize_type(data)
        handler = self._handlers.get(incoming, message_type, data)
        if handler:
            # TODO: не спаунить, если хэндлер не нужно запускать
            await self._scheduler.spawn(
                self.__handler(handler, Message(self, data, self._context, incoming, message_type))
            )

    async def _get_updates(self):
        while self._closed is False:
            params = {"offset": self._update_id} if self._update_id else {}
            data = await self.client.request("get", "getUpdates", params=params)
            await self._process_updates(data)
            await asyncio.sleep(0.1)

    async def _process_updates(self, data: Union[None, dict]):
        if data:
            for raw in data["result"]:
                await self.process_update(raw)
                self._update_id = max(raw["update_id"], self._update_id)
            self._update_id += 1 if data["result"] else 0

    async def __handler(self, handler: Handler, message: Message):
        if message.incoming is not None and message.incoming.is_message_or_post:
            self.__chat_id.set(message.raw[message.incoming.value]["chat"]["id"])
        await handler(message)
