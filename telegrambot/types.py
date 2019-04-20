from enum import Enum, auto


class MessageType(Enum):
    ANIMATION = auto()
    AUDIO = auto()
    COMMAND = auto()
    CONTACT = auto()
    GAME = auto()
    FILE = auto()
    LOCATION = auto()
    PHOTO = auto()
    POLL = auto()
    STICKER = auto()
    TEXT = auto()
    VENUE = auto()
    VIDEO = auto()
    VOICE = auto()
    VIDEO_NOTE = auto()
