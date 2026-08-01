#!/bin/sh
# Copy the apps and your badge/QR content onto the Badger.
#
#   pip install mpremote      # once
#   tools/deploy.sh           # auto-detects the board
#   PORT=/dev/cu.usbmodem2101 tools/deploy.sh
#
# Flash the firmware first - see README.md. Deploying is a one-off; after this
# the badge runs standalone on battery.
set -e
cd "$(dirname "$0")/.."

PORT="${PORT:-auto}"
# Two different needs, see README:
#   - breaking IN wants the soft reset that plain mpremote does
#   - everything after wants `resume`, so the badge never reboots into the
#     launcher and never sleeps mid-deploy
mp() { mpremote connect "$PORT" resume "$@"; }

# First contact: soft-reset into the raw REPL (this does not run main.py).
if ! mpremote connect "$PORT" exec "pass" 2>/dev/null; then
    echo "Cannot reach the badge." >&2
    echo "Unplug it, plug it back in, and re-run this within a few seconds -" >&2
    echo "once it sleeps, the serial link is gone until the next boot." >&2
    exit 1
fi

# First run: seed the templates so there is something to show
for template in badges/*.txt.example qrcodes/*.txt.example; do
    real="${template%.example}"
    [ -e "$real" ] || { cp "$template" "$real"; echo "seeded $real"; }
done

mp fs mkdir :/examples 2>/dev/null || true
mp fs mkdir :/badges   2>/dev/null || true
mp fs mkdir :/qrcodes  2>/dev/null || true
mp fs mkdir :/cheats   2>/dev/null || true

for file in examples/*.py examples/*.png; do
    echo "-> /$file"
    mp fs cp "$file" ":/$file"
done

# Only the filled-in files, never the .example templates
for file in badges/*.txt badges/*.png badges/*.jpg qrcodes/*.txt cheats/*.txt; do
    [ -e "$file" ] || continue
    echo "-> /$file"
    mp fs cp "$file" ":/$file"
done

# The two boot files go last and are read back. A half-written one leaves the
# board unreachable over USB - recovering needs the BOOT button and a reflash.
for boot in launcher.py main.py; do
    echo "-> /$boot"
    mp fs cp "$boot" ":/$boot"
    local_size=$(wc -c < "$boot" | tr -d ' ')
    device_size=$(mp exec "import os; print(os.stat('/$boot')[6])" | tr -d ' \r\n')
    if [ "$local_size" = "$device_size" ]; then
        echo "   verified ($device_size bytes)"
    else
        echo "   $boot IS TRUNCATED ON THE DEVICE ($device_size of $local_size bytes)." >&2
        echo "   Re-run this script before unplugging - a half-written boot file" >&2
        echo "   leaves the badge unreachable without BOOT + reflash." >&2
        exit 1
    fi
done

echo
echo "Done. Reset the badge (or unplug it) to see the new launcher pages."
