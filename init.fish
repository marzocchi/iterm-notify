function iterm-notify
  function log
    sed 's/^/iterm-notify: /' >&2
  end

  function _base64
    cat | base64 | tr -d '\n'
  end

  if test -n "$TMUX"
    echo "fish in tmux is not supported yet :-(" | log
    return 42
  end

  if not count $argv > /dev/null
    echo usage: "before-command|after-command|config-set|send" | log
    return 1
  end

  set cmd "$argv[1]"
  set argv $argv[2..-1]


  set iterm_notify_identity_file "$HOME/.iterm-notify-identity"

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
    read message
    set type "$argv[1]"
    set title "$argv[2]"

    printf "\033]1337;Custom=id=%s:%s,%s,%s,%s\a" "$iterm_notify_identity" "notify" (echo -n "$type" | _base64) (echo -n "$message" | _base64) (echo -n "$title" | _base64)
  case '*'
    echo "unknown subcommand $cmd" | log
    return 1
  end
end

function _iterm_notify_before_command_hook --on-event fish_preexec
  iterm-notify before-command "$argv[1]"
end

function _iterm_notify_after_command_hook --on-event fish_prompt
  iterm-notify after-command "$status"
end

