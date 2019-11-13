from copy import copy
from typing import Optional, List


class _EventHandlers:
    def __init__(self):
        self._handlers = []

    def __iadd__(self, other):
        self._handlers.append(other)
        return self

    def __isub__(self, other):
        self._handlers.remove(other)
        return self

    def reset(self):
        self._handlers = []

    def dispatch(self):
        for h in self._handlers:
            h()


class Config:
    def __init__(self,
                 notifications_backend: str,
                 logger_name: str,
                 logger_level: str,
                 command_complete_timeout: int,
                 success_title: str,
                 success_message: str,
                 failure_title: str,
                 failure_message: str,
                 success_icon: Optional[str] = None, success_sound: Optional[str] = None,
                 failure_icon: Optional[str] = None, failure_sound: Optional[str] = None):
        self.logger_name = logger_name
        self.logger_level = logger_level
        self.command_complete_timeout = command_complete_timeout
        self.notifications_backend = notifications_backend

        self.failure_icon = failure_icon
        self.failure_sound = failure_sound
        self.failure_message = failure_message
        self.failure_title = failure_title

        self.success_icon = success_icon
        self.success_sound = success_sound
        self.success_message = success_message
        self.success_title = success_title

    def to_dict(self) -> dict:
        return {
            'logger-name': self.logger_name,
            'logger-level': self.logger_level,
            'command-complete-timeout': self.command_complete_timeout,
            'notifications-backend': self.notifications_backend,
            'success-title': self.success_title,
            'success-message': self.success_message,
            'success-icon': self.success_icon,
            'success-sound': self.success_sound,
            'failure-title': self.failure_title,
            'failure-message': self.failure_message,
            'failure-icon': self.failure_icon,
            'failure-sound': self.failure_sound,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        return cls(
            success_title=data['success-title'],
            success_message=data['success-message'],
            success_icon=data['success-icon'],
            success_sound=data['success-sound'],
            failure_title=data['failure-title'],
            failure_message=data['failure-message'],
            failure_icon=data['failure-icon'],
            failure_sound=data['failure-sound'],
            notifications_backend=data['notifications-backend'],
            logger_name=data['logger-name'],
            logger_level=data['logger-level'],
            command_complete_timeout=data['command-complete-timeout']
        )

    def update(self, other: dict):
        self.__dict__.update(other)


def create_default(session_id: str) -> Config:
    return Config(
        notifications_backend="osascript",
        logger_name=session_id,
        logger_level="DEBUG",
        command_complete_timeout=30,
        success_title="#win ({duration_seconds:d})",
        success_message="{command_line}",
        failure_title="#fail ({duration_seconds:d})",
        failure_message="{command_line}"
    )


class Stack:
    def __init__(self, data: List[Config]):
        self._data: List[Config] = data

        self.on_push = _EventHandlers()
        self.on_pop = _EventHandlers()
        self.on_change = _EventHandlers()

    @property
    def current(self) -> Config:
        return self._data[len(self._data) - 1]

    @classmethod
    def from_dict(cls, data: List[dict]) -> 'Stack':
        lst = []
        for d in data:
            lst.append(Config.from_dict(d))

        return Stack(lst)

    def to_dict(self) -> List[dict]:
        return [c.to_dict() for c in self._data]

    def push(self):
        cp = copy(self.current)
        self._data.append(cp)
        self.on_push.dispatch()

    def pop(self) -> Config:
        if len(self._data) == 1:
            raise IndexError("can't pop the last item")

        popped = self._data.pop()

        self.on_pop.dispatch()
        return popped

    @property
    def success_title(self) -> str:
        return self.current.success_title

    @success_title.setter
    def success_title(self, v: str):
        self.current.success_title = v
        self.on_change.dispatch()

    @property
    def success_message(self) -> str:
        return self.current.success_message

    @success_message.setter
    def success_message(self, v: str):
        self.current.success_message = v
        self.on_change.dispatch()

    @property
    def success_icon(self) -> Optional[str]:
        return self.current.success_icon

    @success_icon.setter
    def success_icon(self, v: Optional[str]):
        self.current.success_icon = v
        self.on_change.dispatch()

    @property
    def success_sound(self) -> Optional[str]:
        return self.current.success_sound

    @success_sound.setter
    def success_sound(self, v: Optional[str]):
        self.current.success_sound = v
        self.on_change.dispatch()

    @property
    def failure_title(self) -> str:
        return self.current.failure_title

    @failure_title.setter
    def failure_title(self, v: str):
        self.current.failure_title = v
        self.on_change.dispatch()

    @property
    def failure_message(self) -> str:
        return self.current.failure_message

    @failure_message.setter
    def failure_message(self, v: str):
        self.current.failure_message = v
        self.on_change.dispatch()

    @property
    def failure_icon(self) -> Optional[str]:
        return self.current.failure_icon

    @failure_icon.setter
    def failure_icon(self, v: Optional[str]):
        self.current.failure_icon = v
        self.on_change.dispatch()

    @property
    def failure_sound(self) -> Optional[str]:
        return self.current.failure_sound

    @failure_sound.setter
    def failure_sound(self, v: Optional[str]):
        self.current.failure_sound = v
        self.on_change.dispatch()

    @property
    def command_complete_timeout(self) -> int:
        return self.current.command_complete_timeout

    @command_complete_timeout.setter
    def command_complete_timeout(self, v: int):
        self.current.command_complete_timeout = v
        self.on_change.dispatch()

    @property
    def logger_name(self) -> str:
        return self.current.logger_name

    @logger_name.setter
    def logger_name(self, v: str):
        self.current.logger_name = v
        self.on_change.dispatch()

    @property
    def logger_level(self) -> str:
        return self.current.logger_name

    @logger_level.setter
    def logger_level(self, v: str):
        self.current.logger_level = v
        self.on_change.dispatch()

    @property
    def notifications_backend(self) -> str:
        return self.current.notifications_backend

    @notifications_backend.setter
    def notifications_backend(self, v: str):
        self.current.notifications_backend = v
        self.on_change.dispatch()
