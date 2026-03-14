---
title: "VMware Workstation"
weight: 5
prev: docs/virtualization/podman
next: docs/known-issues
---

VMware Workstation werkt goed op CachyOS met wat initiële configuratie. De belangrijkste stappen zijn het installeren van het pakket uit de AUR, het herstellen van de DKMS kernel modules en het instellen van netwerken. Op GNOME 49 Wayland is ook een keyboard grab fix nodig.

**Pakket:** `vmware-workstation` 25H2u1-1 uit de [AUR](https://aur.archlinux.org/packages/vmware-workstation)

![VMware Workstation - hoofdvenster](/images/vmware-workstation-main.avif)

![VMware Workstation - VM draaiend](/images/vmware-workstation-running.avif)


## Installatie

{{% steps %}}

### VMware Workstation installeren

```bash
paru -S vmware-workstation
sudo pacman -S linux-cachyos-headers dkms linux-headers
sudo systemctl enable --now vmware-networks.service
```

### DKMS modules (vmmon/vmnet) herstellen

Na installatie kan het voorkomen dat de `vmmon` en `vmnet` kernel modules niet worden gebouwd. Controleer eerst het build-logboek:

```bash
sudo cat /var/lib/dkms/vmmon/1/build/make.log
```

Installeer de community-ondersteunde host modules en herbouw:

```bash
paru -Syu vmware-host-modules-dkms-git
sudo dkms autoinstall
sudo vmware-modconfig --console --install-all
```

Controleer of de modules correct zijn geladen:

```bash
lsmod | grep vm
sudo dmesg | grep -e vmmon -e vmnet
```

Herstart daarna:

```bash
reboot
```

{{% /steps %}}


## Netwerken

{{% details title="vmnet1/vmnet8 netwerken herstellen" closed="true" %}}

Als de virtuele netwerkinterfaces niet werken, controleer dan eerst het kernellog:

```bash
sudo dmesg | grep vmnet
```

Reset de VMware netwerkconfiguratie:

```bash
sudo rm -rf /etc/vmware/networking /etc/vmware/vmnet* /var/lib/vmware/Network*
sudo vmware-networks --stop
sudo vmware-networks --start
sudo systemctl restart vmware vmware-networks
```

**Handmatig `/etc/vmware/networking` (bij een directory-fout):**

```bash
sudo rm -rf /etc/vmware/networking
sudo mkdir -p /etc/vmware
echo '[devices]' | sudo tee /etc/vmware/networking
echo 'vmnet1 = "yes"' | sudo tee -a /etc/vmware/networking
echo 'vmnet8 = "yes"' | sudo tee -a /etc/vmware/networking
```

**In Virtual Network Editor (GUI):**

- VMnet1 → Host-only
- VMnet8 → NAT
- Apply/Save

{{% /details %}}


## GNOME 49 Wayland Toetsenbord Grab

{{% details title="Toetsenbordinvoer in VM's herstellen op GNOME 49 Wayland" closed="true" %}}

Op GNOME 49 met Wayland kan toetsenbordinvoer onjuist werken in VMware VM's. XWayland keyboard grab moet expliciet worden toegestaan voor VMware processen.

```bash
gsettings set org.gnome.mutter.wayland xwayland-allow-grabs true
gsettings set org.gnome.mutter.wayland xwayland-grab-access-rules "['vmware', 'vmware-vmx']"
gsettings reset org.gnome.desktop.wm.keybindings switch-applications
gsettings reset org.gnome.desktop.wm.keybindings switch-windows
```

Herstart GNOME Shell zonder uit te loggen:

```
Alt+F2 → r → Enter
```

**In VMware:**

- Gebruik **Ctrl+Alt** om input grab te wisselen
- Schakel volledig scherm in voor betere toetsenbordafhandeling
- Windows-sneltoetsen werken nu in de guest

{{% /details %}}


## Aanvullende bronnen

- [AUR: vmware-workstation](https://aur.archlinux.org/packages/vmware-workstation)
- [Arch Wiki: VMware](https://wiki.archlinux.org/title/VMware)
