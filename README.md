iTerm-notify
---

Desktop notifications for local and remote long-running commands in iTerm2 and Zsh.

Requirements
---
- iTerm2 with the Python API enabled with version > 3.8 of the Python Runtime (at the time of writing, this is only
  available with the beta)
- Zsh
- [terminal-notifier.app][terminal-notifier] and `/Applications/terminal-notifier.app/Contents/MacOS/` in your `$PATH`

Install
---
1. Clone this repository
1. Create your "identity" by entering a random string as the first line in `$HOME/.iterm-notify-identity`
    - The identity is a security feature of [iTerm2's Custom Control Sequences][explain-id] support, so don't be too lazy
1. Symlink `notify.py` to `~/Library/ApplicationSupport/iTerm2/Scripts/AutoLaunch/notify.py`
1. Source `init.sh` in your `.zshrc`
1. Start `notify.py` from iTerm2's Scripts menu (Scripts > AutoLaunch > notify.py)

Configuration
---

The behavior of iterm-notify can be modified by using `iterm-notify-set-config`, for example by calling it in `.zshrc` 
right **after** sourcing `init.sh`.

- Set a custom title for error and success notifications:

        iterm-notify-set-config failure-title "Command failed"
        iterm-notify-set-config success-title "Command finished successfully!"

    The value can also be a Python format string using any of these placeholders:
    
    - `exit_code`: the command's exit code
    - `command_line`: the command's full command line (eg.: everything typed at the prompt by the user)
    - `duration_second`: the command's duration, in seconds
        
- Replace the boring default notification icons for failure or success. Use paths to image files or URLs.
        
        iterm-notify-set-config failure-icon "/path/to/error-icon.png"
        iterm-notify-set-config success-icon "/path/to/success-icon.png"
        
    Try [this][dogefy.sh]. Wow.
    
- Set a different timeout for notifications:

        iterm-notify-set-config command-complete-timeout 15


[explain-id]: https://www.iterm2.com/python-api/customcontrol.html
[terminal-notifier]: https://github.com/julienXX/terminal-notifier
[dogefy.sh]: https://gist.github.com/marzocchi/1bf65095962494a0ff17c417d6b1bb4b
