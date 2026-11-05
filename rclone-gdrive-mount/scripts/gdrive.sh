#!/usr/bin/env bash
# Set up a Google Drive rclone remote with the user's own OAuth client and
# mount it at login with a systemd user service.
#
# Usage: gdrive.sh <command> [--remote NAME] [--mount-dir DIR] [options]
#   check                       Report tools, existing remote, folder, service
#   create --client-id ID       Create the remote and run the browser sign-in
#                               (secret is read from $GDRIVE_CLIENT_SECRET)
#   set-secret                  Replace the secret ($GDRIVE_CLIENT_SECRET)
#   reconnect                   Run the browser sign-in again
#   verify                      List top-level Drive folders
#   install-mount [--dry-run]   Write and start the mount service
#   status                      Show service and mount state
#
# Access and refresh tokens are never printed.

set -uo pipefail

REMOTE="gdrive"
MOUNT_DIR="$HOME/GoogleDrive"
CLIENT_ID=""
DRY_RUN=0

die() { echo "ERROR: $*" >&2; exit 1; }

usage() { sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

CMD="${1:-}"; [ -n "$CMD" ] || usage 1; shift
while [ $# -gt 0 ]; do
  case "$1" in
    --remote)    REMOTE="${2:?--remote needs a value}"; shift 2 ;;
    --mount-dir) MOUNT_DIR="${2:?--mount-dir needs a value}"; shift 2 ;;
    --client-id) CLIENT_ID="${2:?--client-id needs a value}"; shift 2 ;;
    --dry-run)   DRY_RUN=1; shift ;;
    -h|--help)   usage 0 ;;
    *) die "unknown option: $1" ;;
  esac
done
REMOTE="${REMOTE%:}"
MOUNT_DIR="${MOUNT_DIR/#\~/$HOME}"
SERVICE="rclone-${REMOTE}.service"
SERVICE_FILE="$HOME/.config/systemd/user/$SERVICE"

remote_exists() { rclone listremotes 2>/dev/null | grep -qx "${REMOTE}:"; }
is_mounted()    { findmnt -n "$MOUNT_DIR" >/dev/null 2>&1; }
fusermount_bin() { command -v fusermount3 || command -v fusermount; }

need_secret() {
  [ -n "${GDRIVE_CLIENT_SECRET:-}" ] || die "set GDRIVE_CLIENT_SECRET in the environment (keeps the secret out of the command line)"
}

# Turn known rclone / Google errors in a log into plain-language advice.
explain_errors() {
  local log="$1"
  if grep -q 'invalid_client' "$log"; then
    echo "CAUSE: Google rejected the client ID/secret pair (invalid_client)."
    echo "FIX:   In Google Cloud Console > APIs & Services > Credentials, open the OAuth client,"
    echo "       check the Client ID matches, add a new client secret, then run 'set-secret' and 'reconnect'."
  elif grep -q 'redirect_uri_mismatch' "$log"; then
    echo "CAUSE: Redirect URL mismatch. The OAuth client must be type 'Desktop app'"
    echo "       (or, for a 'Web application' client, have http://127.0.0.1:53682/ as a redirect URI)."
  elif grep -qE 'access_denied|has not completed the Google verification' "$log"; then
    echo "CAUSE: Google blocked the sign-in. On the OAuth consent screen, add this Google account"
    echo "       as a test user (or publish the app), then run 'reconnect'."
  elif grep -qE 'accessNotConfigured|has not been used in project|API has not been used|is disabled' "$log"; then
    echo "CAUSE: The Google Drive API is not enabled for this Cloud project."
    echo "FIX:   Enable it at https://console.cloud.google.com/apis/library/drive.googleapis.com , wait a minute, retry."
  elif grep -qiE 'address already in use|53682' "$log" && grep -qi 'bind' "$log"; then
    echo "CAUSE: Another sign-in is already waiting on port 53682. Stop it (or finish it) and retry."
  elif grep -q 'empty token found' "$log"; then
    echo "CAUSE: The remote exists but the sign-in never finished. Run 'reconnect'."
  else
    echo "CAUSE: Unrecognised error. Last lines of rclone output:"
    grep -vE '"(access|refresh)_token"' "$log" | grep -E 'ERROR|Error|CRITICAL|Fatal' | tail -5
  fi
}

# Run an rclone auth command: print the sign-in link as soon as it appears,
# hide tokens, and explain failures.
run_auth() {
  local log; log="$(mktemp)"
  echo "Waiting for browser sign-in. If no page opens, or it was closed, open the SIGN-IN LINK below."
  "$@" 2>&1 \
    | grep --line-buffered -vE '"(access|refresh)_token"|^Usage:|^  rclone config|^Flags:|^  -|^      --|^Use "rclone' \
    | tee "$log" \
    | sed -u -nE 's#.*go to the following link: (http://127\.0\.0\.1:[0-9]+/auth[^ ]*).*#SIGN-IN LINK: \1#p; /Got code/p'
  local rc=${PIPESTATUS[0]}
  if [ "$rc" -ne 0 ] || grep -qE 'Fatal error|^Error:|CRITICAL' "$log"; then
    explain_errors "$log"; rm -f "$log"; exit 1
  fi
  rm -f "$log"
  if ! grep -q '^token = ' <(sed -n "/^\[${REMOTE}\]/,/^\[/p" "$(rclone config file | tail -1)"); then
    echo "CAUSE: Sign-in did not save a token. Run 'reconnect'."; exit 1
  fi
  echo "OK: signed in; token saved for remote '${REMOTE}:'."
}

case "$CMD" in
  check)
    ok=1
    if command -v rclone >/dev/null; then echo "rclone:     $(rclone version 2>/dev/null | head -1)"
    else echo "rclone:     MISSING (install: sudo dnf install rclone  /  sudo apt install rclone)"; ok=0; fi
    if fusermount_bin >/dev/null; then echo "fuse:       $(fusermount_bin)"
    else echo "fuse:       MISSING (install: fuse3)"; ok=0; fi
    if remote_exists; then echo "remote:     '${REMOTE}:' ALREADY EXISTS"; else echo "remote:     '${REMOTE}:' free"; fi
    if is_mounted; then echo "mount dir:  $MOUNT_DIR (mounted)"
    elif [ -d "$MOUNT_DIR" ] && [ -n "$(ls -A "$MOUNT_DIR" 2>/dev/null)" ]; then echo "mount dir:  $MOUNT_DIR EXISTS AND IS NOT EMPTY"
    elif [ -d "$MOUNT_DIR" ]; then echo "mount dir:  $MOUNT_DIR (empty, usable)"
    else echo "mount dir:  $MOUNT_DIR (will be created)"; fi
    if [ -e "$SERVICE_FILE" ]; then echo "service:    $SERVICE ALREADY EXISTS"; else echo "service:    $SERVICE free"; fi
    [ "$ok" -eq 1 ] || exit 1
    ;;

  create)
    [ -n "$CLIENT_ID" ] || die "--client-id is required"
    need_secret
    remote_exists && die "remote '${REMOTE}:' already exists. Ask the user before changing it (use set-secret/reconnect, or pick another --remote)."
    run_auth rclone config create "$REMOTE" drive \
      "client_id=$CLIENT_ID" "client_secret=$GDRIVE_CLIENT_SECRET" \
      scope=drive config_is_local=true --auto-confirm
    ;;

  set-secret)
    need_secret
    remote_exists || die "remote '${REMOTE}:' does not exist"
    rclone config update "$REMOTE" "client_secret=$GDRIVE_CLIENT_SECRET" --no-output </dev/null >/dev/null 2>&1 \
      || die "could not update the secret"
    echo "OK: secret updated for '${REMOTE}:'. Now run 'reconnect'."
    ;;

  reconnect)
    remote_exists || die "remote '${REMOTE}:' does not exist"
    run_auth rclone config reconnect "${REMOTE}:" --auto-confirm
    ;;

  verify)
    remote_exists || die "remote '${REMOTE}:' does not exist"
    log="$(mktemp)"
    if timeout 60 rclone lsd "${REMOTE}:" >"$log" 2>&1; then
      n=$(wc -l <"$log")
      echo "OK: '${REMOTE}:' works; $n top-level folders. First few:"
      awk '{ $1=$2=$3=$4=""; sub(/^ +/, ""); print "  " $0 }' "$log" | head -10
      rm -f "$log"
    else
      explain_errors "$log"; rm -f "$log"; exit 1
    fi
    ;;

  install-mount)
    remote_exists || die "remote '${REMOTE}:' does not exist; run 'create' first"
    [ "$DRY_RUN" -eq 0 ] && [ -e "$SERVICE_FILE" ] && die "$SERVICE_FILE already exists. Ask the user before replacing it."
    if [ -d "$MOUNT_DIR" ] && ! is_mounted && [ -n "$(ls -A "$MOUNT_DIR" 2>/dev/null)" ]; then
      die "$MOUNT_DIR is not empty; rclone cannot mount over it. Ask the user for another --mount-dir."
    fi
    FUSERMOUNT="$(fusermount_bin)" || die "fusermount not found (install fuse3)"
    UNIT="[Unit]
Description=rclone mount of ${REMOTE}: at ${MOUNT_DIR}
Wants=network-online.target
After=network-online.target

[Service]
Type=notify
ExecStart=$(command -v rclone) mount ${REMOTE}: \"${MOUNT_DIR}\" --vfs-cache-mode writes --dir-cache-time 5m
ExecStop=${FUSERMOUNT} -uz \"${MOUNT_DIR}\"
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target"
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "DRY RUN: would write $SERVICE_FILE:"; echo "$UNIT"; exit 0
    fi
    mkdir -p "$MOUNT_DIR" "$(dirname "$SERVICE_FILE")"
    printf '%s\n' "$UNIT" >"$SERVICE_FILE"
    echo "Wrote $SERVICE_FILE"
    systemctl --user daemon-reload
    if systemctl --user enable --now "$SERVICE"; then
      sleep 3
      if is_mounted; then echo "OK: $SERVICE running; ${REMOTE}: mounted at $MOUNT_DIR (starts at every login)."
      else echo "Service started but $MOUNT_DIR is not mounted yet. Check: journalctl --user -u $SERVICE -n 30"; exit 1; fi
    else
      echo "Could not start the service. Ask the user to run:"
      echo "  systemctl --user enable --now $SERVICE"
      exit 1
    fi
    ;;

  status)
    echo "service:  $SERVICE $(systemctl --user is-active "$SERVICE" 2>/dev/null), $(systemctl --user is-enabled "$SERVICE" 2>/dev/null || echo not-installed)"
    if is_mounted; then echo "mount:    $MOUNT_DIR mounted"; else echo "mount:    $MOUNT_DIR NOT mounted"; fi
    ;;

  *) usage 1 ;;
esac
