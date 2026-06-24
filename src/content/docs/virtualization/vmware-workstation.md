---
title: "VMware Workstation"
weight: 5
prev: docs/virtualization/podman
next: docs/known-issues
---

VMware Workstation runs well on CachyOS with some initial setup. The main steps are installing the package from AUR, fixing the DKMS kernel modules, and configuring networking. On GNOME 49 Wayland there is also a keyboard grab fix required.

**Package:** `vmware-workstation` 25H2u1-1 from [AUR](https://aur.archlinux.org/packages/vmware-workstation)

![VMware Workstation - main window](/images/vmware-workstation-main.avif)

![VMware Workstation - VM running](/images/vmware-workstation-running.avif)


## Installation

{{% steps %}}

### Install VMware Workstation

```bash
paru -S vmware-workstation
sudo pacman -S linux-cachyos-headers dkms linux-headers
sudo systemctl enable --now vmware-networks.service
```

### Fix DKMS modules (vmmon/vmnet)

After installation, the `vmmon` and `vmnet` kernel modules may fail to build. Check the build log first:

```bash
sudo cat /var/lib/dkms/vmmon/1/build/make.log
```

Rebuild the modules:

```bash
sudo dkms autoinstall
sudo vmware-modconfig --console --install-all
```

Verify the modules loaded correctly:

```bash
lsmod | grep vm
sudo dmesg | grep -e vmmon -e vmnet
```

Then reboot:

```bash
reboot
```

{{% /steps %}}


## VM Configuration

The VM settings dialog lets you adjust hardware resources assigned to a virtual machine.

![VMware Workstation - VM settings](/images/vmware-workstation-settings.avif)

{{% details title="Recommended VMware preferences" closed="true" %}}

Open **Edit → Preferences** to configure global VMware settings. The Workspace tab shows the default VM storage location and hardware compatibility level.

![VMware Preferences - Workspace](/images/vmware-preferences-workspace.avif)

{{% /details %}}


## Networking

{{% details title="Fix vmnet1/vmnet8 networking" closed="true" %}}

If the virtual network interfaces are not working, check the kernel log first:

```bash
sudo dmesg | grep vmnet
```

Reset the VMware networking configuration:

```bash
sudo rm -rf /etc/vmware/networking /etc/vmware/vmnet* /var/lib/vmware/Network*
sudo vmware-networks --stop
sudo vmware-networks --start
sudo systemctl restart vmware vmware-networks
```

**Manual `/etc/vmware/networking` (if a directory error occurs):**

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


## GNOME 49 Wayland Keyboard Grab

{{% details title="Fix keyboard input inside VMs on GNOME 49 Wayland" closed="true" %}}

On GNOME 49 with Wayland, keyboard input may not work correctly inside VMware VMs. XWayland keyboard grab needs to be explicitly permitted for VMware processes.

```bash
gsettings set org.gnome.mutter.wayland xwayland-allow-grabs true
gsettings set org.gnome.mutter.wayland xwayland-grab-access-rules "['vmware', 'vmware-vmx']"
gsettings reset org.gnome.desktop.wm.keybindings switch-applications
gsettings reset org.gnome.desktop.wm.keybindings switch-windows
```

Apply the changes by restarting your GNOME session:

- Log out of GNOME and log back in, or reboot your system.

After restarting the session, the new XWayland keyboard grab settings will be active.

**In VMware:**

- Use **Ctrl+Alt** to toggle input grab
- Enable fullscreen to improve keyboard handling
- Windows shortcuts now work inside the guest

![VMware Preferences - Input](/images/vmware-preferences-input.avif)

![VMware Preferences - Hot Keys](/images/vmware-preferences-hotkeys.avif)

{{% /details %}}


## Additional Resources

- [AUR: vmware-workstation](https://aur.archlinux.org/packages/vmware-workstation)
- [Arch Wiki: VMware](https://wiki.archlinux.org/title/VMware)
