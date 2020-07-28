iTerm-notify [![Build Status](https://github.com/marzocchi/iterm-notify/workflows/Tests/badge.svg?branch=master)](https://github.com/marzocchi/iterm-notify/actions)
---

Desktop notifications for local and remote long-running commands in iTerm2 and Zsh or Bash.

Usage
--- 

iTerm-notify hooks into your shell and iTerm to send you Desktop notifications when those commands you started and
forgot about in some tab finally finish. To use it, follow the instructions below to run the `notify.py` script with
iTerm and load `init.sh` in your shell's initialization file.

Once iTerm-notify is hooked up, you can also use `iterm-notify send TITLE MESSAGE` to immediately send notifications
from the shell.

### Requirements
- iTerm2 with the Python API enabled with version > 3.8 of the Python Runtime (at the time of writing, this is only
  available with the beta)
- Zsh or Bash (with [bash-preexec][bash-preexec])

### Installation
1. Clone this repository
1. Create your "identity file" by entering a random string as the first line in `$HOME/.iterm-notify-identity`
    - The _identity_ is an important **security feature** of [iTerm2's Custom Control Sequences][explain-id] support,
      so don't be lazy and choose a... well, random string
1. Symlink `notify.py` to `~/Library/ApplicationSupport/iTerm2/Scripts/AutoLaunch/notify.py`
1. Source `init.sh` in your shell initialization file
1. Start `notify.py` from iTerm2's Scripts menu (Scripts > AutoLaunch > notify.py)
1. Copy the identity file and `init.sh` (and source it!) on any other machine you want to receive notifications from.
1. For Bash: download and install [bash-preexec][bash-preexec] (bundled with iTerm2's shell integration)

iTerm-notify also works over SSH: just copy your identity file, and upload and source `init.sh` in the shell on any
server you want to use it.

Supported shells
---

iTerm-notify needs to track commands starting and finishing and it can work out of the box with shells that provide
hooks around the prompt, such as Zsh's `preexec`/`precmd` [hooks][zsh-hooks]. In Bash, [bash-preexec][bash-preexec]
(which is bundled with iTerm2's shell integration) is required and must be loaded before `init.sh`.

Users of other shells can try to make it work by rolling out their own integration:

- `iterm-notify before-command COMMAND_LINE` must be called before executing every command, passing whatever the user
   typed on the prompt as the first argument 

- `iterm-notify after-command EXIT_CODE` must be called after the command finished, passing it the exit code as the
   first argument

### Limitations

iTerm-notify uses iTerm2's support for [Custom Control Sequences][explain-id] to send text **from** the shell **to**
iTerm which in turn forwards the text to Python-based daemon (if the "identity" matches). So, tracking commands
works correctly only in these scenarios:

- Zsh or Bash running locally or in an SSH session, even when nested or in iTerm's buried sessions
- Zsh or Bash running locally in TMUX
- TMUX in an SSH session, but not SSH in a TMUX session

Configuration
---

The behavior of `iterm-notify` can be modified by using `iterm-notify config-set`, giving a parameter and its value as
first and second arguments, or giving `-` as the first and only argument, and parameters and their values one per line
on STDIN.

**Watch out!** Calls to `config-set` during an interactive session have effect only for the current command
(eg. between `before-command` and `after-command`). A configuration will last past `after-command` it  must be
`source`d from a file. To persist a configuration across iTerm session just add calls to `iterm-notify config-set` to
your shell's initialization file, **after** sourcing `init.sh`. 

- Set the notification backend:

    ```shell
    iterm-notify config-set notifications-backend terminal-notifier 
    ```
    
    Supported backends:
    - `iterm`: notifies using a modal alert using iTerm2's own Alert mechanism; can only display notification
       title and text (no sound, etc)
    - `osascript` (default): shows notification in Notification Center using `display notification` from Apple Script's
       StandardAdditions.osax; can show title, message and play sounds, but no custom icons
    - `terminal-notifier`: requires manual installation of [terminal-notifier.app][terminal-notifier] and
      `(...)/terminal-notifier.app/Contents/MacOS` must be in `$PATH`; can show title, message, icons and play sounds
         
- Customize the notifications (check above for what will actually work with your preferred backend):

    ```shell
    iterm-notify config-set success-title Command finished successfully!
    iterm-notify config-set success-icon /path/to/success-icon.png
    iterm-notify config-set success-sound Glass
    ```

    Replace "success" with "failure" for, well, customizing failure notifications. The value for `icon` can also be an
    URL when using the `terminal-notifier`; backend. Try [this][dogefy.sh]. Wow. The value for `sound` should be a sound
    name, you can find a list in Sound Preferences.
    
    The value for `title` can also be a Python format string using any of these placeholders:
    
    - `exit_code`: the command's exit code
    - `command_line`: the full command line typed by the user at the prompt
    - `duration`: the command's duration, as a `datetime.timedelta`
        
    
- Set a different timeout for notifications:

    ```shell
    iterm-notify config-set command-complete-timeout 15
    ```


[explain-id]: https://www.iterm2.com/python-api/customcontrol.html
[terminal-notifier]: https://github.com/julienXX/terminal-notifier
[dogefy.sh]: https://gist.github.com/marzocchi/1bf65095962494a0ff17c417d6b1bb4b
[bash-preexec]: https://github.com/rcaloras/bash-preexec
[zsh-hooks]: http://zsh.sourceforge.net/Doc/Release/Functions.html#Hook-Functions
