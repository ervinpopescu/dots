from libqtile import bar
from libqtile.config import Output, Screen

from modules.settings import bar_bg, settings
from modules.widgets import build_widget_lists

bh = settings.bar_height
ms = settings.margin_size

# Identifiers for the three connected displays (from wlr-randr).
# Update these if the physical setup changes.
PORT_INTERNAL = "eDP-1"  # Lenovo internal display (no serial)
SERIAL_DP = "CN41010NQC"  # HP E23 G4 on DP-2
SERIAL_HDMI = "CN410825SN"  # HP E23 G4 on HDMI-A-1


def statusbar(widgets, margin, size):
    return bar.Bar(
        widgets,
        size=size,
        margin=margin,
        background=bar_bg,
    )


def _primary_screen(widgets):
    return Screen(
        bottom=statusbar(
            widgets=widgets,
            size=bh,
            margin=[0, ms, ms, ms],
        ),
    )


def _secondary_screen(widgets):
    return Screen(
        bottom=statusbar(
            widgets=widgets,
            size=bh * 2 // 3,
            margin=[0, ms - 5, ms - 5, ms - 5],
        ),
    )


def generate_screens(outputs: list[Output]) -> list[Screen]:
    """Return a Screen per connected output, matched by port/serial.

    Screen ordering:
      0 — eDP-1     (internal, full bar)
      1 — DP-2      (CN41010NQC, smaller bar)
      2 — HDMI-A-1  (CN410825SN, smaller bar)

    Unknown outputs (projectors, new monitors) get a secondary bar appended
    after the known screens.
    """
    w1, w2, w3 = build_widget_lists()
    result: list[Screen] = []

    # Internal screen first (screen 0)
    if any(o.port == PORT_INTERNAL for o in outputs):
        result.append(_primary_screen(w1))

    # DP-2 second (screen 1)
    if any(o.serial == SERIAL_DP for o in outputs):
        result.append(_secondary_screen(w2))

    # HDMI-A-1 third (screen 2)
    if any(o.serial == SERIAL_HDMI for o in outputs):
        result.append(_secondary_screen(w3))

    # Unknown outputs: append a secondary bar (e.g. projector, new monitor)
    for o in outputs:
        if o.port != PORT_INTERNAL and o.serial not in (SERIAL_DP, SERIAL_HDMI):
            result.append(_secondary_screen(w2))

    # Guard: always return at least one screen
    if not result:
        result.append(_primary_screen(w1))

    return result
