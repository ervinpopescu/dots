# Arch install notes

## Install

`ping archlinux.org`

`timedatectl set-ntp true`

create partition with `fdisk` : 500M for boot 20G for root the rest for home (change type to 1 for boot to UEFI)

`mkfs.fat -F32` for boot and `mkfs.ext4` for root and home

`mount` /mnt on root fs and /mnt/home (mkdir) on home fs

`cp /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.backup`

`pacman -Sy pacman-mirrorlist`

`rankmirrors -n 6 /etc/pacman.d/mirrorlist.backup > /etc/pacman.d/mirrorlist`

`pacstrap /mnt base base-devel vim git reflector`

`genfstab -U -p /mnt >> /mnt/etc/fstab`

`arch-chroot /mnt`

## Post-Install

#### logged in as root

- edit /etc/pacman.conf
  - `testing,core,extra,community-testing,community`
  - `Color,CheckSpace,VerbosePkgLists,ParallelDownloads = 5,ILoveCandy`

```sh
echo "arch" > /etc/hostname
echo -e "127.0.0.1 localhost\n::1 localhost" > /etc/hosts
useradd -m -g wheel ervin
passwd ervin
EDITOR=vim visudo
systemctl start reflector.service
su ervin
```

#### logged in as ervin

```sh
cd
git clone https://aur.archlinux.org/yay.git && cd yay && makepkg -si --noconfirm
yay -Syyu < pkgs-to-install.txt
```

```sh
cd
bash <(curl -s https://raw.githubusercontent.com/lunarvim/lunarvim/master/utils/installer/install.sh)
git clone https://github.com/ervinpopescu/dots && cd dots
mkdir ~/.config && cp -alrf .config/* ~/.config
cp -alrf bin ~
cp -alrf etc /etc
cp -alrf usr /usr
cp -alrf etc /etc
fc-cache -f -v
```

## Useful

- `lscpu | grep MHz`
- `fc-list | grep -i awesome`
- `fc-cache -f -v`
