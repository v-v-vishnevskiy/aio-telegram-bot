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
        self.__middleware = None

    def append(self, fn: Callable):
        if self.__middleware is None:
            self.__middleware = fn
        else:
            self.__middleware = _append_middleware(fn, self.__middleware)

    def extend(self, *fns: Callable):
        for fn in fns:
            self.append(fn)

    async def __call__(self, message: Message, handler: Handler):
        if self.__middleware:
            await self.__middleware(message, handler)
        else:
            await handler(message)
