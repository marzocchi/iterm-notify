from unittest import TestCase

from notifications import NotificationFactory, Notification
from notifications.handlers import Command
from datetime import datetime


class TestNotificationFactory(TestCase):
    TS_1 = 1572889271
    TS_2 = 1572889290

    def test_create_from_successful_command(self):
        f = NotificationFactory(
            success=Notification(title="success in {duration_seconds:d} seconds", message="{command_line}",
                                 icon='success.png'),
            failure=Notification(title="failure in {duration_seconds:d} seconds", message="{command_line}",
                                 icon='failure.png')
        )

        cmd = Command(datetime.fromtimestamp(self.TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(self.TS_2))

        n = f.create(cmd)

        self.assertEqual("success in 19 seconds", n.title)
        self.assertEqual("some command", n.message)
        self.assertEqual("success.png", n.icon)

    def test_create_from_failed_command(self):
        f = NotificationFactory(
            success=Notification(title="success in {duration_seconds:d} seconds", message="{command_line}",
                                 icon='success.png'),
            failure=Notification(title="failure in {duration_seconds:d} seconds", message="{command_line}",
                                 icon='failure.png')
        )

        cmd = Command(datetime.fromtimestamp(self.TS_1), "some command")
        cmd.done(1, datetime.fromtimestamp(self.TS_2))

        n = f.create(cmd)

        self.assertEqual("failure in 19 seconds", n.title)
        self.assertEqual("some command", n.message)
        self.assertEqual("failure.png", n.icon)

    def test_create_failure_without_icon(self):
        f = NotificationFactory(
            success=Notification(title="success in {duration_seconds:d} seconds", message="{command_line}",
                                 icon='success.png'),
            failure=Notification(title="failure in {duration_seconds:d} seconds", message="{command_line}")
        )

        cmd = Command(datetime.fromtimestamp(self.TS_1), "some command")
        cmd.done(1, datetime.fromtimestamp(self.TS_2))

        n = f.create(cmd)

        self.assertEqual("failure in 19 seconds", n.title)
        self.assertEqual("some command", n.message)
        self.assertIsNone(n.icon)

    def test_create_success_without_icon(self):
        f = NotificationFactory(
            success=Notification(title="success in {duration_seconds:d} seconds", message="{command_line}"),
            failure=Notification(title="failure in {duration_seconds:d} seconds", message="{command_line}",
                                 icon='failure.png')
        )

        cmd = Command(datetime.fromtimestamp(self.TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(self.TS_2))

        n = f.create(cmd)

        self.assertEqual("success in 19 seconds", n.title)
        self.assertEqual("some command", n.message)
        self.assertIsNone(n.icon)
