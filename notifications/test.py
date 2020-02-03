from unittest import TestCase
from notifications import Command, Factory, Notification, apply_template
from datetime import datetime

TS_1 = 1572889271
TS_2 = 1572889290.1234567


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


class TestFactory(TestCase):
    def test_create_success(self):
        f = Factory(
            success=Notification(title="", message="", icon="success.png", sound="Success"),
            failure=Notification(title="", message="", icon="failure.png", sound="Failure"),
        )

        n = f.create("message", "title")

        self.assertEqual("message", n.message)
        self.assertEqual("title", n.title)
        self.assertEqual("success.png", n.icon)
        self.assertEqual("Success", n.sound)

    def test_create_failure(self):
        f = Factory(
            success=Notification(title="", message="", icon="success.png", sound="Success"),
            failure=Notification(title="", message="", icon="failure.png", sound="Failure"),
        )

        n = f.create("message", "title", success=False)

        self.assertEqual("message", n.message)
        self.assertEqual("title", n.title)
        self.assertEqual("failure.png", n.icon)
        self.assertEqual("Failure", n.sound)

    def test_from_command_successful(self):
        f = Factory(
            success=Notification(title="success in {duration}", message="{command_line}",
                                 icon='success.png'),
            failure=Notification(title="failure in {duration}", message="{command_line}",
                                 icon='failure.png')
        )

        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(TS_2))

        n = f.from_command(cmd)

        self.assertEqual("success in 0:00:19", n.title)
        self.assertEqual("some command", n.message)
        self.assertEqual("success.png", n.icon)

    def test_from_command_failed(self):
        f = Factory(
            success=Notification(title="success in {duration}", message="{command_line}",
                                 icon='success.png'),
            failure=Notification(title="failure in {duration}", message="{command_line}",
                                 icon='failure.png')
        )

        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        cmd.done(1, datetime.fromtimestamp(TS_2))

        n = f.from_command(cmd)

        self.assertEqual("failure in 0:00:19", n.title)
        self.assertEqual("some command", n.message)
        self.assertEqual("failure.png", n.icon)

    def test_from_command_failed_without_icon(self):
        f = Factory(
            success=Notification(title="success in {duration}", message="{command_line}",
                                 icon='success.png'),
            failure=Notification(title="failure in {duration}", message="{command_line}")
        )

        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        cmd.done(1, datetime.fromtimestamp(TS_2))

        n = f.from_command(cmd)

        self.assertEqual("failure in 0:00:19", n.title)
        self.assertEqual("some command", n.message)
        self.assertIsNone(n.icon)

    def test_from_command_successful_without_icon(self):
        f = Factory(
            success=Notification(title="success in {duration}", message="{command_line}"),
            failure=Notification(title="failure in {duration}", message="{command_line}",
                                 icon='failure.png')
        )

        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(TS_2))

        n = f.from_command(cmd)

        self.assertEqual("success in 0:00:19", n.title)
        self.assertEqual("some command", n.message)
        self.assertIsNone(n.icon)

    def test_from_command_failure_without_sound(self):
        f = Factory(
            success=Notification(title="success in {duration}", message="{command_line}",
                                 icon='success.png', sound='Glass'),
            failure=Notification(title="failure in {duration}", message="{command_line}",
                                 icon='failure.png')
        )

        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        cmd.done(1, datetime.fromtimestamp(TS_2))

        n = f.from_command(cmd)

        self.assertEqual("failure in 0:00:19", n.title)
        self.assertEqual("some command", n.message)
        self.assertEqual("failure.png", n.icon)
        self.assertIsNone(n.sound)

    def test_from_command_successful_without_sound(self):
        f = Factory(
            success=Notification(title="success in {duration}", message="{command_line}",
                                 icon='success.png'),
            failure=Notification(title="failure in {duration}", message="{command_line}",
                                 icon='failure.png', sound='Glass')
        )

        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(TS_2))

        n = f.from_command(cmd)

        self.assertEqual("success in 0:00:19", n.title)
        self.assertEqual("some command", n.message)
        self.assertEqual("success.png", n.icon)
        self.assertIsNone(n.sound)

    def test_from_command_without_vars(self):
        f = Factory(
            success=Notification(title="no vars", message="{command_line}"),
            failure=Notification(title="no vars", message="{command_line}")
        )

        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(TS_2))

        n = f.from_command(cmd)
        self.assertEqual("no vars", n.title)

    def test_from_command_does_not_raise_with_unknown_vars_in_title(self):
        f = Factory(
            success=Notification(title="{some_var}", message="{command_line}"),
            failure=Notification(title="{some_var}", message="{command_line}")
        )

        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(TS_2))

        n = f.from_command(cmd)

        self.assertEqual("{some_var}", n.title)
        self.assertEqual("some command", n.message)

    def test_from_command_does_not_raise_with_unknown_vars_in_message(self):
        f = Factory(
            success=Notification(title="{duration}", message="{some_var}"),
            failure=Notification(title="{duration}", message="{some_var}")
        )

        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(TS_2))

        n = f.from_command(cmd)

        self.assertEqual("0:00:19", n.title)
        self.assertEqual("{some_var}", n.message)


class TestApplyTemplate(TestCase):
    def test(self):
        cmd = Command(datetime.fromtimestamp(TS_1), "some command")
        cmd.done(0, datetime.fromtimestamp(TS_2))

        self.assertEqual("0:00:19", apply_template("{duration}", cmd))
        self.assertEqual("some command", apply_template("{command_line}", cmd))
        self.assertEqual("0", apply_template("{exit_code}", cmd))

