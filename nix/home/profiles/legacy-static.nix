{
  lib,
  pkgs,
  profile,
  ...
}:
let
  capabilities = import ../../lib/profiles.nix { inherit profile; };

  runtimeConfigPaths = [
    "nvim/lua/plugins/colorscheme.lua"
    "VSCodium/User/settings.json"
  ]
  ++ lib.optionals (configEnabled "qtile") [
    "qtile/firefox_themes/firefox_theme.json"
    "qtile/json/config.json"
  ]
  ++ lib.optionals (configEnabled "qtile-wl") [
    "qtile-wl/firefox_themes/firefox_theme.json"
    "qtile-wl/json/config.json"
  ];

  staticSourceFilter =
    path: type:
    let
      name = builtins.baseNameOf path;
      pathString = toString path;
      isRuntimeConfig = lib.any (relative: lib.hasSuffix "/${relative}" pathString) runtimeConfigPaths;
    in
    type == "directory"
    || (
      !isRuntimeConfig
      && !lib.hasSuffix ".tmpl" name
      && !lib.hasPrefix "encrypted_" name
      && !lib.hasSuffix ".log" name
      && name != "focus_history.json"
    );

  staticConfigSource = builtins.path {
    path = ../../../dot_config;
    name = "dots-static-config-source";
    filter = staticSourceFilter;
  };

  staticBinSource = builtins.path {
    path = ../../../bin;
    name = "dots-static-bin-source";
    filter = staticSourceFilter;
  };

  staticConfig = pkgs.runCommand "dots-static-config" { } ''
    mkdir -p "$out"
    cp -R ${staticConfigSource}/. "$out/"
  '';

  staticBin = pkgs.runCommand "dots-static-bin" { } ''
    mkdir -p "$out"
    cp -R ${staticBinSource}/. "$out/"
  '';

  renderedBinSources = import ../../lib/rendered-bin.nix {
    inherit lib pkgs profile;
  };

  configEntries = builtins.readDir ../../../dot_config;
  binEntries = builtins.readDir ../../../bin;

  chezmoiOwnedConfigEntries = [
    "Code"
    "Code - OSS"
    "git"
    "lazygit"
    "nvim"
    "qtile"
    "qtile-wl"
    "rofi"
    "spicetify"
    "tmux"
    "zsh"
  ];

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

  configEnabled =
    name:
    !lib.hasSuffix ".tmpl" name
    && !builtins.elem name chezmoiOwnedConfigEntries
    && (name != "qtile-wl" || profile == "lenovo")
    && (name != "conky" || profile == "cloudtop")
    && (name != "lf" || capabilities.isLinux)
    && (name != "systemd" || capabilities.isServer)
    && (isDesktopLinux || !builtins.elem name desktopConfigEntries);

  binTarget = name: lib.removeSuffix ".tmpl" (lib.removePrefix "executable_" name);

  binEnabled =
    name:
    let
      target = binTarget name;
    in
    lib.hasPrefix "executable_" name
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
        source =
          if builtins.hasAttr name renderedBinSources then
            renderedBinSources.${name}
          else
            "${staticBin}/${name}";
        executable = true;
      };
    }) (lib.filter binEnabled (builtins.attrNames binEntries))
  );

  sshFiles = {
    ".ssh/config".source = ../../../private_dot_ssh/config;
    ".ssh/config.d/archnet".source = ../../../private_dot_ssh/config.d/archnet;
  }
  // lib.optionalAttrs (!capabilities.isServer) {
    ".ssh/config.d/hetzner".source = ../../../private_dot_ssh/config.d/hetzner;
  };
in
{
  xdg.configFile = configFiles;

  home.activation.initializeVSCodiumSettings = lib.mkIf isDesktopLinux (
    lib.hm.dag.entryBefore [ "linkGeneration" ] ''
      settings_file="$HOME/.config/VSCodium/User/settings.json"
      if [[ ! -e "$settings_file" && ! -L "$settings_file" ]]; then
        settings_dir=$(dirname -- "$settings_file")
        $DRY_RUN_CMD mkdir -p -- "$settings_dir"
        if [[ -z ''${DRY_RUN:-} ]]; then
          settings_temporary=$(${pkgs.coreutils}/bin/mktemp \
            "$settings_dir/.settings.json.XXXXXX")
          ${pkgs.coreutils}/bin/install -m 0600 \
            ${../defaults/vscodium-settings.jsonc} "$settings_temporary"
          if ! ${pkgs.coreutils}/bin/ln -- "$settings_temporary" "$settings_file"; then
            if [[ ! -e "$settings_file" && ! -L "$settings_file" ]]; then
              ${pkgs.coreutils}/bin/rm -f -- "$settings_temporary"
              exit 1
            fi
          fi
          ${pkgs.coreutils}/bin/rm -f -- "$settings_temporary"
        fi
      fi
    ''
  );

  home.file =
    binFiles
    // sshFiles
    // {
      ".jq".source = ../../../dot_jq;
      ".local/share/zsh/completions" = {
        source = ../../../private_dot_local/private_share/zsh/completions;
        recursive = true;
      };
    };
}
