#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/apps/agent-usage-bar/.build/release/usagebar"
DEST="$HOME/Applications/Agent Usage Bar.app"
mkdir -p "$HOME/Applications"
cd "$ROOT/apps/agent-usage-bar"
swift build -c release
mkdir -p "$DEST/Contents/MacOS"
cp "$APP" "$DEST/Contents/MacOS/usagebar"
cat > "$DEST/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>Agent Usage Bar</string>
<key>CFBundleDisplayName</key><string>Agent Usage Bar</string>
<key>CFBundleIdentifier</key><string>jp.subaruono.agent-usage-bar</string>
<key>CFBundleExecutable</key><string>usagebar</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSUIElement</key><true/>
<key>LSMinimumSystemVersion</key><string>14.0</string>
</dict></plist>
PLIST
open "$DEST"
printf 'Installed and launched: %s\n' "$DEST"
