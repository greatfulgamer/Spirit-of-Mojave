#!/bin/bash
# rollout-desktop-icons.sh — push generator + portraits to every online fleet node, generate there.
# Each node auto-skips its own icon. Ports/mirrors the established receiver pattern.
set -u
REPO="$HOME/NCR-RobCo-GX-9000-Mainframe"
SEND="$REPO/send-command.sh"
PUSH="$REPO/scripts/blaster-file-push.sh"
# node|tailscale-ip  (raul handled specially: it already has ~/Pictures/portraits)
NODES="randall-clark|100.114.132.6
mr-new-vegas|100.73.250.34
general-lee-oliver|100.93.165.28
ranger-andy|100.127.121.103"

# 1. ensure the tarball exists on raul (source of portraits)
bash "$SEND" ranger-andy exec '{"command":"tar -czf /tmp/portraits.tar.gz -C ~/Pictures portraits 2>/dev/null && echo tar-ok"}' | grep -q tar-ok || echo "WARN: raul tarball"

for LINE in $NODES; do
  NODE="${LINE%%|*}"; IP="${LINE##*|}"
  echo "=== $NODE ($IP)"
  # 2. push generator + receiver (small files, chunk-acked)
  bash "$PUSH" "$NODE" "$REPO/scripts/build-desktop-rdp-icons.sh" "~/NCR-RobCo-GX-9000-Mainframe/scripts/build-desktop-rdp-icons.sh" | grep -E "✓|✗" 
  bash "$PUSH" "$NODE" "$REPO/scripts/file-receiver.py" "~/NCR-RobCo-GX-9000-Mainframe/scripts/file-receiver.py" | grep -E "✓|✗"
  if [ "$NODE" = "ranger-andy" ]; then
    # raul: portraits already local, just mirror into Documents and generate
    bash "$SEND" "$NODE" exec '{"command":"mkdir -p ~/Documents && cp -r ~/Pictures/portraits ~/Documents/ 2>/dev/null; bash ~/NCR-RobCo-GX-9000-Mainframe/scripts/build-desktop-rdp-icons.sh 2>&1 | tail -2"}' | grep -A3 '"output"' | head -4
  else
    # 3. start receiver on target
    bash "$SEND" "$NODE" exec '{"command":"pkill -f file-receiver 2>/dev/null; setsid nohup python3 ~/NCR-RobCo-GX-9000-Mainframe/scripts/file-receiver.py > /tmp/fr.log 2>&1 < /dev/null & sleep 1; curl -s -m 3 http://127.0.0.1:8899/ping"}' | grep -oE "pong" | head -1
    # 4. raul uploads tarball to target
    bash "$SEND" ranger-andy exec "{\"command\":\"curl -s -m 120 -T /tmp/portraits.tar.gz http://$IP:8899/portraits.tar.gz && echo UPLOADED\"}" | grep -oE "UPLOADED" | head -1
    # 5. extract + generate + cleanup
    bash "$SEND" "$NODE" exec '{"command":"tar -xzf ~/Documents/portraits-incoming/portraits.tar.gz -C ~/Documents/ && bash ~/NCR-RobCo-GX-9000-Mainframe/scripts/build-desktop-rdp-icons.sh 2>&1 | tail -2; rm -rf ~/Documents/portraits-incoming /tmp/portraits.tar.gz"}' | grep -A3 '"output"' | head -4
  fi
done
echo "=== rollout pass complete"
