---
title: ""
weight: 1
toc: false
---

# My Setup Notes

Everything I've documented while running CachyOS on the ROG Zephyrus G16. Start with Getting Started if you're setting up from scratch, or jump to whichever section is relevant to your situation.

## Getting Started

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Getting Started"
    subtitle="From fresh CachyOS install to fully configured system"
    icon="play"
    link="getting-started"
  >}}
{{< /hextra/feature-grid >}}

## Hardware & Drivers

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="NVIDIA Driver Installation"
    subtitle="Proprietary NVIDIA drivers with Secure Boot on CachyOS"
    icon="chip"
    link="hardware/nvidia-driver-installation"
  >}}
  {{< hextra/feature-card
    title="Secure Boot"
    subtitle="Custom signing keys with sbctl, UEFI Secure Boot enabled"
    icon="shield-check"
    link="hardware/secure-boot"
  >}}
  {{< hextra/feature-card
    title="asusctl & ROG Control Center"
    subtitle="Fan curves, performance profiles, GPU switching, Slash LED"
    icon="adjustments"
    link="hardware/asusctl-rog-control"
  >}}
{{< /hextra/feature-grid >}}

## Security & Privacy

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="YubiKey 5C NFC"
    subtitle="FIDO2 LUKS unlock and what currently works"
    icon="key"
    link="security/yubikey"
  >}}
  {{< hextra/feature-card
    title="GDM Autologin"
    subtitle="Skip GDM login after LUKS unlock"
    icon="lock-open"
    link="security/autologin"
  >}}
{{< /hextra/feature-grid >}}

## Applications

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Applications"
    subtitle="Browser, communication, development tools, and system configuration"
    icon="collection"
    link="applications"
  >}}
{{< /hextra/feature-grid >}}

## Networking

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="eduroam Network Installation"
    subtitle="PEAP/MSCHAPv2 setup that actually works on Linux"
    icon="wifi"
    link="networking/eduroam-network-installation"
  >}}
{{< /hextra/feature-grid >}}

## Virtualization

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Windows 11 VM Setup"
    subtitle="KVM/QEMU VM with VirtIO and SPICE GL"
    icon="desktop-computer"
    link="virtualization/vm-setup"
  >}}
  {{< hextra/feature-card
    title="Looking Glass B7"
    subtitle="GPU passthrough via Looking Glass, not working on this hardware"
    icon="eye"
    link="virtualization/looking-glass-attempt"
  >}}
  {{< hextra/feature-card
    title="Podman & Podman Desktop"
    subtitle="Docker replacement with rootless containers and a desktop GUI"
    icon="server"
    link="virtualization/podman"
  >}}
{{< /hextra/feature-grid >}}

## Known Issues

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Known Issues"
    subtitle="Issues without a solution yet"
    icon="exclamation-circle"
    link="known-issues"
  >}}
{{< /hextra/feature-grid >}}
