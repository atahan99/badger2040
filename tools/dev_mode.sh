#!/bin/sh
# Stop the badge putting itself to sleep while you work on it.
#
#   tools/dev_mode.sh on     # park main.py, board stays at the REPL
#   tools/dev_mode.sh off    # restore it, back to normal behaviour
#   tools/dev_mode.sh status
#
# Normally the badge boots into the launcher and calls halt() within a few
# seconds, cutting the 3V3 rail and dropping off USB. That is correct for
# battery life and hopeless for a work session: every tool invocation races
# the sleep. Renaming main.py means a reboot lands at the REPL and stays
# there, so testing runs without racing anything.
#
# ALWAYS run `off` when you are done, or the badge boots to a blank screen.
set -e
cd "$(dirname "$0")/.."

PORT="${PORT:-auto}"
# Plain mpremote, not `resume`: this is usually the first thing you run, and
# only the soft reset can break into a busy board. Raw REPL skips main.py, so
# the reset does not start the launcher. See README.
mp() { mpremote connect "$PORT" "$@"; }

case "${1:-status}" in
on)
    mp exec "
import os
files = os.listdir('/')
if 'main.py' in files:
    if 'main.py.parked' in files:
        os.remove('/main.py.parked')
    os.rename('/main.py', '/main.py.parked')
    print('dev mode ON - main.py parked, board will stay at the REPL')
elif 'main.py.parked' in files:
    print('dev mode already ON')
else:
    print('WARNING: no main.py at all - re-run tools/deploy.sh')
"
    ;;
off)
    mp exec "
import os
files = os.listdir('/')
if 'main.py' in files:
    # A deploy already replaced it; the parked copy is stale, just drop it
    if 'main.py.parked' in files:
        os.remove('/main.py.parked')
        print('dev mode OFF - main.py already current, stale parked copy removed')
    else:
        print('dev mode already OFF')
elif 'main.py.parked' in files:
    os.rename('/main.py.parked', '/main.py')
    print('dev mode OFF - main.py restored, badge boots to the menu again')
else:
    print('WARNING: no main.py at all - re-run tools/deploy.sh')
"
    ;;
status)
    mp exec "
import os
files = os.listdir('/')
# main.py present means normal boot, whether or not a stale parked copy exists
print('dev mode OFF' if 'main.py' in files
      else 'dev mode ON (main.py parked)' if 'main.py.parked' in files
      else 'WARNING: no main.py at all - re-run tools/deploy.sh')
"
    ;;
*)
    echo "usage: $0 on|off|status" >&2
    exit 2
    ;;
esac
