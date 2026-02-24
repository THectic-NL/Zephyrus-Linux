---
title: "Aan de slag"
weight: 2
---

Dit is mijn persoonlijke setup-documentatie voor de ROG Zephyrus G16 op CachyOS (Arch). Ik ben geen software-engineer of developer — gewoon iemand die overgestapt is naar Linux en daarna tegen van alles aanliep wat niet meteen werkte. Ik heb alles opgeschreven zodat anderen niet hetzelfde hoeven uit te zoeken als ik.

Als iets hier je helpt: mooi. Loop je ergens tegenaan wat ik niet behandeld heb, laat het gerust weten — ik denk graag mee.

## Hardware

| Onderdeel | Specificatie |
|-----------|--------------|
| **Model** | ASUS ROG Zephyrus G16 GA605WV (2024) |
| **CPU** | AMD Ryzen AI 9 HX 370 |
| **iGPU** | AMD Radeon 890M |
| **dGPU** | NVIDIA GeForce RTX 4060 Laptop (Max-Q) |
| **OS** | CachyOS (Arch) |
| **Kernel** | 6.19.3-2 |
| **Display Server** | Wayland (GNOME 49) |
| **Secure Boot** | Ingeschakeld |

## Aanbevolen volgorde

Dit is de volgorde die logisch aanvoelde na een schone CachyOS-installatie:

{{% steps %}}

### Hardware & Drivers

Installeer NVIDIA-drivers, stel Secure Boot in met je eigen ondertekeningssleutels, en configureer ASUS ROG hardware-functies (fan curves, prestatieprofielen, GPU-switching).

→ [NVIDIA Driver Installatie]({{< relref "/docs/hardware/nvidia-driver-installation" >}})
→ [Secure Boot]({{< relref "/docs/hardware/secure-boot" >}})
→ [asusctl & ROG Control Center]({{< relref "/docs/hardware/asusctl-rog-control" >}})

### Beveiliging & Privacy

Stel hardware-gebaseerde LUKS-ontgrendeling in met een YubiKey, en configureer optioneel GDM om het inlogscherm over te slaan na schijfontsluiting.

→ [YubiKey 5C NFC]({{< relref "/docs/security/yubikey" >}})
→ [GDM Autologin]({{< relref "/docs/security/autologin" >}})

### Applicaties

Installeer en configureer applicaties — browser, communicatietools, ontwikkelomgeving en hulpprogramma's. Inclusief niet-voor-de-hand-liggende workarounds voor Brave op GNOME Wayland en touchpad-scrollsnelheid.

→ [Applicaties]({{< relref "/docs/applications" >}})

### Netwerk

eduroam werkend krijgen. De officiële installers werken niet op Linux; een handmatige PEAP/MSCHAPv2-configuratie via nmcli wel.

→ [eduroam Netwerkinstallatie]({{< relref "/docs/networking/eduroam-network-installation" >}})

### Virtualisatie

Windows 11 VM opzetten voor software die niet op Linux draait (Microsoft 365, etc.).

→ [Windows 11 VM Setup]({{< relref "/docs/virtualization/vm-setup" >}})

{{% /steps %}}
