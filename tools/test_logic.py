#!/usr/bin/env python3
"""Run the games' pure logic on the desktop:  python3 tools/test_logic.py

Each app keeps its hardware-free logic above a `# --- hardware below ---`
marker. This execs only that part, so there is nothing to keep in sync and
no badger2040 import to stub out.
"""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
MARKER = "# --- hardware below ---"


def pure(app):
    with open(os.path.join(ROOT, "examples", app + ".py")) as f:
        source = f.read()
    assert MARKER in source, "{}.py is missing the {!r} marker".format(app, MARKER)
    namespace = {}
    exec(compile(source.split(MARKER)[0], app + ".py", "exec"), namespace)
    return namespace


def test_life():
    life = pure("life")
    cols = rows = 5
    cur = bytearray(cols * rows)
    for x in (1, 2, 3):                       # horizontal blinker
        cur[2 * cols + x] = 1
    nxt = bytearray(cols * rows)

    assert life["step"](cur, nxt, cols, rows) == 3
    vertical = {(2, 1), (2, 2), (2, 3)}
    assert {(x, y) for y in range(rows) for x in range(cols) if nxt[y * cols + x]} == vertical

    back = bytearray(cols * rows)
    life["step"](nxt, back, cols, rows)
    assert back == cur, "blinker should have period 2"

    empty = bytearray(cols * rows)
    assert life["step"](empty, nxt, cols, rows) == 0

    seeded = life["randomise"](bytearray(100), 10, 10, density=1)
    assert sum(seeded) == 100, "density=1 means every cell lives"


def test_snake():
    snake = pure("snake")
    move, RIGHT, UP = snake["move"], snake["RIGHT"], snake["UP"]

    body = [(2, 1), (1, 1)]
    moved, ate, dead = move(body, RIGHT, (9, 9), 10, 10)
    assert (moved, ate, dead) == ([(3, 1), (2, 1)], False, False)

    grown, ate, dead = move(body, RIGHT, (3, 1), 10, 10)
    assert ate and not dead and grown == [(3, 1), (2, 1), (1, 1)]

    _, _, dead = move([(9, 1), (8, 1)], RIGHT, (0, 0), 10, 10)
    assert dead, "running into the right wall is fatal"

    _, _, dead = move([(0, 1), (1, 1)], snake["LEFT"], (5, 5), 10, 10)
    assert dead, "running into the left wall is fatal"

    # Coiled snake: head at (1,1), tail at (2,1)
    coil = [(1, 1), (1, 2), (2, 2), (2, 1)]
    _, _, dead = move(coil, RIGHT, (9, 9), 10, 10)
    assert not dead, "the tail vacates the square as the head arrives"
    _, _, dead = move(coil, snake["DOWN"], (9, 9), 10, 10)
    assert dead, "biting the middle of the body is fatal"

    placed = snake["place_food"]([(0, 0)], 2, 1, rand=lambda n: 0)
    assert placed == (1, 0), "food must avoid the snake"
    assert snake["place_food"]([(0, 0)], 1, 1) is None, "no free square"


def test_2048():
    game = pure("p2048")
    slide, move, stuck = game["slide"], game["move"], game["stuck"]

    assert slide([2, 2, 4, 4]) == ([4, 8, 0, 0], 12)
    assert slide([0, 0, 0, 2]) == ([2, 0, 0, 0], 0)
    assert slide([2, 0, 2, 4]) == ([4, 4, 0, 0], 4)
    assert slide([4, 4, 4, 0]) == ([8, 4, 0, 0], 8), "only one merge per tile"
    assert slide([2, 4, 8, 16]) == ([2, 4, 8, 16], 0)

    board = [2, 2, 0, 0,
             0, 0, 0, 0,
             0, 0, 0, 0,
             0, 0, 0, 0]
    left, points, changed = move(board, "L")
    assert changed and points == 4 and left[0] == 4
    right, _, _ = move(board, "R")
    assert right[3] == 4
    down, _, _ = move(board, "D")
    assert down[12] == 2 and down[13] == 2
    _, _, changed = move(right, "R")
    assert not changed, "a move that shifts nothing is not a move"

    assert not stuck([2, 4, 2, 4] * 4), "equal rows can always merge vertically"
    checker = [2, 4, 2, 4,
               4, 2, 4, 2,
               2, 4, 2, 4,
               4, 2, 4, 2]
    assert stuck(checker)

    assert game["tile_shade"](2) == 15
    assert game["tile_shade"](4) < game["tile_shade"](2)
    assert game["tile_shade"](2048) == 0

    grown = game["spawn"]([0] * 16, rand=lambda n: 0)
    assert sum(1 for v in grown if v) == 1
    assert game["spawn"]([2] * 16) == [2] * 16, "a full board cannot spawn"


def test_dino():
    dino = pure("dino")
    physics, overlap, advance = dino["physics"], dino["overlap"], dino["advance_obstacles"]

    # A jump must leave the ground, peak, and land again
    y, vy, on_ground = dino["GROUND"] - 24, dino["JUMP_VELOCITY"], False
    heights = []
    for _ in range(20):
        y, vy, on_ground = physics(y, vy, dino["GROUND"] - 24)
        heights.append(y)
        if on_ground:
            break
    assert min(heights) < dino["GROUND"] - 24, "the dino never left the ground"
    assert on_ground, "the dino never came back down"
    assert 3 <= len(heights) <= 12, "jump lasts {} frames, retune gravity".format(len(heights))

    assert overlap(0, 0, 10, 10, 5, 5, 10, 10)
    assert not overlap(0, 0, 10, 10, 10, 0, 10, 10), "touching edges do not overlap"

    obstacles, points = advance([5.0, 200.0], 10.0, 296, rand=lambda a, b: a)
    assert points == 0 and obstacles[0] == -5.0
    obstacles, points = advance([5.0, 200.0], 20.0, 296, rand=lambda a, b: a)
    assert points == 1, "an obstacle left the screen"
    assert len(obstacles) == 2, "a replacement obstacle is queued"
    assert min(obstacles[1:]) > 180, "new obstacles spawn off to the right"


def test_pomodoro():
    pom = pure("timer")
    phase_after, clock = pom["phase_after"], pom["clock"]

    assert phase_after(0, 25) == ("work", 25, True)
    assert phase_after(1, 25) == ("break", pom["SHORT_BREAK"], False)
    assert phase_after(2, 25) == ("work", 25, True)
    # Every 4th break is the long one
    assert phase_after(7, 25) == ("long break", pom["LONG_BREAK"], False)
    assert phase_after(3, 25)[0] == "break"
    assert phase_after(15, 25)[0] == "long break"

    assert clock(0) == "00:00"
    assert clock(59.9) == "00:59"
    assert clock(1500) == "25:00"
    assert clock(-5) == "00:00", "a finished timer never shows negative time"


def test_batt():
    batt = pure("batt")
    pct = batt["percentage"]

    assert pct(3.0) == 100 and pct(2.0) == 0
    assert pct(2.5) == 50, "midpoint should be half"
    assert pct(3.6) == 100, "over-full clamps, never 160%"
    assert pct(0.0) == 0, "a disconnected pack clamps, never negative"
    assert pct(2.0, empty=2.0, full=2.0) == 0, "equal bounds must not divide by zero"


def test_cheats():
    cheats = pure("cheats")
    paginate = cheats["paginate"]

    assert paginate(["a", "b", "c"], per_page=2) == [["a", "b"], ["c"]]
    assert paginate([], per_page=5) == [[]], "an empty sheet still needs one page"
    assert paginate(["a", "b"], per_page=2) == [["a", "b"]], "exact fit is one page"
    assert len(paginate(["x"] * 10, per_page=0)) == 10, "per_page 0 must not hang or divide by zero"


def test_count():
    count = pure("count")
    clamp = count["clamp"]

    assert clamp(5) == 5
    assert clamp(-1) == 0, "a tally cannot go negative"
    assert clamp(999999) == 99999, "clamped so the digits still fit the screen"


def test_dice():
    dice = pure("dice")
    face, roll = dice["face"], dice["roll"]

    assert face("coin", 1) == "heads" and face("coin", 2) == "tails"
    assert face("yes/no", 1) == "yes" and face("yes/no", 2) == "no"
    assert face("d20", 17) == "17"

    assert roll(6, rand=lambda a, b: a) == 1
    assert roll(6, rand=lambda a, b: b) == 6, "the top face must be reachable"
    # Every die's faces must map to something printable
    for label, sides in dice["DICE"]:
        for value in range(1, sides + 1):
            assert face(label, value), "{} has no face for {}".format(label, value)


def test_launcher_order():
    """The patched launcher orders pages from an ORDER list. A typo there is
    silent - the app just reappears at the end - so check the list itself."""
    import ast

    with open(os.path.join(ROOT, "launcher.py")) as f:
        tree = ast.parse(f.read())
    order = next(ast.literal_eval(node.value) for node in tree.body
                 if isinstance(node, ast.Assign)
                 and getattr(node.targets[0], "id", None) == "ORDER")

    assert len(order) == len(set(order)), "duplicate entry in ORDER"

    local = {f[:-3] for f in os.listdir(os.path.join(ROOT, "examples"))
             if f.endswith(".py")}
    stock = {"clock", "ebook", "fonts", "help", "image", "info", "list", "qrgen"}
    unknown = set(order) - local - stock
    assert not unknown, "ORDER names an app that does not exist: {}".format(unknown)
    missing = local - set(order)
    assert not missing, "app missing from ORDER, it would land on the last page: {}".format(missing)

    pages = [order[i:i + 3] for i in range(0, len(order), 3)]
    assert pages[0] == ["badge", "qrgen", "image"], "page 1 should be the essentials"
    assert pages[1] == ["dino", "life", "snake"], "page 2 should be the games"
    assert len(pages) == 6, "expected 6 pages, got {}".format(len(pages))


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok  {}".format(name))
    print("all good")
