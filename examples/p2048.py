# 2048.
#
#   UP/DOWN  up/down    A  left    C  right    B  new game    A+C  quit
import random

SIZE = 4


def slide(row):
    """Collapse one row towards index 0. Returns (row, points scored)."""
    tiles = [v for v in row if v]
    out = []
    gained = 0
    i = 0
    while i < len(tiles):
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            merged = tiles[i] * 2
            out.append(merged)
            gained += merged
            i += 2
        else:
            out.append(tiles[i])
            i += 1
    return out + [0] * (len(row) - len(out)), gained


def _lines(direction, size):
    """Yield index lists, ordered so that index 0 is the direction of travel."""
    for i in range(size):
        if direction == "L":
            yield [i * size + j for j in range(size)]
        elif direction == "R":
            yield [i * size + j for j in range(size - 1, -1, -1)]
        elif direction == "U":
            yield [j * size + i for j in range(size)]
        else:  # "D"
            yield [j * size + i for j in range(size - 1, -1, -1)]


def move(board, direction, size=SIZE):
    """Returns (new_board, points, changed)."""
    new = list(board)
    points = 0
    for line in _lines(direction, size):
        collapsed, gained = slide([board[i] for i in line])
        points += gained
        for i, value in zip(line, collapsed):
            new[i] = value
    return new, points, new != list(board)


def spawn(board, rand=random.randrange):
    empty = [i for i, v in enumerate(board) if not v]
    if not empty:
        return board
    board = list(board)
    board[empty[rand(len(empty))]] = 4 if rand(10) == 0 else 2
    return board


def stuck(board, size=SIZE):
    return not any(move(board, d, size)[2] for d in "LRUD")


def tile_shade(value):
    """15 (white) for 2, darkening by one step per doubling. int.bit_length is
    not available on every MicroPython build, hence the loop."""
    steps = 0
    while value > 2:
        value >>= 1
        steps += 1
    return max(0, 15 - steps * 2)


# --- hardware below ---
import badger2040
import badger_os

TILE = 30
GAP = 2
ORIGIN_X = 2
ORIGIN_Y = 2


display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_TURBO)
display.set_font("bitmap8")

state = {"high": 0}
badger_os.state_load("p2048", state)

board = []
score = 0
over = False


def new_game():
    global board, score, over
    board = spawn(spawn([0] * (SIZE * SIZE)))
    score = 0
    over = False


def render():
    display.set_pen(15)
    display.clear()

    for i, value in enumerate(board):
        x = ORIGIN_X + (i % SIZE) * (TILE + GAP)
        y = ORIGIN_Y + (i // SIZE) * (TILE + GAP)
        display.set_pen(0)
        display.rectangle(x, y, TILE, TILE)
        if not value:
            display.set_pen(15)
            display.rectangle(x + 1, y + 1, TILE - 2, TILE - 2)
            continue
        # Bigger tiles get darker so the board reads at a glance
        shade = tile_shade(value)
        display.set_pen(shade)
        display.rectangle(x + 1, y + 1, TILE - 2, TILE - 2)
        display.set_pen(0 if shade > 7 else 15)
        label = str(value)
        w = display.measure_text(label, 1.0)
        display.text(label, x + (TILE - w) // 2, y + TILE // 2 - 3, TILE, 1.0)

    display.set_pen(0)
    panel = ORIGIN_X + SIZE * (TILE + GAP) + 6
    display.text("2048", panel, 10, 160, 2.0)
    display.text("score", panel, 40, 160, 1.0)
    display.text(str(score), panel, 54, 160, 2.0)
    display.text("best", panel, 80, 160, 1.0)
    display.text(str(state["high"]), panel, 94, 160, 2.0)
    display.text("B: new game" if over else "A+C exit", panel, 114, 160, 1.0)
    display.update()


def apply(direction):
    global board, score, over
    board, points, changed = move(board, direction)
    if not changed:
        return
    score += points
    board = spawn(board)
    if score > state["high"]:
        state["high"] = score
        badger_os.state_save("p2048", state)
    over = stuck(board)
    render()


new_game()
render()

while True:
    display.keepalive()

    if display.pressed(badger2040.BUTTON_B):
        new_game()
        render()
    elif not over:
        if display.pressed(badger2040.BUTTON_UP):
            apply("U")
        elif display.pressed(badger2040.BUTTON_DOWN):
            apply("D")
        elif display.pressed(badger2040.BUTTON_A):
            apply("L")
        elif display.pressed(badger2040.BUTTON_C):
            apply("R")

    display.halt()
