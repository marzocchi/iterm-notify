import subprocess
from tempfile import NamedTemporaryFile
from typing import Protocol, Optional
from notifications import Notification
from abc import ABC, abstractmethod
import iterm2
import asyncio
import logging


class _Exec(Protocol):  # pragma: no cover
    def exec(self, cmd: list): pass


class ExecSubprocess:
    def exec(self, cmd: list):
        subprocess.run(cmd, stdin=None, capture_output=False, check=True, timeout=5)


class Backend(ABC):
    @abstractmethod
    def notify(self, n: Notification): pass


class Selectable(Backend):
    def __init__(self, notifiers: dict, selected: str, logger: Optional[logging.Logger] = None):
        self._logger = logger
        self._notifiers = notifiers
        self._selected = ''
        self.selected = selected

    @property
    def selected(self) -> str:
        return self._selected

    @selected.setter
    def selected(self, v: str):
        if v not in self._notifiers:
            raise RuntimeError("unknown notifier: {}".format(v))

        self._selected = v

    def notify(self, n: Notification):
        self._logger and self._logger.info("sending notification with {} backend".format(self._selected))
        self._notifiers[self._selected].notify(n)


class Iterm(Backend):
    def __init__(self, conn: iterm2.Connection, logger: Optional[logging.Logger] = None):
        self._logger = logger
        self._conn = conn

    def notify(self, n: Notification):
        alert = iterm2.Alert(n.title, n.message)
        self._logger and self._logger.info("sending notification: {}".format(n))
        asyncio.get_event_loop().create_task(alert.async_run(self._conn))


class OsaScript(Backend):
    _SCRIPT = "to run args\n" \
              "  tell application \"iTerm\"\n" \
              "    if item 3 of args is equal to \"\"\n" \
              "      display notification (item 1 of args as text) with title (item 2 of args as text)\n" \
              "    else\n" \
              "      display notification (item 1 of args as text) with title (item 2 of args as text)" \
              "        sound name (item 3 of args as text)\n" \
              "    end\n" \
              "  end tell\n" \
              "end run"

    def __init__(self, ex: _Exec, logger: Optional[logging.Logger] = None):
        self._logger = logger
        self._exec = ex

    def notify(self, n: Notification):
        with NamedTemporaryFile(mode='w') as tmp_file:
            tmp_file.write(self._SCRIPT)
            tmp_file.flush()

            cmd = [
                'osascript',
                tmp_file.name,
                n.message,
                n.title,
                "" if n.sound is None else n.sound
            ]

            self._logger and self._logger.info("sending notification: {}".format(n))
            self._exec.exec(cmd)


class TerminalNotifier(Backend):
    def __init__(self, ex: _Exec, path: str = 'terminal-notifier', logger: Optional[logging.Logger] = None):
        self._logger = logger
        self._exec = ex
        self.terminal_notifier_path = path

    def notify(self, n: Notification):
        cmd = [
            self.terminal_notifier_path,
            '-activate',
            'com.googlecode.iterm2',
            '-title',
            n.title,
            '-message',
            n.message
        ]

        if n.icon is not None:
            cmd.append('-appIcon')
            cmd.append(n.icon)

        if n.sound is not None:
            cmd.append('-sound')
            cmd.append(n.sound)

        self._logger and self._logger.info("sending notification: {}".format(n))
        self._exec.exec(cmd)
