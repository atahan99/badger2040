# Pomodoro timer.
#
#   A  start / pause    B  reset    C  skip phase    UP/DOWN  work length +/-5
#   A+C  quit to launcher
#
# The Badger 2040 (non-W) has no battery-backed clock, so this counts elapsed
# ticks rather than wall time and cannot sleep while running - it stays awake
# for the whole phase. Expect a few hours of battery, not days.

# The RP2040's clock is not a crystal-accurate timekeeper. If a 25 minute
# phase ends consistently early or late, nudge this: >1.0 makes phases longer.
CLOCK_CAL = 1.0

# Seconds between screen refreshes while counting. E-ink is slow and every
# refresh costs power, so this is deliberately coarse.
REFRESH_EVERY = 15

SHORT_BREAK = 5
LONG_BREAK = 15
LONG_BREAK_EVERY = 4


def phase_after(step, work_minutes):
    """`step` counts phases from 0. Even steps are work, odd are breaks.
    Returns (name, minutes, is_work)."""
    if step % 2 == 0:
        return "work", work_minutes, True
    if ((step + 1) // 2) % LONG_BREAK_EVERY == 0:
        return "long break", LONG_BREAK, False
    return "break", SHORT_BREAK, False


def clock(seconds):
    seconds = max(0, int(seconds))
    return "{:02d}:{:02d}".format(seconds // 60, seconds % 60)


# --- hardware below ---
import time
import badger2040
import badger_os

WIDTH = badger2040.WIDTH

display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_FAST)
display.set_font("bitmap8")

state = {"work_minutes": 25, "pomodoros": 0}
badger_os.state_load("timer", state)

step = 0
name = ""
minutes = 0
is_work = True
left = 0          # seconds remaining in this phase
started = None    # ticks_ms when the current run began, None when paused
last_drawn = None


def reset_phase():
    global name, minutes, is_work, left, started, last_drawn
    name, minutes, is_work = phase_after(step, state["work_minutes"])
    left = minutes * 60
    started = None
    last_drawn = None


def elapsed():
    if started is None:
        return 0
    return time.ticks_diff(time.ticks_ms(), started) / 1000 * CLOCK_CAL


def render(seconds):
    global last_drawn
    display.set_pen(15)
    display.clear()

    display.set_pen(0)
    display.rectangle(0, 0, WIDTH, 18)
    display.set_pen(15)
    display.text(name.upper(), 5, 5, WIDTH, 1.0)
    display.text("{} done".format(state["pomodoros"]), WIDTH - 70, 5, WIDTH, 1.0)

    display.set_pen(0)
    label = clock(seconds)
    w = display.measure_text(label, 3.0)
    display.text(label, (WIDTH - w) // 2, 58, WIDTH, 3.0)

    total = minutes * 60
    display.rectangle(20, 92, WIDTH - 40, 10)
    display.set_pen(15)
    display.rectangle(21, 93, WIDTH - 42, 8)
    display.set_pen(0)
    display.rectangle(21, 93, int((WIDTH - 42) * (total - seconds) / total) if total else 0, 8)

    display.text("A {}   B reset   C skip".format(
        "pause" if started is not None else "start"), 20, 108, WIDTH, 1.0)
    display.text("UP/DOWN {}min   A+C exit".format(state["work_minutes"]), 20, 118, WIDTH, 1.0)
    display.update()
    last_drawn = seconds


def finish_phase():
    """Phase over - flash the LED and move to the next one."""
    global step
    if is_work:
        state["pomodoros"] += 1
        badger_os.state_save("timer", state)
    for _ in range(6):
        display.led(255)
        time.sleep(0.15)
        display.led(0)
        time.sleep(0.15)
    step += 1
    reset_phase()
    render(left)


def restart_at_work():
    """UP/DOWN changed the work length - rewind to the start of this cycle."""
    global step
    badger_os.state_save("timer", state)
    step -= step % 2
    reset_phase()
    render(left)


reset_phase()
render(left)

while True:
    display.keepalive()

    if display.pressed(badger2040.BUTTON_A):
        if started is None:
            started = time.ticks_ms()
        else:
            left -= elapsed()
            started = None
        render(left)
    elif display.pressed(badger2040.BUTTON_B):
        state["pomodoros"] = 0
        step = 0
        badger_os.state_save("timer", state)
        reset_phase()
        render(left)
    elif display.pressed(badger2040.BUTTON_C):
        step += 1
        reset_phase()
        render(left)
    elif display.pressed(badger2040.BUTTON_UP):
        state["work_minutes"] = min(60, state["work_minutes"] + 5)
        restart_at_work()
    elif display.pressed(badger2040.BUTTON_DOWN):
        state["work_minutes"] = max(5, state["work_minutes"] - 5)
        restart_at_work()

    if started is None:
        # Paused: nothing to count, so it is safe to sleep
        display.halt()
        continue

    now = left - elapsed()
    if now <= 0:
        left = 0
        finish_phase()
        continue

    if last_drawn is None or last_drawn - now >= REFRESH_EVERY:
        render(now)

    time.sleep(0.2)
