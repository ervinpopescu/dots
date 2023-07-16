import os

from xdg.IconTheme import getIconPath

from qtile_extras import widget


class LaunchBar(widget.LaunchBar):
    defaults = [
        (
            "theme_path",
            None,
            "Path to icon theme to be used by pyxdg for icons. ``None`` will use default icon theme.",
        ),
    ]

    def __init__(self, **config):
        widget.LaunchBar.__init__(self, **config)
        self.add_defaults(LaunchBar.defaults)

    def _lookup_icon(self, name):
        """Search for the icon corresponding to one command."""
        self.icons_files[name] = None
        # if the software_name is directly an absolute path icon file
        if os.path.isabs(name):
            # name start with '/' thus it's an absolute path
            root, ext = os.path.splitext(name)
            if ext == ".png":
                self.icons_files[name] = name if os.path.isfile(name) else None
            else:
                # try to add the extension
                self.icons_files[name] = f"{name}.png" if os.path.isfile(f"{name}.png") else None
        else:
            self.icons_files[name] = getIconPath(name, theme=self.theme_path)
        # no search method found an icon, so default icon
        if self.icons_files[name] is None:
            self.icons_files[name] = self.default_icon
