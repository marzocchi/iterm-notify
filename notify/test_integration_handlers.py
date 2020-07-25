from unittest import TestCase
from unittest.mock import Mock

from notify.config import Config, SelectedBackend, SelectedStrategy, Stack
from notify.handlers import MaintainConfig
from notify.notifications import Notification


class TestMaintainConfigHandler(TestCase):
    def test_on_pop_restores_previous_config(self):
        mock_logger = Mock(['name', 'level', 'setLevel'])

        success_template = Notification("success title", "success message")
        failure_template = Notification("failure title", "failure message")

        stack = Stack(
            [Config(notifications_backend=SelectedBackend("test"), logger_name="", logger_level="",
                    notifications_strategy=SelectedStrategy("test", ["5"]),
                    success_title="", success_message="", failure_title="", failure_message="")])

        h = MaintainConfig(stack=stack,
                           success_template=success_template,
                           failure_template=failure_template,
                           logger=mock_logger)

        h.command_complete_timeout_handler("10")
        self.assertEqual([10], stack.current.notifications_strategy.args)

        stack.push()

        h.command_complete_timeout_handler("42")
        self.assertEqual([42], stack.current.notifications_strategy.args)

        stack.pop()
        self.assertEqual([10], stack.current.notifications_strategy.args)
