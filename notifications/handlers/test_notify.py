from unittest import TestCase
from unittest.mock import MagicMock
from . import Notify
import notifications


class TestNotify(TestCase):
    def test_notify(self):
        n = notifications.Notification(title='title', message='message')

        mock_factory = MagicMock(['create'])
        mock_factory.create = MagicMock(return_value=n)

        mock_backend = MagicMock(['notify'])

        notify = Notify(mock_factory, mock_backend)
        notify.notify("message", "title")

        mock_factory.create.assert_called_with(message='message', title='title')
        mock_backend.notify.assert_called_with(n)
