#!/bin/bash
# onboard-remote-account.sh — create the fleet-standard secondary remote-access account
# Run as root on any Bazzite/GNOME fleet node (or via blaster exec with sudo).
#
# WHY: GNOME Remote Login (3389) works fully interactive ONLY for fresh logins.
# Logging into an account that already has an active session triggers the
# fleet-wide "limbo" bug (black screen, dead handover). A dedicated secondary
# account that is never logged in elsewhere guarantees every remote login is fresh.
#
# Convention (fleet standard):
#   Username: Greatful        Password: <see .secrets.local>   (wheel)
#   Never use this account at the physical console.
#   Primary users keep their own accounts for console sessions.

set -e
USER_NAME="${FLEET_REMOTE_USER:-Greatful}"
USER_PASS="${FLEET_REMOTE_PASS:?set FLEET_REMOTE_PASS - never hardcode a fleet password}"

if id "$USER_NAME" >/dev/null 2>&1; then
    echo "= $USER_NAME already exists, ensuring password"
    echo "$USER_NAME:$USER_PASS" | chpasswd
else
    useradd -m -G wheel -c "Fleet-remote-access" "$USER_NAME"
    echo "$USER_NAME:$USER_PASS" | chpasswd
    echo "+ created $USER_NAME (wheel)"
fi

# Remote Login (system GRD) credentials + the mandatory daemon restart.
# The restart is REQUIRED: the daemon caches credentials at startup;
# skipping it yields ERRCONNECT_LOGON_FAILURE until it bounces.
if command -v grdctl >/dev/null 2>&1; then
    grdctl --system rdp set-credentials "$USER_NAME" "$USER_PASS" 2>/dev/null || \
        echo "! grdctl --system set-credentials failed (check manually)" >&2
    systemctl enable --now gnome-remote-desktop.service 2>/dev/null || true
    systemctl restart gnome-remote-desktop.service
    echo "+ system GRD creds set + daemon restarted"
else
    echo "! grdctl not found — GNOME Remote Desktop not installed?" >&2
fi

# Verify
ss -tln | grep -q :3389 && echo "+ 3389 listening" || echo "! 3389 NOT listening" >&2
id "$USER_NAME" && echo "✓ $USER_NAME ready on $(hostname)"
echo "NOTE: do NOT clone a primary user's ~/.config into this account —"
echo "      cloned session state freezes the desktop. Vanilla is the supported state."
