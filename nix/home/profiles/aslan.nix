{ lib, pkgs, ... }:
{
  # Aslan's root-owned runtime configuration is exposed separately through
  # systemConfigs.aslan and System Manager. Home Manager only owns ervin's
  # user environment here.

  # The kvm2 Minikube profile lives below $HOME/.local/share. QEMU runs as the
  # libvirt-qemu account and needs traversal, but not listing or read access, on
  # these otherwise-private ancestors.
  home.activation.ensureMinikubeLibvirtTraversal = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    for path in "$HOME/.local" "$HOME/.local/share"; do
      if [ -d "$path" ]; then
        $DRY_RUN_CMD ${pkgs.acl}/bin/setfacl -m u:libvirt-qemu:--x "$path"
      fi
    done
  '';
}
