from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock, PropertyMock

from notify.commands import Command
from notify.config import Config, Stack
from notify.notifications import Factory, apply_template

TS_1 = 1572889271
TS_2 = 1572889290.1234567


def mock_properties(mock: Mock, **kwargs):
    for k in kwargs:
        setattr(type(mock), k, PropertyMock(return_value=kwargs[k]))


class TestFactory(TestCase):
    def setUp(self) -> None:
        self.__mock_config = Mock(spec=Config)
        self.__mock_stack = Mock(spec=Stack)

        mock_properties(self.__mock_config, success_title="success in {duration}", success_message="{command_line}",
                        success_icon="success.png", success_sound="Success", failure_title="failure in {duration}",
                        failure_message="{command_line}", failure_icon="failure.png", failure_sound="Failure")

        mock_properties(self.__mock_stack, current=self.__mock_config)
        self.__factory = Factory(stack=self.__mock_stack)

    def test_create_success(self):
        n = self.__factory.create("message", "title")
        self.assertEqual("message", n.message)
        self.assertEqual("title", n.title)
        self.assertEqual("success.png", n.icon)
        self.assertEqual("Success", n.sound)

    def test_create_failure(self):
        n = self.__factory.create("message", "title", success=False)
        self.assertEqual("message", n.message)
        self.assertEqual("title", n.title)
        self.assertEqual("failure.png", n.icon)
        self.assertEqual("Failure", n.sound)

    def test_from_command_successful(self):
        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        complete_command = cmd.complete(0, datetime.fromtimestamp(TS_2))

        n = self.__factory.from_command(complete_command)

        self.assertEqual("success in 0:00:19", n.title)
        self.assertEqual("some command", n.message)
        self.assertEqual("success.png", n.icon)

    def test_from_command_failed(self):
        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        complete_command = cmd.complete(1, datetime.fromtimestamp(TS_2))

        n = self.__factory.from_command(complete_command)

        self.assertEqual("failure in 0:00:19", n.title)
        self.assertEqual("some command", n.message)
        self.assertEqual("failure.png", n.icon)

    def test_from_command_failed_without_icon(self):
        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        complete_command = cmd.complete(1, datetime.fromtimestamp(TS_2))

        mock_properties(self.__mock_config, failure_icon=None)

        n = self.__factory.from_command(complete_command)

        self.assertEqual("failure in 0:00:19", n.title)
        self.assertEqual("some command", n.message)
        self.assertIsNone(n.icon)

    def test_from_command_successful_without_icon(self):
        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        complete_command = cmd.complete(0, datetime.fromtimestamp(TS_2))

        mock_properties(self.__mock_config, success_icon=None)

        n = self.__factory.from_command(complete_command)

        self.assertEqual("success in 0:00:19", n.title)
        self.assertEqual("some command", n.message)
        self.assertIsNone(n.icon)

    def test_from_command_failure_without_sound(self):
        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        complete_command = cmd.complete(1, datetime.fromtimestamp(TS_2))

        mock_properties(self.__mock_config, failure_sound=None)

        n = self.__factory.from_command(complete_command)

        self.assertEqual("failure in 0:00:19", n.title)
        self.assertEqual("some command", n.message)
        self.assertEqual("failure.png", n.icon)
        self.assertIsNone(n.sound)

    def test_from_command_successful_without_sound(self):
        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        complete_command = cmd.complete(0, datetime.fromtimestamp(TS_2))

        mock_properties(self.__mock_config, success_sound=None)

        n = self.__factory.from_command(complete_command)

        self.assertEqual("success in 0:00:19", n.title)
        self.assertEqual("some command", n.message)
        self.assertEqual("success.png", n.icon)
        self.assertIsNone(n.sound)

    def test_from_command_without_vars(self):
        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        complete_command = cmd.complete(0, datetime.fromtimestamp(TS_2))

        mock_properties(self.__mock_config, success_title="no vars")

        n = self.__factory.from_command(complete_command)
        self.assertEqual("no vars", n.title)

    def test_from_command_does_not_raise_with_unknown_vars_in_title(self):
        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        complete_command = cmd.complete(0, datetime.fromtimestamp(TS_2))

        mock_properties(self.__mock_config, success_title="{some_var}")

        n = self.__factory.from_command(complete_command)

        self.assertEqual("{some_var}", n.title)
        self.assertEqual("some command", n.message)

    def test_from_command_does_not_raise_with_unknown_vars_in_message(self):
        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        complete_command = cmd.complete(0, datetime.fromtimestamp(TS_2))

        mock_properties(self.__mock_config, success_message="{some_var}")

        n = self.__factory.from_command(complete_command)

        self.assertEqual("success in 0:00:19", n.title)
        self.assertEqual("{some_var}", n.message)


class TestApplyTemplate(TestCase):
    def test(self):
        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        complete_cmd = cmd.complete(0, datetime.fromtimestamp(TS_2))

        self.assertEqual("0:00:19", apply_template("{duration}", complete_cmd))
        self.assertEqual("some command", apply_template("{command_line}", complete_cmd))
        self.assertEqual("0", apply_template("{exit_code}", complete_cmd))
