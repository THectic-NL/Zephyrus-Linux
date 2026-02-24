---
title: "Nieuws"
weight: 90
toc: false
---

## Overgestapt naar CachyOS (Arch) — de beste distro voor deze hardware

Na het testen van meerdere distributies ben ik overgestapt op CachyOS (Arch) als mijn dagelijkse driver. CachyOS is een op Arch gebaseerde distributie met diepgaande hardware-specifieke optimalisaties die het onderscheiden voor de Zephyrus G16:

- **BORE/EEVDF scheduler** — CachyOS wordt geleverd met een verbeterde CPU-scheduler die betere responsiviteit en lagere latency biedt bij gemengde workloads
- **Verbeterd energiebeheer** — Betere afhandeling van suspend/resume en ACPI power states op AMD+NVIDIA hybride setups
- **Ondersteuning voor dynamische verversingsfrequentie** — Standaard ondersteuning voor variable refresh rate op het ROG Nebula Display
- **Ingebouwde iGPU- en dGPU-drivers** — De AMD Radeon 890M en NVIDIA RTX 4060 werken correct vanaf een verse installatie, inclusief GPU-switching via `supergfxctl`
- **ASUS Linux-patches gemerged** — Het werk van [Luke Jones](https://asus-linux.org/) (asus-linux.org), waaronder de `asus-armoury`-driver en `asusctl`-tooling, is gemerged in CachyOS. Dit geeft native ondersteuning voor ROG-specifieke functies zoals fan curves, prestatieprofielen en het Slash LED-paneel

Mijn eerste keuze is CachyOS voor deze hardware. Fedora is een sterke tweede — het komt dicht in de buurt en is ook een uitstekende optie als je de voorkeur geeft aan een stabielere releasecyclus boven rolling.

## Kernel 7.0: ASUS laptop quirks + nieuw AMDGPU-werk

Linus heeft bevestigd dat de volgende kernel 7.0 is, met de merge window nu open en een stabiele release verwacht rond midden april 2026. Voor deze ASUS ROG G16 is het belangrijkste nieuws betere grafische driver-ondersteuning: de DRM-updates brengen AMDGPU-ondersteuning voor nieuwere RDNA 3.5-klasse IP blocks (GFX11.5.4) plus verder werk aan NVIDIA Nova/Nouveau, wat moet zorgen voor betere afhandeling van zowel de iGPU als dGPU. Verwachting is dat de Radeon 890M ongeveer 20% sneller kan worden. CachyOS pikt dit op zodra het beschikbaar is.

**Bronnen:** [Linus bevestigt Linux 7.0](https://www.phoronix.com/news/Linux-7.0-Is-Next) · [HID laptop quirks voor ASUS ROG modellen](https://www.phoronix.com/news/Linux-7.0-HID) · [Linux 7.0 DRM/AMDGPU updates](https://www.phoronix.com/news/Linux-7.0-Graphics-Drivers)

## Kernel 6.19: asus-armoury driver in mainline Linux

De `asus-armoury` driver is [gemerged in Linux 6.19](https://www.phoronix.com/news/ASUS-Armoury-Driver-Linux-6.19). Deze nieuwe `platform/x86` driver vervangt delen van de oudere `asus-wmi` met een schonere sysfs-gebaseerde API, waarmee o.a. paneel modus wisselen, APU geheugentoewijzing, PPT tuning en meer mogelijk wordt direct vanuit de kernel. De driver is volledig ontwikkeld door de community, door [Luke Jones](https://asus-linux.org/) (ASUS Linux project), zonder enige betrokkenheid van ASUS zelf. CachyOS levert kernel 6.19.3-2, inclusief deze driver en aanvullende ASUS-specifieke patches.

**Voor** — basale asusctl-bediening zonder Armoury-instellingen:

![ROG Control voor asus-armoury in mainline](/images/rog-control-armoury.avif)

**Na** — volledige Armoury-instellingen zichtbaar, inclusief PPT/vermogenslimiet tuning:

![ROG Control System Control met Armoury-instellingen en vermogenslimieten](/images/rog-control-system-control.png)

**Bronnen:** [Phoronix artikel](https://www.phoronix.com/news/ASUS-Armoury-Driver-Linux-6.19) · [Community discussie](https://www.phoronix.com/forums/forum/software/linux-gaming/1593500-asus-armoury-driver-set-to-be-introduced-in-linux-6-19) · [Patch series (lore.kernel.org)](https://lore.kernel.org/all/20251102215319.3126879-1-denis.benato@linux.dev/)
