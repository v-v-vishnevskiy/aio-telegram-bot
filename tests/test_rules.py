import pytest

from aiotelegrambot.errors import RuleError
from aiotelegrambot.rules import Command, Contains, Mention, RegExp, Text, is_match, prepare_rule
from aiotelegrambot.types import Content, Incoming


class TestRegExp:
    def test___init__(self, mocker):
        pattern = "^[0-9]"
        mock_compile = mocker.patch("re.compile")
        re = RegExp(pattern)

        mock_compile.assert_called_once_with(pattern)
        assert re._pattern == mock_compile.return_value

    @pytest.mark.parametrize("isinstance_value", [True, False])
    def test___eq__(self, mocker, isinstance_value):
        mocker.patch("aiotelegrambot.rules.isinstance", return_value=isinstance_value)

        pattern = "^[0-9]{3}"
        re1 = RegExp(pattern)
        re2 = RegExp(pattern)
        if isinstance_value:
            assert re1 == re2
            assert re1 != "123"
        else:
            assert re1 == "123"
            assert re1 != "12"

    def test___hash__(self, mocker):
        pattern = "^[0-9]"
        mock_hash = mocker.patch("aiotelegrambot.rules.hash", return_value=1)
        re = RegExp(pattern)
        data = {re: 1}

        mock_hash.assert_called_once_with(re._pattern)

    def test___repr__(self):
        pattern = "^[0-9]"
        assert str(RegExp(pattern)) == 'RegExp("{}")'.format(pattern)


class TestText:
    def test___init__(self, mocker):
        text = "TEXT"
        t = Text(text)

        assert t._text == text.lower()
        assert t._insensitive is True

    def test___init___sensitive(self, mocker):
        text = "TEXT"
        t = Text(text, False)

        assert t._text == text
        assert t._insensitive is False

    @pytest.mark.parametrize("isinstance_value", [True, False])
    @pytest.mark.parametrize("insensitive", [True, False])
    def test___eq__(self, mocker, isinstance_value, insensitive):
        mocker.patch("aiotelegrambot.rules.isinstance", return_value=isinstance_value)

        text = "TEXT"
        t1 = Text(text, insensitive)
        t2 = Text(text, insensitive)
        if isinstance_value:
            assert t1 == t2
            assert t1 != "TEXT"
        else:
            if insensitive:
                assert t1 == "tExT"
                assert t1 != "12"
            else:
                assert t1 == "TEXT"
                assert t1 != "text"

    def test___hash__(self, mocker):
        text = "TEXT"
        mock_hash = mocker.patch("aiotelegrambot.rules.hash", return_value=1)
        t = Text(text)
        data = {t: 1}

        mock_hash.assert_called_once_with((Text, text.lower(), True))

    def test___repr__(self):
        text = "TEXT"
        assert str(Text(text)) == 'Text("{}", True)'.format(text.lower())


class TestContains:
    @pytest.mark.parametrize("isinstance_value", [True, False])
    @pytest.mark.parametrize("insensitive", [True, False])
    def test___eq__(self, mocker, isinstance_value, insensitive):
        mocker.patch("aiotelegrambot.rules.isinstance", return_value=isinstance_value)

        text = "text"
        c1 = Contains(text, insensitive)
        c2 = Contains(text, insensitive)
        if isinstance_value:
            assert c1 == c2
            assert c1 != "text"
        else:
            if insensitive:
                assert c1 == "tExT"
                assert c1 == "some tExT"
                assert c1 != "tex t"
            else:
                assert c1 == "text"
                assert c1 == "some text"
                assert c1 != "some tEXt"
                assert c1 != "tEXt"

    def test___repr__(self):
        text = "TEXT"
        assert str(Contains(text)) == 'Contains("{}", True)'.format(text.lower())


class TestCommand:
    def test_pattern(self):
        assert Command.pattern.pattern == r"^/[A-Za-z0-9_]+$"

    def test___init__(self, mocker):
        mock_init = mocker.patch("aiotelegrambot.rules.Text.__init__", return_value=None)

        Command("/help")

        mock_init.assert_called_once_with("/help", False)

    def test___init___error(self, mocker):

        with pytest.raises(RuleError):
            Command("help")


class TestMention:
    def test_pattern(self):
        assert Mention.pattern.pattern == r"^@[A-Za-z0-9_]+$"

    def test___init__(self, mocker):
        mock_init = mocker.patch("aiotelegrambot.rules.Text.__init__", return_value=None)

        Mention("@user")

        mock_init.assert_called_once_with("@user", False)

    def test___init___error(self, mocker):

        with pytest.raises(RuleError):
            Mention("user")


@pytest.mark.parametrize(
    "params",
    [
        (Command, Content.COMMAND, "/help"),
        (Mention, Content.MENTION, "@user"),
        (Text, Content.TEXT, 123),
        (str, None, "123")
    ]
)
def test_prepare_rule(params):
    cls, content_type, rule = params
    assert isinstance(prepare_rule(content_type, rule), cls)


@pytest.mark.parametrize(
    "data",
    [
        (
            {
                Incoming.NEW_MESSAGE.value: {
                    "text": "text"
                }
            },
            "text",
            Incoming.NEW_MESSAGE,
            Content.TEXT,
            True
        ),
        (
            {
                Incoming.NEW_MESSAGE.value: {
                    "text": "/stat today",
                    "entities": [{
                        "offset": 0,
                        "length": len("/stat")
                    }]
                }
            },
            Command("/stat"),
            Incoming.NEW_MESSAGE,
            Content.COMMAND,
            True
        ),
        (
            {
                Incoming.NEW_MESSAGE.value: {
                    "text": "/stat1 today",
                    "entities": [{
                        "offset": 0,
                        "length": len("/stat1")
                    }]
                }
            },
            Command("/stat"),
            Incoming.NEW_MESSAGE,
            Content.COMMAND,
            False
        )
    ]
)
def test_is_match(data):
    data, rule, incoming, content_type, result = data
    assert is_match(rule, incoming, content_type, data) == result


def test_is_match_is_not_message_or_post(mocker):
    incoming = mocker.MagicMock()
    incoming.is_message_or_post = False
    assert is_match(mocker.MagicMock(), incoming, mocker.MagicMock(), mocker.MagicMock()) is False
