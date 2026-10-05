#!/bin/bash
# build-desktop-rdp-icons.sh — generate fleet RDP launcher icons on this machine's desktop
# One icon per remote fleet node. Uses today's proven recipe:
#   xfreerdp -> MagicDNS hostname :3389 /u:Greatful (Remote Login, fresh-login convention)
# Icons = fleet portraits (~/Documents/portraits), converted to 256px hicolor icons.
# Skips the local host automatically.

set -e
REPO="$HOME/NCR-RobCo-GX-9000-Mainframe"
PORTRAITS="$HOME/Documents/portraits"
DESKTOP_DIR="$HOME/Desktop"
BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
LOCAL_HOST=$(hostname | sed 's/-[0-9]*$//')   # strip tailscale suffixes like -1

# fleet roster: hostname|friendly|portrait file
ROSTER="
raul-tejada|Raul Tejada|Raul_Tejada.jpg
randall-clark|Randall Clark|Randall Clark.png
general-lee-oliver|General Lee Oliver|General_Lee_Oliver.jpg
ranger-lineholm|Ranger Lineholm|Ranger_Lineholm.jpg
chief-hanlon|Chief Hanlon|Chief_Hanlon.jpg
colonel-james-hsu|Colonel James Hsu|Colonel_James_Hsu.jpg
dr-julie-farkas|Dr. Julie Farkas|Julie_Farkas.jpg
lt-carrie-boyd|Lt. Carrie Boyd|LT_Carrie_Boyd.jpg
mr-new-vegas|Mr. New Vegas|
craig-boone|Craig Boone|Craig_Boone.jpg
"

# 1. generic connect wrapper (one for all)
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/fleet-rdp-connect.sh" <<'EOF'
#!/bin/bash
# fleet-rdp-connect.sh <hostname> [friendly-title] — Remote Login RDP to a fleet node
TARGET="$1"; TITLE="${2:-$1}"
export DISPLAY="${DISPLAY:-:0}"
setsid nohup flatpak run --command=xfreerdp com.freerdp.FreeRDP \
    /v:$TARGET:3389 /u:${FLEET_REMOTE_USER:-Greatful} /p:${FLEET_REMOTE_PASS:?set FLEET_REMOTE_PASS} /cert:ignore \
    < /dev/null > /tmp/opencode/rdp-$(date +%s).log 2>&1 &
for i in $(seq 1 20); do
    WID=$(wmctrl -l | grep "FreeRDP: $TARGET" | awk '{print $1}' | head -1)
    if [ -n "$WID" ]; then wmctrl -i -r "$WID" -T "$TITLE"; break; fi
    sleep 2
done
EOF
chmod +x "$BIN_DIR/fleet-rdp-connect.sh"

# 2. icons + desktop launchers
mkdir -p "$ICON_DIR" "$DESKTOP_DIR"
ADDED=0
while IFS='|' read -r HOST FRIENDLY PORTRAIT; do
    [ -z "$HOST" ] && continue
    [ "$HOST" = "$LOCAL_HOST" ] && continue          # never icon myself
    BASE=$(echo "$FRIENDLY" | tr ' .]' '___' | tr -d '[]')
    ICON_NAME="fleet-rdp-$HOST"
    SRC="$PORTRAITS/$PORTRAIT"
    if [ -n "$PORTRAIT" ] && [ -f "$SRC" ]; then
        # medallion: circular portrait crop + amber fleet ring + green go-dot + drop shadow
        convert "$SRC" -resize 288x288^ -gravity center -extent 288x288 \
            \( +clone -alpha extract -fill black -draw "circle 144,144 144,0" \) \
            -alpha off -compose CopyOpacity -compose over \
            \( -size 288x288 xc:none -fill none -stroke '#e8a33d' -strokewidth 9 \
               -draw "circle 144,144 144,5" \) -compose over -composite \
            \( -size 288x288 xc:none -fill '#4caf50' -stroke '#0d1f33' -strokewidth 3 \
               -draw "circle 216,216 216,193" \) -compose over -composite \
            \( +clone -background '#00000070' -shadow 70x6+0+5 \) +swap \
            -compose over -composite -resize 256x256 "$ICON_DIR/$ICON_NAME.png" 2>/dev/null
    else
        convert -size 256x256 gradient:'#1a3a5c'-'#0d1f33' \
            -fill none -stroke '#e8a33d' -strokewidth 9 -draw "circle 128,128 128,6" \
            -fill '#e8a33d' -pointsize 64 -gravity center -annotate +0+0 "${FRIENDLY:0:2}" \
            \( +clone -background '#00000070' -shadow 70x6+0+5 \) +swap \
            -compose over -composite "$ICON_DIR/$ICON_NAME.png" 2>/dev/null
    fi
    DESK_FILE="$DESKTOP_DIR/RDP $FRIENDLY.desktop"
    cat > "$DESK_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=RDP → $FRIENDLY
Comment=Remote Login to $HOST (Greatful)
Exec=$BIN_DIR/fleet-rdp-connect.sh $HOST "$FRIENDLY"
Icon=$ICON_DIR/$ICON_NAME.png
Terminal=false
Categories=Network;RemoteAccess;
StartupNotify=false
EOF
    gio set "$DESK_FILE" metadata::trusted true 2>/dev/null || true
    chmod +x "$DESK_FILE"
    mkdir -p "$HOME/.local/share/applications"
    cp "$DESK_FILE" "$HOME/.local/share/applications/"   # app-grid copy (works without ding)
    ADDED=$((ADDED+1))
done <<< "$ROSTER"

# 3. refresh icon cache + mark dir browsed
gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
gio set "$DESKTOP_DIR" metadata::istanbul::shown true 2>/dev/null || true
echo "✓ $ADDED RDP launchers on $DESKTOP_DIR + $ADDED icons installed"
echo "  wrapper: $BIN_DIR/fleet-rdp-connect.sh"
ls "$DESKTOP_DIR" | head -12
