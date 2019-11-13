from unittest import TestCase
from unittest.mock import MagicMock
import notifications
from . import NotifyCommandComplete


class TestNotifyCommandComplete(TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.strategy = MagicMock(['should_notify'])

        self.factory = MagicMock(['from_command'])
        self.factory.from_command = MagicMock(
            return_value=notifications.Notification(
                title="title",
                message="message",
                icon='foo.png'
            )
        )

        self.backend = MagicMock(['notify'])
        self.backend.notify = MagicMock(return_value=None)

        self.stack = MagicMock(['push', 'pop'])

        self.command = NotifyCommandComplete(
            stack=self.stack,
            strategy=self.strategy,
            factory=self.factory,
            backend=self.backend,
        )

    def test_push_pop(self):
        self.command.before_command(*['ls -la'])
        self.stack.push.assert_called_once()
        self.stack.pop.assert_not_called()

        self.command.after_command(*['0'])
        self.stack.push.assert_called_once()
        self.stack.pop.assert_called_once()

    def test_after_handler_no_notification(self):
        self.strategy.should_notify = MagicMock(return_value=False)
        self.factory.from_command = MagicMock(
            return_value=notifications.Notification(title="title", message="message", icon='foo.png'))
        self.backend.notify = MagicMock(return_value=None)

        self.command.before_command(*["ls -la"])
        self.command.after_command(*["0"])

        self.strategy.should_notify.assert_called_once()
        self.assertEqual("ls -la", self.strategy.should_notify.call_args[0][0].command_line)

        self.factory.from_command.assert_not_called()
        self.backend.notify.assert_not_called()

        self.stack.push.assert_called_once()
        self.stack.pop.assert_called_once()

    def test_after_handler_notification(self):
        self.strategy.should_notify = MagicMock(return_value=True)

        self.command.before_command(*["ls -la"])
        self.command.after_command(*["0"])

        self.strategy.should_notify.assert_called_once()
        self.assertEqual("ls -la", self.strategy.should_notify.call_args[0][0].command_line)

        self.factory.from_command.assert_called_once()
        self.assertEqual("ls -la", self.factory.from_command.call_args[0][0].command_line)

        self.backend.notify.assert_called_once()
        self.stack.push.assert_called_once()
        self.stack.pop.assert_called_once()

    def test_after_handler_raises_on_unknown_command(self):
        self.strategy.should_notify = MagicMock(return_value=False)

        with self.assertRaises(RuntimeError):
            self.command.after_command(*["0"])

        self.strategy.should_notify.assert_not_called()
        self.factory.from_command.assert_not_called()
        self.backend.notify.assert_not_called()

        self.stack.push.assert_not_called()
        self.stack.pop.assert_not_called()
