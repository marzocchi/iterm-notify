import asyncio
import logging
from base64 import b64decode
from pathlib import Path
from sys import stderr
from typing import Dict, List, Optional

import iterm2

from notify import config, handlers, dispatcher, notifications, strategies, backends
from notify.backends import BackendFactory, Executor
from notify.config import Stack

formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')
console_handler = logging.StreamHandler(stderr)
main_logger = logging.getLogger(__name__)

console_handler.setFormatter(formatter)

main_logger.addHandler(console_handler)
main_logger.setLevel(logging.DEBUG)


def build_dispatcher(stack: config.Stack,
                     strategy_factory: strategies.StrategyFactory,
                     backend_factory: BackendFactory,
                     logger: logging.Logger) -> dispatcher.Dispatcher:
    success_template = notifications.Notification(
        title=stack.success_title,
        message=stack.success_message
    )

    failure_template = notifications.Notification(
        title=stack.failure_title,
        message=stack.failure_message
    )

    factory = notifications.Factory(
        stack=stack,
    )

    command_complete_handler = handlers.NotifyCommandComplete(
        stack=stack,
        strategy_factory=strategy_factory,
        notification_factory=factory,
        backend_factory=backend_factory
    )

    notify_handler = handlers.Notify(stack=stack, backend_factory=backend_factory,
                                     notification_factory=factory)

    cfg_handler = handlers.MaintainConfig(
        stack=stack,
        logger=logger,
        success_template=success_template,
        failure_template=failure_template,
    )

    dsp = dispatcher.Dispatcher(logger)

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
    def __init__(self, identity: str, app: iterm2.App, conn: iterm2.Connection,
                 config_manager: config.SessionManager):
        self.__identity = identity
        self.__app = app
        self.__conn = conn
        self.__dispatchers: Dict[str, dispatcher.Dispatcher] = {}
        self.__session_manager = config_manager

    def __get_session_by_id(self, session_id: str, logger: logging.Logger) -> Optional[iterm2.Session]:
        try:
            return self.__app.get_session_by_id(session_id)
        except:
            logger.exception("can't retrieve session object for {}".format(session_id))
            return None

    async def attach_escapes_monitor(self, session_id: str):
        logger = self.__create_logger(session_id)

        async with iterm2.CustomControlSequenceMonitor(
                connection=self.__conn,
                identity=self.__identity,
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

                args_decoded = [b64decode(s).decode('utf-8') for s in args]

                args = args_decoded

                session = self.__get_session_by_id(session_id, logger)
                if not session:
                    return

                try:
                    dsp = self.__get_or_create_dispatcher(session, logger)
                except:
                    logger.exception("could not create dispatcher")
                    continue

                dsp.dispatch(selector, args)

    def __get_or_create_dispatcher(self, session: iterm2.Session, logger: logging.Logger) -> dispatcher.Dispatcher:
        if session.session_id in self.__dispatchers:
            return self.__dispatchers[session.session_id]

        default_config = config.create_default(session.session_id)

        config_stack = self.__session_manager.initialize_session_stack(session_id=session.session_id,
                                                                       default_stack=Stack([default_config]))

        strategy_factories = {
            'when-inactive': strategies.WhenInactive.create_factory(strategies.iTermAppAdapter(self.__app),
                                                                    session_id=session.session_id),
            'when-slow': strategies.WhenSlow.create_factory()
        }

        backend_factories = {
            'iterm': backends.iTerm.create_factory(logger=logger, conn=self.__conn),
            'osascript': backends.OsaScript.create_factory(logger=logger, executor=Executor(logger)),
            'terminal-notifier': backends.TerminalNotifier.create_factory(logger=logger, executor=Executor(logger))
        }

        dsp = build_dispatcher(stack=config_stack,
                               strategy_factory=strategies.StrategyFactory(strategy_factories),
                               backend_factory=BackendFactory(backend_factories),
                               logger=logger)

        self.__dispatchers[session.session_id] = dsp

        return dsp

    @staticmethod
    def __create_logger(session_id: str):
        logger = logging.getLogger(session_id)
        logger.addHandler(console_handler)
        logger.propagate = False
        logger.setLevel(logging.WARNING)
        return logger


class Monitor:
    def __init__(self, identity: str):
        self.__identity = identity

    async def attach_sessions_monitor(self, connection):
        fs = config.FileStorage(
            Path.home().joinpath('.iterm-notify-temp.json'),
            logger=main_logger
        )

        config_manager = config.SessionManager(fs, logger=main_logger)

        app = await iterm2.async_get_app(connection)

        config_manager.load_and_prune(list_existing_session_ids(app=app))

        # FIXME the following task does nothing of value, except it seems to mitigate a race condition that causes one
        # or two commands from the user's shell init file to be missed when creating new windows (but not tabs or
        # splits).
        async def fallback():
            async with iterm2.CustomControlSequenceMonitor(
                    connection,
                    identity=self.__identity,
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
            SessionsMonitor(self.__identity, app, connection, config_manager=config_manager).attach_escapes_monitor
        )


def list_existing_session_ids(app: iterm2.App):
    existing_sessions: List[str] = []

    for window in app.windows:
        for tab in window.tabs:
            for session in tab.sessions:
                existing_sessions.append(session.session_id)

    return existing_sessions
