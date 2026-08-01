# Chrome's offline dinosaur, at e-ink refresh rates (~4 frames/sec).
# Hold UP to jump - taps between frames can be missed.
#
#   UP  jump / start    B  restart    A+C  quit to launcher
#
# Inspired by niutech/dino-badger2040; written from scratch so this repo
# carries no third-party code.
import random

WIDTH = 296
GROUND = 112

DINO_X = 20
DINO_W = 18
DINO_H = 24
CACTUS_W = 10
CACTUS_H = 20

# Physics is per-frame, not per-second, because the e-ink refresh sets the
# tick. Retune these if you change the update speed.
JUMP_VELOCITY = -23.0
GRAVITY = 7.0
START_SPEED = 14.0
SPEED_PER_POINT = 0.6
MAX_SPEED = 34.0


def physics(y, vy, on_ground_y):
    """One frame of ballistic motion. Returns (y, vy, on_ground)."""
    vy += GRAVITY
    y += vy
    if y >= on_ground_y:
        return on_ground_y, 0.0, True
    return y, vy, False


def overlap(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def advance_obstacles(obstacles, speed, width, rand=random.randrange):
    """Scroll obstacles left. Returns (obstacles, points scored)."""
    points = 0
    out = []
    for x in obstacles:
        x -= speed
        if x + CACTUS_W < 0:
            points += 1
        else:
            out.append(x)
    while len(out) < 2:
        furthest = max(out) if out else width
        out.append(furthest + rand(90, 190))
    return out, points


# --- hardware below ---
import badger2040
import badger_os


display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_TURBO)
display.set_font("bitmap8")

state = {"high": 0}
badger_os.state_load("dino", state)

DINO_GROUND = GROUND - DINO_H

y = DINO_GROUND
vy = 0.0
on_ground = True
obstacles = []
speed = START_SPEED
score = 0
playing = False
stride = 0


def new_game():
    global y, vy, on_ground, obstacles, speed, score, playing, stride
    y = DINO_GROUND
    vy = 0.0
    on_ground = True
    obstacles = [WIDTH + 40, WIDTH + 200]
    speed = START_SPEED
    score = 0
    stride = 0
    playing = True


def draw_dino(px, py):
    display.set_pen(0)
    display.rectangle(px, py + 8, 12, 12)          # body
    display.rectangle(px + 9, py, 9, 9)            # head
    display.set_pen(15)
    display.rectangle(px + 15, py + 3, 2, 2)       # eye, knocked out of the head
    display.set_pen(0)
    display.rectangle(px + 17, py + 6, 4, 2)       # snout
    display.rectangle(px - 6, py + 9, 7, 4)        # tail
    display.rectangle(px + 8, py + 14, 3, 5)       # arm
    if on_ground and stride % 2:
        display.rectangle(px + 1, py + 20, 4, 4)   # legs, alternating
        display.rectangle(px + 8, py + 20, 4, 2)
    else:
        display.rectangle(px + 1, py + 20, 4, 2)
        display.rectangle(px + 8, py + 20, 4, 4)


def render(message=None):
    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    display.rectangle(0, GROUND, WIDTH, 2)

    draw_dino(DINO_X, int(y))
    for x in obstacles:
        display.rectangle(int(x), GROUND - CACTUS_H, CACTUS_W, CACTUS_H)
        display.rectangle(int(x) - 4, GROUND - CACTUS_H + 6, 4, 3)
        display.rectangle(int(x) + CACTUS_W, GROUND - CACTUS_H + 10, 4, 3)

    display.text("{}   best {}".format(score, state["high"]), 3, 4, WIDTH, 1.0)

    if message:
        display.set_pen(15)
        display.rectangle(48, 34, 200, 62)
        display.set_pen(0)
        display.rectangle(50, 36, 196, 58)
        display.set_pen(15)
        display.text(message, 60, 46, 196, 1.0)
        display.text("UP to run", 60, 62, 196, 1.0)
        display.text("A+C exit", 60, 78, 196, 1.0)
    display.update()


new_game()
playing = False
render("Dino")

while True:
    display.keepalive()

    if display.pressed(badger2040.BUTTON_B):
        new_game()
        render()
        continue

    if not playing:
        if display.pressed(badger2040.BUTTON_UP):
            new_game()
            render()
        else:
            display.halt()
        continue

    if on_ground and display.pressed(badger2040.BUTTON_UP):
        vy = JUMP_VELOCITY

    y, vy, on_ground = physics(y, vy, DINO_GROUND)
    obstacles, points = advance_obstacles(obstacles, speed, WIDTH)
    score += points
    speed = min(MAX_SPEED, START_SPEED + score * SPEED_PER_POINT)
    stride += 1

    for x in obstacles:
        if overlap(DINO_X - 6, int(y), DINO_W + 6, DINO_H,
                   int(x) - 4, GROUND - CACTUS_H, CACTUS_W + 8, CACTUS_H):
            playing = False
            if score > state["high"]:
                state["high"] = score
                badger_os.state_save("dino", state)
            render("Game over - {}".format(score))
            break
    else:
        render()
