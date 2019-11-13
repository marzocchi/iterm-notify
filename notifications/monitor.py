import asyncio
import iterm2
import logging
from typing import List, Optional
from sys import stderr
from base64 import b64decode
from pathlib import Path

from notifications import config, backends, dispatcher, strategies, handlers, Notification, Factory, \
    Dispatcher

formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')

console_handler = logging.StreamHandler(stderr)
console_handler.setFormatter(formatter)

main_logger = logging.getLogger(__name__)
main_logger.addHandler(console_handler)
main_logger.setLevel(logging.DEBUG)


def build_dispatcher(stack: config.Stack,
                     strategy: strategies.WhenInactive,
                     backend: backends.Selectable,
                     logger: Optional[logging.Logger] = None) -> Dispatcher:
    success_template = Notification(
        title=stack.success_title,
        message=stack.success_message
    )

    failure_template = Notification(
        title=stack.failure_title,
        message=stack.failure_message
    )

    factory = Factory(
        success=success_template,
        failure=failure_template
    )

    command_complete_handler = handlers.NotifyCommandComplete(
        stack=stack,
        strategy=strategy,
        factory=factory,
        backend=backend
    )

    notify_handler = handlers.Notify(backend=backend,
                                     factory=factory)

    cfg_handler = handlers.MaintainConfig(
        stack=stack,
        logger=logger,
        timeout=strategy,
        success_template=success_template,
        failure_template=failure_template,
        backend_selector=backend
    )

    dsp = Dispatcher(logger)

    dsp.register_handler("before-command", command_complete_handler.before_command)
    dsp.register_handler("after-command", command_complete_handler.after_command)
    dsp.register_handler("notify", notify_handler.notify)

    dsp.register_handler("set-command-complete-timeout", cfg_handler.command_complete_timeout_handler)

    dsp.register_handler("set-success-title", cfg_handler.success_title_handler)
    dsp.register_handler("set-success-icon", cfg_handler.success_icon_handler)
    dsp.register_handler("set-success-sound", cfg_handler.success_sound_handler)

    dsp.register_handler("set-failure-title", cfg_handler.failure_title_handler)
    dsp.register_handler("set-failure-icon", cfg_handler.failure_icon_handler)
    dsp.register_handler("set-failure-sound", cfg_handler.failure_sound_handler)

    dsp.register_handler("set-notifications-backend", cfg_handler.notifications_backend_handler)

    dsp.register_handler('set-logger-name', cfg_handler.logging_name_handler)
    dsp.register_handler('set-logger-level', cfg_handler.logging_level_handler)

    return dsp


class SessionsMonitor:
    def __init__(self, identity: str, app: iterm2.App, conn: iterm2.Connection, config_manager: config.Manager):
        self._identity = identity
        self._app = app
        self._conn = conn
        self._dispatchers = {}
        self._config_manager = config_manager

    def _get_session_by_id(self, session_id: str, logger: logging.Logger) -> Optional[iterm2.Session]:
        try:
            return self._app.get_session_by_id(session_id)
        except:
            logger.exception("can't retrieve session object for {}".format(session_id))
            return None

    async def attach_escapes_monitor(self, session_id: str):
        logger = self._create_logger(session_id)

        async with iterm2.CustomControlSequenceMonitor(
                connection=self._conn,
                identity=self._identity,
                regex=r'^([^,]+),(.+)$',
                session_id=session_id
        ) as mon:
            while True:
                try:
                    matches = await mon.async_get()
                except asyncio.CancelledError:
                    logger.error("got CancelledError while waiting for new Control Sequences for session_id {}".format(
                        session_id))
                    continue
                except:
                    logger.exception("can't receive new Control Sequences for session_id {}".format(session_id))
                    continue

                selector = matches.group(1)
                args = matches.group(2).split(",")
                args = list(map(lambda s: b64decode(s).decode('utf-8'), args))

                session = self._get_session_by_id(session_id, logger)
                if not session:
                    return

                try:
                    dsp = self._get_or_create_dispatcher(session, logger)
                except:
                    logger.exception("could not create dispatcher")
                    continue

                dsp.dispatch(selector, args)

    def _get_or_create_dispatcher(self, session: iterm2.Session, logger: logging.Logger) -> dispatcher.Dispatcher:
        if session.session_id in self._dispatchers:
            return self._dispatchers[session.session_id]

        stack = self._config_manager.get(session_id=session.session_id)
        if not stack:
            cfg = config.create_default(session.session_id)
            stack = config.Stack([cfg])
            self._config_manager.register(session.session_id, stack)

        strategy = strategies.WhenInactive(
            app=strategies.iTermApp(self._app),
            session_id=session.session_id,
            when_slow=strategies.WhenSlow(timeout=30)
        )

        backend = backends.Selectable(
            {
                'iterm': backends.Iterm(self._conn, logger=logger),
                'osascript': backends.OsaScript(backends.ExecSubprocess(), logger=logger),
                'terminal-notifier': backends.TerminalNotifier(backends.ExecSubprocess(), logger=logger)
            },
            stack.notifications_backend,
            logger=logger
        )

        dsp = build_dispatcher(stack=stack,
                               strategy=strategy,
                               backend=backend,
                               logger=logger)

        self._dispatchers[session.session_id] = dsp

        return dsp

    @staticmethod
    def _create_logger(session_id: str):
        logger = logging.getLogger(session_id)
        logger.addHandler(console_handler)
        logger.propagate = False
        logger.setLevel(logging.WARNING)
        return logger


class Monitor:
    def __init__(self, identity: str):
        self._identity = identity

    async def attach_sessions_monitor(self, connection):
        fs = config.manager.FileStorage(
            Path.home().joinpath('.iterm-notify-temp.json'),
            logger=main_logger
        )

        config_manager = config.Manager(fs, logger=main_logger)

        app = await iterm2.async_get_app(connection)

        config_manager.load(list_existing_session_ids(app=app))

        # FIXME the following task does nothing of value, except it seems to mitigate a race condition that causes one
        # or two commands from the user's shell init file to be missed when creating new windows (but not tabs or
        # splits).
        async def fallback():
            async with iterm2.CustomControlSequenceMonitor(
                    connection,
                    identity=self._identity,
                    regex=r'^([^,]+),(.+)$') as mon:
                while True:
                    await mon.async_get()

        async def on_session_termination():
            async with iterm2.SessionTerminationMonitor(connection=connection) as mon:
                while True:
                    try:
                        session_id = await mon.async_get()
                    except:
                        main_logger.exception("could not get a closed session")
                        continue

                    config_manager.delete(session_id)
                    main_logger.debug("session deleted: {}".format(session_id))

        asyncio.create_task(fallback())
        asyncio.create_task(on_session_termination())

        await iterm2.EachSessionOnceMonitor.async_foreach_session_create_task(
            app,
            SessionsMonitor(self._identity, app, connection, config_manager=config_manager).attach_escapes_monitor
        )


def list_existing_session_ids(app: iterm2.App):
    existing_sessions: List[str] = []

    for window in app.windows:
        for tab in window.tabs:
            for session in tab.sessions:
                existing_sessions.append(session.session_id)

    return existing_sessions
