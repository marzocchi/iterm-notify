import logging
import typing

import notifications
from notifications import handlers, Notification


class Dispatcher:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._handlers: dict[str: typing.Callable[[list], None]] = {}

    def register_handler(self, selector: str, handler: typing.Callable[[list], None]):
        self._handlers[selector] = handler

    def dispatch(self, selector: str, args: list):
        if selector not in self._handlers:
            raise RuntimeError("can't dispatch to unknown selector: {}".format(selector))

        self._logger.info("dispatching {} with args: {}".format(selector, args))
        self._handlers[selector](args)


class _Strategy(typing.Protocol):
    @property
    def timeout(self) -> int: pass

    @timeout.setter
    def timeout(self, v: int): pass

    def should_notify(self, cmd: handlers.Command) -> bool: pass


class _Backend(typing.Protocol):
    @property
    def selected(self) -> str: pass

    @selected.setter
    def selected(self, v: str): pass

    def notify(self, n: Notification): pass


def build(notification_strategy: _Strategy, notification_backend: _Backend, logger: logging.Logger,
          on_prefs_change: typing.Callable[[dict], None] = None,
          defaults: dict = {}) -> Dispatcher:
    success_template = notifications.Notification(
        title="#win (in {duration_seconds:d}s)",
        message="{command_line}"
    )

    failure_template = notifications.Notification(
        title="#fail (in {duration_seconds:d}s)",
        message="{command_line}"
    )

    notification_factory = notifications.NotificationFactory(
        success=success_template,
        failure=failure_template
    )

    command_complete = handlers.NotifyCommandComplete(
        notification_strategy=notification_strategy,
        notification_factory=notification_factory,
        notification_backend=notification_backend
    )

    notify = handlers.Notify(notification_backend=notification_backend, notification_factory=notification_factory)

    config = handlers.ConfigHandler(logger=logger,
                                    timeout=notification_strategy,
                                    defaults=defaults,
                                    on_change=on_prefs_change,
                                    success_template=success_template,
                                    failure_template=failure_template,
                                    notifications_backend_selector=notification_backend)

    dsp = Dispatcher(logger)

    dsp.register_handler("before-command", command_complete.before_handler)
    dsp.register_handler("after-command", command_complete.after_handler)
    dsp.register_handler("notify", notify.notify_handler)

    dsp.register_handler("set-command-complete-timeout", config.set_timeout_handler)

    dsp.register_handler("set-success-title", config.set_success_title_handler)
    dsp.register_handler("set-success-icon", config.set_success_icon_handler)
    dsp.register_handler("set-success-sound", config.set_success_sound_handler)

    dsp.register_handler("set-failure-title", config.set_failure_title_handler)
    dsp.register_handler("set-failure-icon", config.set_failure_icon_handler)
    dsp.register_handler("set-failure-sound", config.set_failure_sound_handler)

    dsp.register_handler("set-notifications-backend", config.set_notifications_backend_handler)

    dsp.register_handler('set-logger-name', config.set_logging_name_handler)
    dsp.register_handler('set-logger-level', config.set_logging_level_handler)

    return dsp
