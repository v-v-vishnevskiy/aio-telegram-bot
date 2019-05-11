import asynctest
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


# async def test_get_updates(mocker):
#     mocker.patch("aiohttp.ClientSession")
#     client = Client("TOKEN")
