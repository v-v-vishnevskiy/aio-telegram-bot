from typing import Optional

from aiohttp.client import ClientResponse


class BotError(Exception):
    pass


class TelegramApiError(BotError):

    def __init__(self, msg: str, data: Optional[dict], response: ClientResponse):
        self.data = data
        self.response = response
        super().__init__(msg)


class HandlerError(BotError):
    pass


class RuleError(BotError):
    pass
