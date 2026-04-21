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


def _primary_screen(widgets):
    return Screen(
        bottom=statusbar(
            widgets=widgets,
            size=bh,
            margin=[0, ms, ms, ms],
        ),
        x11_drag_polling_rate=60,
    )


def _secondary_screen(widgets):
    return Screen(
        bottom=statusbar(
            widgets=widgets,
            size=bh,
            margin=[0, ms, ms, ms],
        ),
        x11_drag_polling_rate=60,
    )


def generate_screens(outputs: list[Output]) -> list[Screen]:
    """Return one Screen per connected output.

    Outputs are sorted left-to-right by x-coordinate; the leftmost display
    becomes screen 0 (primary bar with Systray). Remaining outputs receive
    secondary bars without Systray, since X11 only allows one per session.
    """
    w1, w2, w3 = build_widget_lists()
    secondary_widgets = [w2, w3]
    result: list[Screen] = []

    for i, _o in enumerate(sorted(outputs, key=lambda o: o.rect.x)):
        if i == 0:
            result.append(_primary_screen(w1))
        else:
            result.append(
                _secondary_screen(secondary_widgets[min(i - 1, len(secondary_widgets) - 1)])
            )

    return result if result else [_primary_screen(w1)]
