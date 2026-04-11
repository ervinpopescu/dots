from pydantic import BaseModel, Field
from typing import List


class GtkThemeSettings(BaseModel):
    theme_name: str = Field(..., alias="Net/ThemeName")


class Commands(BaseModel):
    blueman: List[str]
    emoji: List[str]
    htop: List[str]
    menu: List[str]
    nwgbar: List[str]
    terminal: str
    dropdown_term: str
    transmission: List[str]
    update: List[str]
    wallpaper: List[str]
    browser: str


class Keymaps(BaseModel):
    mod: str
    alt: str


class Group(BaseModel):
    name: str
    label: str
    layout: str
    screen_affinity: int
    # names: List[str]


class WidgetDefaults(BaseModel):
    font: str
    fontsize: int
    padding: int


class Settings(BaseModel):
    apps: List[List[str]]
    bar_height: int
    cmds: Commands
    dropdown_opacity: float
    extension_defaults: WidgetDefaults
    font_size: int
    keymaps: Keymaps
    groups: List[Group]
    icon_font: str
    icon_fontsize: int
    margin_size: int
    text_font: str
    widget_defaults: WidgetDefaults
