import dataclasses
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Union

from notify.commands import CompleteCommand
from notify.config import Stack


@dataclass(frozen=True)
class Notification:
    title: str
    message: str
    icon: Optional[str] = None
    sound: Optional[str] = None

    def with_title(self, v: str) -> 'Notification':
        return dataclasses.replace(self, title=v)

    def with_message(self, v: str) -> 'Notification':
        return dataclasses.replace(self, message=v)

    def with_icon(self, v: Union[str, None]) -> 'Notification':
        return dataclasses.replace(self, icon=v)

    def with_sound(self, v: Union[str, None]) -> 'Notification':
        return dataclasses.replace(self, sound=v)


class Factory:
    def __init__(self, stack: Stack):
        self.__stack = stack

    def __get_template(self, success: bool):
        if success:
            return Notification(
                title=self.__stack.current.success_title,
                message=self.__stack.current.success_message,
                icon=self.__stack.current.success_icon,
                sound=self.__stack.current.success_sound,
            )
        else:
            return Notification(
                title=self.__stack.current.failure_title,
                message=self.__stack.current.failure_message,
                icon=self.__stack.current.failure_icon,
                sound=self.__stack.current.failure_sound,
            )

    def create(self, message: str, title: str, success: bool = True) -> Notification:
        template = self.__get_template(success)

        n = Notification(
            title=title,
            message=message,
            icon=template.icon,
            sound=template.sound,
        )

        return n

    def from_command(self, cmd: CompleteCommand) -> Notification:
        template = self.__get_template(cmd.successful)

        icon = template.icon
        sound = template.sound

        try:
            title = apply_template(template.title, cmd)
        except KeyError:
            title = template.title

        try:
            message = apply_template(template.message, cmd)
        except KeyError:
            message = template.message

        return Notification(title=title, message=message, icon=icon, sound=sound)


def apply_template(tpl: str, cmd: CompleteCommand) -> str:
    vars = {
        'duration': "{}".format(timedelta(seconds=round(cmd.duration.total_seconds()))),
        'command_line': cmd.command.command_line,
        'exit_code': cmd.exit_code
    }

    return tpl.format(**vars)
