from unittest import TestCase
from unittest.mock import MagicMock

from notifications.handlers import NotifyCommandComplete, Command, Dispatcher, ConfigHandler
from notifications import Notification


class MockStrategy(object):
    def should_notify(self, cmd: Command) -> bool:
        pass


class MockBackend(object):
    def notify(self, n: Notification):
        pass


class MockFactory(object):
    def from_command(self, cmd: Command) -> Notification:
        pass


class TestNotifyCommandComplete(TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.strategy = MockStrategy()

        self.factory = MockFactory()
        self.factory.from_command = MagicMock(return_value=Notification(title="title", message="message", icon='foo.png'))

        self.backend = MockBackend()
        self.backend.notify = MagicMock(return_value=None)

        self.command = NotifyCommandComplete(
            notification_strategy=self.strategy,
            notification_factory=self.factory,
            notification_backend=self.backend,
        )

    def test_after_handler_no_notification(self):
        self.strategy.should_notify = MagicMock(return_value=False)
        self.factory.from_command = MagicMock(return_value=Notification(title="title", message="message", icon='foo.png'))
        self.backend.notify = MagicMock(return_value=None)

        self.command.before_handler(["ls -la"])
        self.command.after_handler(["0"])

        self.strategy.should_notify.assert_called_once()
        self.assertEqual("ls -la", self.strategy.should_notify.call_args[0][0].command_line)

        self.factory.from_command.assert_not_called()
        self.backend.notify.assert_not_called()

    def test_after_handler_notification(self):
        self.strategy.should_notify = MagicMock(return_value=True)

        self.command.before_handler(["ls -la"])
        self.command.after_handler(["0"])

        self.strategy.should_notify.assert_called_once()
        self.assertEqual("ls -la", self.strategy.should_notify.call_args[0][0].command_line)

        self.factory.from_command.assert_called_once()
        self.assertEqual("ls -la", self.factory.from_command.call_args[0][0].command_line)

        self.backend.notify.assert_called_once()

    def test_after_handler_raises_on_unknown_command(self):
        self.strategy.should_notify = MagicMock(return_value=False)

        with self.assertRaises(RuntimeError) as context:
            self.command.after_handler(["0"])

        self.strategy.should_notify.assert_not_called()
        self.factory.from_command.assert_not_called()
        self.backend.notify.assert_not_called()

    def test_before_handler_raises_when_missing_calls_to_after_command(self):
        self.strategy.should_notify = MagicMock(return_value=False)

        self.command.before_handler(["ls -l"])

        with self.assertRaises(RuntimeError) as context:
            self.command.before_handler(["ls -la"])

        self.strategy.should_notify.assert_not_called()
        self.factory.from_command.assert_not_called()
        self.backend.notify.assert_not_called()


class MockHandler(object):
    def handle(self, args: list) -> None:
        pass


class TestDispatcher(TestCase):
    def test_dispatch(self):
        foo = MockHandler()
        foo.handle = MagicMock()

        bar = MockHandler()
        bar.handle = MagicMock()

        d = Dispatcher()

        d.register_handler("foo", foo.handle)
        d.register_handler("bar", bar.handle)

        d.dispatch("foo", ['a', 'b'])

        foo.handle.assert_called_with(['a', 'b'])
        bar.handle.assert_not_called()

    def test_dispatcher_raises(self):
        d = Dispatcher()

        with self.assertRaises(RuntimeError):
            d.dispatch("foo", ['a'])


class MockWithTimeout(object):
    _timeout: int = 0

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, v: int):
        self._timeout = v


class NotificationsBackendSelectorMock(object):
    @property
    def selected(self) -> str:
        pass

    @selected.setter
    def selected(self, v: str):
        pass


class TestConfigHandler(TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.notifications_backend_selector = NotificationsBackendSelectorMock()

        self.success_template = Notification(title="", message="")
        self.failure_template = Notification(title="", message="")
        self.timeout = MockWithTimeout()

        self.cfg = ConfigHandler(timeout=self.timeout, success_template=self.success_template,
                                 failure_template=self.failure_template,
                                 notifications_backend_selector=self.notifications_backend_selector)

    def test_set_timeout_handler(self):
        self.cfg.set_timeout_handler(['42'])
        self.assertEqual(42, self.timeout.timeout)

    def test_set_timeout_handler_raises(self):
        with self.assertRaises(ValueError):
            self.cfg.set_timeout_handler(['foo'])

        self.assertEqual(0, self.timeout.timeout)

    def test_set_failure_templates(self):
        self.cfg.set_failure_title_handler(['failure message'])
        self.assertEqual('failure message', self.failure_template.title)

    def test_set_success_templates(self):
        self.cfg.set_success_title_handler(['success message'])
        self.assertEqual('success message', self.success_template.title)
