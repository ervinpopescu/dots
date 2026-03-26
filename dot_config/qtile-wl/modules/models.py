from typing import Dict, List, Optional

from pydantic import BaseModel

class Commands(BaseModel):
    blueman: List[str]
    emoji: List[str]
    htop: List[str]
    lock: List[str]
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
    label: str
    layout: str
    screen_affinity: int

class WidgetDefaults(BaseModel):
    font: str
    fontsize: int
    padding: int

class Settings(BaseModel):
    bar_height: int
    cmds: Commands
    dropdown_opacity: float
    font_size: int
    keymaps: Keymaps
    groups: Dict[str, Group]
    icon_font: str
    icon_fontsize: int
    margin_size: int
    text_font: str
    openweather_api_key: Optional[str] = None
    theme: str
    widget_defaults: WidgetDefaults
