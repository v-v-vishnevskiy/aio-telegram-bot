from typing import Callable, Optional

from aiotelegrambot.client import Client
from aiotelegrambot.types import Chat, Content, Incoming


class Message:
    def __init__(
            self,
            client: Client,
            raw: dict,
            ctx: dict,
            chat_type: Optional[Chat] = None,
            incoming: Optional[Incoming] = None,
            content_type: Optional[Content] = None
    ):
        self._client = client
        self.raw = raw
        self.ctx = ctx
        self.chat_type = chat_type
        self.incoming = incoming
        self.content_type = content_type

        if incoming is not None and incoming.is_message_or_post:
            self._chat_id = raw[incoming.value]["chat"]["id"]
            self._message_id = raw[incoming.value]["message_id"]
        else:
            self._chat_id = None
            self._message_id = None

    async def send_message(self, text: str, reply_to_message: bool = False):
        await self._client.send_message(text, self._chat_id, self._message_id if reply_to_message else None)

    @property
    def request(self) -> Callable:
        return self._client.request
