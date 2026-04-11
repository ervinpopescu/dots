from libqtile import widget

from modules.settings import colors, settings


def chord():
    return widget.Chord(
        chords_colors={
            "launch": (colors["red"], colors["bg0"]),
        },
        font=settings.text_font,
        fontsize=settings.font_size,
        name_transform=lambda name: name.upper(),
    )
