from modules.theme import colors

apps = [
    (("nemo",) * 3),
    ("Alacritty", "alacritty", "alacritty"),
    (("vscodium",) * 3),
    (("firefox",) * 3),
    (("virtualbox",) * 3),
]

# Keys
cmds = dict(
    mod="mod4",
    alt="mod1",
    menu="rofi -modes drun -show drun -terminal alacritty -show-icons".split(),
    terminal="alacritty",
    update="alacritty -o font.size=10 --class qtile_yay_update --hold -e yay -Syyu --noconfirm".split(),
    nwgbar="nwgbar -b 1d1d2d -o 0.4".split(),
    htop="alacritty --class htop -o 'font.size=10' -e htop".split(),
    transmission="alacritty -o font.size=10 --class alacritty-transmission -e watch -c -n 1 -t transmission.py".split(),
    emoji="rofi -modes emoji -show emoji".split(),
)

# Groups
group_names = [
    "coding",
    "files",
    "www",
    "social",
    "settings",
    "etc",
    "media",
]
group_labels = [
    "",
    "",
    "",
    "",
    "",
    "",
    "",
]
group_layouts = [
    "monadwide",
    "max",
    "max",
    "max",
    "max",
    "bsp",
    "monadthreecol",
]

# Widgets
bar_bg = "00000000"
decor_bg = colors["bg0"]
bar_height: int = 56
margin_size: int = 20
text_font = "CaskaydiaCove Nerd Font Mono Bold"
icon_font = "Font Awesome 6 Free Solid"
fontsize = 30
layout_defaults = dict(
    margin=margin_size,
    border_width=5,
    border_focus=colors["purple"],
    border_normal=colors["bg0"],
)

widget_defaults = dict(
    # font="CodeNewRoman Nerd Font Mono Bold",
    font="Font Awesome 6 Free Solid",
    fontsize=30,
    padding=6,
    # background=decor_bg
)
extension_defaults = widget_defaults.copy()
