---
title: "Aan de slag"
weight: 1
next: docs/hardware/nvidia-driver-installation
---

Dit is mijn persoonlijke setup-documentatie voor de ROG Zephyrus G16 op CachyOS (Arch). Ik ben geen software-engineer of developer, gewoon iemand die overgestapt is naar Linux en daarna tegen van alles aanliep wat niet meteen werkte. Ik heb alles opgeschreven zodat anderen niet hetzelfde hoeven uit te zoeken als ik.

Als iets hier je helpt: mooi. Loop je ergens tegenaan wat ik niet behandeld heb, laat het gerust weten; ik denk graag mee.

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

![Systeeminformatie-overzicht](/images/system-info.avif)

## Waarom CachyOS?

Na het testen van meerdere distributies ben ik overgestapt op CachyOS (Arch) als mijn dagelijkse driver. CachyOS is een op Arch gebaseerde distributie met hardware-specifieke optimalisaties die het onderscheiden voor de Zephyrus G16:

- **BORE/EEVDF scheduler**: CachyOS wordt geleverd met een verbeterde CPU-scheduler die betere responsiviteit en lagere latency biedt bij gemengde workloads
- **Verbeterd energiebeheer**: betere afhandeling van suspend/resume en ACPI power states op AMD+NVIDIA hybride setups
- **Ondersteuning voor dynamische verversingsfrequentie**: standaard ondersteuning voor variable refresh rate op het ROG Nebula Display
- **Ingebouwde iGPU- en dGPU-drivers**: de AMD Radeon 890M en NVIDIA RTX 4060 werken correct vanaf een verse installatie, inclusief GPU-switching via `asusctl armoury`
- **ASUS Linux-patches**: een deel van het werk van [Luke Jones](https://asus-linux.org/) is gemerged in de Linux kernel zelf (de `asus-armoury`-driver vanaf 6.19), terwijl aanvullende ROG-specifieke patches en `asusctl`-verbeteringen via CachyOS worden meegeleverd. Zowel `asusctl` als `rog-control-center` zijn direct beschikbaar vanuit de CachyOS repos; twee packages installeren en je bent klaar, zonder diepe systeemconfiguratie. CachyOS bevat op dit moment de meest volledige set aan optimalisaties voor deze hardware

Fedora is een sterke tweede, een solide keuze als je de voorkeur geeft aan een stabielere releasecyclus boven rolling. Je zit goed zolang je op kernel 6.19 draait, die al beschikbaar is op Fedora, maar je moet wel even updaten. Dat gezegd hebbende voelt CachyOS nog altijd beter aan voor deze hardware: de CPU-scheduler tuning (BORE/EEVDF), vooraf geconfigureerde NVIDIA-driver ondersteuning en nauwere integratie met `asusctl` maken het dagelijks gebruik soepeler, zonder extra configuratie.

## CachyOS Kernel Manager

CachyOS wordt geleverd met de **CachyOS Kernel Manager** als voorgeïnstalleerde GUI-tool. Hiermee beheer je geïnstalleerde kernels en configureer je de `sched-ext` scheduler, het extensible scheduler framework van de Linux kernel waarmee een userspace-scheduler de standaard kan vervangen.

Ik gebruik `scx_lavd` met het profiel ingesteld op **Auto**. LAVD (Latency-criticality Aware Virtual Deadline) is een scheduler die ontworpen is voor gemengde interactieve en compute-workloads, wat hem goed geschikt maakt voor een laptop die je zowel dagelijks als voor gaming gebruikt.

![CachyOS Kernel Manager - Configure sched-ext met scx_lavd](/images/cachyos-kernel-manager-sched-ext.avif)

De scheduler kan op elk moment worden gewijzigd zonder herstart.

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

Installeer en configureer applicaties: browser, communicatietools, ontwikkelomgeving en hulpprogramma's. Inclusief niet-voor-de-hand-liggende workarounds voor Brave op GNOME Wayland en touchpad-scrollsnelheid.

→ [Applicaties]({{< relref "/docs/applications" >}})

### Netwerk

eduroam werkend krijgen. De officiële installers werken niet op Linux; een handmatige PEAP/MSCHAPv2-configuratie via nmcli wel.

→ [eduroam Netwerkinstallatie]({{< relref "/docs/networking/eduroam-network-installation" >}})

### Virtualisatie

Windows 11 VM opzetten voor software die niet op Linux draait (Microsoft 365, etc.).

→ [Windows 11 VM Setup]({{< relref "/docs/virtualization/vm-setup" >}})

{{% /steps %}}
