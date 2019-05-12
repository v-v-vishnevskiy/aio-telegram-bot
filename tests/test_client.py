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

    mock_timeout = mocker.MagicMock()
    mock_json_serialize = mocker.MagicMock()
    Client(token, timeout=mock_timeout, json_serialize=mock_json_serialize)

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
            mock_error.assert_called_once_with("Status: 500", extra=data)
        else:
            assert await client.request("get", "getUpdates") is None
            mock_error.assert_called_once_with("Status: 400", extra=data)