#!/bin/bash
# blaster-file-push.sh — push a local file to a fleet node's path via blaster exec
# Usage: blaster-file-push.sh <target> <local-file> <remote-path>
# Method: base64 chunks (<=1.8KB) via send-command.sh exec, reassembled + md5 verified.
set -e
TARGET="$1"; SRC="$2"; DST="$3"
SEND="$HOME/NCR-RobCo-GX-9000-Mainframe/send-command.sh"
[ -f "$SRC" ] || { echo "no such file: $SRC"; exit 1; }
[ -n "$TARGET" ] && [ -n "$DST" ] || { echo "usage: $0 <target> <local-file> <remote-path>"; exit 1; }
# Map local-home prefixes to remote ~ (caller's shell expands ~ before we see it)
DST="${DST/#$HOME/~}"

B64=$(base64 -w0 "$SRC")
TOTAL=${#B64}
CHUNK=1800
TMP="/tmp/bfp-$$.b64"
echo "→ $TARGET: $SRC ($(stat -c%s "$SRC") bytes, b64 $TOTAL chars) → $DST"

# clean remote temp + stream chunks (per-chunk files: retries are idempotent)
bash "$SEND" "$TARGET" exec "{\"command\":\"rm -f $TMP.*\"}" > /dev/null
OFF=1; N=0
while [ $OFF -le $TOTAL ]; do
    N=$((N+1))
    PIECE=$(printf '%s' "$B64" | cut -c "${OFF}-$((OFF+CHUNK-1))")
    for attempt in 1 2 3; do
        RES=$(bash "$SEND" "$TARGET" exec "{\"command\":\"printf %s $PIECE > $TMP.$N\"}")
        if echo "$RES" | grep -q '"ok": true'; then
            break
        fi
        echo "  chunk $N attempt $attempt failed, retrying..." >&2
        sleep 1
        [ $attempt -eq 3 ] && { echo "✗ chunk $N failed after 3 attempts"; exit 1; }
    done
    OFF=$((OFF+CHUNK))
done
echo "  sent $N chunks (all acked)"

# reassemble + verify (separate small execs: no nested quotes, resilient to response loss)
# NOTE: single-recv client loses responses occasionally — a MISMATCH here may be a lost
# verify response. Always confirm with a manual md5sum fetch before assuming corruption.
bash "$SEND" "$TARGET" exec "{\"command\":\"mkdir -p \$(dirname $DST) && cat $TMP.* | base64 -d > $DST\"}" > /dev/null
sleep 1
RES=$(bash "$SEND" "$TARGET" exec "{\"command\":\"md5sum $DST\"}")
LOCAL_MD5=$(md5sum "$SRC" | cut -d' ' -f1)
REMOTE_MD5=$(echo "$RES" | grep -oE '[a-f0-9]{32}' | head -1)
bash "$SEND" "$TARGET" exec "{\"command\":\"rm -f $TMP.*\"}" > /dev/null
if [ "$LOCAL_MD5" = "$REMOTE_MD5" ]; then
    echo "✓ $TARGET: $DST verified md5=$REMOTE_MD5"
else
    echo "✗ $TARGET: md5 MISMATCH local=$LOCAL_MD5 remote=${REMOTE_MD5:-none}"
    exit 1
fi
