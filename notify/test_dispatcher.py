from unittest import TestCase
from unittest.mock import MagicMock

from notify.dispatcher import Dispatcher


class TestDispatcher(TestCase):
    def test_dispatch(self):
        foo = MagicMock(['handle'])
        bar = MagicMock(['handle'])

        d = Dispatcher()

        d.register_handler("foo", foo.handle)
        d.register_handler("bar", bar.handle)

        d.dispatch("foo", ['a', 'b'])

        foo.handle.assert_called_with('a', 'b')
        bar.handle.assert_not_called()

    def test_dispatcher_raises_with_unknown_handler(self):
        d = Dispatcher()

        with self.assertRaises(RuntimeError):
            d.dispatch("foo", ['a'])
