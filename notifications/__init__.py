import typing
from datetime import timedelta


class _Command(typing.Protocol):
    @property
    def command_line(self) -> str:
        pass

    @property
    def exit_code(self) -> int:
        pass

    @property
    def duration(self) -> timedelta:
        pass


class Notification(object):
    def __init__(self, title: str, message: str, icon: typing.Union[str, None] = None):
        self._title = title
        self._message = message
        self._icon = icon

    @property
    def icon(self) -> typing.Union[str, None]:
        return self._icon

    @icon.setter
    def icon(self, v: typing.Union[str, None]):
        self._icon = v

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


class NotificationFactory(object):
    def __init__(self, success: Notification, failure: Notification):

        self._failure = failure
        self._success = success

    def _vars(self, cmd: _Command) -> dict:
        return {
            'duration_seconds': cmd.duration.seconds,
            'command_line': cmd.command_line,
            'exit_code': cmd.exit_code
        }

    def create(self, cmd: _Command) -> Notification:

        if cmd.exit_code == 0:
            template = self._success
        else:
            template = self._failure

        tpl_vars = self._vars(cmd)

        title = template.title.format(**tpl_vars)
        message = template.message.format(**tpl_vars)
        icon = template.icon

        return Notification(title=title, message=message, icon=icon)
