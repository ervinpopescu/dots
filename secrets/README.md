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
transmission/rpc-password: replace-me
```

The Lenovo Home Manager profile enables the user Transmission service only
when `secrets/lenovo.yaml` exists. The rendered settings file is installed
with mode `0600`; the password is never written to the Nix store or the
repository in plaintext. Follow the Lenovo verification steps in the [Nix
operations runbook](../markdown/nix-operations.md).
