{
  lib,
  pkgs,
  profile,
}:
let
  capabilities = import ./profiles.nix { inherit profile; };
  volctlTemplate = builtins.readFile ../../bin/executable_volctl.sh.tmpl;
  volctlParts = lib.splitString "{{- if .is_macbook }}" volctlTemplate;
  volctlBranches = lib.splitString "{{- else }}" (builtins.elemAt volctlParts 1);
  renderedVolctl =
    builtins.elemAt volctlParts 0
    + lib.replaceStrings [ "{{- end }}" ] [ "" ] (
      if capabilities.isMacbook then
        builtins.elemAt volctlBranches 0
      else
        builtins.elemAt volctlBranches 1
    );
in
{
  "executable_netspeed.sh.tmpl" = pkgs.writeText "netspeed.sh" (
    builtins.readFile ../../bin/executable_netspeed.sh.tmpl
  );
  "executable_volctl.sh.tmpl" = pkgs.writeText "volctl.sh" renderedVolctl;
  "executable_wallpaper.sh.tmpl" = pkgs.writeText "wallpaper.sh" (
    builtins.readFile ../../bin/executable_wallpaper.sh.tmpl
  );
  "executable_wallpaper-wl.sh.tmpl" = pkgs.writeText "wallpaper-wl.sh" (
    builtins.readFile ../../bin/executable_wallpaper-wl.sh.tmpl
  );
}
