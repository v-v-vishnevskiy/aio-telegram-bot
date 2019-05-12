import asynctest

from aiotelegrambot.message import Message
from aiotelegrambot.types import Incoming


def test___init__(mocker):
    client = mocker.MagicMock()
    incoming = Incoming.NEW_MESSAGE
    chat_id = mocker.MagicMock()
    raw = {
        incoming.value: {
            "chat": {
                "id": chat_id
            }
        }
    }
    chat_type = mocker.MagicMock()
    content_type = mocker.MagicMock()

    m = Message(client, raw, chat_type, incoming, content_type)

    assert m._client == client
    assert m.chat_type is chat_type
    assert m.incoming is incoming
    assert m.content_type is content_type
    assert m.raw is raw
    assert m._chat_id is chat_id

    ##################################

    incoming = None
    assert Message(client, raw, chat_type, incoming, content_type)._chat_id is None

    ##################################

    incoming = mocker.MagicMock()
    incoming.is_message_or_post = False
    assert Message(client, raw, chat_type, incoming, content_type)._chat_id is None


async def test_send_message(mocker):
    client = mocker.MagicMock()
    client.send_message = asynctest.CoroutineMock()
    incoming = Incoming.NEW_MESSAGE
    chat_id_1 = mocker.MagicMock()
    chat_id_2 = mocker.MagicMock()
    raw = {
        incoming.value: {
            "chat": {
                "id": chat_id_1
            }
        }
    }
    text = mocker.MagicMock()

    m = Message(client, raw, incoming=incoming)
    await m.send_message(text)
    client.send_message.assert_called_once_with(text, chat_id_1)

    ##################################

    client.send_message = asynctest.CoroutineMock()

    m = Message(client, raw, incoming=incoming)
    await m.send_message(text, chat_id_2)
    client.send_message.assert_called_once_with(text, chat_id_2)


def test_request(mocker):
    client = mocker.MagicMock()
    client.request = mocker.MagicMock()
    m = Message(client, mocker.MagicMock())
    assert m.request is client.request
