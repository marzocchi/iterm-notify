#!/usr/bin/env python3.8

import iterm2
import notify
from notify import identity

iterm2.run_forever(notify.Monitor(identity.load_from_default_path()).attach_sessions_monitor)
