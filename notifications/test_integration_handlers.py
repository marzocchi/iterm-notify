from unittest import TestCase
from unittest.mock import MagicMock
from notifications.handlers import MaintainConfig
from notifications.config import Config, Stack
from notifications import Notification


class TestMaintainConfigHandler(TestCase):
    def test_on_pop_restores_previous_config(self):
        mock_timeout = MagicMock([])
        mock_backend_selector = MagicMock([])
        mock_logger = MagicMock(['name', 'level', 'setLevel'])

        success_template = Notification("success title", "success message")
        failure_template = Notification("failure title", "failure message")

        stack = Stack(
            [Config(notifications_backend="", logger_name="", logger_level="", command_complete_timeout=0,
                    success_title="", success_message="", failure_title="", failure_message="")])

        h = MaintainConfig(stack=stack, timeout=mock_timeout,
                           backend_selector=mock_backend_selector,
                           success_template=success_template,
                           failure_template=failure_template,
                           logger=mock_logger)

        h.command_complete_timeout_handler(10)
        self.assertEqual(10, stack.current.command_complete_timeout)

        stack.push()

        h.command_complete_timeout_handler(42)
        self.assertEqual(42, stack.current.command_complete_timeout)

        stack.pop()
        self.assertEqual(10, stack.current.command_complete_timeout)
