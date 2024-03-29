import pathlib

from libqtile import qtile
from libqtile.core.manager import Qtile

qtile: Qtile

qtile_info = qtile.qtile_info()
if len(qtile_info) != 0:
    config_path = str(pathlib.Path(qtile_info["config_path"]).parent.resolve())
else:
    config_path = str(pathlib.Path(__file__).parent.parent.resolve())
