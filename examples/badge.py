# Multi-profile badge. UP/DOWN cycles through every .txt in /badges.
#
# Each file is 7 lines:
#   1 company / context      2 name
#   3 detail 1 title         4 detail 1 text
#   5 detail 2 title         6 detail 2 text
#   7 image path (optional - leave blank for a full-width text badge)
#
# Adapted from the stock BadgerOS badge.py, which showed a single badge.
import os
import badger2040
import badger_os
import jpegdec
import pngdec

WIDTH = badger2040.WIDTH
HEIGHT = badger2040.HEIGHT

IMAGE_WIDTH = 104
COMPANY_HEIGHT = 30
DETAILS_HEIGHT = 20
NAME_HEIGHT = HEIGHT - COMPANY_HEIGHT - (DETAILS_HEIGHT * 2) - 2

COMPANY_TEXT_SIZE = 0.6
DETAILS_TEXT_SIZE = 0.5
LEFT_PADDING = 5
NAME_PADDING = 20
DETAIL_SPACING = 10

BADGE_DIR = "/badges"
DEFAULT_TEXT = """mustelid inc
H. Badger
RP2040
2MB Flash
E ink
296x128px
/badges/badge.jpg
"""

display = badger2040.Badger2040()
display.led(128)
display.set_update_speed(badger2040.UPDATE_NORMAL)
display.set_thickness(2)

jpeg = jpegdec.JPEG(display.display)
png = pngdec.PNG(display.display)


def list_badges():
    try:
        names = sorted(f for f in os.listdir(BADGE_DIR) if f.endswith(".txt"))
    except OSError:
        os.mkdir(BADGE_DIR)
        names = []
    if not names:
        with open("{}/badge.txt".format(BADGE_DIR), "w") as f:
            f.write(DEFAULT_TEXT)
        names = ["badge.txt"]
    return names


badges = list_badges()

state = {"index": 0}
badger_os.state_load("badge", state)
state["index"] %= len(badges)


# Trim a string until it fits the given width
def truncatestring(text, text_size, width):
    while text and display.measure_text(text, text_size) > width:
        text = text[:-1]
    return text


def read_badge(name):
    with open("{}/{}".format(BADGE_DIR, name), "r") as f:
        lines = [f.readline().strip() for _ in range(7)]
    return lines


def draw_image(path):
    """Draw the badge photo. Returns the width left over for text."""
    if not path:
        return WIDTH - 1
    for lib in (png, jpeg):
        try:
            lib.open_file(path)
            lib.decode(WIDTH - IMAGE_WIDTH, 0)
            break
        except (OSError, RuntimeError):
            continue
    else:
        # No usable image - hand the space back to the text
        return WIDTH - 1

    display.set_pen(0)
    display.line(WIDTH - IMAGE_WIDTH, 0, WIDTH - 1, 0)
    display.line(WIDTH - IMAGE_WIDTH, 0, WIDTH - IMAGE_WIDTH, HEIGHT - 1)
    display.line(WIDTH - IMAGE_WIDTH, HEIGHT - 1, WIDTH - 1, HEIGHT - 1)
    display.line(WIDTH - 1, 0, WIDTH - 1, HEIGHT - 1)
    return WIDTH - IMAGE_WIDTH - 1


def draw_page_dots(count, current):
    if count < 2:
        return
    for i in range(count):
        # Drawn over the white name panel, so filled = current
        x, y = 3, int((HEIGHT / 2) - (count * 10 / 2) + (i * 10))
        display.set_pen(0)
        display.rectangle(x, y, 6, 6)
        if i != current:
            display.set_pen(15)
            display.rectangle(x + 1, y + 1, 4, 4)


def draw_badge():
    company, name, d1_title, d1_text, d2_title, d2_text, image = read_badge(badges[state["index"]])

    display.set_pen(0)
    display.clear()

    text_width = draw_image(image)

    company = truncatestring(company, COMPANY_TEXT_SIZE, text_width)
    d1_title = truncatestring(d1_title, DETAILS_TEXT_SIZE, text_width)
    d1_text = truncatestring(d1_text, DETAILS_TEXT_SIZE,
                             text_width - DETAIL_SPACING - display.measure_text(d1_title, DETAILS_TEXT_SIZE))
    d2_title = truncatestring(d2_title, DETAILS_TEXT_SIZE, text_width)
    d2_text = truncatestring(d2_text, DETAILS_TEXT_SIZE,
                             text_width - DETAIL_SPACING - display.measure_text(d2_title, DETAILS_TEXT_SIZE))

    # Company, knocked out of the black bar at the top
    display.set_pen(15)
    display.set_font("serif")
    display.text(company, LEFT_PADDING, (COMPANY_HEIGHT // 2) + 1, WIDTH, COMPANY_TEXT_SIZE)

    # Name, scaled down until it fits
    display.set_pen(15)
    display.rectangle(1, COMPANY_HEIGHT + 1, text_width, NAME_HEIGHT)
    display.set_pen(0)
    display.set_font("sans")
    name_size = 2.0
    while True:
        name_length = display.measure_text(name, name_size)
        if name_length >= (text_width - NAME_PADDING) and name_size >= 0.1:
            name_size -= 0.01
        else:
            display.text(name, (text_width - name_length) // 2,
                         (NAME_HEIGHT // 2) + COMPANY_HEIGHT + 1, WIDTH, name_size)
            break

    # Two detail rows
    display.set_pen(15)
    display.rectangle(1, HEIGHT - DETAILS_HEIGHT * 2, text_width, DETAILS_HEIGHT - 1)
    display.rectangle(1, HEIGHT - DETAILS_HEIGHT, text_width, DETAILS_HEIGHT - 1)
    display.set_pen(0)
    title_length = display.measure_text(d1_title, DETAILS_TEXT_SIZE)
    display.text(d1_title, LEFT_PADDING, HEIGHT - ((DETAILS_HEIGHT * 3) // 2), WIDTH, DETAILS_TEXT_SIZE)
    display.text(d1_text, LEFT_PADDING + title_length + DETAIL_SPACING,
                 HEIGHT - ((DETAILS_HEIGHT * 3) // 2), WIDTH, DETAILS_TEXT_SIZE)
    title_length = display.measure_text(d2_title, DETAILS_TEXT_SIZE)
    display.text(d2_title, LEFT_PADDING, HEIGHT - (DETAILS_HEIGHT // 2), WIDTH, DETAILS_TEXT_SIZE)
    display.text(d2_text, LEFT_PADDING + title_length + DETAIL_SPACING,
                 HEIGHT - (DETAILS_HEIGHT // 2), WIDTH, DETAILS_TEXT_SIZE)

    draw_page_dots(len(badges), state["index"])
    display.update()


draw_badge()

while True:
    display.keepalive()

    changed = False
    if display.pressed(badger2040.BUTTON_UP):
        state["index"] = (state["index"] - 1) % len(badges)
        changed = True
    if display.pressed(badger2040.BUTTON_DOWN):
        state["index"] = (state["index"] + 1) % len(badges)
        changed = True

    if changed:
        badger_os.state_save("badge", state)
        draw_badge()

    display.halt()
