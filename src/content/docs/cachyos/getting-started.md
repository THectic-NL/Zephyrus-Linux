---
title: "Getting Started"
weight: 1
prev: docs/cachyos
next: docs/cachyos/updates
distro: cachyos
---

CachyOS is an Arch-based distribution with hardware-specific optimizations, and one of the two I've daily-driven on the G16. This is the option for wanting the machine in your hands: you choose the kernel, the scheduler and every package, and you carry the maintenance that comes with that. If that trade doesn't appeal, read [Bazzite]({{< relref "/docs/bazzite/getting-started" >}}) instead before you install anything.

## Why CachyOS

- **BORE/EEVDF scheduler**: CachyOS ships with an improved CPU scheduler that provides better responsiveness and lower latency under mixed workloads
- **Improved power management**: better handling of suspend/resume and ACPI power states on AMD+NVIDIA hybrid setups
- **Dynamic refresh rate support**: out-of-the-box support for variable refresh rate on the ROG Nebula Display
- **Built-in iGPU and dGPU drivers**: the AMD Radeon 890M and NVIDIA RTX 4060 work correctly from a fresh install, including GPU switching via `asusctl armoury`
- **ASUS Linux patches**: part of [Luke Jones'](https://asus-linux.org/) work has been merged into the Linux kernel mainline (the `asus-armoury` driver since 6.19), while additional ROG-specific patches and `asusctl` tooling improvements are carried by CachyOS. Both `asusctl` and `rog-control-center` are available directly from the CachyOS repos; install two packages and you're done, no deep system configuration required

## What rolling means here

Packages arrive as upstream releases them. There is no release to upgrade to and no version number to be behind on, but there is also nothing holding a change back, so `sudo pacman -Syu` is something you run deliberately rather than something that happens to you. The system is fully writable, so a package is usable the moment it installs; only a new kernel needs a reboot. When an update goes wrong you roll it back by hand — the main practical difference with Bazzite, where a bad update is one `rpm-ostree rollback` away.

→ [Updating]({{< relref "/docs/cachyos/updates" >}}) covers `pacman`, the kernel and the CachyOS Kernel Manager, and keeping everything current in one command with Topgrade.

## Secure Boot before you install

CachyOS doesn't use shim, so Secure Boot has to be **off** before the installer will boot. You can enable it again afterwards with your own signing keys.

→ [Secure Boot on CachyOS]({{< relref "/docs/cachyos/secure-boot" >}})

## Recommended setup order

After a fresh CachyOS install, this is the order that made sense for me:

{{% steps %}}

### Hardware & Drivers

The NVIDIA driver is already configured by the installer, so this is mostly verification. Then set up Secure Boot with your own signing keys and configure the ASUS ROG hardware features (fan curves, performance profiles, GPU switching).

→ [NVIDIA Driver: CachyOS]({{< relref "/docs/cachyos/nvidia" >}})
→ [Secure Boot on CachyOS]({{< relref "/docs/cachyos/secure-boot" >}})
→ [asusctl & ROG Control Center]({{< relref "/docs/hardware/asusctl-rog-control" >}})
→ [Display Color Profiles]({{< relref "/docs/hardware/color-profiles" >}})

### Security & Privacy

Optionally configure GDM to skip the login screen after disk unlock. Set up the YubiKey for `sudo` and the GNOME lock screen via pam-u2f.

→ [GDM Autologin]({{< relref "/docs/security/autologin" >}})
→ [YubiKey]({{< relref "/docs/security/yubikey" >}})

### Applications

Install and configure applications: browser, communication tools, development environment, and utilities. Includes non-obvious workarounds for Brave on GNOME Wayland and touchpad scroll speed.

→ [Applications]({{< relref "/docs/applications" >}})

### Networking

Get eduroam working. The official installers don't work on Linux; a manual PEAP/MSCHAPv2 configuration via nmcli does.

→ [eduroam Network Installation]({{< relref "/docs/networking/eduroam-network-installation" >}})

### Virtualization

Set up a Windows 11 VM for software that doesn't run on Linux (Microsoft 365, etc.), or run VMware Workstation for more advanced virtualization needs.

→ [Virt-Manager / KVM]({{< relref "/docs/virtualization/vm-setup" >}})
→ [VMware Workstation]({{< relref "/docs/virtualization/vmware-workstation" >}})

{{% /steps %}}

## Additional Resources

- [CachyOS Wiki](https://wiki.cachyos.org/)
- [CachyOS installation docs](https://wiki.cachyos.org/installation/installation_on_root/)
- [Arch Wiki](https://wiki.archlinux.org/)
