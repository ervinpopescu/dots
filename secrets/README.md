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
when `secrets/lenovo.yaml` exists. It creates the rendered settings file with
mode `0600` only when no settings file already exists; an existing file is
preserved rather than overwritten. The password is never written to the Nix
store or repository in plaintext. Follow the deliberate-cutover and
verification steps in the [Nix operations runbook](../markdown/nix-operations.md).
