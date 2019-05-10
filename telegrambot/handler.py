from collections import defaultdict
from typing import Callable, Optional

from telegrambot.errors import HandlerError
from telegrambot.rules import _RuleType, _is_match, _prepare_rule
from telegrambot.types import ChatType, Incoming, MessageType


class Handler:
    def __init__(
            self,
            handler: Optional[Callable] = None,
            chat_type: Optional[ChatType] = None,
            incoming: Optional[Incoming] = None,
            message_type: Optional[MessageType] = None,
            rule: Optional[_RuleType] = None
    ):
        self.name = handler.__name__ if handler else None
        self.chat_type = chat_type
        self.incoming = incoming
        self.message_type = message_type
        self.rule = rule
        self._handler = handler

    @property
    def priority(self):
        if hasattr(self.rule, "priority"):
            return self.rule.priority
        return 1000000

    async def __call__(self, *args, **kwargs):
        if self:
            await self._handler(*args, **kwargs)

    def __bool__(self):
        return self._handler is not None

    def __hash__(self):
        return hash((self.name, self.chat_type, self.incoming, self.message_type, self.rule))

    def __repr__(self):
        return "Handler({}, {}, {}, {}, {})".format(
            self.name, self.chat_type, self.incoming, self.message_type, self.rule
        )


class Handlers:
    def __init__(self, handler_cls: type(Handler) = Handler):
        self._handler_cls = handler_cls
        self._handlers = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self.__default_handler = handler_cls()

    def get(
            self,
            chat_type: ChatType,
            incoming: Incoming,
            message_type: Optional[MessageType],
            raw: dict
    ) -> Optional[Handler]:
        for _chat_type in (chat_type, None):
            for _incoming in (incoming, None):
                for _message_type in (message_type, None):
                    for handler in self._handlers[_chat_type][_incoming][_message_type] or []:
                        if _is_match(handler.rule, incoming, message_type, raw):
                            return handler
        return self.__default_handler

    def add(
            self,
            chat_type: ChatType = None,
            incoming: Incoming = None,
            message_type: MessageType = None,
            rule: _RuleType = None
    ) -> Callable:
        """Add handler"""

        if incoming is not None and not incoming.is_message_or_post:
            if message_type is not None:
                raise HandlerError("The `message_type` allowed only for message or post incoming")
            elif rule is not None:
                raise HandlerError("The `pattern` allowed only for message or post incoming")

        if rule is not None:
            rule = _prepare_rule(message_type, rule)

        def decorator(handler: Callable):
            if not callable(handler):
                raise ValueError("The `handler` must be callable type")

            for h in self._handlers[chat_type][incoming][message_type]:
                if h.rule == rule:
                    raise HandlerError(
                        "The handler with chat_type={}, incoming={}, message_type={} and rule `{}` already in.".format(
                            chat_type, incoming, message_type, rule
                        )
                    )

            self._handlers[chat_type][incoming][message_type].append(
                self._handler_cls(handler, chat_type, incoming, message_type, rule)
            )
            self._handlers[chat_type][incoming][message_type].sort(key=lambda x: x.priority)
            return handler
        return decorator

    def __bool__(self) -> bool:
        return bool(self._handlers)
