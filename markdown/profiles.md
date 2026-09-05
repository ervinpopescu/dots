# Machine Profiles

The repository uses one pinned Nix flake with five Home Manager profiles. The
profile is selected by the flake output and is separate from the hostname in
some cases. Cloudtop's output uses the invoking account's existing `$HOME`,
rather than assuming a repository-controlled home path.

## Profile matrix

| Profile    | Hostname   | Platform   | Linux | Server | Wayland | Battery | Desktop behavior                         |
| ---------- | ---------- | ---------- | ----- | ------ | ------- | ------- | ---------------------------------------- |
| `lenovo`   | `lenovo`   | Arch Linux | yes   | no     | yes     | yes     | Qtile Wayland, standard DPI, 24px cursor |
| `cloudtop` | `cloudtop` | Debian     | yes   | no     | no      | no      | Qtile X11, HiDPI, 48px cursor            |
| `macbook`  | prompted   | macOS      | no    | no     | no      | yes     | Native macOS tools and Homebrew paths    |
| `hp`       | `hp`       | Linux      | yes   | no     | no      | yes     | Qtile X11, 48px cursor                   |
| `aslan`    | `aslan`    | Arch Linux | yes   | yes    | no      | no      | Headless server configuration            |

For remaining legacy chezmoi sources, `is_arch` is derived from the host
operating system rather than hardcoded to a profile; `system/arch/` applies only
when that flag is true. In the Nix ownership model, the `aslan` profile exposes
the Aslan-only `system/hetzner/` tree to System Manager, including Nginx,
monitoring, security, and systemd configuration. Transmission is Lenovo-only
and runs as a Home Manager user service.

## Detection

Flake outputs are named explicitly:

- `homeConfigurations.ervin@lenovo`
- `homeConfigurations.ervin@cloudtop` (requires `--impure`; uses `$HOME`)
- `homeConfigurations.ervin@hp`
- `homeConfigurations.ervin@aslan` (legacy profile name: `hetzner`)
- `homeConfigurations.ervin@macbook-apple-silicon`
- `darwinConfigurations.macbook-apple-silicon`
- `systemConfigs.aslan` (named build output)
- `systemConfigs.default` (Aslan-only System Manager CLI alias)

The MacBook architecture is selected by the output name. Linux hosts keep
their current distribution; Nix and Home Manager provide the user environment
without replacing the native kernel, bootloader, or package manager.

## Capability flags

Nix modules use these equivalent profile capabilities:

| Flag          | Enabled for                    |
| ------------- | ------------------------------ |
| `is_lenovo`   | `lenovo`                       |
| `is_cloudtop` | `cloudtop`                     |
| `is_macbook`  | `macbook`                      |
| `is_hp`       | `hp`                           |
| `is_server`   | `aslan`                        |
| `is_linux`    | every profile except `macbook` |
| `has_wayland` | `lenovo`                       |
| `has_battery` | `lenovo`, `macbook`, `hp`      |

Use the narrowest flag that describes the behavior. For example, use
`has_battery` for status-bar modules and `is_server` for server-only files;
do not infer server behavior from `is_linux`.

## Profile-specific exclusions

- Wayland Qtile files are included only for `lenovo`.
- GUI-heavy desktop configuration is excluded for `macbook` and `aslan`.
- Cloudtop receives its HiDPI/X11 and Apigee-specific profile. Its Home Manager
  output reads the invoking account's `$HOME` under `--impure`; it must not be
  activated as another account or with a fabricated home directory.
- Aslan receives the `system/hetzner/` runtime configuration through System
  Manager; it does not receive Transmission configuration.
- Lenovo receives the Transmission package and user service. Its RPC password
  is supplied from an encrypted `secrets/lenovo.yaml` file.
