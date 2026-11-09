# Nix secrets

Encrypted YAML files in this directory are managed with `sops-nix` and may be
committed. Plaintext files, decrypted output, age private keys, and runtime
state must never be committed.

## Lenovo Transmission secret

Create the encrypted file after installing `sops` and placing the age identity
at `~/.config/sops/age/keys.txt`:

```bash
sops secrets/lenovo.yaml
```

Add this field in the editor:

```yaml
transmission:
  rpc-password: replace-me
```

Stage or commit the encrypted file before evaluating the local flake so Git
includes it in the flake source:

```bash
git add secrets/lenovo.yaml
```

The Lenovo Home Manager profile enables the user Transmission service only
when `secrets/lenovo.yaml` exists. It installs a mode `0600` rendered settings
file through an out-of-store symlink. On the first `hm-switch`, an existing
settings path is moved into the rollback-aware collision manifest before the
managed symlink is installed; it is retained for restoration if a rollback
leaves the path unmanaged. The password is never written to the Nix store or
repository in plaintext. Follow the deliberate-cutover and verification steps
in the [Nix operations runbook](../markdown/nix-operations.md).
