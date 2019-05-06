import asyncio
import contextvars
from dataclasses import dataclass
from typing import Callable, Optional, Union

import aiojobs

from telegrambot.client import Client
from telegrambot.errors import BotError
from telegrambot.handler import Handler, Handlers
from telegrambot.types import ChatType, Incoming, MessageType, _recognize_type


@dataclass
class Message:
    bot: "Bot"
    raw: dict
    context: dict
    handler: Handler
    chat_type: Optional[ChatType]
    incoming: Optional[Incoming]
    message_type: Optional[MessageType]


class Bot:
    def __init__(self, client: Client, handlers: Handlers = None, context: dict = None):
        self.client = client
        self.handlers: Handlers = handlers or Handlers()
        self.context = context or {}
        self.__scheduler: Optional[aiojobs.Scheduler] = None
        self.__closed = True
        self.__update_id = 0
        self.__chat_id = contextvars.ContextVar("chat_id")

    async def initialize(self, *, webhooks: bool = False, interval: float = 0.1, **kwargs):
        if self.__closed is False:
            return

        if not self.handlers:
            raise BotError("Can't initialize with no one handler")

        self.__closed = False
        self.__scheduler = await aiojobs.create_scheduler(**kwargs)
        if webhooks is False:
            await self.__scheduler.spawn(self._get_updates(interval))

    async def close(self):
        if self.__closed:
            return

        self.__closed = True

        await self.__scheduler.close()
        self.__scheduler = None

        self.__update_id = 0

    def add_handler(self, handler: Callable, *args, **kwargs):
        self.handlers.add(*args, **kwargs)(handler)

    async def send_text(self, text: str, chat_id: int = None):
        chat_id = chat_id or self.__chat_id.get()
        await self.client.request("get", "sendMessage", params={"chat_id": chat_id, "text": text})

    async def process_update(self, data: dict):
        if self.__closed is True:
            raise RuntimeError("The bot isn't initialized")

        chat_type, incoming, message_type = _recognize_type(data)
        handler = self.handlers.get(chat_type, incoming, message_type, data)
        if handler:
            await self.__scheduler.spawn(
                self.__handler(handler, Message(self, data, self.context, handler, chat_type, incoming, message_type))
            )

    async def _get_updates(self, interval: float):
        while self.__closed is False:
            params = {"offset": self.__update_id} if self.__update_id else {}
            data = await self.client.request("get", "getUpdates", params=params)
            await self._process_updates(data)
            await asyncio.sleep(interval)

    async def _process_updates(self, data: Union[None, dict]):
        if data:
            for raw in data["result"]:
                await self.process_update(raw)
                self.__update_id = max(raw["update_id"], self.__update_id)
            self.__update_id += 1 if data["result"] else 0

    async def __handler(self, handler: Handler, message: Message):
        if message.incoming is not None and message.incoming.is_message_or_post:
            self.__chat_id.set(message.raw[message.incoming.value]["chat"]["id"])
        await handler(message)
