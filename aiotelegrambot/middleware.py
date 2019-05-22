from functools import partial
from typing import Callable

from aiotelegrambot.handler import Handler
from aiotelegrambot.message import Message


def _append_middleware(middleware: Callable, prev_middleware: Callable) -> Callable:
    async def wrapper(message: Message, handler: Callable):
        _middleware = partial(middleware, handler=handler)
        await prev_middleware(message, _middleware)
    return wrapper


class Middlewares:
    def __init__(self):
        self._middleware = None

    def append(self, fn: Callable):
        if self._middleware is None:
            self._middleware = fn
        else:
            self._middleware = _append_middleware(fn, self._middleware)

    def extend(self, *fns: Callable):
        for fn in fns:
            self.append(fn)

    async def __call__(self, message: Message, handler: Handler):
        if self._middleware:
            await self._middleware(message, handler)
        else:
            await handler(message)
