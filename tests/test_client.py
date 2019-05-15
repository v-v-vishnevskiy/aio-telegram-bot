import json

import aiohttp
import asynctest
import pytest
from aioresponses import aioresponses

from aiotelegrambot import Client


def test_base_url():
    assert Client.base_url == "https://api.telegram.org/bot"


def test___init__(mocker):
    token = "TOKEN"
    mock_client_session = mocker.patch("aiohttp.ClientSession")
    mock_client_timeout = mocker.patch("aiohttp.ClientTimeout")
    client = Client(token)

    assert client._url == "https://api.telegram.org/botTOKEN/"
    assert client._session == mock_client_session.return_value
    mock_client_timeout.assert_called_once_with(total=1)
    mock_client_session.assert_called_once_with(timeout=mock_client_timeout.return_value)


def test__init___kwargs(mocker):
    token = "TOKEN"
    mock_client_session = mocker.patch("aiohttp.ClientSession")

    mock_json_loads = mocker.MagicMock()
    mock_timeout = mocker.MagicMock()
    mock_json_serialize = mocker.MagicMock()
    client = Client(token, json_loads=mock_json_loads, timeout=mock_timeout, json_serialize=mock_json_serialize)

    assert client._json_loads is mock_json_loads
    mock_client_session.assert_called_once_with(timeout=mock_timeout, json_serialize=mock_json_serialize)


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
        mock_request.assert_called_once_with("get", "getUpdates", params={param: 1})
    else:
        assert await client.get_updates() == mock_request.return_value
        mock_request.assert_called_once_with("get", "getUpdates", params={})


async def test_send_message(mocker):
    mocker.patch("aiohttp.ClientSession")
    mock_request = mocker.patch("aiotelegrambot.Client.request", new=asynctest.CoroutineMock())
    client = Client("TOKEN")

    mock_text = mocker.MagicMock()
    mock_chat_id = mocker.MagicMock()

    await client.send_message(mock_text, mock_chat_id)
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
            ("allowed_updates", mock_dumps.return_value)
        ],
        "data": {"certificate": mock_open.return_value}
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


@pytest.mark.parametrize("data", [{"ok": [1]}, {"ok": []}])
async def test_request(mocker, data):
    mock_error = mocker.patch("aiotelegrambot.client.logger.error")
    client = Client("TOKEN")

    with aioresponses() as m:
        m.get(client._url + "getUpdates", payload=data)

        assert await client.request("get", "getUpdates") == (data if data["ok"] else None)
        if not data["ok"]:
            mock_error.assert_called_once_with("Unsuccessful request", extra=data)


@pytest.mark.parametrize("status", [400, 500])
async def test_request_error(mocker, status):
    mock_error = mocker.patch("aiotelegrambot.client.logger.error")
    client = Client("TOKEN")

    data = {"ok": [1]}
    with aioresponses() as m:
        m.get(client._url + "getUpdates", status=status, payload=data)

        if status == 500:
            with pytest.raises(aiohttp.ClientResponseError):
                await client.request("get", "getUpdates")
            mock_error.assert_called_once_with("Status: 500", extra=json.dumps(data))
        else:
            assert await client.request("get", "getUpdates") is None
            mock_error.assert_called_once_with("Status: 400", extra=json.dumps(data))
