# Chezmoi Migration Design

## Overview

Migrate dotfiles management from per-machine git branches with `cp -alf` deployment to chezmoi with templates, age-encrypted secrets, and a single branch.

## Goals

- Eliminate branch drift between `lenovo` and `cloudtop`
- Encrypt secrets (API keys, tokens) that are currently committed in plaintext
- Automate deployment of both `$HOME` configs and system-level files (`/etc`, `/usr`)
- Make setting up a new machine a simple `chezmoi init` + `chezmoi apply` workflow

## Repository Structure

The repo root becomes the chezmoi source directory (`~/.local/share/chezmoi/`):

```
.chezmoi.toml.tmpl               # per-machine config template
.chezmoiignore                   # machine-conditional file exclusion
.chezmoiexternal.toml            # (if needed for external deps)
dot_config/
  git/                           # shared
  nvim/                          # shared
  tmux/                          # shared
  zsh/
    .zshrc                       # shared
    .zshenv                      # shared
    .zprofile.tmpl               # templated (wayland vs X11 startup)
    env/
      vars.zsh.tmpl              # templated (machine-specific vars, secrets)
      aliases.zsh                # shared
      functions.zsh              # shared
      bookmarks.zsh              # shared
      misc.zsh                   # shared
      path.zsh                   # shared
    rc/                          # shared
    files/                       # shared
    plugins/                     # shared
  qtile/                         # cloudtop only (excluded on lenovo via .chezmoiignore)
  qtile-wl/                      # lenovo only (excluded on cloudtop via .chezmoiignore)
  rofi/                          # shared
  zathura/                       # shared
  lf/                            # shared
  alacritty/                     # shared
  conky/                         # shared
  dunst/                         # shared
  spicetify/                     # shared
  nwg-launchers/                 # shared
  VSCodium/                      # shared
  X11/                           # shared
  md-preview/                    # shared
bin/
  executable_*                   # chezmoi prefix for +x permission
system/                          # system-level configs, NOT deployed by chezmoi
  etc/
    pacman.conf
    xdg/
    zsh/
  usr/
    lib/
    share/
run_after_system-deploy.sh.tmpl  # deploys system/ files via sudo
secrets.age                      # age-encrypted secrets file (committed)
```

### Key naming conventions

- `dot_` prefix → deployed as `.` (e.g., `dot_config/` → `.config/`)
- `executable_` prefix → deployed with +x permission
- `.tmpl` suffix → processed as Go template before deployment
- `encrypted_` prefix → age-decrypted before deployment
- Files in `system/` are excluded from chezmoi via `.chezmoiignore` and deployed by `run_after_` script

## Machine Differentiation

### Config template (`.chezmoi.toml.tmpl`)

```toml
{{ $hostname := .chezmoi.hostname -}}

encryption = "age"

[data]
  hostname = "{{ $hostname }}"
  is_lenovo = {{ eq $hostname "lenovo" }}
  is_cloudtop = {{ eq $hostname "cloudtop" }}
  has_wayland = {{ eq $hostname "lenovo" }}
  has_battery = {{ eq $hostname "lenovo" }}

[age]
  identity = "~/.config/chezmoi/key.txt"
  recipient = "AGE_PUBLIC_KEY_HERE"
```

### Ignore rules (`.chezmoiignore`)

```
README.md
CLAUDE.md
docs/**
system/**

{{ if not .is_lenovo }}
dot_config/qtile-wl/**
bin/battery-notification.py
{{ end }}

{{ if not .is_cloudtop }}
dot_config/qtile/**
{{ end }}
```

### Templated files

Files that are mostly shared but differ per-machine use `.tmpl`:

**`.zprofile.tmpl`** — conditionally starts Wayland (lenovo) or just X11:
```zsh
{{ if .has_wayland -}}
if [ -z "$WAYLAND_DISPLAY" ] && [ "$XDG_VTNR" -eq 3 ]; then
  exec qtile start -b wayland -c ~/.config/qtile-wl/config.py
fi
{{ end -}}

if [ -z "${DISPLAY}" ] && [ "${XDG_VTNR}" -eq 2 ]; then
  exec startx
fi
```

**`vars.zsh.tmpl`** — machine-specific env vars and secrets:
```zsh
# XDG vars, shared tool configs...
{{ if .has_wayland -}}
export QT_QPA_PLATFORM=wayland
export QT_STYLE_OVERRIDE=kvantum
export SDL_VIDEODRIVER=wayland
{{ end -}}

# Secrets (from encrypted data)
export OPENSUBTITLES_API_KEY="{{ .opensubtitles_api_key }}"
export TSTRUCT_TOKEN="{{ .tstruct_token }}"
```

## Secrets Management

### Encryption method: age

- Key pair generated with `age-keygen` (separate tool, not a chezmoi subcommand)
- Private key: `~/.config/chezmoi/key.txt` (local only, never committed)
- Public key: in `.chezmoi.toml.tmpl` `[age]` section

### Secret storage

**Standalone secret files** (e.g., `github_token`): stored with `encrypted_` prefix in the source dir. Chezmoi decrypts on apply.

**Inline secrets** (e.g., API keys in `vars.zsh`): chezmoi does not auto-decrypt `.age` files in `.chezmoidata/`. Instead, secrets are stored in a `secrets.age` file at the repo root (age-encrypted, committed) and decrypted into `~/.config/chezmoi/chezmoidata.toml` (local, not committed) by a `run_once_` setup script on first apply.

The plaintext `chezmoidata.toml` (never committed) contains:
```toml
opensubtitles_api_key = "<value>"
tstruct_token = "<value>"
```

Chezmoi automatically reads `~/.config/chezmoi/chezmoidata.toml` and makes the values available as template variables (e.g., `{{ .opensubtitles_api_key }}`).

**Important:** `chezmoidata.toml` must be decrypted manually before the first `chezmoi apply` on a new machine (see New Machine Setup). Chezmoi renders all templates before executing scripts, so a `run_once_` script cannot bootstrap this — the data file must already exist.

To update secrets:
```bash
# Edit the plaintext file
$EDITOR ~/.config/chezmoi/chezmoidata.toml
# Re-encrypt and commit
age -e -R <(age-keygen -y ~/.config/chezmoi/key.txt) \
  ~/.config/chezmoi/chezmoidata.toml > "$(chezmoi source-path)/secrets.age"
cd "$(chezmoi source-path)" && git add secrets.age && git commit -m "update secrets"
```

### Secret inventory

| Secret | Current location | Chezmoi location |
|--------|-----------------|-----------------|
| `github_token` | `qtile-wl/github_token` (plaintext file) | `encrypted_dot_config/qtile-wl/github_token` |
| `OPENSUBTITLES_API_KEY` | `zsh/env/vars.zsh` (hardcoded) | `secrets.age` → `chezmoidata.toml` |
| `TSTRUCT_TOKEN` | `zsh/env/vars.zsh` (hardcoded) | `secrets.age` → `chezmoidata.toml` |

## System Files Deployment

System-level configs (`/etc`, `/usr`) live in `system/` and are deployed by a `run_after_` script:

```bash
# run_after_system-deploy.sh.tmpl
#!/bin/bash
CHEZMOI_SOURCE="{{ .chezmoi.sourceDir }}"
SYSTEM_DIR="$CHEZMOI_SOURCE/system"

[ ! -d "$SYSTEM_DIR" ] && exit 0

for src in $(find "$SYSTEM_DIR" -type f); do
  dest="${src#$SYSTEM_DIR}"
  if ! cmp -s "$src" "$dest" 2>/dev/null; then
    echo "System file changed: $dest"
    sudo install -Dm644 "$src" "$dest" 2>/dev/null || echo "WARN: needs sudo for $dest"
  fi
done
```

The script only copies files that have actually changed to minimize sudo prompts.

## Workflow

### Daily usage

```bash
chezmoi edit --apply ~/.config/zsh/env/aliases.zsh  # edit + deploy
chezmoi add ~/.config/newapp/config.toml             # track new file
chezmoi add --encrypt ~/.config/newapp/secret.key    # track encrypted
chezmoi diff                                          # preview changes
chezmoi apply                                         # deploy all
```

### New machine setup

```bash
# 1. Install chezmoi and clone the repo (do NOT --apply yet, age key not in place)
sh -c "$(curl -fsLS get.chezmoi.io)" -- init ervinpopescu/dots

# 2. Provide the age key for secret decryption
mkdir -p ~/.config/chezmoi
cp /path/to/key.txt ~/.config/chezmoi/key.txt

# 3. Decrypt secrets into chezmoi data (must happen before first apply,
#    because chezmoi renders all templates before running any scripts)
age -d -i ~/.config/chezmoi/key.txt "$(chezmoi source-path)/secrets.age" \
  > ~/.config/chezmoi/chezmoidata.toml

# 4. Deploy system-level files first (needed for ZDOTDIR bootstrap)
sudo cp -a "$(chezmoi source-path)/system/etc/." /etc/
sudo cp -a "$(chezmoi source-path)/system/usr/." /usr/

# 5. Now apply everything
chezmoi apply
```

**Notes:**
- Step 3 is critical: chezmoi renders templates (including `vars.zsh.tmpl` which references secrets) at the start of `apply`, before any `run_once_`/`run_after_` scripts execute. The `chezmoidata.toml` must exist before the first apply.
- Step 4 is needed because `/etc/zsh/zshenv` sets `ZDOTDIR=$HOME/.config/zsh`, which must be in place before zsh can find configs deployed by `chezmoi apply`. On existing machines where `/etc/zsh/zshenv` is already correct, step 4 can be skipped.

### Git workflow

Single `main` branch. Push/pull as normal. No branch-per-machine.

## Migration Path

1. Install chezmoi, generate age key pair
2. Initialize chezmoi source directory
3. Restructure current `configs/` into chezmoi layout with `dot_` prefixes
4. Convert machine-specific files to `.tmpl` templates
5. Encrypt secrets into `secrets.age`
6. Move system configs to `system/`, create `run_after_` script
7. Create `.chezmoiignore` with machine-conditional rules
8. Test on lenovo with `chezmoi diff` / `chezmoi apply --dry-run`
9. Remove old `configs/` directory structure
10. Merge cloudtop-specific files (qtile X11 config) into the single branch
11. Update README
