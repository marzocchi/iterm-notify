function iterm-notify
  function log
    sed 's/^/iterm-notify: /' >&2
  end

  function _base64
    cat | base64 | tr -d '\n'
  end

  if test -n "$TMUX"
    return 42
  end

  if not count $argv > /dev/null
    echo usage: "before-command|after-command|config-set|send" | log
    return 1
  end

  set cmd "$argv[1]"
  set argv $argv[2..-1]


  if test -n "$ITERM_NOTIFY_IDENTITY_FILE"
    set iterm_notify_identity_file "$ITERM_NOTIFY_IDENTITY_FILE"
  else
    set iterm_notify_identity_file "$HOME/.iterm-notify-identity"
  end

  if test -s "$iterm_notify_identity_file"
    set iterm_notify_identity (head -n1 "$iterm_notify_identity_file" | sed 's/^\ *//' | sed 's/\ *$//')
  end

  if test -z "$iterm_notify_identity"
    echo "$iterm_notify_identity_file does not exist or is empty" | log
    return 1
  end

  switch $cmd
  case before-command
    printf "\033]1337;Custom=id=%s:%s,%s\a" "$iterm_notify_identity" "before-command" (echo -n "$argv[1]" | _base64)
  case after-command
    printf "\033]1337;Custom=id=%s:%s,%s\a" "$iterm_notify_identity" "after-command" (echo -n "$argv[1]" | _base64)
  case config-set
    if test (count $argv) -lt 2
      if test "$argv[1]" = "-"
        if test -t 0
          echo "enter one parameter, value pair on each line; hit CTRL-D when done..." | log
        end

        while read k v
          iterm-notify config-set "$k" "$v"
        end

        return 0
      end

      echo usage: iterm-notify config-set NAME VALUE | log
      echo usage: echo NAME VALUE \| iterm-notify config-set - | log
      return 1
    end


    set k "$argv[1]"
    set v "$argv[2]"

    printf "\033]1337;Custom=id=%s:%s,%s\a" "$iterm_notify_identity" set-$k (echo -n "$v" | _base64)
  case send
    set title "$argv[1]"
    set message ""

    if test 2 -eq (count $argv)
      set message "$argv[2]"
    end

    if test -z "$title"
      echo usage: iterm-notify send TITLE MESSAGE | log
      echo usage: echo MESSAGE \| iterm-notify send TITLE | log
      return 1
    end

    if test -z "$message"
      read message

      if test -z "$message"
        echo usage: iterm-notify send TITLE MESSAGE | log
        echo usage: echo MESSAGE \| iterm-notify send TITLE | log
        return 1
      end
    end

    printf "\033]1337;Custom=id=%s:%s,%s,%s\a" "$iterm_notify_identity" "notify" \
      (echo -n "$message" | _base64)\
      (echo -n "$title" | _base64)

  case '*'
    echo "unknown subcommand $cmd" | log
    return 1
  end
end

set -g _iterm_notify_did_run_before_hook ""

function _iterm_notify_before_command_hook --on-event fish_preexec
  if test $argv[1] != ""
    iterm-notify before-command "$argv[1]"
    set _iterm_notify_did_run_before_hook "yep"
  end
end

function _iterm_notify_after_command_hook --on-event fish_prompt
  set last_status "$status"

  if test "$_iterm_notify_did_run_before_hook" = yep
    iterm-notify after-command "$last_status"
  end

  set _iterm_notify_did_run_before_hook ""
end

