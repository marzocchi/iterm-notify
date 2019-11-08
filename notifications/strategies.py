import iterm2
import typing
from datetime import timedelta


class _Command(typing.Protocol):
    @property
    def exit_code(self) -> int:
        pass

    @property
    def duration(self) -> timedelta:
        pass


class App(typing.Protocol):
    @property
    def active(self) -> bool:
        pass

    @property
    def current_session_id(self) -> typing.Union[None, str]:
        pass


class iTermApp(object):
    def __init__(self, iterm: iterm2.App):
        self._iterm = iterm

    @property
    def active(self) -> bool:
        return self._iterm.app_active

    @property
    def current_session_id(self) -> typing.Union[None, str]:
        for tab in self._iterm.current_window.tabs:
            for s in tab.sessions:
                if tab.active_session_id == s.session_id and tab.tab_id == self._iterm.current_window.selected_tab_id:
                    return s.session_id

        return None


class WhenSlow(object):
    def __init__(self, timeout: int):
        self._timeout = timeout

    def should_notify(self, cmd: _Command):
        return cmd.duration.seconds > self._timeout

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, v: int):
        self._timeout = v


class WhenInactive():
    def __init__(self, app: App, session_id: str, when_slow:WhenSlow):
        self._app = app
        self._session_id = session_id
        self._when_slow = when_slow

    @property
    def timeout(self) -> int:
        return self._when_slow.timeout

    @timeout.setter
    def timeout(self, v: int):
        self._when_slow.timeout = v

    def should_notify(self, cmd: _Command) -> bool:
        # no need to notify about a successful command that run fast
        failed = cmd.exit_code > 0
        slow = self._when_slow.should_notify(cmd)

        if not failed and not slow:
            return False

        # if the command failed or was slow, notify if this is not the current session or the app is not active
        # (as we don't if the session's tab is active, but eg. covered by some other window)
        active_session = self._app.active and self._session_id == self._app.current_session_id

        return not active_session
