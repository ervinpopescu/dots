from libqtile import bar
from libqtile.config import Output, Screen

from modules.settings import bar_bg, settings
from modules.widgets import build_widget_lists

bh = settings.bar_height
ms = settings.margin_size


def statusbar(widgets, margin, size):
    return bar.Bar(
        widgets,
        size=size,
        margin=margin,
        background=bar_bg,
    )


def _screen(widgets, size, margin):
    return Screen(
        bottom=statusbar(widgets=widgets, size=size, margin=margin),
        x11_drag_polling_rate=60,
    )


def generate_screens(outputs: list[Output]) -> list[Screen]:
    """Return one Screen per connected output.

    Screen ordering follows physical position (left to right by x-coordinate).
    Screen 0 gets the full primary bar (with Systray); the rest get secondary
    bars without Systray, since X11 only allows one Systray per session.
    """
    w1, w2, w3 = build_widget_lists()

    # Sort outputs by horizontal position so screen numbering is stable
    sorted_outputs = sorted(outputs, key=lambda o: o.rect.x)
    secondary_widgets = [w2, w3]

    result: list[Screen] = []
    for i, _o in enumerate(sorted_outputs):
        if i == 0:
            result.append(_screen(w1, bh, [0, ms, ms, ms]))
        else:
            sec = secondary_widgets[min(i - 1, len(secondary_widgets) - 1)]
            result.append(_screen(sec, bh, [0, ms, ms, ms]))

    return result if result else [_screen(w1, bh, [0, ms, ms, ms])]
