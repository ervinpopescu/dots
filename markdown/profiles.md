# Machine Profiles

The repository uses one chezmoi source tree with five profiles. The profile is
stored in `.machine`; it is separate from the hostname in some cases.

## Profile matrix

| Profile    | Hostname   | Platform   | Linux | Server | Wayland | Battery | Desktop behavior                         |
| ---------- | ---------- | ---------- | ----- | ------ | ------- | ------- | ---------------------------------------- |
| `lenovo`   | `lenovo`   | Arch Linux | yes   | no     | yes     | yes     | Qtile Wayland, standard DPI, 24px cursor |
| `cloudtop` | `cloudtop` | Arch Linux | yes   | no     | no      | no      | Qtile X11, HiDPI, 48px cursor            |
| `macbook`  | prompted   | macOS      | no    | no     | no      | yes     | Native macOS tools and Homebrew paths    |
| `hp`       | `hp`       | Linux      | yes   | no     | no      | yes     | Qtile X11, 48px cursor                   |
| `hetzner`  | `aslan`    | Arch Linux | yes   | yes    | no      | no      | Headless server configuration            |

`is_arch` is derived from the host operating system, not hardcoded to a
profile. The `hetzner` profile enables the Aslan-only `system/hetzner/` tree,
including Nginx, monitoring, security, systemd, and Transmission configuration.
The `system/arch/` tree (`pacman.conf`, `reflector.conf`) is applied only when
`is_arch` is true.

## Detection

Known hostnames are mapped automatically in `.chezmoi.toml.tmpl`:

- `lenovo` → `lenovo`
- `cloudtop` → `cloudtop`
- `hp` → `hp`
- `aslan` → `hetzner`

`macbook` has no automatic hostname mapping and is selected by the profile
prompt. Unknown hostnames also prompt for a profile. The prompt accepts:

```text
lenovo, cloudtop, macbook, hp, hetzner
```

## Capability flags

Templates can use these common data flags:

| Flag                       | Enabled for                    |
| -------------------------- | ------------------------------ |
| `is_lenovo`                | `lenovo`                       |
| `is_cloudtop`              | `cloudtop`                     |
| `is_macbook`               | `macbook`                      |
| `is_hp`                    | `hp`                           |
| `is_hetzner` / `is_server` | `hetzner`                      |
| `is_linux`                 | every profile except `macbook` |
| `has_wayland`              | `lenovo`                       |
| `has_battery`              | `lenovo`, `macbook`, `hp`      |

Use the narrowest flag that describes the behavior. For example, use
`has_battery` for status-bar modules and `is_server` for server-only files;
do not infer server behavior from `is_linux`.

## Profile-specific exclusions

- Wayland Qtile files are included only for `lenovo`.
- GUI-heavy desktop configuration is excluded for `macbook` and `hetzner`.
- Cloudtop receives the HiDPI/X11 settings and Apigee-related Neovim LSP setup.
- Aslan receives the `system/hetzner/` runtime configuration and the private
  Transmission settings template.
