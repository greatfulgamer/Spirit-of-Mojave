#!/bin/bash
# fleet-talk.sh — GX-9000 tiered comms protocol (BINDING)
# ─────────────────────────────────────────────────────────────
# TIER 1: blaster exec          ← ALWAYS FIRST
# TIER 2: blaster exec (retry)  ← once, after brief delay
# TIER 3: tailscale SSH         ← FAILOVER ONLY, must be noted
#
# Usage: fleet-talk.sh <node> <command...>
#   e.g. fleet-talk.sh randall-clark "uptime"
# Uses configs/comms-policy.json for users/blaster rules.

REPO="$HOME/NCR-RobCo-GX-9000-Mainframe"
SEND="$REPO/send-command.sh"
POLICY="$REPO/configs/comms-policy.json"
NODE="$1"; shift
CMD="$*"
BLASTER_PORT=8190
TIMEOUT_S="${FLEET_TALK_TIMEOUT:-15}"

NODE_IP=$(grep "\[\"$NODE\"\]" "$SEND" 2>/dev/null | head -1 | sed 's/.*="\([^"]*\)".*/\1/')
[ -z "$NODE_IP" ] && { echo "✗ unknown node: $NODE"; exit 1; }

USER_NAME=$(python3 -c "import json;print(json.load(open('$POLICY'))['users_by_node'].get('$NODE','bazzite'))" 2>/dev/null || echo bazzite)

# ── TIER 1 + 2: blaster ──────────────────────────────────────
for ATTEMPT in $(seq 1 "${FLEET_TALK_ATTEMPTS:-4}"); do
    RES=$(printf 'exec {"command":"%s"}\n' "$CMD" | timeout $((TIMEOUT_S + 5)) python3 -c "
import socket, sys
s = socket.socket(); s.settimeout($TIMEOUT_S)
try:
    s.connect(('$NODE_IP', $BLASTER_PORT))
    s.sendall(sys.stdin.buffer.read())
    print(s.recv(65536).decode())
except Exception as e:
    print('ERR ' + str(e))
" 2>/dev/null)
    if echo "$RES" | grep -q '"ok": true'; then
        [ $ATTEMPT -gt 1 ] && echo "[tier2: blaster retry succeeded]" >&2
        echo "$RES" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('output','') or d.get('error',''))"
        exit 0
    fi
    [ $ATTEMPT -lt "${FLEET_TALK_ATTEMPTS:-4}" ] && sleep 2
done

# ── TIER 3: tailscale SSH failover ───────────────────────────
echo "[tier3: FAILOVER — blaster down on $NODE, using tailscale ssh (note this!)]" >&2
timeout 45 ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "$USER_NAME@$NODE" "$CMD" 2>&1
RC=$?
[ $RC -eq 0 ] && echo "[failover ssh succeeded — $NODE blaster needs attention: systemctl --user start blaster + enable linger]" >&2
exit $RC
