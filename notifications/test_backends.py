from unittest import TestCase
from unittest.mock import MagicMock, ANY
from notifications import *
from notifications.backends import OsaScript, TerminalNotifier, Selectable


class TestTerminalNotifier(TestCase):
    DEFAULTS = ['/some/path', '-activate',
                'com.googlecode.iterm2']

    def test_notify(self):
        ex = MagicMock(['exec'])

        notifier = TerminalNotifier(ex, path="/some/path")

        n = Notification(title="sorry to bother you", message="but something happened!", icon=None)
        notifier.notify(n)

        ex.exec.assert_called_once_with(
            self.DEFAULTS + ['-title', 'sorry to bother you', '-message', 'but something happened!'])

    def test_notify_with_icon(self):
        ex = MagicMock(['exec'])

        notifier = TerminalNotifier(ex, path="/some/path")

        n = Notification(title="sorry to bother you", message="but something happened!", icon='foo.png')
        notifier.notify(n)

        ex.exec.assert_called_once_with(
            self.DEFAULTS + ['-title', 'sorry to bother you', '-message', 'but something happened!', '-appIcon',
                             'foo.png'])


class TestOsaScriptNotifier(TestCase):
    DEFAULTS = ['osascript', ANY]

    def test_notify(self):
        ex = MagicMock(['exec'])

        notifier = OsaScript(ex)

        n = Notification(title="sorry to bother you", message="but something happened!", sound=None)
        notifier.notify(n)

        ex.exec.assert_called_once_with(
            self.DEFAULTS + ['but something happened!', 'sorry to bother you', ''])

    def test_notify_with_icon(self):
        ex = MagicMock(['exec'])

        notifier = OsaScript(ex)

        n = Notification(title="sorry to bother you", message="but something happened!", sound='Glass')
        notifier.notify(n)

        ex.exec.assert_called_once_with(
            self.DEFAULTS + ['but something happened!', 'sorry to bother you', 'Glass'])


class TestSwitchableNotifier(TestCase):
    def test_raises(self):
        with self.assertRaises(RuntimeError):
            Selectable({}, 'n1')

        n1 = MagicMock()
        sw = Selectable({'n1': n1}, 'n1')

        with self.assertRaises(RuntimeError):
            sw.selected = 'n2'

    def test_switches_with_first_selection(self):
        n1 = MagicMock(['notify'])
        n1.notify = MagicMock()

        n2 = MagicMock(['notify'])
        n2.notify = MagicMock()

        sw = Selectable(
            {
                'n1': n1,
                'n2': n2,
            },
            'n2'
        )

        n = Notification(title='t', message='m')

        sw.notify(n)

        n1.notify.assert_not_called()
        n2.notify.assert_called_once_with(n)

    def test_switches(self):
        n1 = MagicMock(['notify'])
        n1.notify = MagicMock()

        n2 = MagicMock(['notify'])
        n2.notify = MagicMock()

        sw = Selectable(
            {
                'n1': n1,
                'n2': n2,
            },
            'n2'
        )

        n = Notification(title='t', message='m')

        sw.selected = 'n1'
        sw.notify(n)

        n1.notify.assert_called_once_with(n)
        n2.notify.assert_not_called()
