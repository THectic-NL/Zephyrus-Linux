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
  Persoonlijke Linux setup en instellingen voor de ROG Zephyrus G16
{{< /hextra/hero-subtitle >}}
</div>

<div class="hx-mb-6">
{{< hextra/hero-badge link="/nl/docs/" >}}
  <span>Bekijk de handleidingen</span>
  {{< icon name="arrow-circle-right" attributes="height=14" >}}
{{< /hextra/hero-badge >}}
</div>

<div class="hx-mt-6"></div>

{{< callout type="info" >}}
**Persoonlijke documentatie.** Ik ben geen developer of Linux-expert — gewoon iemand die overgestapt is naar Linux op deze laptop en dingen uitzoekend onderweg. Ik deel wat werkte zodat anderen niet helemaal opnieuw hoeven te beginnen. Alles is op eigen risico. Kom je ergens niet uit, laat het gerust weten — ik denk graag mee. Draait kernel 6.19.3-2 op CachyOS (Arch).
{{< /callout >}}

## Huidige Systeemconfiguratie

| Onderdeel | Specificatie |
|-----------|--------------|
| **Model** | ASUS ROG Zephyrus G16 GA605WV (2024) |
| **CPU** | AMD Ryzen AI 9 HX 370 |
| **iGPU** | AMD Radeon 890M |
| **dGPU** | NVIDIA GeForce RTX 4060 Laptop (Max-Q) |
| **OS** | CachyOS (Arch) |
| **Kernel** | 6.19.3-2 |
| **Display Server** | Wayland (GNOME 49) |
| **CPU Scheduler** | scx_lavd (sched_ext) |
| **Secure Boot** | Ingeschakeld |

## Aan de slag

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Aan de slag"
    subtitle="Van schone CachyOS-installatie tot volledig geconfigureerd systeem"
    icon="play"
    link="docs/getting-started"
  >}}
{{< /hextra/feature-grid >}}

## Hardware & Drivers

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="NVIDIA Driver Installatie"
    subtitle="Proprietary NVIDIA drivers met Secure Boot op CachyOS"
    icon="chip"
    link="docs/hardware/nvidia-driver-installation"
  >}}
  {{< hextra/feature-card
    title="Secure Boot"
    subtitle="Aangepaste ondertekeningssleutels met sbctl, HSI:3 naar HSI:4"
    icon="shield-check"
    link="docs/hardware/secure-boot"
  >}}
  {{< hextra/feature-card
    title="asusctl & ROG Control Center"
    subtitle="Fan curves, performance profielen, GPU switching, Slash LED"
    icon="adjustments"
    link="docs/hardware/asusctl-rog-control"
  >}}
{{< /hextra/feature-grid >}}

## Beveiliging & Privacy

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="YubiKey 5C NFC"
    subtitle="FIDO2 LUKS-poging en wat vandaag werkt"
    icon="key"
    link="docs/security/yubikey"
  >}}
  {{< hextra/feature-card
    title="GDM Autologin"
    subtitle="GDM-inlogscherm overslaan na LUKS-ontgrendeling"
    icon="lock-open"
    link="docs/security/autologin"
  >}}
{{< /hextra/feature-grid >}}

## Applicaties

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Applicaties"
    subtitle="Browser, communicatie, ontwikkeltools en systeemconfiguratie"
    icon="collection"
    link="docs/applications"
  >}}
{{< /hextra/feature-grid >}}

## Netwerk

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="eduroam Setup"
    subtitle="PEAP/MSCHAPv2 configuratie die daadwerkelijk werkt op Linux"
    icon="wifi"
    link="docs/networking/eduroam-network-installation"
  >}}
{{< /hextra/feature-grid >}}

## Virtualisatie

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Windows 11 VM Setup"
    subtitle="KVM/QEMU VM met VirtIO en SPICE GL"
    icon="desktop-computer"
    link="docs/virtualization/vm-setup"
  >}}
  {{< hextra/feature-card
    title="Looking Glass Poging"
    subtitle="GPU passthrough poging (werkt niet op deze hardware)"
    icon="eye"
    link="docs/virtualization/looking-glass-attempt"
  >}}
{{< /hextra/feature-grid >}}

---
