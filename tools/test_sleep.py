#!/usr/bin/env python3
"""Put apps through a sleep/wake cycle on the desktop:  python3 tools/test_sleep.py

On battery, halt() powers the badge off and the next button press boots it from
scratch, so anything an app keeps only in memory is gone. These tests fake just
enough of badger2040 and badger_os to boot an app with some saved state and a
wake button, run it until it halts, then check what it saved and how often it
refreshed the screen.
"""
import binascii
import json
import os
import sys
import time
import types

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
BUTTONS = {"BUTTON_A": 12, "BUTTON_B": 13, "BUTTON_C": 14, "BUTTON_UP": 15, "BUTTON_DOWN": 11}


class Halt(Exception):
    """The badge powered off."""


def boot(app, saved=None, wake=None):
    """Boot examples/<app>.py once, woken by button `wake` (None = power-on).

    Returns (app globals, saved state per app, number of screen refreshes).
    `saved` is updated in place, so it can be passed to the next boot.
    """
    saved = {} if saved is None else saved
    pending = {BUTTONS[wake]} if wake else set()
    refreshes = []

    class Badger2040:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None      # drawing is a no-op

        def measure_text(self, text, scale=1.0, *args):
            return int(len(text) * 6 * scale)

        def update(self):
            refreshes.append(1)

        def pressed(self, button):
            # Like pressed_to_wake_get_once: the wake press is seen once
            if button in pending:
                pending.discard(button)
                return True
            return False

        def pressed_any(self):
            return False

        def halt(self):
            raise Halt

    badger2040 = types.ModuleType("badger2040")
    badger2040.__dict__.update(BUTTONS, WIDTH=296, HEIGHT=128, Badger2040=Badger2040,
                               UPDATE_NORMAL=0, UPDATE_MEDIUM=1, UPDATE_FAST=2, UPDATE_TURBO=3,
                               woken_by_button=lambda: wake is not None)

    badger_os = types.ModuleType("badger_os")
    badger_os.state_load = lambda name, data: data.update(json.loads(saved.get(name, "{}")))
    badger_os.state_save = lambda name, data: saved.__setitem__(name, json.dumps(data))

    fake_time = types.ModuleType("time")
    fake_time.__dict__.update(vars(time), ticks_ms=lambda: 0, ticks_us=lambda: 0,
                              ticks_diff=lambda a, b: a - b)

    fakes = {"badger2040": badger2040, "badger_os": badger_os, "time": fake_time}
    real = {name: sys.modules.get(name) for name in fakes}
    sys.modules.update(fakes)
    path = os.path.join(ROOT, "examples", app + ".py")
    namespace = {"__name__": app}
    try:
        with open(path) as f:
            exec(compile(f.read(), path, "exec"), namespace)
    except Halt:
        pass
    else:
        raise AssertionError("{} returned without halting".format(app))
    finally:
        for name, module in real.items():
            if module is None:
                del sys.modules[name]
            else:
                sys.modules[name] = module
    return namespace, saved, len(refreshes)


def state(saved, app):
    return json.loads(saved[app])


def test_2048_keeps_the_board():
    board = [2, 2, 0, 0] + [0] * 12
    saved = {"p2048": json.dumps({"high": 0, "board": board, "score": 0})}
    app, saved, _ = boot("p2048", saved, wake="BUTTON_A")
    assert app["board"][0] == 4 and app["score"] == 4, "the saved board was not loaded"
    assert state(saved, "p2048")["board"] == app["board"], "the move was not saved"

    app, saved, _ = boot("p2048", {})
    assert sum(1 for v in state(saved, "p2048")["board"] if v) == 2, "a new game is saved straight away"


def test_timer_keeps_its_place():
    _, saved, _ = boot("timer", wake="BUTTON_C")          # skip work -> break
    assert state(saved, "timer")["step"] == 1

    app, saved, _ = boot("timer", saved)                  # power-on
    assert app["name"] == "break", "the phase was lost across a sleep"

    saved["timer"] = json.dumps({"work_minutes": 25, "pomodoros": 0, "step": 0, "left": 754.5})
    app, _, _ = boot("timer", saved)
    assert app["left"] == 754.5, "a paused timer lost its remaining time"


def test_life_keeps_the_grid():
    probe, _, _ = boot("life")
    cols, rows = probe["COLS"], probe["ROWS"]
    grid = bytearray(cols * rows)
    for x in (10, 11, 12):                                 # horizontal blinker
        grid[5 * cols + x] = 1
    saved = {"life": json.dumps({"grid": binascii.hexlify(grid).decode(), "generation": 7})}

    _, saved, _ = boot("life", saved, wake="BUTTON_C")    # single step
    after = binascii.unhexlify(state(saved, "life")["grid"])
    live = {(i % cols, i // cols) for i, v in enumerate(after) if v}
    assert live == {(11, 4), (11, 5), (11, 6)}, "C should step the saved grid, not reseed"
    assert state(saved, "life")["generation"] == 8


def test_one_refresh_per_press():
    """E-ink refreshes are slow and cost battery: a wake press draws once."""
    for app, button in (("count", "BUTTON_A"), ("dice", "BUTTON_A"), ("p2048", "BUTTON_A"),
                        ("timer", "BUTTON_C"), ("life", "BUTTON_C")):
        _, _, refreshes = boot(app, wake=button)
        assert refreshes == 1, "{} refreshed {} times for one press".format(app, refreshes)
        _, _, refreshes = boot(app)
        assert refreshes == 1, "{} refreshed {} times on launch".format(app, refreshes)

    app, saved, _ = boot("count", wake="BUTTON_A")
    assert state(saved, "count")["counts"][0] == 1, "the wake press must still count"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok  {}".format(name))
    print("all good")
