from unittest import TestCase
from unittest.mock import MagicMock, ANY
from notifications import Notification, handlers
from notifications.dispatcher import Dispatcher, build
import logging
import typing


class _Logger(object):
    def debug(self, msg: str): pass

    def info(self, msg: str): pass

    def warning(self, msg: str): pass

    def error(self, msg: str): pass

    def critical(self, msg: str): pass


class _MockHandler(object):
    def handle(self, args: list) -> None: pass


class TestDispatcher(TestCase):
    def test_dispatch(self):
        foo = _MockHandler()
        foo.handle = MagicMock()

        bar = _MockHandler()
        bar.handle = MagicMock()

        d = Dispatcher(logger=_Logger())

        d.register_handler("foo", foo.handle)
        d.register_handler("bar", bar.handle)

        d.dispatch("foo", ['a', 'b'])

        foo.handle.assert_called_with(['a', 'b'])
        bar.handle.assert_not_called()

    def test_dispatcher_raises(self):
        d = Dispatcher(logger=_Logger())

        with self.assertRaises(RuntimeError):
            d.dispatch("foo", ['a'])


class _MockStrategy(object):
    def __init__(self):
        self._timeout = 0

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, v: int):
        self._timeout = v

    def should_notify(self, cmd: handlers.Command) -> bool: pass


class _MockBackend(object):
    @property
    def selected(self) -> str: pass

    @selected.setter
    def selected(self, v: str): pass

    def notify(self, n: Notification): pass


class TestIntegrationDispatcher(TestCase):
    def test(self):
        strategy = _MockStrategy()
        strategy.should_notify = MagicMock(return_value=True)
        strategy.timeout = 42

        backend = _MockBackend()
        backend.notify = MagicMock()

        logger = logging.getLogger("test-dispatcher")
        logger.setLevel(logging.DEBUG)

        d = build(strategy, backend, logger=logger)

        d.dispatch('set-command-complete-timeout', ["1"])
        self.assertEqual(1, strategy.timeout)

        d.dispatch('before-command', ['ls -l'])
        d.dispatch('after-command', ['1'])

        backend.notify.assert_called_once()

        n = backend.notify.call_args[0][0]

        self.assertEqual('#fail (in 0s)', n.title)
        self.assertEqual('ls -l', n.message)
        self.assertIsNone(n.icon)
        self.assertIsNone(n.sound)
