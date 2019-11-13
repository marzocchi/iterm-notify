from typing import Optional
from datetime import datetime, timedelta


class Command:
    def __init__(self, timestamp: datetime, command_line: str):
        self._timestamp: datetime = timestamp
        self._command_line: str = command_line

        self._duration: Optional[timedelta] = None
        self._exit_code: Optional[int] = None

    @property
    def command_line(self) -> str:
        return self._command_line

    @property
    def exit_code(self) -> int:
        return self._exit_code

    @property
    def duration(self) -> timedelta:
        return self._duration

    def done(self, exit_code: int, ref: datetime):
        self._exit_code = exit_code
        self._duration = ref - self._timestamp


class Notification:
    def __init__(self, title: str, message: str, icon: Optional[str] = None,
                 sound: Optional[str] = None):
        self._title = title
        self._message = message
        self._icon = icon
        self._sound = sound

    @property
    def icon(self) -> Optional[str]:
        return self._icon

    @icon.setter
    def icon(self, v: Optional[str]):
        self._icon = v

    @property
    def sound(self) -> Optional[str]:
        return self._sound

    @sound.setter
    def sound(self, v: Optional[str]):
        self._sound = v

    @property
    def message(self) -> str:
        return self._message

    @message.setter
    def message(self, v: str):
        self._message = v

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, v: str):
        self._title = v


class Factory:
    def __init__(self, success: Notification, failure: Notification):

        self._failure = failure
        self._success = success

    def _vars(self, cmd: Command) -> dict:
        return {
            'duration_seconds': cmd.duration.seconds,
            'command_line': cmd.command_line,
            'exit_code': cmd.exit_code
        }

    def create(self, message: str, title: str, success: bool = True) -> Notification:
        template = self._success if success else self._failure

        n = Notification(
            message=message,
            icon=template.icon,
            sound=template.sound,
            title=title
        )

        return n

    def from_command(self, cmd: Command) -> Notification:
        if cmd.exit_code == 0:
            template = self._success
        else:
            template = self._failure

        tpl_vars = self._vars(cmd)

        icon = template.icon
        sound = template.sound

        try:
            title = template.title.format(**tpl_vars)
        except KeyError:
            title = template.title

        try:
            message = template.message.format(**tpl_vars)
        except KeyError:
            message = template.message

        return Notification(title=title, message=message, icon=icon, sound=sound)


