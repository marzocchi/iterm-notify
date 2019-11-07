from datetime import datetime, timedelta
import typing
from notifications import Notification


class Dispatcher:
    def __init__(self):
        self._handlers: dict[str: typing.Callable[[list], None]] = {}

    def register_handler(self, selector: str, handler: typing.Callable[[list], None]):
        self._handlers[selector] = handler

    def dispatch(self, selector: str, args: list):
        if selector not in self._handlers:
            raise RuntimeError("can't dispatch with unknown selector: {}".format(selector))

        self._handlers[selector](args)


class Command(object):
    def __init__(self, timestamp: datetime, command_line: str):
        self._timestamp: datetime = timestamp
        self._command_line: str = command_line

        self._duration: typing.Union[timedelta, None] = None
        self._exit_code: typing.Union[int, None] = None

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

    def __str__(self) -> str:
        return "'{command_line}' started at {timestamp}".format(command_line=self._command_line,
                                                                timestamp=self._timestamp)


class _NotificationBackend(typing.Protocol):
    def notify(self, n: Notification):
        pass


class _NotificationStrategy(typing.Protocol):
    def should_notify(self, cmd: Command) -> bool:
        pass


class _NotificationFactory(typing.Protocol):
    def create(self, code: int, message: str, title: str) -> Notification:
        pass

    def from_command(self, cmd: Command) -> Notification:
        pass


class Notify(object):
    def __init__(self, notification_factory: _NotificationFactory, notification_backend: _NotificationBackend):
        self._notification_factory = notification_factory
        self._notification_backend = notification_backend

    def notify_handler(self, args: list):
        if len(args) < 2:
            raise RuntimeError("not enough arguments, needs at least [code, message, title]")

        n = self._notification_factory.create(code=int(args[0]), message=args[1], title=args[2])
        self._notification_backend.notify(n)


class NotifyCommandComplete(object):
    def __init__(self, notification_strategy: _NotificationStrategy,
                 notification_factory: _NotificationFactory,
                 notification_backend: _NotificationBackend):

        self._notification_strategy = notification_strategy
        self._notification_factory = notification_factory
        self._notification_backend = notification_backend
        self._cmd: typing.Union[Command, None] = None

    def before_handler(self, args: list):
        command_line = ",".join(args)

        if self._cmd is not None:
            raise RuntimeError("before_handler called more than once without calling after_command in between")

        self._cmd = Command(datetime.now(), command_line)

    def after_handler(self, args: list):
        exit_code = int(args[0])

        if not self._cmd:
            raise RuntimeError("after_command without a command")

        self._cmd.done(exit_code, datetime.now())

        if self._notification_strategy.should_notify(self._cmd):
            self._notification_backend.notify(self._notification_factory.from_command(self._cmd))

        self._cmd = None


class _WithTimeout(typing.Protocol):
    @property
    def timeout(self) -> int:
        pass

    @timeout.setter
    def timeout(self, v: int):
        pass


class _NotificationsBackendSelector(typing.Protocol):
    @property
    def selected(self) -> str:
        pass

    @selected.setter
    def selected(self, v: str):
        pass


class ConfigHandler(object):
    def __init__(self, timeout: _WithTimeout, success_template: Notification, failure_template: Notification,
                 notifications_backend_selector: _NotificationsBackendSelector,
                 on_change: typing.Union[None, typing.Callable[[dict], None]] = None,
                 defaults: dict = {}):

        self._notifications_backend = notifications_backend_selector
        self._success_template = success_template
        self._failure_template = failure_template

        self._timeout = timeout
        self._on_change = on_change

        self._apply(defaults)

    def _apply(self, cfg: dict):
        if 'success-title' in cfg:
            self._success_template.title = cfg['success-title']

        if 'success-icon' in cfg:
            self._success_template.icon = cfg['success-icon']

        if 'success-sound' in cfg:
            self._success_template.sound = cfg['success-sound']

        if 'failure-title' in cfg:
            self._failure_template.title = cfg['failure-title']

        if 'failure-icon' in cfg:
            self._failure_template.icon = cfg['failure-icon']

        if 'failure-sound' in cfg:
            self._failure_template.sound = cfg['failure-sound']

        if 'command-complete-timeout' in cfg:
            self._timeout.timeout = cfg['command-complete-timeout']

        if 'notifications-backend' in cfg:
            self._notifications_backend.selected = cfg['notifications-backend']

    def _dump(self) -> dict:
        return {
            'command-complete-timeout': self._timeout.timeout,

            'success-title': self._success_template.title,
            'success-icon': self._success_template.icon,
            'success-sound': self._success_template.sound,

            'failure-title': self._failure_template.title,
            'failure-icon': self._failure_template.icon,
            'failure-sound': self._failure_template.sound,

            'notifications-backend': self._notifications_backend.selected,
        }

    def set_notifications_backend_handler(self, args: list):
        self._notifications_backend.selected = args[0]

        if self._on_change is not None:
            self._on_change(self._dump())

    def set_success_title_handler(self, args: list):
        self._success_template.title = args[0]

        if self._on_change is not None:
            self._on_change(self._dump())

    def set_failure_title_handler(self, args: list):
        self._failure_template.title = args[0]

        if self._on_change is not None:
            self._on_change(self._dump())

    def set_failure_icon_handler(self, args: list):
        self._failure_template.icon = args[0] if args[0] != "" else None

        if self._on_change is not None:
            self._on_change(self._dump())

    def set_success_icon_handler(self, args: list):
        self._success_template.icon = args[0] if args[0] != "" else None

        if self._on_change is not None:
            self._on_change(self._dump())

    def set_success_sound_handler(self, args: list):
        self._success_template.sound = args[0] if args[0] != "" else None

        if self._on_change is not None:
            self._on_change(self._dump())

    def set_failure_sound_handler(self, args: list):
        self._failure_template.sound = args[0] if args[0] != "" else None

        if self._on_change is not None:
            self._on_change(self._dump())

    def set_timeout_handler(self, args: list):
        self._timeout.timeout = int(args[0])

        if self._on_change is not None:
            self._on_change(self._dump())
