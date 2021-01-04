import json

import asynctest
import pytest

from aiotelegrambot import Client


@pytest.fixture
def response(mocker):
    def make(status: int, data: dict):
        result = mocker.MagicMock()
        result.status = status
        result.text = asynctest.CoroutineMock(return_value=json.dumps(data))
        return result

    return make


def test_base_url():
    assert Client.base_url == "https://api.telegram.org/bot"


def test___init__(mocker):
    token = "TOKEN"
    mock_client_session = mocker.patch("aiohttp.ClientSession")
    mock_client_timeout = mocker.patch("aiohttp.ClientTimeout")
    client = Client(token)

    assert client._url == "https://api.telegram.org/botTOKEN/"
    assert client._session == mock_client_session.return_value
    mock_client_timeout.assert_called_once_with(total=10)
    mock_client_session.assert_called_once_with(timeout=mock_client_timeout.return_value)


def test__init___kwargs(mocker):
    token = "TOKEN"
    mock_client_session = mocker.patch("aiohttp.ClientSession")
    mock_client_timeout = mocker.patch("aiohttp.ClientTimeout")

    mock_json_loads = mocker.MagicMock()
    mock_json_serialize = mocker.MagicMock()
    client = Client(token, json_loads=mock_json_loads, json_serialize=mock_json_serialize)

    assert client._json_loads is mock_json_loads
    mock_client_session.assert_called_once_with(
        timeout=mock_client_timeout.return_value, json_serialize=mock_json_serialize
    )


async def test_close(mocker):
    token = "TOKEN"
    mocker.patch("aiohttp.ClientSession.__init__", return_value=None)
    mock_close = mocker.patch("aiohttp.ClientSession.close", new=asynctest.CoroutineMock())
    client = Client(token)
    await client.close()

    mock_close.assert_called_once_with()


@pytest.mark.parametrize("param", [None, "offset", "limit", "timeout"])
async def test_get_updates(mocker, param):
    mocker.patch("aiohttp.ClientSession")
    mock_request = mocker.patch("aiotelegrambot.Client.request", new=asynctest.CoroutineMock())
    client = Client("TOKEN")

    if param:
        assert await client.get_updates(**{param: 1}) == mock_request.return_value
        mock_request.assert_called_once_with("get", "getUpdates", raise_exception=True, params={param: 1})
    else:
        assert await client.get_updates() == mock_request.return_value
        mock_request.assert_called_once_with("get", "getUpdates", raise_exception=True, params={})


@pytest.mark.parametrize("has_message", [True, False])
async def test_send_message(mocker, has_message):
    mocker.patch("aiohttp.ClientSession")
    mock_request = mocker.patch("aiotelegrambot.Client.request", new=asynctest.CoroutineMock())
    client = Client("TOKEN")

    mock_text = mocker.MagicMock()
    mock_chat_id = mocker.MagicMock()
    if has_message:
        mock_message_id = mocker.MagicMock()
    else:
        mock_message_id = None

    await client.send_message(mock_text, mock_chat_id, mock_message_id)
    if has_message:
        mock_request.assert_called_once_with(
            "get",
            "sendMessage",
            params={"chat_id": mock_chat_id, "text": mock_text, "reply_to_message_id": mock_message_id},
        )
    else:
        mock_request.assert_called_once_with("get", "sendMessage", params={"chat_id": mock_chat_id, "text": mock_text})


async def test_set_webhook(mocker):
    mocker.patch("aiohttp.ClientSession")
    mock_request = mocker.patch("aiotelegrambot.Client.request", new=asynctest.CoroutineMock())
    client = Client("TOKEN")

    mock_url = mocker.MagicMock()

    await client.set_webhook(mock_url)
    mock_request.assert_called_once_with("post", "setWebhook", params=[("url", mock_url)])


async def test_set_webhook_kwargs(mocker):
    mocker.patch("aiohttp.ClientSession")
    mock_request = mocker.patch("aiotelegrambot.Client.request", new=asynctest.CoroutineMock())
    mock_open = mocker.patch("aiotelegrambot.client.open")
    mock_dumps = mocker.patch("aiotelegrambot.client.dumps")
    client = Client("TOKEN")

    mock_url = mocker.MagicMock()
    mock_certificate = mocker.MagicMock()
    mock_max_connections = mocker.MagicMock()
    mock_allowed_updates = mocker.MagicMock()

    expected_kwargs = {
        "params": [
            ("url", mock_url),
            ("max_connections", mock_max_connections),
            ("allowed_updates", mock_dumps.return_value),
        ],
        "data": {"certificate": mock_open.return_value},
    }

    await client.set_webhook(mock_url, mock_certificate, mock_max_connections, mock_allowed_updates)
    mock_request.assert_called_once_with("post", "setWebhook", **expected_kwargs)
    mock_open.assert_called_once_with(mock_certificate, "r")
    mock_dumps.assert_called_once_with(mock_allowed_updates)


async def test_get_webhook_info(mocker):
    mocker.patch("aiohttp.ClientSession")
    mock_request = mocker.patch("aiotelegrambot.Client.request", new=asynctest.CoroutineMock())
    client = Client("TOKEN")

    await client.get_webhook_info()
    mock_request.assert_called_once_with("get", "getWebhookInfo")


async def test_delete_webhook(mocker):
    mocker.patch("aiohttp.ClientSession")
    mock_request = mocker.patch("aiotelegrambot.Client.request", new=asynctest.CoroutineMock())
    client = Client("TOKEN")

    await client.delete_webhook()
    mock_request.assert_called_once_with("get", "deleteWebhook")


@pytest.mark.parametrize("data", [{"ok": True}, {"ok": False, "description": "error"}])
async def test__request(mocker, data, response):
    status = 200
    mock_response = response(status, data)
    mock_process_error = mocker.patch("aiotelegrambot.Client.process_error")
    mocker.patch("aiohttp.ClientSession._request", new=asynctest.CoroutineMock(return_value=mock_response))

    client = Client("TOKEN")

    assert await client._request("get", "getUpdates", False) == (data if data["ok"] is True else None)
    if data["ok"] is False:
        mock_process_error.assert_called_once_with("Unsuccessful request", mock_response, data, False)


@pytest.mark.parametrize("status", [501, 500, 401, 400])
async def test__request_error(mocker, status, response):
    mock_process_error = mocker.patch("aiotelegrambot.Client.process_error")

    mock_description = "error"
    data = {"ok": False, "description": mock_description}
    mock_response = response(status, data)
    mocker.patch("aiohttp.ClientSession._request", new=asynctest.CoroutineMock(return_value=mock_response))

    client = Client("TOKEN")

    assert await client._request("get", "getUpdates", False) is None
    if status >= 500:
        msg = "Server error"
        data = None
    elif status == 401:
        msg = "Invalid access token provided"
    else:
        msg = "Unexpected behavior"

    mock_process_error.assert_called_once_with(msg, mock_response, data, False)
