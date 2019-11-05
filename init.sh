iterm_notify_identity_file="$HOME/.iterm-notify-identity"

if [[ -s "$iterm_notify_identity_file" ]]; then
  iterm_notify_identity=$(head -n1 "$iterm_notify_identity_file" | sed 's/^\ *//' | sed 's/\ *$//')
fi

if [[ -z "$iterm_notify_identity" ]]; then
  echo "iterm-notify: ${iterm_notify_identity_file} does not exist or is empty" >&2
fi

iterm-notify-printf() {
  if [ -n "$TMUX" ]; then
    echo iterm-notify-tmux-printf
  else
    echo iterm-notify-standard-printf
  fi
}

iterm-notify-standard-printf() {
  printf $@
}

iterm-notify-tmux-printf() {
  t=$(iterm-notify-standard-printf $@)
  printf '\ePtmux;\e%s\e\\' "$t"
}

iterm-notify-set-config() {
  k="$1"
  v="$2"

  if [[ -z "$k" ]]; then
    echo usage: iterm-notify-set-config NAME VALUE >&2
    return 1
  fi

  $(iterm-notify-printf) "\033]1337;Custom=id=%s:%s,%s\a" "$iterm_notify_identity" set-"$k" "$v"
}

iterm-notify-before-command() {
  $(iterm-notify-printf) "\033]1337;Custom=id=%s:%s,%s\a" "$iterm_notify_identity" "before-command" "$1"
}

iterm-notify-after-command() {
  local last_status=$?
  $(iterm-notify-printf) "\033]1337;Custom=id=%s:%s,%s\a" "$iterm_notify_identity" "after-command" "$last_status"
}

if [[ -n "$ZSH_VERSION" ]]; then
  autoload add-zsh-hook
  add-zsh-hook preexec iterm-notify-before-command
  add-zsh-hook precmd iterm-notify-after-command
fi
