---
name: rclone-gdrive-mount
description: >-
  Set up Google Drive on Linux with rclone, using the user's own Google OAuth
  client ID and secret, and mount it as a folder that appears at every login
  (systemd user service). Use when the user gives Google Drive / Google Cloud
  OAuth client credentials, or asks to connect, mount or sync Google Drive with
  rclone. Also covers fixing invalid_client, redirect, test-user and
  "Drive API not enabled" errors.
version: 0.1.0
author: Shawon Ashraf
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [rclone, google-drive, fuse, systemd, linux]
    related_skills: []
---

# rclone Google Drive Mount

## Overview

Given a Google OAuth **client ID** and **client secret**, this skill:

1. creates an rclone remote (default name `gdrive`, full `drive` access),
2. runs the Google sign-in in the user's browser,
3. checks that Drive can be listed,
4. installs a systemd **user** service (`rclone-<remote>.service`) that mounts
   Drive at `~/GoogleDrive` at every login.

Defaults: remote `gdrive`, folder `~/GoogleDrive`, scope `drive`, cache mode
`writes` (files are written to a local cache before upload, which most apps need
to save files). Only change these if the user asks.

All steps use `scripts/gdrive.sh` (bash; needs `rclone` and `fuse3`). Use the
absolute path of this skill's folder when calling it.

## Dependencies

None. No other skill covers rclone.

## Quick Start

```bash
S=<skill-dir>/scripts/gdrive.sh
$S check                                              # 1. tools + name clashes
GDRIVE_CLIENT_SECRET='GOCSPX-…' $S create \
    --client-id '1234-abc.apps.googleusercontent.com' # 2. run in BACKGROUND
$S verify                                             # 3. list Drive folders
$S install-mount                                      # 4. mount at login
$S status
```

## Utility Script: `scripts/gdrive.sh`

Every command accepts `--remote NAME` (default `gdrive`) and
`--mount-dir DIR` (default `~/GoogleDrive`). Output is a few short lines.
Access and refresh tokens are never printed. Exit code 1 means failure, and the
output then contains a `CAUSE:` / `FIX:` explanation.

| Command | What it does |
|---|---|
| `check` | Shows rclone/fuse versions and whether the remote, mount folder and service already exist. |
| `create --client-id ID` | Creates the remote and starts the browser sign-in. Secret comes from `$GDRIVE_CLIENT_SECRET`. Refuses if the remote exists. Prints `SIGN-IN LINK: http://127.0.0.1:53682/auth?state=…` as soon as it is ready. |
| `set-secret` | Replaces the secret (from `$GDRIVE_CLIENT_SECRET`). Follow with `reconnect`. |
| `reconnect` | Runs the browser sign-in again for an existing remote. Also prints `SIGN-IN LINK:`. |
| `verify` | Lists top-level Drive folders (count + first 10 names). |
| `install-mount [--dry-run]` | Writes `~/.config/systemd/user/rclone-<remote>.service`, then `enable --now`. Refuses if the service file exists or the folder is non-empty. `--dry-run` only prints the unit. |
| `status` | Service active/enabled state and whether the folder is mounted. |

## Workflow

### 1. Check
Run `check`. If rclone or fuse is missing, tell the user the install command it
prints. If the remote name or service **already exists**, or the folder is not
empty, **stop and ask the user** whether to reuse it, pick another name, or
replace it. Never overwrite without a clear yes.

### 2. Create and sign in
- Run `create` **in the background** (it waits up to a few minutes for the
  browser). Pass the secret through `GDRIVE_CLIENT_SECRET`, not as an argument.
- Read the output once for the `SIGN-IN LINK:` line. Tell the user to approve
  access in the browser page rclone opened.
- If the user closed the page or no page opened: `xdg-open '<SIGN-IN LINK>'`.
  The link stays valid while `create`/`reconnect` is still running.
- Wait for the background task to finish. Success line: `OK: signed in`.

### 3. On failure: explain, then ask
Relay the `CAUSE:` / `FIX:` lines in plain words and wait for the user. Common
cases are in the table below. After the user fixes something:
- new secret: `GDRIVE_CLIENT_SECRET=… $S set-secret`, then `reconnect` (background),
- Console-side fix (test user, API, client type): just `reconnect`.

### 4. Verify
Run `verify`. Show the user a few folder names as proof it works.

### 5. Mount
Run `install-mount`. If the permission system blocks `systemctl` or the start
fails, do **not** look for a workaround: give the user the exact command to run
themselves, for example in Claude Code:

```
! systemctl --user enable --now rclone-gdrive.service && sleep 3 && ls ~/GoogleDrive
```

Then run `status` to confirm `active, enabled` and `mounted`.

### 6. Wrap up
Tell the user: where Drive is mounted, that it mounts at every login, and how to
stop or restart it (`systemctl --user stop|restart rclone-<remote>`). If the
secret was pasted into the chat, suggest rotating it in Google Cloud Console.

## Getting a client ID and secret (short guide for the user)

1. https://console.cloud.google.com → create or pick a project.
2. **APIs & Services → Library** → enable **Google Drive API**.
3. **OAuth consent screen** → External → fill the required fields →
   add the user's Google account under **Test users**.
4. **Credentials → Create credentials → OAuth client ID** → type
   **Desktop app** → copy the Client ID and Client secret.

## Error Guide

| Error text | Meaning | Fix |
|---|---|---|
| `invalid_client` / "client secret is invalid" | Secret does not belong to that client ID, or was reset/deleted | Add a new secret on that client; `set-secret` then `reconnect` |
| `redirect_uri_mismatch` | Client is "Web application" without the right redirect | Use a **Desktop app** client, or add `http://127.0.0.1:53682/` |
| `access_denied`, "has not completed the Google verification" | Account isn't a test user | Add it under OAuth consent screen → Test users; `reconnect` |
| `accessNotConfigured`, "has not been used in project" | Drive API disabled | Enable Google Drive API; wait a minute; `reconnect` / `verify` |
| `empty token found` | Remote exists but sign-in never finished | `reconnect` |
| Port 53682 in use | Another sign-in is still waiting | Finish or stop it, then retry |

## Common Mistakes

- **Filtering rclone output with `grep -v token`.** rclone's real error lines
  contain the word "token", so this hides the cause. The script only hides the
  actual `access_token` / `refresh_token` values.
- **Running `create` in the foreground.** It blocks until the browser sign-in
  finishes; run it in the background and read the `SIGN-IN LINK:`.
- **Mounting over a non-empty folder or re-creating an existing remote.**
  Always run `check` first and ask before replacing anything.
