from unittest import TestCase
from datetime import timedelta
from notifications import strategies
import typing


class MockCommand(object):
    def __init__(self, exit_code: int, duration: timedelta):
        self._exit_status = exit_code
        self._duration = duration

    @property
    def exit_code(self) -> int:
        return self._exit_status

    @property
    def duration(self) -> timedelta:
        return self._duration


class MockApp(object):
    def __init__(self, active: bool, current_session_id: typing.Union[None, str]):
        self._current_session_id = current_session_id
        self._active = active

    @property
    def active(self) -> bool:
        return self._active

    @property
    def current_session_id(self) -> typing.Union[None, str]:
        return self._current_session_id


class TestIfSlow(TestCase):
    def test_set_timeout(self):
        s = strategies.IfSlow(timeout=2)

        s.timeout = 5
        self.assertEqual(5, s.timeout)

    def test_will_notify(self):
        s = strategies.IfSlow(timeout=2)

        command = MockCommand(exit_code=0, duration=timedelta(seconds=5))
        self.assertTrue(s.should_notify(command))

    def test_will_not_notify(self):
        s = strategies.IfSlow(timeout=6)

        command = MockCommand(exit_code=0, duration=timedelta(seconds=5))
        self.assertFalse(s.should_notify(command))


class TestIfInactive(TestCase):
    def test_set_timeout(self):
        s = strategies.IfInactive(app=MockApp(active=True, current_session_id=None), session_id="foo", timeout=2)

        s.timeout = 5
        self.assertEqual(5, s.timeout)

    def test_will_notify_success_when_not_current_session(self):
        app = MockApp(active=True, current_session_id="bar")
        s = strategies.IfInactive(app=app, timeout=2, session_id="foo")

        command = MockCommand(exit_code=0, duration=timedelta(seconds=5))
        self.assertTrue(s.should_notify(command))

    def test_will_notify_success_when_app_not_active(self):
        app = MockApp(active=False, current_session_id="foo")
        s = strategies.IfInactive(app=app, timeout=2, session_id="foo")

        command = MockCommand(exit_code=0, duration=timedelta(seconds=5))
        self.assertTrue(s.should_notify(command))

    def test_will_not_notify_success_for_fast_commands(self):
        app = MockApp(active=False, current_session_id="bar")
        s = strategies.IfInactive(app=app, timeout=2, session_id="foo")

        command = MockCommand(exit_code=0, duration=timedelta(seconds=1))
        self.assertFalse(s.should_notify(command))

    def test_will_notify_failure_for_fast_commands(self):
        app = MockApp(active=True, current_session_id="bar")
        s = strategies.IfInactive(app=app, timeout=2, session_id="foo")

        command = MockCommand(exit_code=1, duration=timedelta(seconds=1))
        self.assertTrue(s.should_notify(command))

    def test_will_not_notify_success_when_in_front(self):
        app = MockApp(active=True, current_session_id="foo")
        s = strategies.IfInactive(app=app, timeout=2, session_id="foo")

        command = MockCommand(exit_code=0, duration=timedelta(seconds=4))
        self.assertFalse(s.should_notify(command))

    def test_will_not_notify_failure_when_current_session(self):
        app = MockApp(active=True, current_session_id="foo")
        s = strategies.IfInactive(app=app, timeout=2, session_id="foo")

        command = MockCommand(exit_code=1, duration=timedelta(seconds=4))
        self.assertFalse(s.should_notify(command))
