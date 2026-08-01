# Snake. Walls are fatal, tail is fatal.
#
#   UP/DOWN  up/down    A  left    C  right    B  start / restart    A+C  quit
import random

CELL = 8
HEADER = 10
COLS = 296 // CELL
ROWS = (128 - HEADER) // CELL

UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)


def move(snake, direction, food, cols, rows):
    """Advance the snake one cell.

    snake is a list of (x, y), head first. Returns (snake, ate, dead);
    the returned snake is a new list and is left untouched when dead.
    """
    head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
    if not (0 <= head[0] < cols and 0 <= head[1] < rows):
        return snake, False, True
    ate = head == food
    body = snake if ate else snake[:-1]
    if head in body:
        return snake, False, True
    return [head] + body, ate, False


def place_food(snake, cols, rows, rand=random.randrange):
    free = [(x, y) for y in range(rows) for x in range(cols) if (x, y) not in snake]
    if not free:
        return None
    return free[rand(len(free))]


# --- hardware below ---
import badger2040
import badger_os


display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_TURBO)
display.set_font("bitmap8")

state = {"high": 0}
badger_os.state_load("snake", state)

snake = []
food = None
direction = RIGHT
score = 0
playing = False


def new_game():
    global snake, food, direction, score, playing
    snake = [(4, ROWS // 2), (3, ROWS // 2), (2, ROWS // 2)]
    direction = RIGHT
    food = place_food(snake, COLS, ROWS)
    score = 0
    playing = True


def cell(x, y):
    display.rectangle(x * CELL, HEADER + y * CELL, CELL - 1, CELL - 1)


def render(message=None):
    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    for x, y in snake:
        cell(x, y)
    if food:
        display.rectangle(food[0] * CELL + 2, HEADER + food[1] * CELL + 2, CELL - 5, CELL - 5)
    display.rectangle(0, 0, 296, HEADER)
    display.set_pen(15)
    display.text("score {}   best {}".format(score, state["high"]), 3, 1, 296, 1.0)

    if message:
        display.set_pen(15)
        display.rectangle(38, 34, 220, 62)
        display.set_pen(0)
        display.rectangle(40, 36, 216, 58)
        display.set_pen(15)
        display.text(message, 50, 46, 216, 1.0)
        display.text("B to play", 50, 62, 216, 1.0)
        display.text("A+C exit", 50, 78, 216, 1.0)
    display.update()


new_game()
playing = False
render("Snake")

while True:
    display.keepalive()

    if display.pressed(badger2040.BUTTON_B):
        new_game()
        render()
        continue

    if not playing:
        display.halt()
        continue

    # Ignore reversals - they would eat the neck instantly
    if display.pressed(badger2040.BUTTON_UP) and direction != DOWN:
        direction = UP
    elif display.pressed(badger2040.BUTTON_DOWN) and direction != UP:
        direction = DOWN
    elif display.pressed(badger2040.BUTTON_A) and direction != RIGHT:
        direction = LEFT
    elif display.pressed(badger2040.BUTTON_C) and direction != LEFT:
        direction = RIGHT

    snake, ate, dead = move(snake, direction, food, COLS, ROWS)

    if dead:
        playing = False
        if score > state["high"]:
            state["high"] = score
            badger_os.state_save("snake", state)
        render("Game over - {}".format(score))
        continue

    if ate:
        score += 1
        food = place_food(snake, COLS, ROWS)

    render()
