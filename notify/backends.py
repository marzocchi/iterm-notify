import asyncio
import logging
import shlex
import subprocess
from abc import ABC, abstractmethod
from tempfile import NamedTemporaryFile
from typing import Dict, List, Protocol

import iterm2

from notify.config import SelectedBackend
from notify.notifications import Notification


class Executor:
    def __init__(self, logger: logging.Logger):
        self.__logger = logger

    def execute(self, cmd: list):
        self.__logger.info(f"executing {shlex.join(cmd)}")
        subprocess.run(cmd, stdin=None, capture_output=False, check=True, timeout=5)


class Backend(ABC):
    @abstractmethod
    def notify(self, n: Notification): ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def args(self) -> List[str]: ...


class BackendInitializer(Protocol):
    def __call__(self, *args) -> Backend: ...


class BackendFactory:
    def __init__(self, initializers: Dict[str, BackendInitializer]):
        self.__initializers = initializers

    def create(self, selected_backend: SelectedBackend) -> Backend:
        if not isinstance(selected_backend, SelectedBackend):
            raise ValueError(f"argument must be a SelectedBackend, got {selected_backend}")

        try:
            if selected_backend.name not in self.__initializers:
                raise ValueError("unknown backend: {}".format(selected_backend.name))
        except TypeError as e:
            raise e

        return self.__initializers[selected_backend.name](*selected_backend.args)


class iTerm(Backend):
    def __init__(self, logger: logging.Logger, conn: iterm2.Connection):
        self.__logger = logger
        self.__conn = conn

    @property
    def name(self) -> str:
        return 'iterm'

    @property
    def args(self) -> List[str]:
        return []

    @classmethod
    def create_factory(cls, logger: logging.Logger, conn: iterm2.Connection) -> BackendInitializer:
        def create_iterm(*args):
            return cls(logger=logger, conn=conn)

        return create_iterm

    def notify(self, n: Notification):
        alert = iterm2.Alert(n.title, n.message)
        self.__logger.info("sending notification: {}".format(n))
        asyncio.get_event_loop().create_task(alert.async_run(self.__conn))


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

    def __init__(self, logger: logging.Logger, executor: Executor):
        self.__executor = executor
        self.__logger = logger

    @property
    def name(self) -> str:
        return 'osascript'

    @property
    def args(self) -> List[str]:
        return []

    @classmethod
    def create_factory(cls, logger: logging.Logger, executor: Executor) -> BackendInitializer:
        def create_osascript(*args) -> Backend:
            return cls(logger=logger, executor=executor)

        return create_osascript

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

            self.__logger.info("sending notification: {}".format(n))
            self.__executor.execute(cmd)


class TerminalNotifier(Backend):
    def __init__(self, logger: logging.Logger, executor: Executor, path: str):
        self.__executor = executor
        self.__logger = logger
        self.__terminal_notifier_path = path

    @property
    def name(self) -> str:
        return 'terminal-notifier'

    @property
    def args(self) -> List[str]:
        return [self.__terminal_notifier_path]

    @classmethod
    def create_factory(cls, logger: logging.Logger, executor: Executor) -> BackendInitializer:
        def create_terminal_notifier(*args) -> Backend:
            return cls(logger=logger, executor=executor, path=args[0])

        return create_terminal_notifier

    def notify(self, n: Notification):
        cmd = [
            self.__terminal_notifier_path,
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

        self.__logger.info("sending notification: {}".format(n))
        self.__executor.execute(cmd)
