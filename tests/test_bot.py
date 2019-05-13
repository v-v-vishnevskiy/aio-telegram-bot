import asynctest
import pytest

from aiotelegrambot.bot import Bot
from aiotelegrambot.errors import BotError


@pytest.fixture
def bot(mocker):
    client = mocker.MagicMock()
    return Bot(client)


def test___init__(mocker):
    mock_middlewares = mocker.patch("aiotelegrambot.bot.Middlewares")
    client = mocker.MagicMock()
    handlers = mocker.MagicMock()
    b = Bot(client, handlers)

    assert b.client is client
    assert b.handlers is handlers
    assert b.middlewares is mock_middlewares.return_value
    assert b._scheduler is None
    assert b._closed is True
    assert b._update_id == 0


@pytest.mark.parametrize("webhooks_value", [True, False])
async def test_initialize(mocker, webhooks_value):
    mock_create_scheduler = asynctest.CoroutineMock()
    mock_spawn = mocker.patch.object(mock_create_scheduler.return_value, "spawn", new=asynctest.CoroutineMock())
    mocker.patch("aiotelegrambot.bot.aiojobs.create_scheduler", new=mock_create_scheduler)
    client = mocker.MagicMock()
    handlers = mocker.MagicMock()
    b = Bot(client, handlers)

    mock_get_updates = mocker.patch.object(b, "_get_updates")

    scheduler_options = {"a": 1}
    interval = mocker.MagicMock()

    await b.initialize(webhooks=webhooks_value, interval=interval, **scheduler_options)

    assert b._closed is False
    assert b._scheduler is mock_create_scheduler.return_value
    mock_create_scheduler.assert_called_once_with(**scheduler_options)

    if webhooks_value:
        assert mock_spawn.call_count == 0
        assert mock_get_updates.call_count == 0
    else:
        mock_spawn.assert_called_once_with(mock_get_updates.return_value)
        mock_get_updates.assert_called_once_with(interval)


async def test_initialize_error(mocker, bot):
    mock_create_scheduler = mocker.patch("aiotelegrambot.bot.aiojobs.create_scheduler")

    with pytest.raises(BotError):
        await bot.initialize()

    ##################################

    bot._closed = False
    await bot.initialize()

    assert mock_create_scheduler.call_count == 0


async def test_close(mocker, bot):
    mock_close = asynctest.CoroutineMock()
    bot._scheduler = mocker.MagicMock()
    bot._scheduler.close = mock_close

    await bot.close()

    assert mock_close.call_count == 0

    ##################################

    bot._closed = False
    bot._update_id = 1

    await bot.close()

    mock_close.assert_called_once_with()
    assert bot._closed is True
    assert bot._update_id == 0


def test_add_handler(mocker, bot):
    mock_decorator = mocker.MagicMock()
    mock_add = mocker.MagicMock()
    mock_add.return_value = mock_decorator
    bot.handlers = mocker.MagicMock()
    bot.handlers.add = mock_add

    handler = mocker.MagicMock()
    param1 = mocker.MagicMock()
    param2 = mocker.MagicMock()
    bot.add_handler(handler, param1, param2=param2)
    mock_add.assert_called_once_with(param1, param2=param2)
    mock_decorator.assert_called_once_with(handler)


async def test_process_update_error(bot):
    with pytest.raises(RuntimeError):
        await bot.process_update({})


async def test_process_update(mocker, bot):
    mock_message = mocker.patch("aiotelegrambot.bot.Message")

    mock_chat_type = mocker.MagicMock()
    mock_incoming = mocker.MagicMock()
    mock_content_type = mocker.MagicMock()

    mock_recognize_type = mocker.patch(
        "aiotelegrambot.bot.recognize_type",
        return_value=(mock_chat_type, mock_incoming, mock_content_type)
    )
    mock_spawn = asynctest.CoroutineMock()
    bot._scheduler = mocker.MagicMock()
    bot._scheduler.spawn = mock_spawn

    bot.handlers.get = mocker.MagicMock()
    bot.middlewares = mocker.MagicMock()

    data = mocker.MagicMock()

    bot._closed = False

    await bot.process_update(data)

    mock_recognize_type.assert_called_once_with(data)
    bot.handlers.get.assert_called_once_with(mock_chat_type, mock_incoming, mock_content_type, data)
    mock_message.assert_called_once_with(bot.client, data, mock_chat_type, mock_incoming, mock_content_type)
    bot.middlewares.assert_called_once_with(mock_message.return_value, bot.handlers.get.return_value)
    mock_spawn.assert_called_once_with(bot.middlewares.return_value)


async def test__get_updates(mocker, bot):
    mock_update_id = mocker.MagicMock()
    bot._closed = False
    bot._update_id = mock_update_id

    mock_get_updates = asynctest.CoroutineMock(return_value=bot)
    bot.client.get_updates = mock_get_updates

    mock_sleep = mocker.patch("aiotelegrambot.bot.asyncio.sleep", new=asynctest.CoroutineMock())

    async def _process_updates(self):
        self._closed = True

    mocker.patch.object(bot, "_process_updates", new=_process_updates)

    mock_interval = mocker.MagicMock()
    await bot._get_updates(mock_interval)

    mock_get_updates.assert_called_once_with(mock_update_id)
    mock_sleep.assert_called_once_with(mock_interval)


@pytest.mark.parametrize("result", [None, [], [{"update_id": 2}]])
async def test__process_updates(bot, result):
    bot.process_update = asynctest.CoroutineMock()

    if result is not None:
        data = {"result": result}
    else:
        data = {}
    update_id = bot._update_id

    await bot._process_updates(data)

    if result:
        bot.process_update.assert_called_once_with(result[0])
        assert bot._update_id == (result[0]["update_id"] + 1)
    else:
        assert bot.process_update.call_count == 0
        assert update_id == bot._update_id
