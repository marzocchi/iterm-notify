from unittest import TestCase
from unittest.mock import MagicMock
import logging
from notifications.config import Stack, Config
from notifications.monitor import build_dispatcher


class TestIntegrationDispatcher(TestCase):
    def test(self):
        strategy = MagicMock(['should_notify', 'timeout'])
        strategy.should_notify = MagicMock(return_value=True)
        strategy.timeout = 42

        backend = MagicMock(['notify'])
        backend.notify = MagicMock()

        cfg = Config(notifications_backend="", logger_name="", logger_level=logging.CRITICAL,
                     command_complete_timeout=0, success_title="", success_message="",
                     failure_title="#fail (in 0s)", failure_message="{command_line}")

        d = build_dispatcher(
            stack=Stack([cfg]),
            strategy=strategy,
            backend=backend,
            logger=logging.getLogger(__name__)
        )

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
