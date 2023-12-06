from qtile_extras.widget.decorations import PowerLineDecoration, RectDecoration

from modules.settings import decor_bg
from modules.theme import colors

decorations = dict(
    single_decor=dict(
        decorations=[
            RectDecoration(
                colour=decor_bg,
                radius=20,
                filled=True,
                padding_y=0,
                padding_x=0,
            ),
        ],
    ),
    group_single_decor=dict(
        decorations=[
            RectDecoration(
                colour=decor_bg,
                radius=17,
                filled=True,
                padding_y=0,
                padding_x=0,
                group=True,
                clip=True,
            ),
        ],
    ),
    double_decor=dict(
        decorations=[
            RectDecoration(
                colour=colors["darkblue"],
                radius=8,
                filled=True,
                padding_y=4,
                padding_x=4,
            ),
            RectDecoration(
                colour=decor_bg,
                radius=8,
                filled=True,
                padding_y=8,
                padding_x=8,
                clip=True,
            ),
        ],
    ),
    group_double_decor=dict(
        decorations=[
            RectDecoration(
                colour=colors["darkblue"],
                radius=8,
                filled=True,
                padding_y=4,
                padding_x=4,
                group=True,
                clip=True,
            ),
            RectDecoration(
                colour=decor_bg,
                radius=8,
                filled=True,
                padding_y=8,
                padding_x=8,
                group=True,
                clip=True,
            ),
        ],
    ),
    launchbar_decor=dict(
        decorations=[
            RectDecoration(
                colour=decor_bg,
                radius=40,
                filled=True,
                padding_y=0,
                padding_x=0,
            ),
        ],
    ),
    systray_decor=dict(
        decorations=[
            RectDecoration(
                colour=decor_bg,
                radius=10,
                extrawidth=10,
                line_width=8,
                line_colour=decor_bg,
                padding_y=-3,
                padding_x=3,
                # filled=True,
            ),
        ],
    ),
    separator_decor=dict(
        decorations=[
            PowerLineDecoration(
                extrawidth=10,
                override_colour=colors["fg1"],
                override_next_colour=colors["fg2"],
                size=3,
                path="forward_slash",
            )
        ]
    ),
)
