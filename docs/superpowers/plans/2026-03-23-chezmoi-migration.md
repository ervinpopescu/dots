# Chezmoi Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate dotfiles from per-machine git branches with `cp -alf` to chezmoi with templates, age-encrypted secrets, and a single branch.

**Architecture:** Repo root becomes the chezmoi source directory. Machine differences handled via Go templates and `.chezmoiignore`. Secrets encrypted with age. System files (`/etc`, `/usr`) deployed via `run_after_` script.

**Tech Stack:** chezmoi, age, zsh, git

**Spec:** `docs/superpowers/specs/2026-03-23-chezmoi-migration-design.md`

---

### Task 1: Install chezmoi and generate age key pair

**Files:**

- Create: `~/.config/chezmoi/key.txt` (local only, never committed)

- [ ] **Step 1: Install chezmoi**

```bash
pacman -S chezmoi
```

- [ ] **Step 2: Install age**

```bash
pacman -S age
```

- [ ] **Step 3: Generate age key pair**

```bash
mkdir -p ~/.config/chezmoi
age-keygen -o ~/.config/chezmoi/key.txt 2>&1 | tee /dev/stderr | grep "public key:" | awk '{print $3}'
```

Save the public key output — it goes in `.chezmoi.toml.tmpl` in the next task.

- [ ] **Step 4: Verify**

```bash
chezmoi --version
cat ~/.config/chezmoi/key.txt | head -2
```

Expected: chezmoi version output and age key header line (`# created:` + `AGE-SECRET-KEY-...`).

---

### Task 2: Initialize chezmoi and create config scaffolding

**Files:**

- Create: `.chezmoi.toml.tmpl`
- Create: `.chezmoiignore`

- [ ] **Step 1: Initialize chezmoi pointing at existing repo**

```bash
chezmoi init --source /home/ervin/src/mine/dots
```

This tells chezmoi to use the existing dots repo as its source directory.

- [ ] **Step 2: Create `.chezmoi.toml.tmpl`**

Create `/home/ervin/src/mine/dots/.chezmoi.toml.tmpl`:

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

Replace `AGE_PUBLIC_KEY_HERE` with the public key from Task 1 Step 3.

- [ ] **Step 3: Create `.chezmoiignore`**

Create `/home/ervin/src/mine/dots/.chezmoiignore`:

```
README.md
CLAUDE.md
LICENSE
docs/**
system/**
markdown/**
secrets.age
*.md

{{ if not .is_lenovo }}
dot_config/qtile-wl/**
bin/executable_battery-notification.py
{{ end }}

{{ if not .is_cloudtop }}
dot_config/qtile/**
{{ end }}
```

- [ ] **Step 4: Verify chezmoi reads the config**

```bash
chezmoi data | head -20
```

Expected: JSON output showing `hostname`, `is_lenovo`, `has_wayland`, etc.

- [ ] **Step 5: Commit**

```bash
cd /home/ervin/src/mine/dots
git add .chezmoi.toml.tmpl .chezmoiignore
git commit -m "chezmoi: add config template and ignore rules"
```

---

### Task 3: Restructure configs into chezmoi layout

This is the big structural move. Rename `configs/.config/` → `dot_config/`, `configs/bin/` → `bin/`, `configs/etc/` + `configs/usr/` → `system/`.

**Files:**

- Move: `configs/.config/*` → `dot_config/`
- Move: `configs/bin/*` → `bin/` (with `executable_` prefix)
- Move: `configs/etc/*` → `system/etc/`
- Move: `configs/usr/*` → `system/usr/`
- Move: `configs/pkgs` → `system/pkgs`
- Move: `configs/.jq` → `dot_jq`
- Move: `configs/lfub` → `bin/executable_lfub`
- Delete: `configs/` (empty after moves)

- [ ] **Step 1: Create target directories**

```bash
cd /home/ervin/src/mine/dots
mkdir -p dot_config system bin
```

- [ ] **Step 2: Move .config contents to dot_config**

```bash
git mv configs/.config/* dot_config/
```

- [ ] **Step 3: Move bin scripts with executable\_ prefix**

```bash
for f in configs/bin/*; do
  name=$(basename "$f")
  git mv "$f" "bin/executable_${name}"
done
```

- [ ] **Step 4: Move system files**

```bash
git mv configs/etc system/etc
git mv configs/usr system/usr
git mv configs/pkgs system/pkgs
```

- [ ] **Step 5: Move remaining root-level dotfiles**

```bash
git mv configs/.jq dot_jq
git mv configs/lfub bin/executable_lfub
```

- [ ] **Step 6: Remove empty configs directory**

```bash
rmdir configs 2>/dev/null || rm -rf configs
```

- [ ] **Step 7: Verify structure**

```bash
ls -la /home/ervin/src/mine/dots/
# Should show: dot_config/ bin/ system/ .chezmoi.toml.tmpl .chezmoiignore ...
ls dot_config/ | head -10
ls bin/ | head -5
ls system/
```

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "chezmoi: restructure configs/ into chezmoi source layout"
```

---

### Task 4: Convert machine-specific files to templates

**Files:**

- Rename+modify: `dot_config/zsh/.zprofile` → `dot_config/zsh/.zprofile.tmpl`
- Rename+modify: `dot_config/zsh/env/vars.zsh` → `dot_config/zsh/env/vars.zsh.tmpl`

- [ ] **Step 1: Convert .zprofile to template**

```bash
git mv dot_config/zsh/.zprofile dot_config/zsh/.zprofile.tmpl
```

Then edit `dot_config/zsh/.zprofile.tmpl` to contain:

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

- [ ] **Step 2: Convert vars.zsh to template**

```bash
git mv dot_config/zsh/env/vars.zsh dot_config/zsh/env/vars.zsh.tmpl
```

Edit `dot_config/zsh/env/vars.zsh.tmpl`: replace the hardcoded secret values with template variables and wrap wayland-specific exports in conditionals.

The two secrets lines become:

```zsh
export OPENSUBTITLES_API_KEY="{{ .opensubtitles_api_key }}"
export TSTRUCT_TOKEN="{{ .tstruct_token }}"
```

The wayland-specific block gets wrapped:

```zsh
{{ if .has_wayland -}}
export QT_QPA_PLATFORM=wayland
export QT_STYLE_OVERRIDE=kvantum
export SDL_VIDEODRIVER=wayland
{{ end -}}
```

And the `MOZ_ENABLE_WAYLAND` conditional at the end:

```zsh
{{ if .has_wayland -}}
export MOZ_ENABLE_WAYLAND=1
{{ end -}}
```

Remove the existing `if [ "$XDG_SESSION_TYPE" = "wayland" ]` shell conditional since the template handles it.

- [ ] **Step 3: Verify templates parse**

```bash
chezmoi execute-template < dot_config/zsh/.zprofile.tmpl
chezmoi execute-template < dot_config/zsh/env/vars.zsh.tmpl
```

Expected: rendered output without Go template syntax. The secrets will show empty strings until Task 5.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chezmoi: convert zprofile and vars.zsh to machine-conditional templates"
```

---

### Task 5: Encrypt secrets

**Files:**

- Create: `secrets.age`
- Create: `~/.config/chezmoi/chezmoidata.toml` (local only, never committed)
- Create: `dot_config/qtile-wl/encrypted_github_token` (replaces plaintext)

- [ ] **Step 1: Create plaintext chezmoidata.toml**

Read the current secret values from the live `vars.zsh` and `github_token`, then create `~/.config/chezmoi/chezmoidata.toml`:

```toml
opensubtitles_api_key = "VALUE_FROM_VARS_ZSH"
tstruct_token = "VALUE_FROM_VARS_ZSH"
```

- [ ] **Step 2: Encrypt into secrets.age**

```bash
cd /home/ervin/src/mine/dots
age -e -R <(age-keygen -y ~/.config/chezmoi/key.txt) \
  ~/.config/chezmoi/chezmoidata.toml > secrets.age
```

- [ ] **Step 3: Verify decryption roundtrip**

```bash
age -d -i ~/.config/chezmoi/key.txt secrets.age
```

Expected: plaintext TOML with the secret values.

- [ ] **Step 4: Encrypt github_token file**

```bash
chezmoi add --encrypt ~/.config/qtile-wl/github_token
```

This creates an `encrypted_` prefixed file in the source dir under `dot_config/qtile-wl/`.

- [ ] **Step 5: Remove plaintext github_token from source dir if it exists**

```bash
rm -f dot_config/qtile-wl/github_token
```

- [ ] **Step 6: Verify template variables now resolve**

```bash
chezmoi execute-template '{{ .opensubtitles_api_key }}'
```

Expected: the actual API key value.

- [ ] **Step 7: Commit**

```bash
git add secrets.age dot_config/qtile-wl/
git commit -m "chezmoi: encrypt secrets with age"
```

---

### Task 6: Create system files deployment script

**Files:**

- Create: `run_after_system-deploy.sh.tmpl`

- [ ] **Step 1: Create the run_after script**

Create `/home/ervin/src/mine/dots/run_after_system-deploy.sh.tmpl`:

```bash
#!/bin/bash
CHEZMOI_SOURCE="{{ .chezmoi.sourceDir }}"
SYSTEM_DIR="$CHEZMOI_SOURCE/system"

[ ! -d "$SYSTEM_DIR" ] && exit 0

changed=0
while IFS= read -r -d '' src; do
  dest="${src#"$SYSTEM_DIR"}"
  if ! cmp -s "$src" "$dest" 2>/dev/null; then
    echo "System file changed: $dest"
    sudo install -Dm644 "$src" "$dest" 2>/dev/null || echo "WARN: needs sudo for $dest"
    changed=1
  fi
done < <(find "$SYSTEM_DIR" -type f -print0)

[ "$changed" -eq 0 ] && echo "System files: no changes detected."
```

- [ ] **Step 2: Commit**

```bash
git add run_after_system-deploy.sh.tmpl
git commit -m "chezmoi: add run_after script for system file deployment"
```

---

### Task 7: Test with dry run on lenovo

- [ ] **Step 1: Check what chezmoi would do**

```bash
chezmoi diff
```

Review the output carefully. It should show the files chezmoi wants to create/update in `$HOME`.

- [ ] **Step 2: Dry-run apply**

```bash
chezmoi apply --dry-run --verbose
```

Expected: list of file operations without actually writing anything. Verify:

- `.config/zsh/.zprofile` contains wayland block (lenovo)
- `.config/zsh/env/vars.zsh` contains decrypted secrets and wayland vars
- `.config/qtile-wl/` files are included
- `.config/qtile/` files are excluded (lenovo)
- `~/bin/` scripts have correct names (no `executable_` prefix in target)
- No `system/`, `docs/`, `README.md`, `CLAUDE.md` in target

- [ ] **Step 3: Fix any issues found**

Address any problems from the dry run before proceeding.

- [ ] **Step 4: Apply for real**

```bash
chezmoi apply --verbose
```

- [ ] **Step 5: Verify live configs work**

```bash
# zsh should still work
source ~/.config/zsh/.zshenv
# Check a secret made it through
grep OPENSUBTITLES_API_KEY ~/.config/zsh/env/vars.zsh
# Check qtile-wl config is present
ls ~/.config/qtile-wl/config.py
# Check a bin script is executable
ls -la ~/bin/autostart.sh
```

- [ ] **Step 6: Commit any fixes**

```bash
cd /home/ervin/src/mine/dots
git add -A
git commit -m "chezmoi: fixes from initial apply testing"
```

---

### Task 8: Merge cloudtop-specific files into single branch

**Files:**

- Add: `dot_config/qtile/` (from cloudtop branch)
- Add: any cloudtop-only files from `configs/bin/`, `configs/.config/`

- [ ] **Step 1: List cloudtop-only files**

```bash
cd /home/ervin/src/mine/dots
# Files in cloudtop but not in lenovo
diff <(git ls-tree -r --name-only cloudtop -- configs/ | sed 's|^configs/||' | sort) \
     <(git ls-tree -r --name-only lenovo -- configs/ | sed 's|^configs/||' | sort) \
  | grep '^<' | sed 's/^< //'
```

- [ ] **Step 2: Extract cloudtop qtile (X11) config**

```bash
# The qtile/ dir already exists from lenovo branch, but cloudtop may have diverged.
# Check out cloudtop's qtile config into the new structure:
git show cloudtop:configs/.config/qtile/config.py > /tmp/cloudtop-qtile-config.py
# Compare with what we have
diff /tmp/cloudtop-qtile-config.py dot_config/qtile/config.py
```

If cloudtop's qtile config is significantly different, use cloudtop's version since that's the machine actually running X11 qtile. Replace files as needed.

- [ ] **Step 3: Extract cloudtop-only zsh files if any differ**

The cloudtop branch uses a flat zsh structure (no `env/`/`rc/` subdirs). Since lenovo's refactored structure is newer, keep lenovo's structure. But check if cloudtop has any unique content:

```bash
for f in aliases vars misc; do
  echo "=== $f ==="
  diff <(git show cloudtop:configs/.config/zsh/${f}.zsh 2>/dev/null) \
       dot_config/zsh/env/${f}.zsh 2>/dev/null | head -20
done
```

Merge any cloudtop-unique content into the appropriate lenovo files (potentially as template conditionals).

- [ ] **Step 4: Extract cloudtop-only system files**

```bash
git show cloudtop:configs/etc/pacman.conf > /tmp/cloudtop-pacman.conf
diff /tmp/cloudtop-pacman.conf system/etc/pacman.conf | head -20
```

If different, template `pacman.conf` or keep the lenovo version (typically machine-specific mirrors are the only difference).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chezmoi: merge cloudtop-specific configs into single branch"
```

---

### Task 9: Clean up and update README

**Files:**

- Delete: `configs/` directory (should be empty/gone after Task 3)
- Modify: `README.md`

- [ ] **Step 1: Verify no leftover configs/ directory**

```bash
ls configs/ 2>/dev/null && echo "WARN: configs/ still exists" || echo "OK: configs/ already removed"
```

- [ ] **Step 2: Update README.md**

Replace the install section with chezmoi instructions:

````markdown
## Install ([+Arch](./markdown/archinstall.md))

### Prerequisites

```console
pacman -S chezmoi age
```
````

### Setup

```console
# Clone and initialize
chezmoi init ervinpopescu/dots

# Provide age key for secrets
mkdir -p ~/.config/chezmoi
cp /path/to/key.txt ~/.config/chezmoi/key.txt

# Decrypt secrets
age -d -i ~/.config/chezmoi/key.txt "$(chezmoi source-path)/secrets.age" \
  > ~/.config/chezmoi/chezmoidata.toml

# Bootstrap system files (first time only)
sudo cp -a "$(chezmoi source-path)/system/etc/." /etc/
sudo cp -a "$(chezmoi source-path)/system/usr/." /usr/

# Apply
chezmoi apply
```

````

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chezmoi: update README with new install instructions, remove old configs/"
````

---

### Task 10: Final verification

- [ ] **Step 1: Full clean apply test**

```bash
chezmoi apply --verbose 2>&1 | tail -20
```

Verify no errors.

- [ ] **Step 2: Verify system deploy script ran**

```bash
# Should report no changes (already deployed)
# Check the run_after_ output
```

- [ ] **Step 3: Verify all critical configs are in place**

```bash
test -f ~/.config/zsh/.zshrc && echo "zsh OK"
test -f ~/.config/zsh/env/vars.zsh && echo "vars OK"
test -f ~/.config/qtile-wl/config.py && echo "qtile-wl OK"
test -f ~/.config/nvim/init.lua && echo "nvim OK"
test -f ~/.config/tmux/tmux.conf && echo "tmux OK"
test -f ~/.config/git/config && echo "git OK"
test -x ~/bin/autostart.sh && echo "bin OK"
grep -q "OPENSUBTITLES_API_KEY" ~/.config/zsh/env/vars.zsh && echo "secrets OK"
```

Expected: all "OK".

- [ ] **Step 4: Push**

```bash
git push origin lenovo
```
