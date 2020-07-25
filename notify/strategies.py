from abc import ABC, abstractmethod
from typing import Dict, Protocol, Union

import iterm2

from notify.commands import CompleteCommand
from notify.config import SelectedStrategy


class App(Protocol):
    # noinspection PyPropertyDefinition
    @property
    def active(self) -> bool: ...

    # noinspection PyPropertyDefinition
    @property
    def current_session_id(self) -> Union[None, str]: ...


class iTermAppAdapter:
    def __init__(self, iterm: iterm2.App):
        self.__iterm = iterm

    @property
    def active(self) -> bool:
        return self.__iterm.app_active

    @property
    def current_session_id(self) -> Union[None, str]:
        for tab in self.__iterm.current_window.tabs:
            for s in tab.sessions:
                if tab.active_session_id == s.session_id and tab.tab_id == self.__iterm.current_window.selected_tab_id:
                    return s.session_id

        return None


class Strategy(ABC):
    @abstractmethod
    def should_notify(self, cmd: CompleteCommand) -> bool: ...


class StrategyInitializer(Protocol):
    def __call__(self, *args) -> Strategy: ...


class StrategyFactory:
    def __init__(self, factories: Dict[str, StrategyInitializer]):
        self.__factories = factories

    def create(self, selected_strategy: SelectedStrategy) -> Strategy:
        if not isinstance(selected_strategy, SelectedStrategy):
            raise ValueError(f"argument must be a SelectedStrategy, got {selected_strategy}")

        if selected_strategy.name not in self.__factories:
            raise ValueError("unknown backend: {}".format(selected_strategy.name))

        return self.__factories[selected_strategy.name](*selected_strategy.args)


class WhenSlow(Strategy):
    def __init__(self, timeout: int):
        self.__timeout = timeout

    @classmethod
    def create_factory(cls) -> StrategyInitializer:
        def f(*args):
            timeout = args[0]
            return WhenSlow(timeout=timeout)

        return f

    def should_notify(self, cmd: CompleteCommand) -> bool:
        return cmd.duration.seconds > self.__timeout

    @property
    def timeout(self) -> int:
        return self.__timeout

    @timeout.setter
    def timeout(self, v: int):
        self.__timeout = v


class WhenInactive(Strategy):
    def __init__(self, app: App, session_id: str, when_slow: WhenSlow):
        self.__app = app
        self.__session_id = session_id
        self.__when_slow = when_slow

    @classmethod
    def create_factory(cls, app: App, session_id: str) -> StrategyInitializer:
        def f(*args):
            timeout = args[0]
            return WhenInactive(app=app, session_id=session_id, when_slow=WhenSlow(timeout=timeout))

        return f

    @property
    def timeout(self) -> int:
        return self.__when_slow.timeout

    @timeout.setter
    def timeout(self, v: int):
        self.__when_slow.timeout = v

    def should_notify(self, cmd: CompleteCommand) -> bool:
        # no need to notify about a successful command that run fast
        slow = self.__when_slow.should_notify(cmd)

        if cmd.successful and not slow:
            return False

        # if the command failed or was slow, notify if this is not the current session or the app is not active
        # (as we don't if the session's tab is active, but eg. covered by some other window)
        active_session = self.__app.active and self.__session_id == self.__app.current_session_id

        return not active_session
