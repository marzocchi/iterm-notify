#!/usr/bin/env python3.8

import iterm2
from notifications import identity
from notifications.monitor import Monitor

iterm2.run_forever(Monitor(identity.load_from_default_path()).attach_sessions_monitor)
