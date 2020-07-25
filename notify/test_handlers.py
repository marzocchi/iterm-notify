from unittest.case import TestCase
from unittest.mock import Mock, PropertyMock

from notify.backends import BackendFactory
from notify.config import SelectedBackend, Stack
from notify.handlers import Notify, NotifyCommandComplete
from notify.notifications import Factory, Notification


class TestNotify(TestCase):
    def test_notify(self):
        n = Notification(title='title', message='message')

        selected_backend = SelectedBackend(name="test")

        mock_stack = Mock(spec=Stack)
        type(mock_stack).notifications_backend = PropertyMock(return_value = selected_backend)

        mock_notification_factory = Mock(spec=Factory)
        mock_backend_factory = Mock(spec=BackendFactory)

        mock_backend = Mock(['notify'])
        mock_backend_factory.create.return_value = mock_backend

        mock_notification_factory.create.return_value = n

        notify = Notify(mock_stack, notification_factory=mock_notification_factory, backend_factory=mock_backend_factory)
        notify.notify("message", "title")

        mock_notification_factory.create.assert_called_with(message='message', title='title', success=True)
        mock_backend.notify.assert_called_with(n)
        mock_backend_factory.create.assert_called_with(selected_backend)


class TestNotifyCommandComplete(TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.__strategy = Mock(['should_notify'])
        self.__strategy_factory = Mock(['create'])
        self.__strategy_factory.create.return_value = self.__strategy

        self.__factory = Mock(['from_command'])
        self.__factory.from_command = Mock(
            return_value=Notification(
                title="title",
                message="message",
                icon='foo.png'
            )
        )

        self.__backend = Mock(['notify'])
        self.__backend.notify.return_value = None

        self.__backend_factory = Mock(['create'])
        self.__backend_factory.create = Mock(return_value=self.__backend)

        self.__current_config = Mock(['notifications_backend', 'notifications_backend'])
        type(self.__current_config).notifications_backend = PropertyMock(return_value={"name": "test"})
        type(self.__current_config).notifications_strategy = PropertyMock(return_value={"name": "test"})

        self.__stack = Mock(['push', 'pop', 'current'])
        type(self.__stack).current = PropertyMock(return_value=self.__current_config)

        self.command = NotifyCommandComplete(
            stack=self.__stack,
            strategy_factory=self.__strategy_factory,
            notification_factory=self.__factory,
            backend_factory=self.__backend_factory,
        )

    def test_push_pop(self):
        self.command.before_command(*['ls -la'])
        self.__stack.push.assert_called_once()
        self.__stack.pop.assert_not_called()

        self.command.after_command(*['0'])
        self.__stack.push.assert_called_once()
        self.__stack.pop.assert_called_once()

    def test_after_handler_no_notification(self):
        self.__strategy.should_notify = Mock(return_value=False)
        self.__factory.from_command = Mock(
            return_value=Notification(title="title", message="message", icon='foo.png'))

        self.__backend_factory.notify = Mock(return_value=None)

        self.command.before_command(*["ls -la"])
        self.command.after_command(*["0"])

        self.__strategy.should_notify.assert_called_once()
        self.assertEqual("ls -la", self.__strategy.should_notify.call_args[0][0].command.command_line)

        self.__factory.from_command.assert_not_called()
        self.__backend_factory.notify.assert_not_called()

        self.__stack.push.assert_called_once()
        self.__stack.pop.assert_called_once()

    def test_after_handler_notification(self):
        self.__strategy.should_notify = Mock(return_value=True)

        self.command.before_command(*["ls -la"])
        self.command.after_command(*["0"])

        self.__strategy.should_notify.assert_called_once()
        self.assertEqual("ls -la", self.__strategy.should_notify.call_args[0][0].command.command_line)

        self.__factory.from_command.assert_called_once()
        self.assertEqual("ls -la", self.__factory.from_command.call_args[0][0].command.command_line)

        self.__backend.notify.assert_called_once()
        self.__stack.push.assert_called_once()
        self.__stack.pop.assert_called_once()

    def test_after_handler_raises_on_unknown_command(self):
        self.__strategy.should_notify = Mock(return_value=False)

        with self.assertRaises(RuntimeError):
            self.command.after_command(*["0"])

        self.__strategy.should_notify.assert_not_called()
        self.__factory.from_command.assert_not_called()
        self.__backend.notify.assert_not_called()

        self.__stack.push.assert_not_called()
        self.__stack.pop.assert_not_called()
