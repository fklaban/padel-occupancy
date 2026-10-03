#!/bin/bash
# Install (or remove with --uninstall) a launchd agent that runs
# scripts/home-scrape.sh at :05 and :35 every hour while this Mac is awake.
# Logs: ~/Library/Logs/padel-occupancy.log
set -euo pipefail

LABEL="cz.padel-occupancy.home"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
REPO="${PADEL_REPO:-$HOME/.padel-occupancy}"
REMOTE="${PADEL_REMOTE:-https://github.com/fklaban/padel-occupancy.git}"
LOG="$HOME/Library/Logs/padel-occupancy.log"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
if [ "${1:-}" = "--uninstall" ]; then
  rm -f "$PLIST"
  echo "Removed $LABEL. The clone in $REPO was left in place."
  exit 0
fi

[ -d "$REPO/.git" ] || git clone -q "$REMOTE" "$REPO"

mkdir -p "$(dirname "$PLIST")"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$REPO/scripts/home-scrape.sh</string></array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>PADEL_REPO</key><string>$REPO</string>
  </dict>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Minute</key><integer>5</integer></dict>
    <dict><key>Minute</key><integer>35</integer></dict>
  </array>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
EOF

launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed $LABEL → runs $REPO/scripts/home-scrape.sh at :05 and :35. Log: $LOG"
