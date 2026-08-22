{ profile }:
let
  linuxProfiles = [
    "lenovo"
    "cloudtop"
    "hp"
    "aslan"
  ];
  desktopProfiles = [
    "lenovo"
    "cloudtop"
    "hp"
    "macbook"
  ];
in
{
  isLinux = builtins.elem profile linuxProfiles;
  isServer = profile == "aslan";
  isMacbook = profile == "macbook";
  isDesktop = builtins.elem profile desktopProfiles;
  hasWayland = profile == "lenovo";
  hasBattery = builtins.elem profile [
    "lenovo"
    "macbook"
    "hp"
  ];
}
