from notifications import Notification
from tempfile import NamedTemporaryFile
import typing
import iterm2
import subprocess
import asyncio


class _Exec(typing.Protocol):  # pragma: no cover
    def exec(self, cmd: list):
        pass


class ExecSubprocess(object):
    def exec(self, cmd: list):
        subprocess.run(cmd, input=None, stdin=None, capture_output=False, check=True, timeout=1)


class SwitchableNotifier(object):
    def __init__(self, notifiers: dict, selected: str):
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
        self._notifiers[self._selected].notify(n)


class iTermNotifier(object):
    def __init__(self, conn: iterm2.Connection):
        self._conn = conn

    def notify(self, n: Notification):
        alert = iterm2.Alert(n.title, n.message)
        asyncio.get_event_loop().create_task(alert.async_run(self._conn))


class OsaScriptNotifier(object):
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

    def __init__(self, ex: _Exec):
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

            self._exec.exec(cmd)


class TerminalNotifier(object):
    def __init__(self, ex: _Exec, path: str = 'terminal-notifier'):
        self._exec = ex
        self.terminal_notifier_path = path

    def notify(self, n: Notification):
        cmd = [
            self.terminal_notifier_path,
            '-activate',
            'com.googlecode.iterm2',
            '-sender',
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

        self._exec.exec(cmd)
