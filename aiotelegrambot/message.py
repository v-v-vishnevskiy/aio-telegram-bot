from typing import Callable, Optional, Union

from aiotelegrambot.client import Client
from aiotelegrambot.types import Chat, Incoming, Content


class Message:
    def __init__(
            self,
            client: Client,
            raw: dict,
            chat_type: Optional[Chat] = None,
            incoming: Optional[Incoming] = None,
            content_type: Optional[Content] = None
    ):
        self._client = client
        self.raw = raw
        self.chat_type = chat_type
        self.incoming = incoming
        self.content_type = content_type

        if incoming is not None and incoming.is_message_or_post:
            self._chat_id = raw[incoming.value]["chat"]["id"]
        else:
            self._chat_id = None

    async def send_message(self, text: str, chat_id: Union[int, str] = None):
        await self._client.send_message(text, chat_id or self._chat_id)

    @property
    def request(self) -> Callable:
        return self._client.request
