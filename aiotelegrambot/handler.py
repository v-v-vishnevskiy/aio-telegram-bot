from collections import defaultdict
from typing import Callable, Optional

from aiotelegrambot.errors import HandlerError
from aiotelegrambot.rules import _RuleType, is_match, prepare_rule
from aiotelegrambot.types import Chat, Content, Incoming


class Handler:
    def __init__(
            self,
            handler: Optional[Callable] = None,
            chat_type: Optional[Chat] = None,
            incoming: Optional[Incoming] = None,
            content_type: Optional[Content] = None,
            rule: Optional[_RuleType] = None
    ):
        self.name = handler.__name__ if handler else None
        self.chat_type = chat_type
        self.incoming = incoming
        self.content_type = content_type
        self.rule = rule
        self.handler = handler

    @property
    def priority(self):
        if hasattr(self.rule, "priority"):
            return self.rule.priority
        return 1000000

    async def __call__(self, *args, **kwargs):
        if self:
            await self.handler(*args, **kwargs)

    def __bool__(self):
        return self.handler is not None

    def __hash__(self):
        return hash((self.name, self.chat_type, self.incoming, self.content_type, self.rule))

    def __repr__(self):
        return "Handler({}, {}, {}, {}, {})".format(
            self.name, self.chat_type, self.incoming, self.content_type, self.rule
        )


class Handlers:
    def __init__(self, handler_cls: type(Handler) = Handler):
        self._handler_cls = handler_cls
        self._handlers = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self._default_handler = handler_cls()

    def get(
            self,
            chat_type: Chat,
            incoming: Incoming,
            content_type: Optional[Content],
            raw: dict
    ) -> Optional[Handler]:
        for _chat_type in (chat_type, None):
            for _incoming in (incoming, None):
                for _content_type in (content_type, None):
                    for handler in self._handlers[_chat_type][_incoming][_content_type] or []:
                        if handler.rule is None or is_match(handler.rule, incoming, content_type, raw):
                            return handler
        return self._default_handler

    def add(
            self,
            chat_type: Chat = None,
            incoming: Incoming = None,
            content_type: Content = None,
            rule: _RuleType = None
    ) -> Callable:
        """Add handler"""

        if incoming is not None and not incoming.is_message_or_post:
            if content_type is not None:
                raise HandlerError("The `content_type` allowed only for message or post incoming")
            elif rule is not None:
                raise HandlerError("The `rule` allowed only for message or post incoming")

        if rule is not None:
            rule = prepare_rule(content_type, rule)

        def decorator(handler: Callable):
            if not callable(handler):
                raise ValueError("The `handler` must be callable type")

            for h in self._handlers[chat_type][incoming][content_type]:
                if h.rule == rule:
                    raise HandlerError(
                        "The handler with chat_type={}, incoming={}, content_type={} and rule `{}` already in.".format(
                            chat_type, incoming, content_type, rule
                        )
                    )

            self._handlers[chat_type][incoming][content_type].append(
                self._handler_cls(handler, chat_type, incoming, content_type, rule)
            )
            self._handlers[chat_type][incoming][content_type].sort(key=lambda x: x.priority)
            return handler
        return decorator

    def __bool__(self) -> bool:
        return bool(self._handlers)
