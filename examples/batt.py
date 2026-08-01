# Battery meter.
#
#   A  re-read    A+C  quit to launcher
#
# Pimoroni's badger_os.get_battery_level() returns 0 on this firmware: the real
# code is still there but commented out, and it references badger2040.PIN_*
# constants the current module no longer defines. So the GPIO numbers are here
# instead, taken from the Badger 2040 (non-W) pinout and checked on hardware.

BATTERY = 29        # ADC3, battery voltage through a /3 divider
VREF_1V24 = 28      # ADC2, the 1.24V reference
VREF_POWER = 27     # drives the reference on
VBUS_DETECT = 24    # high when USB is supplying power

# 2xAAA alkaline: ~3.1V fresh, and the board browns out around 2.0V. Nudge
# these if your pack reads full or flat sooner than it should - cells vary and
# so does the divider.
FULL_V = 3.0
EMPTY_V = 2.0
CAL = 1.0           # scale the reading if it is consistently off


def percentage(volts, empty=EMPTY_V, full=FULL_V):
    """Volts to 0-100, clamped. Linear is wrong for alkalines but honest:
    a fancier curve would just be a different kind of wrong."""
    if full <= empty:
        return 0
    pct = (volts - empty) / (full - empty) * 100
    return int(max(0, min(100, pct)))


# --- hardware below ---
import machine
import time
import badger2040

display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_FAST)
display.set_font("bitmap8")

WIDTH = badger2040.WIDTH


def read_volts():
    """Returns (battery volts, supply volts). The reference is powered only
    while measuring - leaving it on drains the very thing being measured."""
    vref_en = machine.Pin(VREF_POWER, machine.Pin.OUT)
    vref_en.value(1)
    time.sleep(0.05)
    try:
        vref = machine.ADC(VREF_1V24).read_u16()
        raw = machine.ADC(BATTERY).read_u16()
    finally:
        vref_en.value(0)
    if not vref:
        return 0.0, 0.0
    vdd = 1.24 * (65535 / vref)
    return (raw / 65535) * 3 * vdd * CAL, vdd


def on_usb():
    return machine.Pin(VBUS_DETECT, machine.Pin.IN).value() == 1


def render():
    volts, vdd = read_volts()
    usb = on_usb()
    pct = percentage(volts)

    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    display.rectangle(0, 0, WIDTH, 18)
    display.set_pen(15)
    display.text("BATTERY", 5, 5, WIDTH, 1.0)
    display.text("A+C exit", WIDTH - 70, 5, WIDTH, 1.0)

    display.set_pen(0)
    if usb:
        # On USB the pack is disconnected or switched off, so the reading is
        # of nothing in particular. Saying "USB" beats showing a fake 0%.
        display.text("On USB power", 20, 40, WIDTH, 2.0)
        display.text("Unplug to measure the battery", 20, 70, WIDTH, 1.0)
        display.text("supply {:.2f}V".format(vdd), 20, 88, WIDTH, 1.0)
    else:
        display.text("{}%".format(pct), 20, 36, WIDTH, 3.0)
        display.text("{:.2f}V".format(volts), 150, 46, WIDTH, 2.0)
        # Battery outline with a nub, filled to the charge level
        display.rectangle(20, 84, 220, 24)
        display.set_pen(15)
        display.rectangle(22, 86, 216, 20)
        display.set_pen(0)
        display.rectangle(22, 86, int(216 * pct / 100), 20)
        display.rectangle(240, 91, 6, 10)
        display.text("A re-read", 20, 114, WIDTH, 1.0)
    display.update()


render()

while True:
    display.keepalive()
    if display.pressed(badger2040.BUTTON_A):
        render()
    display.halt()
