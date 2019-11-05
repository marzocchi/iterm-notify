from notifications import Notification
import typing
from subprocess import run


class _Runner(typing.Protocol):
    def run(self, cmd: list):
        pass


class RunCommand(object):
    def run(self, cmd: list):
        run(cmd, input=None, stdin=None, capture_output=False, check=True, timeout=1)


class TerminalNotifier(object):
    def __init__(self, runner: _Runner, path: str = 'terminal-notifier'):
        self._runner = runner
        self.terminal_notifier_path = path

    def notify(self, n: Notification):
        cmd = [
            self.terminal_notifier_path,
            '-title',
            n.title,
            '-message',
            n.message
        ]

        if n.icon is not None:
            cmd.append('-appIcon')
            cmd.append(n.icon)

        self._runner.run(cmd)
