from enum import Enum
from functools import lru_cache
from typing import Optional, Tuple


class ChatType(Enum):
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


class Incoming(Enum):
    """Represents the type of incoming message"""
    NEW_MESSAGE = "message"
    EDITED_MESSAGE = "edited_message"
    CHANNEL_POST = "channel_post"
    EDITED_CHANNEL_POST = "edited_channel_post"

    @property
    def is_message_or_post(self):
        return self.name in (
            self.NEW_MESSAGE.name,
            self.EDITED_MESSAGE.name,
            self.CHANNEL_POST.name,
            self.EDITED_CHANNEL_POST.name
        )


class MessageType(Enum):
    ANIMATION = "animation"
    AUDIO = "audio"
    CODE = ("text", "entities", "code")
    COMMAND = ("text", "entities", "bot_command")
    CONTACT = "contact"
    DELETE_CHAT_PHOTO = "delete_chat_photo"
    DOCUMENT = "document"
    GAME = "game"
    EMAIL = ("text", "entities", "email")
    FILE = "file"
    HASHTAG = ("text", "entities", "hashtag")
    INVOICE = "invoice"
    LOCATION = "location"
    MENTION = ("text", "entities", "mention")
    NEW_CHAT_PHOTO = "new_chat_photo"
    NEW_CHAT_MEMBERS = "new_chat_members"
    NEW_CHAT_TITLE = "new_chat_title"
    LEFT_CHAT_MEMBER = "left_chat_member"
    PHONE_NUMBER = ("text", "entities", "phone_number")
    PHOTO = "photo"
    PINNED_MESSAGE = "pinned_message"
    POLL = "poll"
    STICKER = "sticker"
    SUCCESSFUL_PAYMENT = "successful_payment"
    TEXT = "text"
    URL = ("text", "entities", "url")
    VENUE = "venue"
    VIDEO = "video"
    VOICE = "voice"
    VIDEO_NOTE = "video_note"

    @property
    def has_entity(self):
        return isinstance(self.value, tuple)


@lru_cache(maxsize=1)
def _get_by_priority():
    first = []
    second = []

    for message_type in MessageType:
        if isinstance(message_type.value, tuple):
            first.append(message_type)
        else:
            second.append(message_type)
    return first + second


def _recognize_incoming(raw: dict) -> Optional[Incoming]:
    for incoming in Incoming:
        if incoming.value in raw:
            return incoming


def _recognize_type(raw: dict) -> Tuple[Optional[ChatType], Optional[Incoming], Optional[MessageType]]:
    incoming = _recognize_incoming(raw)
    if incoming is None:
        return None, None, None
    elif not incoming.is_message_or_post:
        return None, incoming, None
    raw = raw[incoming.value]

    chat_type = ChatType(raw["chat"]["type"])

    for m_type in _get_by_priority():
        entity_key = entity_type = None
        if isinstance(m_type.value, tuple):
            key, entity_key, entity_type = m_type.value
        else:
            key = m_type.value

        if key in raw:
            if not entity_key:
                return chat_type, incoming, m_type
            elif entity_key in raw:
                entity = raw[entity_key][0]
                if entity["offset"] == 0 and entity["type"] == entity_type:
                    return chat_type, incoming, m_type
