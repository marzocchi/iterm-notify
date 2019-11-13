from typing import Protocol
from notifications import Command, Notification
from datetime import datetime


class _Strategy(Protocol):
    def should_notify(self, cmd: Command) -> bool: pass


class _Stack(Protocol):
    def push(self): pass

    def pop(self): pass


class _Backend(Protocol):
    def notify(self, n: Notification): pass


class _Factory(Protocol):
    def from_command(self, cmd: Command) -> Notification: pass


class NotifyCommandComplete:
    """Handler to send a notification when a command is finished.

    This handler sends a notification created by _Factory using the given _Backend but only when the _Strategy
    allows it.
    """

    def __init__(self, stack: _Stack,
                 strategy: _Strategy,
                 factory: _Factory,
                 backend: _Backend):

        self._stack = stack
        self._strategy = strategy
        self._factory = factory
        self._backend = backend

        self._commands: list = []

    def before_command(self, command_line: str):
        self._stack.push()
        self._commands.append(Command(datetime.now(), command_line))

    def after_command(self, exit_code: str):
        exit_code = int(exit_code)

        if len(self._commands) == 0:
            raise RuntimeError("after_command without a command")

        cmd = self._commands.pop()

        cmd.done(exit_code, datetime.now())

        if self._strategy.should_notify(cmd):
            n = self._factory.from_command(cmd)
            self._backend.notify(n)

        self._stack.pop()
