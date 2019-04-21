from enum import Enum
from functools import lru_cache
from typing import Optional


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


@lru_cache(maxsize=1)
def get_by_priority():
    first = []
    second = []

    for message_type in MessageType:
        if isinstance(message_type.value, tuple):
            first.append(message_type)
        else:
            second.append(message_type)
    return first + second


def recognize_message_type(message: dict) -> Optional[MessageType]:
    for m_type in get_by_priority():
        entity_key = entity_type = None
        if isinstance(m_type.value, tuple):
            key, entity_key, entity_type = m_type.value
        else:
            key = m_type.value

        if key in message:
            if not entity_key:
                return m_type
            elif entity_key in message:
                entity = message[entity_key][0]
                if entity["offset"] == 0 and entity["type"] == entity_type:
                    return m_type
