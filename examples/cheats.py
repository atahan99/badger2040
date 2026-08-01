# Cheat sheets. Reference cards from /cheats/*.txt.
#
#   UP/DOWN  previous / next sheet    A/C  page within a long sheet
#   A+C  quit to launcher
#
# Each file is: line 1 the title, everything after it the body. Same
# data-driven shape as /badges and /qrcodes - add a file, it shows up.
LINE_HEIGHT = 11
HEADER = 18
BODY_LINES = (128 - HEADER - 4) // LINE_HEIGHT


def paginate(lines, per_page=BODY_LINES):
    """Split body lines into pages. Always at least one page, so an empty
    sheet renders as an empty page rather than crashing the pager."""
    if per_page < 1:
        per_page = 1
    pages = [lines[i:i + per_page] for i in range(0, len(lines), per_page)]
    return pages or [[]]


# --- hardware below ---
import os
import badger2040
import badger_os

CHEAT_DIR = "/cheats"
WIDTH = badger2040.WIDTH

DEFAULT = """badger
UP/DOWN  change sheet
A / C    page up / down
A+C      back to the menu

Add your own: drop a .txt in
/cheats - first line is the
title, the rest is the body.
"""

display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_FAST)
display.set_font("bitmap8")


def list_sheets():
    try:
        names = sorted(f for f in os.listdir(CHEAT_DIR) if f.endswith(".txt"))
    except OSError:
        os.mkdir(CHEAT_DIR)
        names = []
    if not names:
        with open("{}/badger.txt".format(CHEAT_DIR), "w") as f:
            f.write(DEFAULT)
        names = ["badger.txt"]
    return names


sheets = list_sheets()
state = {"sheet": 0, "page": 0}
badger_os.state_load("cheats", state)
state["sheet"] %= len(sheets)


def load(index):
    with open("{}/{}".format(CHEAT_DIR, sheets[index])) as f:
        lines = [ln.rstrip("\n") for ln in f]
    title = lines[0].strip() if lines else sheets[index][:-4]
    return title, paginate(lines[1:])


def render():
    title, pages = load(state["sheet"])
    state["page"] %= len(pages)

    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    display.rectangle(0, 0, WIDTH, HEADER)
    display.set_pen(15)
    display.text(title, 5, 5, WIDTH, 1.0)
    marker = "{}/{}  {}/{}".format(state["sheet"] + 1, len(sheets),
                                   state["page"] + 1, len(pages))
    display.text(marker, WIDTH - display.measure_text(marker, 1.0) - 5, 5, WIDTH, 1.0)

    display.set_pen(0)
    y = HEADER + 4
    for line in pages[state["page"]]:
        display.text(line, 4, y, WIDTH, 1.0)
        y += LINE_HEIGHT
    display.update()


render()

while True:
    display.keepalive()
    changed = False

    if display.pressed(badger2040.BUTTON_UP):
        state["sheet"] = (state["sheet"] - 1) % len(sheets)
        state["page"] = 0
        changed = True
    elif display.pressed(badger2040.BUTTON_DOWN):
        state["sheet"] = (state["sheet"] + 1) % len(sheets)
        state["page"] = 0
        changed = True
    elif display.pressed(badger2040.BUTTON_A):
        state["page"] -= 1
        changed = True
    elif display.pressed(badger2040.BUTTON_C):
        state["page"] += 1
        changed = True

    if changed:
        badger_os.state_save("cheats", state)
        render()

    display.halt()
