import asyncio
import logging
from dataclasses import dataclass
from typing import Callable

import aiojobs

from telegrambot.client import Client
from telegrambot.errors import BotError
from telegrambot.handler import Handlers
from telegrambot.rules import RuleType
from telegrambot.types import MessageType

logger = logging.getLogger(__name__)


@dataclass
class Message:
    bot: "Bot"
    message: dict
    context: dict


class Bot:
    def __init__(self, client: Client, handlers: Handlers = None, context: dict = None):
        self.client = client
        self._handlers: Handlers = handlers or Handlers()
        self._context = context
        self._scheduler: aiojobs.Scheduler = None
        self._is_started = False
        self._update_id = None

    async def start(self, **kwargs):
        if self._is_started:
            return

        if not self._handlers:
            raise BotError("Can't start with no one handler")

        self._is_started = True
        self._scheduler = await aiojobs.create_scheduler(**kwargs)
        await self._scheduler.spawn(self._get_updates)

    async def stop(self):
        if not self._is_started:
            return

        self._is_started = False

        await self._scheduler.close()
        self._scheduler = None

        self._update_id = None

    def add_handler(self, handler: Callable, message_type: MessageType, rule: RuleType = None):
        self._handlers(message_type, rule)(handler)

    async def send_message(self, text: str, chat_id: int = None):
        # TODO: получить chat_id, при котором была вызвана эта функция
        await self.client.request("get", "sendMessage", params={"chat_id": chat_id, "text": text})

    async def _get_updates(self):
        while self._is_started:
            params = {}
            if self._update_id:
                params = {"offset": self._update_id}

            try:
                data: dict = await self.client.request("get", "getUpdates", params=params)

                for result in data["result"]:
                    handler = self._handlers.handler(result["message"])
                    if handler:
                        await self._scheduler.spawn(handler(Message(self, result["message"], self._context)))
                    self._update_id = max(result["update_id"], self._update_id)
                self._update_id += 1
            except asyncio.TimeoutError:
                logger.exception("Timeout")
            await asyncio.sleep(0.1)
