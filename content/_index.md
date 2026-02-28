---
title: ""
toc: false
---

<div class="hx-mt-6 hx-mb-6">
{{< hextra/hero-headline >}}
  Zephyrus Linux
{{< /hextra/hero-headline >}}
</div>

<div class="hx-mb-12">
{{< hextra/hero-subtitle >}}
  Personal Linux setup and configuration notes for the ROG Zephyrus G16
{{< /hextra/hero-subtitle >}}
</div>

<div class="hx-mb-6">
{{< hextra/hero-badge link="/docs/" >}}
  <span>Browse the Guides</span>
  {{< icon name="arrow-circle-right" attributes="height=14" >}}
{{< /hextra/hero-badge >}}
</div>

<div class="hx-mt-6"></div>

{{< callout type="info" >}}
**Personal documentation.** I'm not a developer or Linux expert, just someone who switched to Linux on this laptop and figured things out along the way. I share what worked for me so others don't have to start from scratch. Everything here is at your own risk. Feel free to reach out if something doesn't work; I'm happy to think along. Running kernel 6.19.4-2 on CachyOS (Arch).
{{< /callout >}}

## Current System Configuration

| Component | Specification |
|-----------|---------------|
| **Model** | ASUS ROG Zephyrus G16 GA605WV (2024) |
| **CPU** | AMD Ryzen AI 9 HX 370 |
| **iGPU** | AMD Radeon 890M |
| **dGPU** | NVIDIA GeForce RTX 4060 Laptop (Max-Q) |
| **OS** | CachyOS (Arch) |
| **Kernel** | 6.19.4-2 |
| **Display Server** | Wayland (GNOME 49) |
| **CPU Scheduler** | scx_lavd (sched_ext) |
| **Secure Boot** | Enabled |

![System information overview](/images/system-info.avif)

## Getting Started

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Getting Started"
    subtitle="From fresh CachyOS install to fully configured system"
    icon="play"
    link="docs/getting-started"
  >}}
{{< /hextra/feature-grid >}}

## Hardware & Drivers

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="NVIDIA Driver Installation"
    subtitle="Proprietary NVIDIA drivers with Secure Boot on CachyOS"
    icon="chip"
    link="docs/hardware/nvidia-driver-installation"
  >}}
  {{< hextra/feature-card
    title="Secure Boot"
    subtitle="Custom signing keys with sbctl, UEFI Secure Boot enabled"
    icon="shield-check"
    link="docs/hardware/secure-boot"
  >}}
  {{< hextra/feature-card
    title="asusctl & ROG Control Center"
    subtitle="Fan curves, performance profiles, GPU switching, Slash LED"
    icon="adjustments"
    link="docs/hardware/asusctl-rog-control"
  >}}
{{< /hextra/feature-grid >}}

## Security & Privacy

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="YubiKey 5C NFC"
    subtitle="FIDO2 LUKS unlock and what currently works"
    icon="key"
    link="docs/security/yubikey"
  >}}
  {{< hextra/feature-card
    title="GDM Autologin"
    subtitle="Skip GDM login after LUKS unlock"
    icon="lock-open"
    link="docs/security/autologin"
  >}}
{{< /hextra/feature-grid >}}

## Applications

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Applications"
    subtitle="Browser, communication, development tools, and system configuration"
    icon="collection"
    link="docs/applications"
  >}}
{{< /hextra/feature-grid >}}

## Networking

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="eduroam Network Installation"
    subtitle="PEAP/MSCHAPv2 setup that actually works on Linux"
    icon="wifi"
    link="docs/networking/eduroam-network-installation"
  >}}
{{< /hextra/feature-grid >}}

## Virtualization

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Windows 11 VM Setup"
    subtitle="KVM/QEMU VM with VirtIO and SPICE GL"
    icon="desktop-computer"
    link="docs/virtualization/vm-setup"
  >}}
  {{< hextra/feature-card
    title="Looking Glass Attempt"
    subtitle="GPU passthrough attempt, not working on this hardware"
    icon="eye"
    link="docs/virtualization/looking-glass-attempt"
  >}}
  {{< hextra/feature-card
    title="WinBoat"
    subtitle="Windows apps on Linux via Podman container, early beta"
    icon="beaker"
    link="docs/virtualization/winboat"
  >}}
{{< /hextra/feature-grid >}}

---
