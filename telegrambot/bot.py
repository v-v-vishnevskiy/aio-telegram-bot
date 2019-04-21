import asyncio
import logging
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple

import aiojobs

from telegrambot.client import Client
from telegrambot.errors import BotError
from telegrambot.rules import RuleType, prepare_rule
from telegrambot.types import MessageType, get_by_priority

logger = logging.getLogger(__name__)


class Bot:

    def __init__(self, client: Client):
        self.client = client
        self._scheduler: aiojobs.Scheduler = None
        self._is_started = False

        self._default_handlers: Dict[MessageType, Callable] = {}
        self._handlers: Dict[MessageType, List[Tuple[RuleType, Callable]]] = defaultdict(list)

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

    def add_handler(self, handler: Callable, message_type: MessageType, rule: RuleType = None):
        if rule is None:
            self._default_handlers[message_type] = handler
            return

        rule = prepare_rule(message_type, rule)

        for accepted_rule, _ in self._handlers[message_type]:
            if accepted_rule == rule:
                raise BotError(f"The {message_type.name} handler with rule `{rule}` already in")

        self._handlers[message_type].append((rule, handler))

    async def send_message(self, message: str):
        await self.client.request("get", "sendMessage", params={"chat_id": None, "text": message})

    async def _get_updates(self):
        while self._is_started:
            params = {}
            if self._update_id:
                self._update_id += 1
                params = {"offset": self._update_id}

            try:
                data: dict = await self.client.request("get", "getUpdates", params=params)

                for result in data["result"]:
                    self._update_id = max(result["update_id"], self._update_id)
                    message = result["message"]

                    message_type = self._message_type(message)
                    if not message_type:
                        continue

                    handler = None
                    for rule, handler in self._handlers[message_type]:
                        pass
                        # TODO: найти нужный обработчик
                    if not handler:
                        handler = self._default_handlers[message_type]
                    if handler:
                        await self._scheduler.spawn(handler(self, message))

            except asyncio.TimeoutError:
                logger.exception("Timeout")
            await asyncio.sleep(0.1)

    def _message_type(self, message: dict) -> Optional[MessageType]:
        for message_type in get_by_priority():
            entity_key = entity_type = None
            if isinstance(message_type.value, tuple):
                key, entity_key, entity_type = message_type.value
            else:
                key = message_type.value

            if key in message:
                if not entity_key:
                    return message_type
                elif entity_key in message:
                    entity = message[entity_key][0]
                    if entity["offset"] == 0 and entity["type"] == entity_type:
                        return message_type
