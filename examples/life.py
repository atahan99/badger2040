# Conway's Game of Life on a wrapping (toroidal) grid.
#
#   A  run / pause      B  reseed      C  single step      A+C  quit to launcher
import random

CELL = 4
HEADER = 12
COLS = 296 // CELL
ROWS = (128 - HEADER) // CELL


def randomise(grid, cols, rows, density=4, rand=random.randrange):
    """Fill grid with roughly 1-in-`density` live cells."""
    for i in range(cols * rows):
        grid[i] = 1 if rand(density) == 0 else 0
    return grid


def step(cur, nxt, cols, rows):
    """Advance one generation. Returns the live-cell count."""
    population = 0
    for y in range(rows):
        up = ((y - 1) % rows) * cols
        mid = y * cols
        down = ((y + 1) % rows) * cols
        for x in range(cols):
            left = (x - 1) % cols
            right = (x + 1) % cols
            n = (cur[up + left] + cur[up + x] + cur[up + right]
                 + cur[mid + left] + cur[mid + right]
                 + cur[down + left] + cur[down + x] + cur[down + right])
            alive = 1 if (n == 3 or (n == 2 and cur[mid + x])) else 0
            nxt[mid + x] = alive
            population += alive
    return population


# --- hardware below ---
import binascii
import badger2040
import badger_os


display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_TURBO)
display.set_font("bitmap8")

cur = bytearray(COLS * ROWS)
nxt = bytearray(COLS * ROWS)
generation = 0
population = 0
running = False
dirty = False     # grid changed since it was last saved

# On battery a paused grid powers off with the board, and the next press is a
# fresh boot - so the grid is saved before every sleep, as hex (~4KB).
state = {"grid": "", "generation": 0}
badger_os.state_load("life", state)


def save():
    global dirty
    state["grid"] = binascii.hexlify(cur).decode()
    state["generation"] = generation
    badger_os.state_save("life", state)
    dirty = False


def reseed():
    global generation, population, dirty
    randomise(cur, COLS, ROWS)
    generation = 0
    population = sum(cur)
    dirty = True


def render():
    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    for y in range(ROWS):
        row = y * COLS
        py = HEADER + y * CELL
        for x in range(COLS):
            if cur[row + x]:
                display.rectangle(x * CELL, py, CELL - 1, CELL - 1)
    display.set_pen(0)
    display.rectangle(0, 0, 296, HEADER)
    display.set_pen(15)
    display.text("gen {}  pop {}  {}".format(generation, population,
                                             "running" if running else "paused"), 3, 2, 296, 1.0)
    display.text("A+C exit", 232, 2, 296, 1.0)
    display.update()


def advance():
    global cur, nxt, generation, population, dirty
    population = step(cur, nxt, COLS, ROWS)
    cur, nxt = nxt, cur
    generation += 1
    dirty = True


if len(state["grid"]) == COLS * ROWS * 2:
    cur = bytearray(binascii.unhexlify(state["grid"]))
    generation = state["generation"]
    population = sum(cur)
else:
    reseed()
render()

while True:
    display.keepalive()

    if display.pressed(badger2040.BUTTON_A):
        running = not running
        render()
    elif display.pressed(badger2040.BUTTON_B):
        running = False
        reseed()
        render()
    elif display.pressed(badger2040.BUTTON_C):
        running = False
        advance()
        render()

    if running:
        advance()
        render()
        if population == 0:
            running = False
            reseed()
            render()
    else:
        if dirty:
            save()
        display.halt()
