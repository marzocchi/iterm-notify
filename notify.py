#!/usr/bin/env python3.8

import iterm2
import traceback
import typing
from pathlib import Path
from notifications.identity import load
from notifications import backends, handlers, strategies, preferences, NotificationFactory, Notification

home = Path.home()
identity = load(home.joinpath('.iterm-notify-identity'))
prefs = preferences.Preferences(preferences.FileStorage(home.joinpath('.iterm-notify-temp.json')))


async def main(connection):
    app = await iterm2.async_get_app(connection)
    refresh_preferences(app, prefs)

    async def monitor(session_id):
        refresh_preferences(app, prefs)

        session = app.get_session_by_id(session_id)

        if not session:
            return

        dsp = build_dispatcher(app, session_id=session_id, defaults=prefs.get(session_id),
                               on_prefs_change=prefs.handler(session_id))

        async with iterm2.CustomControlSequenceMonitor(
                connection=connection,
                identity=identity,
                regex=r'^([^,]+),(.+)$',
                session_id=session_id
        ) as mon:
            while True:
                matches = await mon.async_get()

                try:
                    cmd_name = matches.group(1)
                    cmd_args = matches.group(2).split(",")

                    dsp.dispatch(cmd_name, cmd_args)
                except:
                    traceback.print_exc()
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


def build_dispatcher(app: iterm2.App, session_id: str, on_prefs_change: typing.Callable[[dict], None],
                     defaults: dict) -> handlers.Dispatcher:
    success_template = Notification(
        title="#win (in {duration:d}s)",
        message="{command_line}"
    )

    failure_template = Notification(
        title="#fail (in {duration:d}s)",
        message="{command_line}"
    )

    notification_factory = NotificationFactory(
        success=success_template,
        failure=failure_template
    )

    notification_strategy = strategies.IfInactive(
        app=strategies.iTermApp(app),
        session_id=session_id,
        timeout=30
    )

    notification_backend = backends.TerminalNotifier(runner=backends.RunCommand())

    command_complete = handlers.NotifyCommandComplete(
        notification_strategy=notification_strategy,
        notification_factory=notification_factory,
        notification_backend=notification_backend
    )

    config = handlers.ConfigHandler(timeout=notification_strategy, success_template=success_template,
                                    failure_template=failure_template, on_change=on_prefs_change,
                                    defaults=defaults)

    dsp = handlers.Dispatcher()

    dsp.register_handler("before-command", command_complete.before_handler)
    dsp.register_handler("after-command", command_complete.after_handler)

    dsp.register_handler("set-command-complete-timeout", config.set_timeout_handler)
    dsp.register_handler("set-success-title", config.set_success_title_handler)
    dsp.register_handler("set-failure-title", config.set_failure_title_handler)
    dsp.register_handler("set-success-icon", config.set_success_icon_handler)
    dsp.register_handler("set-failure-icon", config.set_failure_icon_handler)

    return dsp


def refresh_preferences(app: iterm2.App, prefs: preferences.Preferences):
    prefs.load()

    existing_sessions = list_current_session_ids(app)
    prefs.prune(existing_sessions)


# This instructs the script to run the "main" coroutine and to keep running
# even after it returns.
iterm2.run_forever(main)
