{ lib, pkgs, profile, ... }:
let
  capabilities = import ../../lib/profiles.nix { inherit profile; };

  staticConfig = pkgs.runCommand "dots-static-config" { } ''
    mkdir -p "$out"
    cp -R ${../../../dot_config}/. "$out/"
    chmod -R u+w "$out"
    find "$out" -type f -name '*.tmpl' -delete
  '';

  staticBin = pkgs.runCommand "dots-static-bin" { } ''
    mkdir -p "$out"
    cp -R ${../../../bin}/. "$out/"
    chmod -R u+w "$out"
    find "$out" -type f -name '*.tmpl' -delete
  '';

  configEntries = builtins.readDir ../../../dot_config;
  binEntries = builtins.readDir ../../../bin;

  desktopConfigEntries = [
    "alacritty"
    "Code"
    "Code - OSS"
    "dunst"
    "libinput-gestures.conf"
    "md-preview"
    "nwg-launchers"
    "qtile"
    "qtile-wl"
    "rofi"
    "spicetify"
    "VSCodium"
    "X11"
    "zathura"
  ];

  desktopBinEntries = [
    "alacritty-nemo"
    "autostart.sh"
    "autostart-wl.sh"
    "birthday-notification.sh"
    "bookmarks.py"
    "bookmarkthis.py"
    "brightnessctl.sh"
    "bt-archnet.sh"
    "bt-bat.py"
    "change_theme.py"
    "check-qtile-version.sh"
    "generate_primary_wallpaper.py"
    "hide-show-bar.sh"
    "libinput-gestures-start.sh"
    "location.py"
    "lock_and_sleep.sh"
    "md-preview.py"
    "mediactl.sh"
    "mutevol.sh"
    "netspeed.sh"
    "orar.py"
    "password-window.py"
    "pkg_remove_fzf.sh"
    "qt_html.py"
    "qtilekeys.py"
    "reboot-to-win.sh"
    "rofi-wallpaper"
    "run_wall.sh"
    "run_wall_wl.sh"
    "second_display.sh"
    "start-spotify.py"
    "suspend-toggle"
    "switch_windows_in_group.py"
    "systray_profile.py"
    "tail-qtile-log.sh"
    "volctl.sh"
    "volleyball.py"
    "wallpaper.sh"
    "wallpaper-wl.sh"
    "watcher.py"
  ];

  isDesktopLinux = capabilities.isLinux && !capabilities.isServer;

  configEnabled = name:
    !lib.hasSuffix ".tmpl" name
    && (name != "qtile-wl" || profile == "lenovo")
    && (name != "conky" || profile == "cloudtop")
    && (name != "lf" || capabilities.isLinux)
    && (name != "systemd" || capabilities.isServer)
    && (isDesktopLinux || !builtins.elem name desktopConfigEntries);

  binTarget = name: lib.removePrefix "executable_" name;

  binEnabled = name:
    let
      target = binTarget name;
    in
      lib.hasPrefix "executable_" name
      && !lib.hasSuffix ".tmpl" name
      && (target != "battery-notification.py" || profile == "lenovo")
      && (target != "dismiss-keychain-prompts" || profile == "macbook")
      && (target != "send_cmd_tmux.py" || profile == "cloudtop")
      && (isDesktopLinux || !builtins.elem target desktopBinEntries);

  configFiles = lib.listToAttrs (
    map (name: {
      inherit name;
      value = {
        source = "${staticConfig}/${name}";
        recursive = configEntries.${name} == "directory";
      };
    }) (lib.filter configEnabled (builtins.attrNames configEntries))
  );

  binFiles = lib.listToAttrs (
    map (name: {
      name = "bin/${binTarget name}";
      value = {
        source = "${staticBin}/${name}";
        executable = true;
      };
    }) (lib.filter binEnabled (builtins.attrNames binEntries))
  );

  sshFiles = {
    ".ssh/config".source = ../../../private_dot_ssh/config;
    ".ssh/config.d/archnet".source = ../../../private_dot_ssh/config.d/archnet;
  } // lib.optionalAttrs (!capabilities.isServer) {
    ".ssh/config.d/hetzner".source = ../../../private_dot_ssh/config.d/hetzner;
  };
in
{
  # Static chezmoi source files are copied into the Nix store with Go templates
  # removed. Template targets are migrated separately so no unrendered .tmpl
  # file can reach the home directory.
  xdg.configFile = configFiles;

  home.file = binFiles // sshFiles // {
    ".jq".source = ../../../dot_jq;
    ".local/share/zsh/completions" = {
      source = ../../../private_dot_local/private_share/zsh/completions;
      recursive = true;
    };
  };
}
