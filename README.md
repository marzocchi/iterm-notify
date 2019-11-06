iTerm-notify [![Build Status](https://travis-ci.org/marzocchi/iterm-notify.svg?branch=master)](https://travis-ci.org/marzocchi/iterm-notify)
---

Desktop notifications for local and remote long-running commands in iTerm2 and Zsh or Bash.

Requirements
---
- iTerm2 with the Python API enabled with version > 3.8 of the Python Runtime (at the time of writing, this is only
  available with the beta)
- Zsh, or Bash (with [bash-preexec][bash-preexec], bundled with iTerm2's shell integration)

Install
---
1. Clone this repository
1. Create your "identity file" by entering a random string as the first line in `$HOME/.iterm-notify-identity`
    - The _identity_ is a **security feature** of [iTerm2's Custom Control Sequences][explain-id] support, so don't be too lazy
1. Symlink `notify.py` to `~/Library/ApplicationSupport/iTerm2/Scripts/AutoLaunch/notify.py`
1. Source `init.sh` in your shell initialization file
1. Start `notify.py` from iTerm2's Scripts menu (Scripts > AutoLaunch > notify.py)
1. Copy the identity file and `init.sh` (and source it!) on any other machine you want to receive notifications from.

Supported shells
---

iTerm-notify should work with any shell that provides hooks to invoke functions before a command is executed and after
it is finished. Zsh provides `preexec`/`precmd` [hooks][zsh-hooks] and is supported out of the box.
 
In Bash, [bash-preexec][bash-preexec] (which is bundled with iTerm2's shell integration) is required and must be loaded
before `init.sh`.

Users of other shells can roll out their own integration:

- `iterm-notify before-command COMMAND_LINE` must be called before executing every command, passing whatever the user
   typed on the prompt as the first argument 

- `iterm-notify after-command EXIT_CODE` must be called after the command finished, passing it the exit code as the
   first argument

Configuration
---

The behavior of iterm-notify can be modified by using `iterm-notify config-set`, for example by calling it in `.zshrc` 
right **after** sourcing `init.sh`.

- Set the notification backend:

        iterm-notify config-set notifications-backend terminal-notifier 
    
    Supported backends:
    - `iterm`: notifies using a modal alert using iTerm2's own Alert mechanism; can only display notification
       title and text (no sound, etc)
    - `osascript` (default): shows notification in Notification Center using `display notification` from Apple Script's
       StandardAdditions.osax; can show title, message and play sounds, but no custom icons
    - `terminal-notifier`: requires manual installation of [terminal-notifier.app][terminal-notifier] and
      `(...)/terminal-notifier.app/Contents/MacOS` must be in `$PATH`; can show title, message, icons and play sounds
         
- Customize the notifications (check above for what will actually work with your preferred backend):

        iterm-notify config-set success-title "Command finished successfully!"
        iterm-notify config-set success-icon "/path/to/success-icon.png"
        iterm-notify config-set success-sound "Glass"

    Replace "success" with "failure" for, well, customizing failure notifications. The value for `icon` can also be an
    URL when using the 'terminal-notifier; backend. Try [this][dogefy.sh]. Wow. The value for `sound` should be a sound
    name, you can find a list in Sound Preferences.
    
    The value for `title` can also be a Python format string using any of these placeholders:
    
    - `exit_code`: the command's exit code
    - `command_line`: the full command line typed by the user at the prompt
    - `duration_second`: the command's duration, in seconds
        
    
- Set a different timeout for notifications:

        iterm-notify config-set command-complete-timeout 15


[explain-id]: https://www.iterm2.com/python-api/customcontrol.html
[terminal-notifier]: https://github.com/julienXX/terminal-notifier
[dogefy.sh]: https://gist.github.com/marzocchi/1bf65095962494a0ff17c417d6b1bb4b
[bash-preexec]: https://github.com/rcaloras/bash-preexec
[zsh-hooks]: http://zsh.sourceforge.net/Doc/Release/Functions.html#Hook-Functions
