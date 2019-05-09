import asyncio
from typing import Callable, Optional, Union

import aiojobs

from telegrambot.client import Client
from telegrambot.errors import BotError
from telegrambot.handler import Handlers
from telegrambot.types import ChatType, Incoming, MessageType, _recognize_type


class Message:
    def __init__(
            self,
            client: Client,
            raw: dict,
            chat_type: Optional[ChatType],
            incoming: Optional[Incoming],
            message_type: Optional[MessageType]
    ):
        self.__client = client
        self.raw = raw
        self.chat_type = chat_type
        self.incoming = incoming
        self.message_type = message_type

        if incoming is not None and incoming.is_message_or_post:
            self.__chat_id = raw[incoming.value]["chat"]["id"]
        else:
            self.__chat_id = None

    async def send_message(self, text: str, chat_id: Union[int, str] = None):
        await self.__client.send_message(text, chat_id or self.__chat_id)

    @property
    def request(self) -> Callable:
        return self.__client.request


class Bot:
    def __init__(self, client: Client, handlers: Handlers = None):
        self.client = client
        self.handlers = handlers or Handlers()
        self.__scheduler = None
        self.__closed = True
        self.__update_id = 0
        self.__chat_id = {}

    async def initialize(self, *, webhooks: bool = False, interval: float = 0.1, **scheduler_options):
        if self.__closed is False:
            return

        if not self.handlers:
            raise BotError("Can't initialize with no one handler")

        self.__closed = False
        self.__scheduler = await aiojobs.create_scheduler(**scheduler_options)
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

    async def process_update(self, data: dict):
        if self.__closed is True:
            raise RuntimeError("The bot isn't initialized")

        chat_type, incoming, message_type = _recognize_type(data)
        handler = self.handlers.get(chat_type, incoming, message_type, data)
        await self.__scheduler.spawn(handler(Message(self.client, data, chat_type, incoming, message_type)))

    async def _get_updates(self, interval: float):
        while self.__closed is False:
            data = await self.client.get_updates(self.__update_id)
            await self._process_updates(data)
            await asyncio.sleep(interval)

    async def _process_updates(self, data: Union[None, dict]):
        if data:
            for raw in data["result"]:
                await self.process_update(raw)
                self.__update_id = max(raw["update_id"], self.__update_id)
            self.__update_id += 1 if data["result"] else 0
