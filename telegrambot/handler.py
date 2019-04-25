from collections import defaultdict
from time import monotonic
from typing import Callable, Optional

from telegrambot.errors import HandlerError
from telegrambot.rules import _RuleType, _is_match, _prepare_rule
from telegrambot.types import Incoming, MessageType


class Handler:
    def __init__(self, handler: Callable, pause: int = None):
        if pause is not None and pause < 1:
            raise ValueError(f"The `pause` must be greater or equal 1")

        self.name = handler.__name__
        self.last_call = None
        self.pause = pause
        self._handler = handler

    async def __call__(self, *args, **kwargs):
        if self.last_call is None or self.pause is None or (monotonic() - self.last_call >= self.pause):
            await self._handler(*args, **kwargs)
            self.last_call = monotonic()

    def __repr__(self):
        return f"Handler({self.name}, {self.pause})"


class Handlers:
    def __init__(self, handler_cls: type(Handler) = Handler):
        self._handler_cls = handler_cls
        self._handlers = defaultdict(lambda: defaultdict(list))

    def get(self, incoming: Incoming, message_type: Optional[MessageType], raw: dict) -> Optional[Handler]:
        groups = (
            self._handlers[incoming][message_type],
            self._handlers[None][message_type],
            self._handlers[incoming][None],
            self._handlers[None][None]
        )

        for handlers in groups:
            for rule, handler in handlers:
                if _is_match(rule, incoming, message_type, raw):
                    return handler

    def add(
            self,
            incoming: Incoming = None,
            message_type: MessageType = None,
            rule: _RuleType = None,
            pause: int = None
    ):
        """Add handler"""

        if incoming is not None and not incoming.is_message_or_post:
            if message_type is not None:
                raise HandlerError("The `message_type` allowed only for message or post incoming")
            elif rule is not None:
                raise HandlerError("The `pattern` allowed only for message or post incoming")

        if rule is not None:
            rule = _prepare_rule(message_type, rule)

        def decorator(handler):
            for accepted_pattern, _ in self._handlers[incoming][message_type]:
                if accepted_pattern == rule:
                    raise HandlerError(
                        f"The handler with incoming={incoming}, message_type={message_type} \
                        and rule `{rule}` already in"
                    )

            self._handlers[incoming][message_type].append((rule, self._handler_cls(handler, pause)))
            # TODO: sort by priority:
            # - Exact match [Text, str, int]
            # - Contains (нужен ли этот шаблон?)
            # - RegExp
            # - None
        return decorator

    def __len__(self):
        result = 0
        for incoming_handlers in self._handlers.values():
            for message_type_handlers in incoming_handlers.values():
                result = len(message_type_handlers)
        return result
