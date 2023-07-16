from libqtile import layout
from libqtile.config import Match

from modules.settings import layout_defaults

layouts = [
    layout.Bsp(**layout_defaults),
    layout.Max(margin=layout_defaults["margin"]),
    layout.Zoomy(
        margin=layout_defaults["margin"],
        columnwidth=500,
        property_small="1.0",
    ),
    layout.MonadWide(
        max_ratio=0.95,
        min_ratio=0.01,
        **layout_defaults,
    ),
    layout.MonadTall(
        max_ratio=0.95,
        min_ratio=0.01,
        **layout_defaults,
    ),
    layout.MonadThreeCol(
        border_width=0,
        ratio=0.33333,
        max_ratio=0.95,
        min_ratio=0.01,
        margin=layout_defaults["margin"],
    ),
    layout.Spiral(
        new_client_position="bottom",
        **layout_defaults,
    ),
    layout.Columns(
        num_columns=2,
        **layout_defaults,
    ),
]

floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="flameshot"),
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="lightdm-settings"),
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
        Match(wm_class="Pavucontrol"),
        Match(wm_class="matplotlib"),
    ],
    border_width=layout_defaults["border_width"],
    border_focus=layout_defaults["border_focus"],
    border_normal=layout_defaults["border_normal"],
)
