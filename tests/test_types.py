import pytest

from aiotelegrambot import Chat, Content, Incoming
from aiotelegrambot.types import recognize_incoming, recognize_type


def test_is_message_or_post():
    assert Incoming.NEW_MESSAGE.is_message_or_post is True
    assert Incoming.EDITED_MESSAGE.is_message_or_post is True
    assert Incoming.CHANNEL_POST.is_message_or_post is True
    assert Incoming.EDITED_CHANNEL_POST.is_message_or_post is True


def test_has_entity():
    assert Content.CODE.has_entity is True
    assert Content.CONTACT.has_entity is False


def test_get_by_priority():
    first = []
    second = []
    for content_type in Content.get_by_priority():
        if isinstance(content_type.value, tuple):
            first.append(content_type)
        else:
            second.append(content_type)

    assert first == Content.get_by_priority()[:len(first)]
    assert second == Content.get_by_priority()[len(first):]

    cache_info = Content.get_by_priority.cache_info()
    assert cache_info.hits == 2
    assert cache_info.misses == 1


@pytest.mark.parametrize("field", [incoming.value for incoming in Incoming] + ["unknown"])
def test_recognize_incoming(field):
    data = {field: "value"}

    if field == "unknown":
        assert recognize_incoming(data) is None
    else:
        assert recognize_incoming(data) == Incoming(field)


@pytest.mark.parametrize(
    "data",
    [
        (
            {
                Incoming.NEW_MESSAGE.value: {
                    "text": "text",
                    "chat": {"type": Chat.PRIVATE.value}
                }
            },
            Chat.PRIVATE,
            Incoming.NEW_MESSAGE,
            Content.TEXT
        ),
        (
            {
                Incoming.NEW_MESSAGE.value: {
                    "text": "/stat today",
                    "chat": {"type": Chat.PRIVATE.value},
                    "entities": [{
                        "offset": 0,
                        "type": Content.COMMAND.value[2]
                    }]
                }
            },
            Chat.PRIVATE,
            Incoming.NEW_MESSAGE,
            Content.COMMAND
        ),
        (
            {
                Incoming.NEW_MESSAGE.value: {
                    "chat": {"type": Chat.PRIVATE.value}
                }
            },
            Chat.PRIVATE,
            Incoming.NEW_MESSAGE,
            None
        )
    ]
)
def test_recognize_type(data):
    data, chat_type, incoming, content_type = data
    assert recognize_type(data) == (chat_type, incoming, content_type)


def test_recognize_type_none(mocker):
    mocker.patch("aiotelegrambot.types.recognize_incoming", return_value=None)
    assert recognize_type(mocker.MagicMock()) == (None, None, None)


def test_recognize_type_incoming(mocker):
    incoming = mocker.MagicMock()
    incoming.is_message_or_post = False
    mocker.patch("aiotelegrambot.types.recognize_incoming", return_value=incoming)
    assert recognize_type(mocker.MagicMock()) == (None, incoming, None)
