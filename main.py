# Boot into the launcher menu on a cold start, but let a sleeping app resume.
#
# Stock BadgerOS always reopens the last app you were using, so the badge feels
# like it has no home screen, and a crashing app traps you in a reboot loop.
#
# It cannot simply be switched off, though: halt() powers the board down, and
# pressing a button *reboots* it. Reopening the last app is how an app survives
# its own sleep between button presses. Clearing that unconditionally means
# every button press inside an app kicks you back to the menu - and because the
# press is consumed by the boot, it looks like buttons need pressing twice.
#
# So: only take over when this is a genuine power-on rather than a button wake.
try:
    import badger2040
    import badger_os

    if not badger2040.woken_by_button():
        badger_os.state_modify("launcher", {"running": "launcher"})
except Exception as e:
    # This file is the one that can lock you out of the device, so never let
    # it stop the launcher from starting.
    print("boot-to-menu skipped:", e)

import launcher  # noqa: E402  (must come after the state is set)
