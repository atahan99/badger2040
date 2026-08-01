# Dice, coin and decision maker.
#
#   A  roll    UP/DOWN  change die    A+C  quit to launcher
import random

# (label, sides). "coin" and "yes/no" are dice wearing hats.
DICE = (
    ("coin", 2),
    ("d4", 4),
    ("d6", 6),
    ("d8", 8),
    ("d10", 10),
    ("d12", 12),
    ("d20", 20),
    ("yes/no", 2),
)
COIN_FACES = ("heads", "tails")
YESNO_FACES = ("yes", "no")


def face(label, value):
    """Map a roll onto what to print for this die."""
    if label == "coin":
        return COIN_FACES[value - 1]
    if label == "yes/no":
        return YESNO_FACES[value - 1]
    return str(value)


def roll(sides, rand=random.randint):
    return rand(1, sides)


# --- hardware below ---
import os
import time
import badger2040
import badger_os

WIDTH = badger2040.WIDTH

# MicroPython's PRNG is not seeded from anything by default, so without this
# every boot would roll the identical sequence - which for a dice app is not a
# subtle bug.
try:
    random.seed(int.from_bytes(os.urandom(4), "big"))
except (AttributeError, OSError):
    random.seed(time.ticks_us())

display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_TURBO)
display.set_font("bitmap8")

state = {"die": 2}          # d6 by default
badger_os.state_load("dice", state)
state["die"] %= len(DICE)

result = None


def render():
    label, sides = DICE[state["die"]]

    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    display.rectangle(0, 0, WIDTH, 18)
    display.set_pen(15)
    display.text("DICE  {}".format(label), 5, 5, WIDTH, 1.0)
    display.text("A+C exit", WIDTH - 70, 5, WIDTH, 1.0)

    display.set_pen(0)
    if result is None:
        display.text("press A to roll", 20, 60, WIDTH, 2.0)
    else:
        shown = face(label, result)
        size = 4.0 if len(shown) <= 3 else 2.0
        w = display.measure_text(shown, size)
        display.text(shown, (WIDTH - w) // 2, 56, WIDTH, size)

    display.text("A roll    UP/DOWN change die", 5, 112, WIDTH, 1.0)
    display.update()


render()

while True:
    display.keepalive()
    changed = False

    if display.pressed(badger2040.BUTTON_A):
        result = roll(DICE[state["die"]][1])
        changed = True
    elif display.pressed(badger2040.BUTTON_UP):
        state["die"] = (state["die"] - 1) % len(DICE)
        result = None
        badger_os.state_save("dice", state)
        changed = True
    elif display.pressed(badger2040.BUTTON_DOWN):
        state["die"] = (state["die"] + 1) % len(DICE)
        result = None
        badger_os.state_save("dice", state)
        changed = True

    if changed:
        render()

    display.halt()
