import asyncio
import logging
from collections import defaultdict
from typing import Coroutine, Dict

import aiojobs

from telegrambot.client import Client
from telegrambot.errors import BotError
from telegrambot.types import MessageType

logger = logging.getLogger(__name__)


class Bot:

    def __init__(self, client: Client):
        self.client = client
        self._scheduler: aiojobs.Scheduler = None
        self._is_started = False

        # TODO: заменить дикты на списки
        self._default_handlers: Dict[MessageType, Coroutine] = {}
        self._handlers: Dict[MessageType, Dict[str, Coroutine]] = defaultdict(dict)

        self._update_id = None

    async def start(self, **kwargs):
        if self._is_started:
            return

        len_handlers = 0
        for handlers in self._handlers.values():
            len_handlers = len(handlers)

        if not self._default_handlers and not len_handlers:
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

    def set_default_handler(self, message_type: MessageType, coro: Coroutine):
        self._default_handlers[message_type] = coro

    def add_handler(self, message_type: MessageType, rule: str, coro: Coroutine):
        # TODO: rule скорее всего нужно сделать отдельным классом

        if not (isinstance(rule, str) and rule):
            raise BotError("The rule must be non empty string")

        if message_type is MessageType.COMMAND:
            if rule[0] != "/":
                rule = "/" + rule

        if rule in self._handlers[message_type]:
            raise BotError(f"The {message_type.name} handler with rule `{rule}` already in")

        self._handlers[message_type][rule] = coro

    async def _get_updates(self):
        while self._is_started:
            params = {}
            if self._update_id:
                params = {"offset": self._update_id}

            try:
                data: dict = await self.client.request("get", "getUpdates", params=params)

                for result in data["result"]:
                    self._update_id = max(result["update_id"], self._update_id)
                    message = result["message"]
                    # TODO: find handler and run it
                    # TODO: брать только последний handler из зарегистрированных

            except asyncio.TimeoutError:
                logger.exception("Timeout")
            await asyncio.sleep(0.1)
