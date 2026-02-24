---
title: "Getting Started"
weight: 2
---

This is my personal setup documentation for the ROG Zephyrus G16 running CachyOS (Arch). I'm not a software engineer or developer — just someone who switched to Linux and ran into a lot of things that didn't work out of the box. I figured I'd write it all down so others don't have to go through the same trial and error.

If something here helps you, great. If you run into something I haven't covered, feel free to reach out — I'm happy to think along.

## Hardware

| Component | Specification |
|-----------|---------------|
| **Model** | ASUS ROG Zephyrus G16 GA605WV (2024) |
| **CPU** | AMD Ryzen AI 9 HX 370 |
| **iGPU** | AMD Radeon 890M |
| **dGPU** | NVIDIA GeForce RTX 4060 Laptop (Max-Q) |
| **OS** | CachyOS (Arch) |
| **Kernel** | 6.19.3-2 |
| **Display Server** | Wayland (GNOME 49) |
| **Secure Boot** | Enabled |

## Recommended setup order

After a fresh CachyOS install, this is the order that made sense for me:

{{% steps %}}

### Hardware & Drivers

Install NVIDIA drivers, set up Secure Boot with your own signing keys, and configure ASUS ROG hardware features (fan curves, performance profiles, GPU switching).

→ [NVIDIA Driver Installation]({{< relref "/docs/hardware/nvidia-driver-installation" >}})
→ [Secure Boot]({{< relref "/docs/hardware/secure-boot" >}})
→ [asusctl & ROG Control Center]({{< relref "/docs/hardware/asusctl-rog-control" >}})

### Security & Privacy

Set up hardware-backed LUKS unlock with a YubiKey, and optionally configure GDM to skip the login screen after disk unlock.

→ [YubiKey 5C NFC]({{< relref "/docs/security/yubikey" >}})
→ [GDM Autologin]({{< relref "/docs/security/autologin" >}})

### Applications

Install and configure applications — browser, communication tools, development environment, and utilities. Includes non-obvious workarounds for Brave on GNOME Wayland and touchpad scroll speed.

→ [Applications]({{< relref "/docs/applications" >}})

### Networking

Get eduroam working. The official installers don't work on Linux; a manual PEAP/MSCHAPv2 configuration via nmcli does.

→ [eduroam Network Installation]({{< relref "/docs/networking/eduroam-network-installation" >}})

### Virtualization

Set up a Windows 11 VM for software that doesn't run on Linux (Microsoft 365, etc.).

→ [Windows 11 VM Setup]({{< relref "/docs/virtualization/vm-setup" >}})

{{% /steps %}}
