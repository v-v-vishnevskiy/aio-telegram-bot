from enum import Enum
from functools import lru_cache


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

    for messate_type in MessageType:
        if isinstance(messate_type.value, tuple):
            first.append(messate_type)
        else:
            second.append(messate_type)
    return first + second
