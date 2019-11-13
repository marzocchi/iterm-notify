from unittest import TestCase
from unittest.mock import MagicMock

from notifications.config import Stack


class TestStack(TestCase):
    def test_push_pop(self):
        cfg = MagicMock(['command_complete_timeout'])

        s = Stack([cfg])

        s.current.command_complete_timeout = 5
        self.assertEqual(5, s.current.command_complete_timeout)

        s.push()
        self.assertEqual(5, s.current.command_complete_timeout)

        s.current.command_complete_timeout = 42
        self.assertEqual(42, s.current.command_complete_timeout)

        old = s.pop()
        self.assertEqual(42, old.command_complete_timeout)

        self.assertEqual(5, s.current.command_complete_timeout)

        with self.assertRaises(IndexError):
            s.pop()

    def test_on_pop(self):
        cfg = MagicMock(['command_complete_timeout'])

        s = Stack([cfg])

        s.current.command_complete_timeout = 5
        s.push()

        s.current.command_complete_timeout = 6
        f = MagicMock()

        s.on_pop += f

        s.pop()
        f.assert_called_once()
