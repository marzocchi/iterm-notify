import logging
from datetime import datetime
from typing import List

from notify.backends import BackendFactory
from notify.commands import Command
from notify.config import Config, Stack
from notify.notifications import Factory, Notification
from notify.strategies import StrategyFactory


class MaintainConfig:
    def __init__(self, stack: Stack,
                 success_template: Notification,
                 failure_template: Notification,
                 logger: logging.Logger):
        self.__success_template = success_template
        self.__failure_template = failure_template
        self.__logger = logger

        self.__configuration_stack = stack
        self.__configuration_stack.on_pop += self.__apply_on_pop
        self.__apply_config(self.__configuration_stack.current)

    def __apply_config(self, cfg: Config):
        self.notifications_backend_handler(cfg.notifications_backend.name, *cfg.notifications_backend.args)

        self.success_title_handler(cfg.success_title)
        self.success_message_handler(cfg.success_message)
        self.success_icon_handler(cfg.success_icon or "")
        self.success_sound_handler(cfg.success_sound or "")

        self.failure_title_handler(cfg.failure_title)
        self.failure_message_handler(cfg.failure_message)
        self.failure_icon_handler(cfg.failure_icon or "")
        self.failure_sound_handler(cfg.failure_sound or "")

        self.command_complete_timeout_handler(*cfg.notifications_strategy.args)

        self.logging_name_handler(cfg.logger_name)
        self.logging_level_handler(cfg.logger_level)

    def __apply_on_pop(self):
        self.__apply_config(self.__configuration_stack.current)

    def notifications_backend_handler(self, name: str, *args):
        selected_backend = self.__configuration_stack.notifications_backend.with_name(name, *args)
        self.__configuration_stack.notifications_backend = selected_backend

    def command_complete_timeout_handler(self, t: str):
        selected_strategy = self.__configuration_stack.notifications_strategy.with_args(int(t))
        self.__configuration_stack.notifications_strategy = selected_strategy

    def success_title_handler(self, title: str):
        self.__success_template = self.__success_template.with_title(title)
        self.__configuration_stack.success_title = self.__success_template.title

    def success_message_handler(self, message: str):
        self.__success_template = self.__success_template.with_message(message)
        self.__configuration_stack.success_message = self.__success_template.message

    def success_icon_handler(self, icon: str):
        self.__success_template = self.__success_template.with_icon(icon if icon != "" else None)
        self.__configuration_stack.success_icon = self.__success_template.icon

    def success_sound_handler(self, sound: str):
        self.__success_template = self.__success_template.with_sound(sound if sound != "" else None)
        self.__configuration_stack.success_sound = self.__success_template.sound

    def failure_title_handler(self, title: str):
        self.__failure_template = self.__failure_template.with_title(title)
        self.__configuration_stack.failure_title = self.__failure_template.title

    def failure_message_handler(self, message: str):
        self.__failure_template = self.__failure_template.with_message(message)
        self.__configuration_stack.failure_message = self.__failure_template.message

    def failure_icon_handler(self, icon: str):
        self.__failure_template = self.__failure_template.with_icon(icon if icon != "" else None)
        self.__configuration_stack.failure_icon = self.__failure_template.icon

    def failure_sound_handler(self, sound: str):
        self.__failure_template = self.__failure_template.with_sound(sound if sound != "" else None)
        self.__configuration_stack.failure_sound = self.__failure_template.sound

    def logging_name_handler(self, new_name: str):
        self.__logger.name = new_name
        self.__configuration_stack.logger_name = self.__logger.name

    def logging_level_handler(self, new_level: str):
        self.__logger.setLevel(new_level)
        self.__configuration_stack.logger_level = logging.getLevelName(self.__logger.level)


class Notify:
    def __init__(self, stack: Stack,
                 notification_factory: Factory,
                 backend_factory: BackendFactory):

        self.__stack = stack
        self.__notification_factory = notification_factory
        self.__backend_factory = backend_factory

        self.__commands: list = []

    def notify(self, message: str, title: str):
        n = self.__notification_factory.create(message=message, title=title, success=True)
        self.__backend_factory.create(self.__stack.notifications_backend).notify(n)


class NotifyCommandComplete:
    def __init__(self, stack: Stack,
                 strategy_factory: StrategyFactory,
                 notification_factory: Factory,
                 backend_factory: BackendFactory):

        self.__stack = stack
        self.__strategy_factory = strategy_factory
        self.__notification_factory = notification_factory
        self.__backend_factory = backend_factory

        self.__commands: List[Command] = []

    def before_command(self, command_line: str):
        self.__stack.push()
        self.__commands.append(Command(datetime.now(), command_line))

    def after_command(self, exit_code: str):
        exit_code_number = int(exit_code)

        if len(self.__commands) == 0:
            raise RuntimeError("after_command without a command")

        cmd = self.__commands.pop()
        complete_cmd = cmd.complete(exit_code_number, datetime.now())

        if self.__strategy_factory.create(self.__stack.current.notifications_strategy).should_notify(complete_cmd):
            n = self.__notification_factory.from_command(complete_cmd)
            self.__backend_factory.create(self.__stack.current.notifications_backend).notify(n)

        self.__stack.pop()
