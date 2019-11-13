import logging
from typing import Protocol, Optional

from notifications import Notification
from notifications.config import Config, Stack


class _Timeout(Protocol):
    @property
    def timeout(self) -> int: pass

    @timeout.setter
    def timeout(self, v: int): pass


class _BackendSelector(Protocol):
    @property
    def selected(self) -> str: pass

    @selected.setter
    def selected(self, v: str): pass


class MaintainConfig:
    def __init__(self, stack: Stack,
                 timeout: _Timeout,
                 success_template: Notification,
                 failure_template: Notification,
                 backend_selector: _BackendSelector,
                 logger: logging.Logger):
        self._backend_selector = backend_selector
        self._success_template = success_template
        self._failure_template = failure_template
        self._timeout = timeout
        self._logger = logger

        self._stack = stack
        self._stack.on_pop += self._apply_on_pop
        self._apply_config(self._stack.current)

    def _apply_config(self, cfg: Config):
        self.notifications_backend_handler(cfg.notifications_backend)

        self.success_title_handler(cfg.success_title)
        self.success_message_handler(cfg.success_message)
        self.success_icon_handler(cfg.success_icon)
        self.success_sound_handler(cfg.success_sound)

        self.failure_title_handler(cfg.failure_title)
        self.failure_message_handler(cfg.failure_message)
        self.failure_icon_handler(cfg.failure_icon)
        self.failure_sound_handler(cfg.failure_sound)

        self.command_complete_timeout_handler(cfg.command_complete_timeout)

        self.logging_name_handler(cfg.logger_name)
        self.logging_level_handler(cfg.logger_level)

    def _apply_on_pop(self):
        self._apply_config(self._stack.current)

    def notifications_backend_handler(self, name: str):
        self._backend_selector.selected = name
        self._stack.notifications_backend = self._backend_selector.selected

    def success_title_handler(self, title: str):
        self._success_template.title = title
        self._stack.success_title = self._success_template.title

    def success_message_handler(self, message: str):
        self._success_template.message = message
        self._stack.success_message = self._success_template.message

    def success_icon_handler(self, icon: str):
        self._success_template.icon = icon if icon != "" else None
        self._stack.success_icon = self._success_template.icon

    def success_sound_handler(self, sound: str):
        self._success_template.sound = sound if sound != "" else None
        self._stack.success_sound = self._success_template.sound

    def failure_title_handler(self, title: str):
        self._failure_template.title = title
        self._stack.failure_title = self._failure_template.title

    def failure_message_handler(self, message: str):
        self._failure_template.message = message
        self._stack.failure_message = self._failure_template.message

    def failure_icon_handler(self, icon: str):
        self._failure_template.icon = icon if icon != "" else None
        self._stack.failure_icon = self._failure_template.icon

    def failure_sound_handler(self, sound: str):
        self._failure_template.sound = sound if sound != "" else None
        self._stack.failure_sound = self._failure_template.sound

    def command_complete_timeout_handler(self, t: str):
        self._timeout.timeout = int(t)
        self._stack.command_complete_timeout = self._timeout.timeout

    def logging_name_handler(self, new_name: str):
        self._logger.name = new_name
        self._stack.logger_name = self._logger.name

    def logging_level_handler(self, new_level: str):
        self._logger.setLevel(new_level)
        self._stack.logger_level = self._logger.level
