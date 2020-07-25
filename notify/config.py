import json
import logging
import typing
from copy import copy
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class SelectedStrategy:
    name: str
    args: List[str] = field(default_factory=list)

    def with_args(self, *args) -> 'SelectedStrategy':
        return replace(self, name=self.name, args=list(args))

    def to_dict(self) -> Dict[str, Any]:
        return {'name': self.name, 'args': self.args}

    @classmethod
    def from_dict(cls, v: Dict[str, Any]) -> 'SelectedStrategy':
        return cls(**v)


@dataclass(frozen=True)
class SelectedBackend:
    name: str
    args: List[str] = field(default_factory=list)

    def with_name(self, name: str, *args):
        return replace(self, name=name, args=list(args))

    def to_dict(self) -> Dict[str, Any]:
        return {'name': self.name, 'args': self.args}

    @classmethod
    def from_dict(cls, v: Dict[str, Any]) -> 'SelectedBackend':
        return cls(**v)


class EventHandlers:
    def __init__(self):
        self.__handlers = []

    def __iadd__(self, other):
        self.__handlers.append(other)
        return self

    def __isub__(self, other):
        self.__handlers.remove(other)
        return self

    def dispatch(self):
        for h in self.__handlers:
            h()


@dataclass(frozen=True)
class Config:
    notifications_backend: SelectedBackend
    notifications_strategy: SelectedStrategy
    logger_name: str
    logger_level: str
    success_title: str
    success_message: str
    failure_title: str
    failure_message: str
    success_icon: Optional[str] = None
    success_sound: Optional[str] = None
    failure_icon: Optional[str] = None
    failure_sound: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'logger-name': self.logger_name,
            'logger-level': self.logger_level,
            'notifications-strategy': self.notifications_strategy.to_dict(),
            'notifications-backend': self.notifications_backend.to_dict(),
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
            notifications_backend=SelectedBackend.from_dict(data['notifications-backend']),
            notifications_strategy=SelectedStrategy.from_dict(data['notifications-strategy']),
            logger_name=data['logger-name'],
            logger_level=data['logger-level'],
        )

    def update(self, other: dict):
        self.__dict__.update(other)


def create_default(logger_name: str) -> Config:
    return Config(
        notifications_backend=SelectedBackend(name="osascript"),
        notifications_strategy=SelectedStrategy(name='when-inactive', args=["10"]),
        logger_name=logger_name,
        logger_level="DEBUG",
        success_title="#win ({duration})",
        success_message="{command_line}",
        failure_title="#fail ({duration})",
        failure_message="{command_line}"
    )


class Stack:
    def __init__(self, data: List[Config]):
        self.__data: List[Config] = data
        self.on_push = EventHandlers()
        self.on_pop = EventHandlers()
        self.on_change = EventHandlers()

    @property
    def current(self) -> Config:
        return self.__data[len(self.__data) - 1]

    @current.setter
    def current(self, v: Config):
        self.__data[len(self.__data) - 1] = v
        self.on_change.dispatch()

    @classmethod
    def from_dict(cls, data: List[dict]) -> 'Stack':
        lst = []
        for d in data:
            lst.append(Config.from_dict(d))

        return Stack(lst)

    def to_dict(self) -> List[dict]:
        return [c.to_dict() for c in self.__data]

    def push(self):
        cp = copy(self.current)
        self.__data.append(cp)
        self.on_push.dispatch()

    def pop(self) -> Config:
        if len(self.__data) == 1:
            raise IndexError("can't pop the last item")

        popped = self.__data.pop()

        self.on_pop.dispatch()
        return popped

    @property
    def success_title(self) -> str:
        return self.current.success_title

    @success_title.setter
    def success_title(self, v: str):
        self.current = replace(self.current, success_title=v)

    @property
    def success_message(self) -> str:
        return self.current.success_message

    @success_message.setter
    def success_message(self, v: str):
        self.current = replace(self.current, success_message=v)

    @property
    def success_icon(self) -> Optional[str]:
        return self.current.success_icon

    @success_icon.setter
    def success_icon(self, v: Optional[str]):
        self.current = replace(self.current, success_icon=v)

    @property
    def success_sound(self) -> Optional[str]:
        return self.current.success_sound

    @success_sound.setter
    def success_sound(self, v: Optional[str]):
        self.current = replace(self.current, success_sound=v)

    @property
    def failure_title(self) -> str:
        return self.current.failure_title

    @failure_title.setter
    def failure_title(self, v: str):
        self.current = replace(self.current, failure_title=v)

    @property
    def failure_message(self) -> str:
        return self.current.failure_message

    @failure_message.setter
    def failure_message(self, v: str):
        self.current = replace(self.current, failure_message=v)

    @property
    def failure_icon(self) -> Optional[str]:
        return self.current.failure_icon

    @failure_icon.setter
    def failure_icon(self, v: Optional[str]):
        self.current = replace(self.current, failure_icon=v)

    @property
    def failure_sound(self) -> Optional[str]:
        return self.current.failure_sound

    @failure_sound.setter
    def failure_sound(self, v: Optional[str]):
        self.current = replace(self.current, failure_sound=v)

    @property
    def notifications_strategy(self) -> SelectedStrategy:
        return self.current.notifications_strategy

    @notifications_strategy.setter
    def notifications_strategy(self, v: SelectedStrategy):
        self.current = replace(self.current, notifications_strategy=v)

    @property
    def logger_name(self) -> str:
        return self.current.logger_name

    @logger_name.setter
    def logger_name(self, v: str):
        self.current = replace(self.current, logger_name=v)

    @property
    def logger_level(self) -> str:
        return self.current.logger_name

    @logger_level.setter
    def logger_level(self, v: str):
        self.current = replace(self.current, logger_level=v)

    @property
    def notifications_backend(self) -> SelectedBackend:
        return self.current.notifications_backend

    @notifications_backend.setter
    def notifications_backend(self, v: SelectedBackend):
        self.current = replace(self.current, notifications_backend=v)


class Storage(typing.Protocol):
    def load(self) -> Dict: ...

    def save(self, data: Dict): ...


class FileStorage:
    def __init__(self, path: Path, logger: logging.Logger):
        self.__logger = logger
        self.__path = path

    def load(self) -> Dict:
        try:
            with open(str(self.__path)) as f:
                data = f.read().strip()
                if data == "":
                    return {}
                return json.loads(data)
        except FileNotFoundError:
            return {}

    def save(self, data: dict):
        with open(str(self.__path), 'w') as f:
            txt = json.dumps(data)
            f.write(txt)


class SessionManager:
    def __init__(self, storage: Storage, logger: logging.Logger):
        self.__logger = logger
        self.__storage = storage
        self.__data = {}

    def load_and_prune(self, existing_session_ids: List[str]):
        data = self.__storage.load()
        valid_data = {}
        discarded = []

        for sid in existing_session_ids:
            if sid in data:
                valid_data[sid] = data[sid]
            else:
                discarded.append(sid)

        self.__data = valid_data
        self.__storage.save(self.__data)

    def initialize_session_stack(self, session_id: str, default_stack: Stack) -> Optional[Stack]:
        if session_id not in self.__data:
            self.__register(session_id, default_stack)

        return Stack.from_dict(self.__data[session_id])

    def delete(self, session_id: str):
        if session_id not in self.__data:
            return

        del self.__data[session_id]
        self.__storage.save(self.__data)

    def __register(self, session_id: str, stack: Stack):
        self.__data[session_id] = stack.to_dict()
        self.__storage.save(self.__data)

        def f():
            self.__data[session_id] = stack.to_dict()
            self.__storage.save(self.__data)

        stack.on_pop += f
        stack.on_push += f
        stack.on_change += f
