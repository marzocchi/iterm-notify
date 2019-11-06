from unittest import TestCase

from notifications import NotificationFactory, Notification
from notifications.handlers import Command
from datetime import datetime


class TestNotification(TestCase):
    def test(self):
        n = Notification("title1", "message1")

        self.assertEqual("title1", n.title)
        self.assertEqual("message1", n.message)

        n.title = "title2"
        n.message = "message2"

        self.assertEqual("title2", n.title)
        self.assertEqual("message2", n.message)

        n.icon = 'foo.png'
        self.assertEqual('foo.png', n.icon)

        n.sound = 'Glass'
        self.assertEqual('Glass', n.sound)


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

    def test_create_failure_without_sound(self):
        f = NotificationFactory(
            success=Notification(title="success in {duration_seconds:d} seconds", message="{command_line}",
                                 icon='success.png', sound='Glass'),
            failure=Notification(title="failure in {duration_seconds:d} seconds", message="{command_line}",
                                 icon='failure.png')
        )

        cmd = Command(datetime.fromtimestamp(self.TS_1), "some command")
        cmd.done(1, datetime.fromtimestamp(self.TS_2))

        n = f.create(cmd)

        self.assertEqual("failure in 19 seconds", n.title)
        self.assertEqual("some command", n.message)
        self.assertEqual("failure.png", n.icon)
        self.assertIsNone(n.sound)

    def test_create_success_without_sound(self):
        f = NotificationFactory(
            success=Notification(title="success in {duration_seconds:d} seconds", message="{command_line}",
                                 icon='success.png'),
            failure=Notification(title="failure in {duration_seconds:d} seconds", message="{command_line}",
                                 icon='failure.png', sound='Glass')
        )

        cmd = Command(datetime.fromtimestamp(self.TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(self.TS_2))

        n = f.create(cmd)

        self.assertEqual("success in 19 seconds", n.title)
        self.assertEqual("some command", n.message)
        self.assertEqual("success.png", n.icon)
        self.assertIsNone(n.sound)

    def test_can_omit_vars(self):
        f = NotificationFactory(
            success=Notification(title="no vars", message="{command_line}"),
            failure=Notification(title="no vars", message="{command_line}")
        )

        cmd = Command(datetime.fromtimestamp(self.TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(self.TS_2))

        n = f.create(cmd)
        self.assertEqual("no vars", n.title)

    def test_does_not_raise_if_unknown_vars_in_title(self):
        f = NotificationFactory(
            success=Notification(title="{some_var}", message="{command_line}"),
            failure=Notification(title="{some_var}", message="{command_line}")
        )

        cmd = Command(datetime.fromtimestamp(self.TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(self.TS_2))

        n = f.create(cmd)

        self.assertEqual("{some_var}", n.title)
        self.assertEqual("some command", n.message)

    def test_does_not_raise_if_unknown_vars_in_message(self):
        f = NotificationFactory(
            success=Notification(title="{duration_seconds}", message="{some_var}"),
            failure=Notification(title="{duration_seconds}", message="{some_var}")
        )

        cmd = Command(datetime.fromtimestamp(self.TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(self.TS_2))

        n = f.create(cmd)

        self.assertEqual("19", n.title)
        self.assertEqual("{some_var}", n.message)
