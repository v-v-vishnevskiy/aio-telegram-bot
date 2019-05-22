from aiotelegrambot.errors import TelegramApiError


class TestTelegramApiError:
    def test___init__(self, mocker):
        mock_msg = mocker.MagicMock()
        mock_data = mocker.MagicMock()
        mock_response = mocker.MagicMock()

        e = TelegramApiError(mock_msg, mock_data, mock_response)

        assert e.args[0] == mock_msg
        assert e.data == mock_data
        assert e.response == mock_response
