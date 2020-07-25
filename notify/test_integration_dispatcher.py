import logging
from unittest import TestCase
from unittest.mock import Mock

from notify import build_dispatcher
from notify.backends import Backend, BackendFactory
from notify.config import Config, SelectedBackend, SelectedStrategy, Stack
from notify.strategies import StrategyFactory


class TestIntegrationDispatcher(TestCase):
    def test(self):
        strategy = Mock(['should_notify', 'timeout'])
        strategy.should_notify = Mock(return_value=True)
        strategy.timeout = 42

        strategy_factory = Mock(spec=StrategyFactory)
        strategy_factory.create.return_value = strategy

        backend = Mock(spec=Backend)
        backend.notify = Mock()

        backend_factory = Mock(spec=BackendFactory)
        backend_factory.create.return_value = backend

        cfg = Config(notifications_backend=SelectedBackend("test"), logger_name="",
                     logger_level=logging.getLevelName(logging.CRITICAL),
                     notifications_strategy=SelectedStrategy("test", args=['42']),
                     success_title="",
                     success_message="",
                     failure_title="#fail (in 0s)",
                     failure_message="{command_line}")

        stack = Stack([cfg])

        d = build_dispatcher(
            stack=stack,
            strategy_factory=strategy_factory,
            backend_factory=backend_factory,
            logger=logging.getLogger(__name__)
        )

        d.dispatch('set-command-complete-timeout', ["1"])
        self.assertEqual([1], stack.notifications_strategy.args)

        d.dispatch('before-command', ['ls -l'])
        d.dispatch('after-command', ['1'])

        backend.notify.assert_called_once()

        n = backend.notify.call_args[0][0]

        self.assertEqual('#fail (in 0s)', n.title)
        self.assertEqual('ls -l', n.message)
        self.assertIsNone(n.icon)
        self.assertIsNone(n.sound)
