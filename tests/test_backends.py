from unittest import TestCase
from unittest.mock import ANY, Mock
from notify import *
from notify.backends import Executor, OsaScript, TerminalNotifier
from notify.notifications import Notification


class TestTerminalNotifier(TestCase):
    DEFAULTS = ['/some/path', '-activate',
                'com.googlecode.iterm2']

    def setUp(self) -> None:
        self.__mock_logger = Mock(spec=logging.Logger)
        self.__mock_executor = Mock(spec=Executor)
        self.__notifier = TerminalNotifier(logger=self.__mock_logger, executor=self.__mock_executor, path="/some/path")

    def test_notify(self):
        self.__notifier.notify(Notification(title="sorry to bother you", message="but something happened!", icon=None))
        self.__mock_executor.execute.assert_called_once_with(
            self.DEFAULTS + ['-title', 'sorry to bother you', '-message', 'but something happened!'])

    def test_notify_with_icon(self):
        self.__notifier.notify(Notification(title="sorry to bother you", message="but something happened!", icon='foo.png'))
        self.__mock_executor.execute.assert_called_once_with(
            self.DEFAULTS + ['-title', 'sorry to bother you', '-message', 'but something happened!', '-appIcon',
                             'foo.png'])


class TestOsaScriptNotifier(TestCase):
    DEFAULTS = ['osascript', ANY]

    def setUp(self) -> None:
        self.__mock_executor = Mock(spec=Executor)
        self.__mock_logger = Mock(spec=logging.Logger)

        self.__notifier = OsaScript(self.__mock_logger, self.__mock_executor)

    def test_notify(self):
        self.__notifier.notify(Notification(title="sorry to bother you", message="but something happened!", sound=None))
        self.__mock_executor.execute.assert_called_once_with(
            self.DEFAULTS + ['but something happened!', 'sorry to bother you', ''])

    def test_notify_with_icon(self):
        self.__notifier.notify(
            Notification(title="sorry to bother you", message="but something happened!", sound='Glass'))
        self.__mock_executor.execute.assert_called_once_with(
            self.DEFAULTS + ['but something happened!', 'sorry to bother you', 'Glass'])

