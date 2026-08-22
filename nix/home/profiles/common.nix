{
  hmTools,
  lib,
  pkgs,
  profile,
  ...
}:
let
  capabilities = import ../../lib/profiles.nix { inherit profile; };
in
{
  home.stateVersion = "25.11";
  programs.home-manager.enable = true;

  home.packages =
    with pkgs;
    [
      bash
      bat
      curl
      eza
      fd
      fzf
      git
      git-lfs
      hmTools.preflight
      hmTools.restoreCollisions
      hmTools.switchCommand
      jq
      ripgrep
      tmux
      wget
      zsh
    ]
    ++ lib.optionals (capabilities.hasBattery && capabilities.isLinux) [ acpi ]
    ++ lib.optionals capabilities.isServer [ openssh ]
    ++ lib.optionals capabilities.isMacbook [ hmTools.darwinSwitchCommand ];

  home.activation.checkLinkTargets = lib.mkForce (
    lib.hm.dag.entryBefore [ "writeBoundary" ] ''
      function checkNewGenCollision() {
        local newGenFiles
        newGenFiles="$(readlink -e "$newGenPath/home-files")"
        find "$newGenFiles" \( -type f -or -type l \) \
          -exec ${hmTools.checkCollisions}/bin/hm-check-collisions "$newGenFiles" {} +
      }

      checkNewGenCollision || exit 1
    ''
  );

  home.activation.protectLinkTargets =
    lib.hm.dag.entryBetween [ "linkGeneration" ] [ "writeBoundary" ]
      ''
        export HM_LINK_ORIGINAL_PATH="$PATH"
        export HM_LINK_ACTIVATION_ID="hm-link-$(${pkgs.coreutils}/bin/date +%s)-$$-$RANDOM-$RANDOM"
        export PATH=${hmTools.safeLink}/bin:${hmTools.safeRemove}/bin:$PATH
      '';

  home.activation.restoreLinkCommand = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    export PATH="$HM_LINK_ORIGINAL_PATH"
    ${pkgs.coreutils}/bin/rm -rf -- \
      "''${XDG_STATE_HOME:-$HOME/.local/state}/home-manager/collision-backups/link-guards/$HM_LINK_ACTIVATION_ID"
    if [[ -z ''${DRY_RUN:-} ]]; then
      managed_state="''${XDG_STATE_HOME:-$HOME/.local/state}/home-manager/collision-backups/active-managed-generation"
      ${pkgs.coreutils}/bin/mkdir -p -- "$(${pkgs.coreutils}/bin/dirname -- "$managed_state")"
      managed_state_temporary="$managed_state.$$"
      printf '%s\0' "$newGenPath" >"$managed_state_temporary"
      ${pkgs.coreutils}/bin/mv -f -- "$managed_state_temporary" "$managed_state"
    fi
    unset HM_LINK_ACTIVATION_ID HM_LINK_ORIGINAL_PATH
  '';

  home.activation.deferCollisionRestoration = lib.mkIf (!capabilities.isMacbook) (
    lib.hm.dag.entryAfter [ "restoreLinkCommand" ] ''
      $DRY_RUN_CMD ${hmTools.restoreCollisions}/bin/hm-restore-backups \
        --forward "''${oldGenPath:-}" "$newGenPath" "$newGenPath"
    ''
  );

  home.sessionVariables = {
    EDITOR = "nvim";
    VISUAL = "nvim";
  };
}
