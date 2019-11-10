#!/usr/bin/env python3.8

import iterm2
import logging

from base64 import b64decode
from pathlib import Path
from notifications.identity import load
from notifications import dispatcher, preferences, strategies, backends

import sys

console = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)

main_logger = logging.getLogger(__name__)
main_logger.setLevel(logging.WARNING)

home = Path.home()
identity = load(home.joinpath('.iterm-notify-identity'))
prefs = preferences.Preferences(
    preferences.FileStorage(home.joinpath('.iterm-notify-temp.json')),
    logger=main_logger
)


async def main(connection):
    app = await iterm2.async_get_app(connection)
    refresh_preferences(app, prefs)

    async def monitor(session_id):
        logger = main_logger.getChild(session_id)
        logger.addHandler(console)
        logger.setLevel(logging.WARNING)

        refresh_preferences(app, prefs)

        session = app.get_session_by_id(session_id)

        if not session:
            return

        try:
            notification_strategy = strategies.WhenInactive(
                app=strategies.iTermApp(app),
                session_id=session_id,
                when_slow=strategies.WhenSlow(timeout=30)
            )

            notification_backend = backends.SwitchableNotifier(
                {
                    'iterm': backends.iTermNotifier(connection),
                    'osascript': backends.OsaScriptNotifier(backends.ExecSubprocess()),
                    'terminal-notifier': backends.TerminalNotifier(backends.ExecSubprocess())
                },
                'osascript'
            )

            dsp = dispatcher.build(notification_strategy=notification_strategy, notification_backend=notification_backend,
                                   defaults=prefs.get(session_id),
                                   on_prefs_change=prefs.handler(session_id), logger=logger)
        except:
            logger.exception('could not initialize dispatcher')
            return

        async with iterm2.CustomControlSequenceMonitor(
                connection=connection,
                identity=identity,
                regex=r'^([^,]+),(.+)$',
                session_id=session_id
        ) as mon:
            while True:
                try:
                    matches = await mon.async_get()
                except:
                    logging.exception("can't receive control sequence")
                    continue

                cmd_name = matches.group(1)
                cmd_args = matches.group(2).split(",")

                cmd_args = list(map(lambda s: b64decode(s).decode('utf-8'), cmd_args))

                try:
                    dsp.dispatch(cmd_name, cmd_args)
                except Exception as e:
                    logger.error(e)
                    continue

    # Create a task running `monitor` for each session, including those created
    # in the future.
    await iterm2.EachSessionOnceMonitor.async_foreach_session_create_task(
        app, monitor)


def list_current_session_ids(app: iterm2.App):
    existing_sessions: list[str] = []

    for window in app.windows:
        for tab in window.tabs:
            for session in tab.sessions:
                existing_sessions.append(session.session_id)

    return existing_sessions


def refresh_preferences(app: iterm2.App, prefs: preferences.Preferences):
    prefs.load()

    existing_sessions = list_current_session_ids(app)
    prefs.prune(existing_sessions)


# This instructs the script to run the "main" coroutine and to keep running
# even after it returns.
iterm2.run_forever(main)
