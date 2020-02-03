iterm-notify() {
  local printf cmd

  base64() {
    # some base64 wrap the output
    cat | command base64 | tr -d '\n'
  }

  tmux-printf() {
    local pattern
    pattern="$1"
    shift

    printf "\ePtmux;\e\e${pattern}\e\\" "$@"
  }

  log() {
    sed 's/^/iterm-notify: /' >&2
  }

  if [[ $# == 0 ]]; then
    echo usage: "before-command|after-command|config-set|send" | log
    return 1
  fi

  cmd="$1"
  shift

  if [ -n "$TMUX" ]; then
    printf="tmux-printf"
  else
    printf="printf"
  fi

  if [[ -n "$ITERM_NOTIFY_IDENTITY_FILE" ]]; then
    iterm_notify_identity_file="$ITERM_NOTIFY_IDENTITY_FILE"
  else
    iterm_notify_identity_file="$HOME/.iterm-notify-identity"
  fi

  if [[ -s "$iterm_notify_identity_file" ]]; then
    iterm_notify_identity=$(head -n1 "$iterm_notify_identity_file" 2>/dev/null | sed 's/^\ *//' | sed 's/\ *$//')
  fi

  if [[ -z "$iterm_notify_identity" ]]; then
    echo "${iterm_notify_identity_file} does not exist or is empty" | log
    return 1
  fi

  case $cmd in
  before-command)
    $printf "\033]1337;Custom=id=%s:%s,%s\a" "$iterm_notify_identity" "before-command" "$(echo -n "$1" | base64)"
    ;;
  after-command)
    $printf "\033]1337;Custom=id=%s:%s,%s\a" "$iterm_notify_identity" "after-command" "$(echo -n "$1" | base64)"
    ;;
  config-set)
    local k v

    if [[ $# -lt 2 ]]; then

      if [[ "$1" == "-" ]]; then
        if [[ -t 0 ]]; then
          echo "enter one parameter, value pair on each line; hit CTRL-D when done..." | log
        fi
        while read -r k v; do
          iterm-notify config-set "$k" "$v"
        done

        return 0
      fi

      echo usage: iterm-notify config-set NAME VALUE | log
      echo usage: echo NAME VALUE \| iterm-notify config-set - | log
      return 1
    fi

    k="$1"
    v="$2"

    $printf "\033]1337;Custom=id=%s:%s,%s\a" "$iterm_notify_identity" set-"$k" "$(echo -n "$v" | base64)"
    ;;
  send)
    local message title

    title="$1"
    message="$2"

    if [[ -z "$title" ]]; then
      echo usage: iterm-notify send TITLE MESSAGE | log
      echo usage: echo MESSAGE \| iterm-notify send TITLE | log
      return 1
    fi

    if [[ -z "$message" ]]; then
      read -r message
    fi

    if [[ -z "$message" ]]; then
      echo usage: iterm-notify send TITLE MESSAGE | log
      echo usage: echo MESSAGE \| iterm-notify send TITLE | log
      return 1
    fi

    $printf "\033]1337;Custom=id=%s:%s,%s,%s\a" "$iterm_notify_identity" "notify" \
      "$(echo -n "$message" | base64)" \
      "$(echo -n "$title" | base64)"
    ;;
  *)
    echo "unknown subcommand ${cmd}" | log
    return 1
  esac
}

_iterm_notify_did_run_before_hook=""

_iterm_notify_before_command_hook() {
  iterm-notify before-command "$1"
  _iterm_notify_did_run_before_hook="yep"
}

_iterm_notify_after_command_hook() {
  local last_status="$?"
  test -n "$_iterm_notify_did_run_before_hook" && iterm-notify after-command "$last_status"
  _iterm_notify_did_run_before_hook=""
}

if [[ -n "$ZSH_VERSION" ]]; then
  autoload add-zsh-hook
  add-zsh-hook preexec _iterm_notify_before_command_hook
  add-zsh-hook precmd _iterm_notify_after_command_hook
elif [[ -n "$BASH_VERSION" ]]; then
  preexec_functions+=(_iterm_notify_before_command_hook)
  precmd_functions+=(_iterm_notify_after_command_hook)
fi
