import asynctest

from aiotelegrambot.message import Message
from aiotelegrambot.types import Incoming


def test___init__(mocker):
    client = mocker.MagicMock()
    incoming = Incoming.NEW_MESSAGE
    chat_id = mocker.MagicMock()
    message_id = mocker.MagicMock()
    raw = {
        incoming.value: {
            "chat": {
                "id": chat_id
            },
            "message_id": message_id
        }
    }
    ctx = mocker.MagicMock()
    chat_type = mocker.MagicMock()
    content_type = mocker.MagicMock()

    m = Message(client, raw, ctx, chat_type, incoming, content_type)

    assert m._client == client
    assert m.chat_type is chat_type
    assert m.incoming is incoming
    assert m.content_type is content_type
    assert m.raw is raw
    assert m.ctx is ctx
    assert m._chat_id is chat_id
    assert m._message_id is message_id

    ##################################

    incoming = None
    m = Message(client, raw, ctx, chat_type, incoming, content_type)
    assert m._chat_id is None
    assert m._message_id is None

    ##################################

    incoming = mocker.MagicMock()
    incoming.is_message_or_post = False
    m = Message(client, raw, ctx, chat_type, incoming, content_type)
    assert m._chat_id is None
    assert m._message_id is None


async def test_send_message(mocker):
    client = mocker.MagicMock()
    client.send_message = asynctest.CoroutineMock()
    incoming = Incoming.NEW_MESSAGE
    chat_id = mocker.MagicMock()
    message_id = mocker.MagicMock()
    raw = {
        incoming.value: {
            "chat": {
                "id": chat_id
            },
            "message_id": message_id
        }
    }
    text = mocker.MagicMock()

    m = Message(client, raw, mocker.MagicMock(), incoming=incoming)
    await m.send_message(text)
    client.send_message.assert_called_once_with(text, chat_id, None)

    ##################################

    client.send_message = asynctest.CoroutineMock()

    m = Message(client, raw, mocker.MagicMock(), incoming=incoming)
    await m.send_message(text, True)
    client.send_message.assert_called_once_with(text, chat_id, message_id)


def test_request(mocker):
    client = mocker.MagicMock()
    client.request = mocker.MagicMock()
    m = Message(client, mocker.MagicMock(), mocker.MagicMock())
    assert m.request is client.request
