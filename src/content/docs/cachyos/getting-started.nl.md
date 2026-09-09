---
title: "Aan de slag"
weight: 1
prev: docs/cachyos
next: docs/cachyos/updates
distro: cachyos
---

CachyOS is een op Arch gebaseerde distributie met hardware-specifieke optimalisaties, en één van de twee die ik op de G16 als dagelijks systeem heb gedraaid. Dit is de optie voor wie de machine zelf in handen wil: je kiest de kernel, de scheduler en elk package, en het onderhoud dat daarbij hoort neem je erbij. Spreekt die ruil je niet aan, lees dan eerst [Bazzite]({{< relref "/docs/bazzite/getting-started" >}}) voordat je iets installeert.

## Waarom CachyOS

- **BORE/EEVDF scheduler**: CachyOS wordt geleverd met een verbeterde CPU-scheduler die betere responsiviteit en lagere latency biedt bij gemengde workloads
- **Verbeterd energiebeheer**: betere afhandeling van suspend/resume en ACPI power states op AMD+NVIDIA hybride setups
- **Ondersteuning voor dynamische verversingsfrequentie**: standaard ondersteuning voor variable refresh rate op het ROG Nebula Display
- **Ingebouwde iGPU- en dGPU-drivers**: de AMD Radeon 890M en NVIDIA RTX 4060 werken correct vanaf een verse installatie, inclusief GPU-switching via `asusctl armoury`
- **ASUS Linux-patches**: een deel van het werk van [Luke Jones](https://asus-linux.org/) is gemerged in de Linux kernel zelf (de `asus-armoury`-driver vanaf 6.19), terwijl aanvullende ROG-specifieke patches en `asusctl`-verbeteringen via CachyOS worden meegeleverd. Zowel `asusctl` als `rog-control-center` zijn direct beschikbaar vanuit de CachyOS repos; twee packages installeren en je bent klaar, zonder diepe systeemconfiguratie

## Wat rolling hier betekent

Packages komen binnen zodra upstream ze uitbrengt. Er is geen release om naar te upgraden en geen versienummer om op achter te lopen, maar er is ook niets dat een wijziging tegenhoudt. `sudo pacman -Syu` is dus iets wat je bewust doet, niet iets wat je overkomt. Het systeem is volledig beschrijfbaar, dus een package is bruikbaar zodra het installeert, en alleen een nieuwe kernel vraagt een herstart. Gaat een update mis, dan draai je hem met de hand terug. Dat is het belangrijkste praktische verschil met Bazzite, waar een slechte update één `rpm-ostree rollback` verderop ligt.

→ [Bijwerken]({{< relref "/docs/cachyos/updates" >}}) behandelt `pacman`, de kernel en de CachyOS Kernel Manager, en alles in één commando bijwerken met Topgrade.

## Secure Boot vóór het installeren

CachyOS gebruikt geen shim, dus Secure Boot moet **uit** staan voordat de installer wil opstarten. Daarna kun je het weer aanzetten met je eigen ondertekeningssleutels.

→ [Secure Boot op CachyOS]({{< relref "/docs/cachyos/secure-boot" >}})

## Aanbevolen volgorde

Dit is de volgorde die logisch aanvoelde na een schone CachyOS-installatie:

{{% steps %}}

### Hardware & Drivers

De NVIDIA-driver is al door de installer geconfigureerd, dus dit is vooral controleren. Stel daarna Secure Boot in met je eigen ondertekeningssleutels en configureer de ASUS ROG hardware-functies (fan curves, prestatieprofielen, GPU-switching).

→ [NVIDIA Driver: CachyOS]({{< relref "/docs/cachyos/nvidia" >}})
→ [Secure Boot op CachyOS]({{< relref "/docs/cachyos/secure-boot" >}})
→ [asusctl & ROG Control Center]({{< relref "/docs/hardware/asusctl-rog-control" >}})
→ [Kleurprofielen voor het scherm]({{< relref "/docs/hardware/color-profiles" >}})

### Beveiliging & Privacy

Configureer optioneel GDM om het inlogscherm over te slaan na schijfontsluiting. Stel de YubiKey in voor `sudo` en de GNOME-schermvergrendeling via pam-u2f.

→ [GDM Autologin]({{< relref "/docs/security/autologin" >}})
→ [YubiKey]({{< relref "/docs/security/yubikey" >}})

### Applicaties

Installeer en configureer applicaties: browser, communicatietools, ontwikkelomgeving en hulpprogramma's. Inclusief niet-voor-de-hand-liggende workarounds voor Brave op GNOME Wayland en touchpad-scrollsnelheid.

→ [Applicaties]({{< relref "/docs/applications" >}})

### Netwerk

eduroam werkend krijgen. De officiële installers werken niet op Linux; een handmatige PEAP/MSCHAPv2-configuratie via nmcli wel.

→ [eduroam Netwerkinstallatie]({{< relref "/docs/networking/eduroam-network-installation" >}})

### Virtualisatie

Windows 11 VM opzetten voor software die niet op Linux draait (Microsoft 365, etc.), of VMware Workstation gebruiken voor meer geavanceerde virtualisatiebehoeften.

→ [Virt-Manager / KVM]({{< relref "/docs/virtualization/vm-setup" >}})
→ [VMware Workstation]({{< relref "/docs/virtualization/vmware-workstation" >}})

{{% /steps %}}

## Meer lezen

- [CachyOS Wiki](https://wiki.cachyos.org/)
- [CachyOS installatiedocumentatie](https://wiki.cachyos.org/installation/installation_on_root/)
- [Arch Wiki](https://wiki.archlinux.org/)
