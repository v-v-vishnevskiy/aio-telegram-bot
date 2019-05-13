import asynctest
import pytest

from aiotelegrambot import Content, Handler, Handlers
from aiotelegrambot.errors import HandlerError
from aiotelegrambot.rules import Text


class TestHandler:
    def test___init__(self, mocker):
        async def handler():
            pass

        chat_type = mocker.MagicMock()
        incoming = mocker.MagicMock()
        content_type = mocker.MagicMock()
        rule = mocker.MagicMock()
        h = Handler(handler, chat_type, incoming, content_type, rule)
        assert h.name == "handler"
        assert h.chat_type is chat_type
        assert h.incoming is incoming
        assert h.content_type is content_type
        assert h.rule is rule
        assert h.handler is handler

    def test_priority(self):
        h1 = Handler(rule=Text("text"))
        h2 = Handler(rule="text")

        assert h1.priority == Text.priority
        assert h2.priority == 1000000

    async def test___call__(self, mocker):
        h = Handler()
        mock_handler = mocker.patch.object(h, "handler", new=asynctest.CoroutineMock())
        await h(param=123)
        mock_handler.assert_called_once_with(param=123)

    def test___bool__(self):
        async def handler():
            pass
        h1 = Handler(handler)
        h2 = Handler()

        assert bool(h1) is True
        assert bool(h2) is False

    def test___hash__(self, mocker):
        async def handler():
            pass
        mock_hash = mocker.patch("aiotelegrambot.handler.hash", return_value=1)
        h = Handler(handler)

        assert hash(h) == mock_hash.return_value
        mock_hash.assert_called_once_with((h.name, h.chat_type, h.incoming, h.content_type, h.rule))

    def test___repr__(self):
        h = Handler(rule="text")

        assert str(h) == "Handler(None, None, None, None, text)"


class TestHandlers:
    def test___init__(self):
        h = Handlers()

        assert h._handler_cls is Handler
        assert isinstance(h._default_handler, Handler)
        assert h._default_handler.handler is None
        h._handlers[1][2][3].append(4)

    @pytest.mark.parametrize("chat_type", [True, None])
    @pytest.mark.parametrize("incoming", [True, None])
    @pytest.mark.parametrize("content_type", [True, None])
    @pytest.mark.parametrize("rule", [True, None])
    @pytest.mark.parametrize("is_match_value", [True, False])
    def test_get(self, mocker, is_match_value, rule, content_type, incoming, chat_type):
        chat_type = mocker.MagicMock() if chat_type else None
        incoming = mocker.MagicMock() if incoming else None
        content_type = mocker.MagicMock() if content_type else None
        handler = mocker.MagicMock()
        handler.rule = rule
        raw = mocker.MagicMock()

        mock_is_match = mocker.patch("aiotelegrambot.handler.is_match", return_value=is_match_value)

        h = Handlers()
        h._handlers[chat_type][incoming][content_type].append(handler)

        _incoming = incoming if incoming else 1
        _content_type = content_type if content_type else 1

        assert h.get(
            chat_type if chat_type else 1,
            _incoming,
            content_type if content_type else 1,
            raw
        ) == (handler if rule is None or is_match_value is True else h._default_handler)

        if rule is None:
            assert mock_is_match.call_count == 0
        else:
            mock_is_match.assert_called_once_with(handler.rule, _incoming, _content_type, raw)

    def test_add(self, mocker):
        mock_prepare_rule = mocker.patch("aiotelegrambot.handler.prepare_rule")

        h = Handlers()
        mock_handler_cls = mocker.patch.object(h, "_handler_cls")

        chat_type = mocker.MagicMock()
        incoming = mocker.MagicMock()
        incoming.is_message_or_post = True
        content_type = mocker.MagicMock()
        rule = "/help"

        def handler():
            pass

        result = h.add(chat_type=chat_type, incoming=incoming, content_type=content_type, rule=rule)(handler)
        assert result is handler
        assert len(h._handlers[chat_type][incoming][content_type]) == 1
        assert h._handlers[chat_type][incoming][content_type][0] is mock_handler_cls.return_value
        mock_handler_cls.assert_called_once_with(
            handler, chat_type, incoming, content_type, mock_prepare_rule.return_value
        )

    def test_add_sorted(self, mocker):
        chat_type = mocker.MagicMock()
        incoming = mocker.MagicMock()
        incoming.is_message_or_post = True
        content_type = mocker.MagicMock()

        rule1 = mocker.MagicMock()
        rule1.priority = 1

        rule2 = mocker.MagicMock()
        rule2.priority = 2

        rule3 = mocker.MagicMock()
        rule3.priority = 3

        def handler():
            pass

        h = Handlers()
        h.add(chat_type=chat_type, incoming=incoming, content_type=content_type, rule=rule3)(handler)
        h.add(chat_type=chat_type, incoming=incoming, content_type=content_type, rule=rule1)(handler)
        h.add(chat_type=chat_type, incoming=incoming, content_type=content_type, rule=rule2)(handler)

        handlers = h._handlers[chat_type][incoming][content_type]
        assert handlers[0].priority == rule1.priority
        assert handlers[1].priority == rule2.priority
        assert handlers[2].priority == rule3.priority

    def test_add_error(self, mocker):
        mock_prepare_rule = mocker.patch("aiotelegrambot.handler.prepare_rule")

        h = Handlers()

        incoming = mocker.MagicMock()
        incoming.is_message_or_post = False

        with pytest.raises(HandlerError):
            h.add(incoming=incoming, content_type=Content.TEXT)

        ##################################

        incoming = mocker.MagicMock()
        incoming.is_message_or_post = False

        with pytest.raises(HandlerError):
            h.add(incoming=incoming, rule="/help")

        ##################################

        incoming = mocker.MagicMock()
        incoming.is_message_or_post = True
        content_type = mocker.MagicMock()
        rule = "/help"
        with pytest.raises(ValueError):
            h.add(incoming=incoming, content_type=content_type, rule=rule)(None)
        mock_prepare_rule.assert_called_once_with(content_type, rule)

        ##################################

        chat_type = mocker.MagicMock()
        incoming = mocker.MagicMock()
        incoming.is_message_or_post = True
        content_type = mocker.MagicMock()
        rule = None
        handler = mocker.MagicMock()
        handler.rule = rule
        h._handlers[chat_type][incoming][content_type].append(handler)
        with pytest.raises(HandlerError):
            h.add(chat_type=chat_type, incoming=incoming, content_type=content_type, rule=rule)(handler)
        assert mock_prepare_rule.call_count == 1

    def test___bool__(self):
        h = Handlers()
        assert bool(h) is False

        h._handlers[1][2][3].append(4)
        assert bool(h) is True
