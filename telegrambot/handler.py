from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple

from telegrambot.errors import BotError
from telegrambot.rules import RuleType, is_match, prepare_rule
from telegrambot.types import MessageType, recognize_message_type


class Handlers:
    def __init__(self):
        self._default_handlers: Dict[MessageType, Callable] = {}
        self._handlers: Dict[MessageType, List[Tuple[RuleType, Callable]]] = defaultdict(list)

    def handler(self, message: dict) -> Optional[Callable]:
        message_type = recognize_message_type(message)
        if not message_type:
            return

        for rule, handler in reversed(self._handlers[message_type]):
            if is_match(rule, message_type, message):
                break
        else:
            handler = None
        if not handler:
            handler = self._default_handlers.get(message_type)
        return handler

    def __call__(self, message_type: MessageType, rule: RuleType = None):
        def decorator(handler):
            nonlocal rule, message_type

            if rule is None:
                self._default_handlers[message_type] = handler
                return

            rule = prepare_rule(message_type, rule)

            for accepted_rule, _ in self._handlers[message_type]:
                if accepted_rule == rule:
                    raise BotError(f"The {message_type.name} handler with rule `{rule}` already in")

            self._handlers[message_type].append((rule, handler))
        return decorator

    def __bool__(self):
        len_handlers = 0
        for handlers in self._handlers.values():
            len_handlers = len(handlers)

        return bool(self._default_handlers or len_handlers)
