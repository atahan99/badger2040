#!/bin/sh
# Run each app on the badge and report whether it renders without raising.
#
#   tools/run_on_device.sh          # every app
#   tools/run_on_device.sh snake    # just one
#   PORT=/dev/cu.usbmodem2101 tools/run_on_device.sh
#
# Apps loop forever and end on halt(), so running one as-is would hang. Each is
# rewritten first: the top-level `while True:` becomes a single pass and halt()
# becomes a no-op, so the app exits on its own and prints APP_OK. Nothing here
# needs killing - killing mpremote mid-transfer wedges the macOS tty.
#
# `resume` matters: without it mpremote soft-resets the board before each
# command, which reboots into main.py -> launcher -> halt(), and the badge
# drops off USB before the next app can be sent.
#
# The badge must be awake: hold a front button while plugging in, otherwise it
# sleeps a few seconds after boot and drops off the USB bus. See README.md.
set -e
cd "$(dirname "$0")/.."

PORT="${PORT:-auto}"
WORK="${TMPDIR:-/tmp}/badger-devtest"
mkdir -p "$WORK"

APPS="${*:-badge life snake p2048 dino timer}"
failed=0

for app in $APPS; do
    python3 tools/bounded.py "examples/$app.py" "$WORK/$app.py"
    output=$(mpremote connect "$PORT" resume run "$WORK/$app.py" 2>&1 </dev/null || true)
    if printf '%s' "$output" | grep -q APP_OK; then
        echo "ok    $app"
    else
        echo "FAIL  $app"
        printf '%s\n' "$output" | tail -12 | sed 's/^/      /'
        failed=1
    fi
done

exit $failed
