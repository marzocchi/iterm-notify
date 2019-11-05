from unittest import TestCase
from unittest.mock import MagicMock

from notifications import backends


class MockRunner(object):
    def run(self, cmd: list):
        pass


class TestTerminalNotifier(TestCase):

    def test_notify(self):
        runner = MockRunner()
        runner.run = MagicMock(return_value=None)

        notifier = backends.TerminalNotifier(runner=runner, path="/some/path")

        n = backends.Notification(title="sorry to bother you", message="but something happened!", icon=None)
        notifier.notify(n)

        runner.run.assert_called_once_with(
            ['/some/path', '-title', 'sorry to bother you', '-message', 'but something happened!'])

    def test_notify_with_icon(self):
        runner = MockRunner()
        runner.run = MagicMock(return_value=None)

        notifier = backends.TerminalNotifier(runner=runner, path="/some/path")

        n = backends.Notification(title="sorry to bother you", message="but something happened!", icon='foo.png')
        notifier.notify(n)

        runner.run.assert_called_once_with(
            ['/some/path', '-title', 'sorry to bother you', '-message', 'but something happened!', '-appIcon',
             'foo.png'])
