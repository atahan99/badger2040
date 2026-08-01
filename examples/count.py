# Tally counter. Survives power-off, which is the whole point of it.
#
#   A  +1    C  -1    B  reset (hold UP as well, so a stray press cannot
#   wipe your count)    UP/DOWN  switch counter    A+C  quit to launcher
COUNTERS = ("one", "two", "three")


def clamp(value, low=0, high=99999):
    return max(low, min(high, value))


# --- hardware below ---
import badger2040
import badger_os

WIDTH = badger2040.WIDTH
HEIGHT = badger2040.HEIGHT

display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_TURBO)
display.set_font("bitmap8")

state = {"which": 0, "counts": [0, 0, 0]}
badger_os.state_load("count", state)
# An older state file, or a hand-edited one, should not crash the app
if len(state.get("counts", [])) != len(COUNTERS):
    state["counts"] = [0] * len(COUNTERS)
state["which"] %= len(COUNTERS)


def render():
    which = state["which"]
    display.set_pen(15)
    display.clear()

    display.set_pen(0)
    display.rectangle(0, 0, WIDTH, 18)
    display.set_pen(15)
    display.text("COUNTER {}".format(COUNTERS[which]), 5, 5, WIDTH, 1.0)
    display.text("A+C exit", WIDTH - 70, 5, WIDTH, 1.0)

    display.set_pen(0)
    label = str(state["counts"][which])
    w = display.measure_text(label, 4.0)
    display.text(label, (WIDTH - w) // 2, 56, WIDTH, 4.0)

    display.text("A +1    C -1    UP/DOWN switch", 5, 108, WIDTH, 1.0)
    display.text("B+UP resets", 5, 118, WIDTH, 1.0)

    # Which of the three counters is showing
    for i in range(len(COUNTERS)):
        x = WIDTH - 14
        y = 30 + i * 12
        display.rectangle(x, y, 8, 8)
        if i != which:
            display.set_pen(15)
            display.rectangle(x + 1, y + 1, 6, 6)
            display.set_pen(0)
    display.update()


def save():
    badger_os.state_save("count", state)


render()

while True:
    display.keepalive()
    which = state["which"]
    changed = False

    if display.pressed(badger2040.BUTTON_A):
        state["counts"][which] = clamp(state["counts"][which] + 1)
        changed = True
    elif display.pressed(badger2040.BUTTON_C):
        state["counts"][which] = clamp(state["counts"][which] - 1)
        changed = True
    elif display.pressed(badger2040.BUTTON_B):
        # Two-button reset: losing a tally to a pocket press would be maddening
        if display.pressed(badger2040.BUTTON_UP):
            state["counts"][which] = 0
            changed = True
    elif display.pressed(badger2040.BUTTON_UP):
        state["which"] = (which - 1) % len(COUNTERS)
        changed = True
    elif display.pressed(badger2040.BUTTON_DOWN):
        state["which"] = (which + 1) % len(COUNTERS)
        changed = True

    if changed:
        save()
        render()

    display.halt()
