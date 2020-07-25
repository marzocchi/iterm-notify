from datetime import datetime, timedelta
from typing import Union
from unittest import TestCase

from notify.commands import Command
from notify.strategies import WhenInactive, WhenSlow


class MockApp:
    def __init__(self, active: bool, current_session_id: Union[None, str]):
        self._current_session_id = current_session_id
        self._active = active

    @property
    def active(self) -> bool:
        return self._active

    @property
    def current_session_id(self) -> Union[None, str]:
        return self._current_session_id


class TestIfSlow(TestCase):

    def setUp(self) -> None:
        super().setUp()

        self.started_at = datetime.now()

    def test_set_timeout(self):
        s = WhenSlow(timeout=2)

        s.timeout = 5
        self.assertEqual(5, s.timeout)

    def test_will_notify(self):
        s = WhenSlow(timeout=2)

        command = Command(self.started_at, "ls")
        command_complete = command.complete(0, self.started_at + timedelta(seconds=5))

        self.assertTrue(s.should_notify(command_complete))

    def test_will_not_notify(self):
        s = WhenSlow(timeout=6)

        command = Command(self.started_at, "ls")
        complete_command = command.complete(0, self.started_at + timedelta(seconds=5))

        self.assertFalse(s.should_notify(complete_command))


class TestIfInactive(TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.started_at = datetime.now()

    def test_set_timeout(self):
        s = WhenInactive(app=MockApp(active=True, current_session_id=None), session_id="foo",
                         when_slow=WhenSlow(timeout=2))

        s.timeout = 5
        self.assertEqual(5, s.timeout)

    def test_will_notify_success_when_not_current_session(self):
        app = MockApp(active=True, current_session_id="bar")
        s = WhenInactive(app=app, when_slow=WhenSlow(timeout=2), session_id="foo")

        command = Command(self.started_at, "ls")
        complete_command = command.complete(0, self.started_at + timedelta(seconds=5))

        self.assertTrue(s.should_notify(complete_command))

    def test_will_notify_success_when_app_not_active(self):
        app = MockApp(active=False, current_session_id="foo")
        s = WhenInactive(app=app, when_slow=WhenSlow(timeout=2), session_id="foo")

        command = Command(self.started_at, "ls")
        complete_command = command.complete(0, self.started_at + timedelta(seconds=5))

        self.assertTrue(s.should_notify(complete_command))

    def test_will_not_notify_success_for_fast_commands(self):
        app = MockApp(active=False, current_session_id="bar")
        s = WhenInactive(app=app, when_slow=WhenSlow(timeout=2), session_id="foo")

        command = Command(self.started_at, "ls")
        complete_command = command.complete(0, self.started_at + timedelta(seconds=1))

        self.assertFalse(s.should_notify(complete_command))

    def test_will_notify_failure_for_fast_commands(self):
        app = MockApp(active=True, current_session_id="bar")
        s = WhenInactive(app=app, when_slow=WhenSlow(timeout=2), session_id="foo")

        command = Command(self.started_at, "ls")
        complete_command = command.complete(1, self.started_at + timedelta(seconds=1))

        self.assertTrue(s.should_notify(complete_command))

    def test_will_not_notify_success_when_in_front(self):
        app = MockApp(active=True, current_session_id="foo")
        s = WhenInactive(app=app, when_slow=WhenSlow(timeout=2), session_id="foo")

        command = Command(self.started_at, "ls")
        complete_command = command.complete(0, self.started_at + timedelta(seconds=4))

        self.assertFalse(s.should_notify(complete_command))

    def test_will_not_notify_failure_when_current_session(self):
        app = MockApp(active=True, current_session_id="foo")
        s = WhenInactive(app=app, when_slow=WhenSlow(timeout=2), session_id="foo")

        command = Command(self.started_at, "ls")
        complete_command = command.complete(1, self.started_at + timedelta(seconds=4))

        self.assertFalse(s.should_notify(complete_command))
