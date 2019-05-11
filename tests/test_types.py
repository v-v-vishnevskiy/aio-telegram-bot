from typing import Any, Iterable

import pytest

from aiotelegrambot import Chat, Content, Incoming
from aiotelegrambot.types import recognize_incoming, recognize_type


def messages(chat_type: Iterable=Chat, incoming: Iterable=Incoming, content_type: Iterable=Content) -> list:
    result = []
    for is_bot in (False, True):
        for _chat_type in chat_type:
            for _incoming in incoming:
                for _content_type in content_type:
                    data = {
                        "update_id": 12674014,
                        _incoming.value: {
                            "message_id": 2465,
                            "from": {
                                "id": 201191853,
                                "is_bot": is_bot,
                                "first_name": "Valery",
                                "last_name": "Vishnevskiy",
                                "language_code": "root"
                            },
                            "chat": {
                                "id": 123,
                                "title": "Дотеры-Дегротеры",
                                "type": _chat_type.value
                            },
                            "date": 1557568806
                        }
                    }
                    make_content(data[_incoming.value], _content_type)
                    result.append((data, _chat_type, _incoming, _content_type))
    return result


def make_content(data: dict, content_type: Content) -> Any:
    if content_type is None:
        return

    value = "Some text"
    if content_type.has_entity:
        key = content_type.value[0]
    else:
        key = content_type.value

    data[key] = value

    if content_type.has_entity:
        data[content_type.value[1]] = [
            {
                "offset": 0,
                "length": len(value),
                "type": content_type.value[2]
            }
        ]


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
    messages([Chat.PRIVATE], [Incoming.NEW_MESSAGE], [Content.TEXT, Content.COMMAND, None])
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
