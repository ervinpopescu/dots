{
  config,
  lib,
  pkgs,
  ...
}:
let
  secretFile = ../../../secrets/lenovo.yaml;
  hasSecret = builtins.pathExists secretFile;
  transmissionPackage = lib.attrByPath [ "transmission_4" ] (lib.attrByPath [
    "transmission"
  ] null pkgs) pkgs;
  hasTransmission = transmissionPackage != null;
  transmissionSource = builtins.readFile ../../data/transmission-settings.json;
  transmissionSettings =
    lib.replaceStrings
      [ "__TRANSMISSION_RPC_PASSWORD__" ]
      [ config.sops.placeholder."transmission/rpc-password" ]
      transmissionSource;
in
{
  imports = [ ./desktop.nix ];

  home.packages = lib.optional hasTransmission transmissionPackage;

  sops = lib.optionalAttrs hasSecret {
    age.keyFile = "${config.home.homeDirectory}/.config/sops/age/keys.txt";
    secrets."transmission/rpc-password" = {
      sopsFile = secretFile;
    };
    templates."transmission-settings.json" = {
      content = transmissionSettings;
      mode = "0600";
    };
  };

  home.file = lib.mkIf hasSecret {
    ".config/transmission-daemon/settings.json".source =
      config.lib.file.mkOutOfStoreSymlink
        config.sops.templates."transmission-settings.json".path;
  };

  systemd.user.services.transmission = lib.mkIf (hasSecret && hasTransmission) {
    Unit = {
      Description = "Transmission daemon";
      After = [ "network-online.target" ];
    };
    Service = {
      ExecStart = "${transmissionPackage}/bin/transmission-daemon --foreground --config-dir=%h/.config/transmission-daemon";
      Restart = "on-failure";
      RestartSec = 5;
    };
    Install.WantedBy = [ "default.target" ];
  };
}
