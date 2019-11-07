function iterm-notify() {
  local last_status=$?
  local printf cmd

  _tmux-printf() {
    local pattern="$1"
    shift

    printf "\ePtmux;\e\e${pattern}\e\\" "$@"
  }

  _log() {
    sed 's/^/iterm-notify: /' >&2
  }

  if [[ $# == 0 ]]; then
    echo usage: iterm-notify "before-command|after-command|config-set" >&2
    return 1
  fi

  cmd="$1"
  shift

  if [ -n "$TMUX" ]; then
    printf="_tmux-printf"
  else
    printf="printf"
  fi

  iterm_notify_identity_file="$HOME/.iterm-notify-identity"

  if [[ -s "$iterm_notify_identity_file" ]]; then
    iterm_notify_identity=$(head -n1 "$iterm_notify_identity_file" | sed 's/^\ *//' | sed 's/\ *$//')
  fi

  if [[ -z "$iterm_notify_identity" ]]; then
    echo "${iterm_notify_identity_file} does not exist or is empty" | _log
    return 1
  fi

  case $cmd in
  before-command)
    $printf "\033]1337;Custom=id=%s:%s,%s\a" "$iterm_notify_identity" "before-command" "$1"
    ;;
  after-command)
    $printf "\033]1337;Custom=id=%s:%s,%s\a" "$iterm_notify_identity" "after-command" "$last_status"
    ;;
  config-set)
    local k v

    if [[ $# -lt 2 ]]; then

      if [[ "$1" == "-" ]]; then
        if [[ -t 0 ]]; then
          echo "enter one parameter, value pair on each line; hit CTRL-D when done..." >&2
        fi
        while read -r k v; do
          iterm-notify config-set "$k" "$v"
        done

        return 0
      fi

      echo usage: iterm-notify config-set NAME VALUE >&2
      echo usage: echo NAME VALUE \| iterm-notify config-set - >&2
      return 1
    fi

    k="$1"
    v="$2"

    $printf "\033]1337;Custom=id=%s:%s,%s\a" "$iterm_notify_identity" set-"$k" "$v"
    ;;
  send)
    local type message title
    message="$(cat | head -n1)"
    type="$1"
    title="$2"

    $printf "\033]1337;Custom=id=%s:%s,%s,%s,%s\a" "$iterm_notify_identity" "notify" "$type" "$message" "$title"
    ;;
  *)
    echo "unknown subcommand ${cmd}" | _log
    return 1
  esac
}

_iterm_notify_before_command_hook() {
  iterm-notify before-command "$1"
}

_iterm_notify_after_command_hook() {
  iterm-notify after-command "$?"
}

if [[ -n "$ZSH_VERSION" ]]; then
  autoload add-zsh-hook
  add-zsh-hook preexec _iterm_notify_before_command_hook
  add-zsh-hook precmd _iterm_notify_after_command_hook
elif [[ -n "$BASH_VERSION" ]]; then
  preexec_functions+=(_iterm_notify_before_command_hook)
  precmd_functions+=(_iterm_notify_after_command_hook)
fi
