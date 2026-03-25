# Home, sweet home!

```
       ██              ██               
  ▄███▄██   ▄████▄   ███████   ▄▄█████▄ 
 ██▀  ▀██  ██▀  ▀██    ██      ██▄▄▄▄ ▀ 
 ██    ██  ██    ██    ██       ▀▀▀▀██▄ 
 ▀██▄▄███  ▀██▄▄██▀    ██▄▄▄   █▄▄▄▄▄██ 
   ▀▀▀ ▀▀    ▀▀▀▀       ▀▀▀▀    ▀▀▀▀▀▀  
```                                                    


## [Features](./markdown/features.md)

## Install ([+Arch](./markdown/archinstall.md))

Managed with [chezmoi](https://www.chezmoi.io/). Secrets are age-encrypted.

```console
# 1. Install dependencies
pacman -S chezmoi age

# 2. Place age key (get from backup/password manager)
mkdir -p ~/.config/chezmoi
cp /path/to/key.txt ~/.config/chezmoi/key.txt

# 3. Initialize (prompts for machine profile + secrets on first run)
chezmoi init --source /path/to/this/repo

# 4. Preview and apply
chezmoi diff
chezmoi apply
```

System files under `system/` are deployed via a post-apply script with `sudo`.

## [Keybindings](./markdown/keybinds.md)

## [Directory tree](./markdown/tree.md)
