---
title: "CachyOS"
weight: 1
prev: docs/getting-started
next: docs/getting-started/bazzite
---

CachyOS is een op Arch gebaseerde distributie met hardware-specifieke optimalisaties, en het is wat ik als dagelijkse driver op de G16 draai. Dit is de optie voor wie de machine zelf in handen wil: je kiest de kernel, de scheduler en elk package, en het onderhoud dat daarbij hoort neem je erbij. Spreekt die ruil je niet aan, lees dan eerst [Bazzite]({{< relref "/docs/getting-started/bazzite" >}}) voordat je iets installeert.

## Waarom CachyOS

- **BORE/EEVDF scheduler**: CachyOS wordt geleverd met een verbeterde CPU-scheduler die betere responsiviteit en lagere latency biedt bij gemengde workloads
- **Verbeterd energiebeheer**: betere afhandeling van suspend/resume en ACPI power states op AMD+NVIDIA hybride setups
- **Ondersteuning voor dynamische verversingsfrequentie**: standaard ondersteuning voor variable refresh rate op het ROG Nebula Display
- **Ingebouwde iGPU- en dGPU-drivers**: de AMD Radeon 890M en NVIDIA RTX 4060 werken correct vanaf een verse installatie, inclusief GPU-switching via `asusctl armoury`
- **ASUS Linux-patches**: een deel van het werk van [Luke Jones](https://asus-linux.org/) is gemerged in de Linux kernel zelf (de `asus-armoury`-driver vanaf 6.19), terwijl aanvullende ROG-specifieke patches en `asusctl`-verbeteringen via CachyOS worden meegeleverd. Zowel `asusctl` als `rog-control-center` zijn direct beschikbaar vanuit de CachyOS repos; twee packages installeren en je bent klaar, zonder diepe systeemconfiguratie

## Wat rolling hier betekent

Packages komen binnen zodra upstream ze uitbrengt. Er is geen release om naar te upgraden en geen versienummer om op achter te lopen, maar er is ook niets dat een wijziging tegenhoudt — updaten is dus iets wat je bewust doet, niet iets wat je overkomt.

```bash
sudo pacman -Syu
```

Het systeem is volledig beschrijfbaar. `pacman` installeert in `/usr` en het package is bruikbaar zodra het klaar is; alleen een nieuwe kernel vraagt om een herstart.

Gaat een update wél mis, dan draai je hem met de hand terug — het package downgraden vanuit de pacman-cache in `/var/cache/pacman/pkg/`, of vanuit het [Arch Linux Archive](https://wiki.archlinux.org/title/Arch_Linux_Archive). Handig om te weten vóórdat je het nodig hebt. Dit is het belangrijkste praktische verschil met Bazzite, waar een slechte update één `rpm-ostree rollback` verderop ligt.

{{< callout type="info" >}}
Alles in één keer bijwerken — pacman, de AUR, Flatpak en de rest — staat op de pagina [Topgrade]({{< relref "/docs/getting-started/topgrade" >}}).
{{< /callout >}}

## CachyOS Kernel Manager

CachyOS wordt geleverd met de **CachyOS Kernel Manager** als voorgeïnstalleerde GUI-tool. Hiermee beheer je geïnstalleerde kernels en configureer je de `sched-ext` scheduler, het extensible scheduler framework van de Linux kernel waarmee een userspace-scheduler de standaard kan vervangen.

Ik gebruik `scx_lavd` met het profiel ingesteld op **Auto**. LAVD (Latency-criticality Aware Virtual Deadline) is een scheduler die ontworpen is voor gemengde interactieve en compute-workloads, wat hem goed geschikt maakt voor een laptop die je zowel dagelijks als voor gaming gebruikt.

![CachyOS Kernel Manager - Configure sched-ext met scx_lavd](/images/cachyos-kernel-manager-sched-ext.avif)

De scheduler kan op elk moment worden gewijzigd zonder herstart.

## Secure Boot vóór het installeren

CachyOS gebruikt geen shim, dus Secure Boot moet **uit** staan voordat de installer wil opstarten. Daarna kun je het weer aanzetten met je eigen ondertekeningssleutels.

→ [Secure Boot op CachyOS]({{< relref "/docs/hardware/secure-boot-cachyos" >}})

## Aanbevolen volgorde

Dit is de volgorde die logisch aanvoelde na een schone CachyOS-installatie:

{{% steps %}}

### Hardware & Drivers

De NVIDIA-driver is al door de installer geconfigureerd, dus dit is vooral controleren. Stel daarna Secure Boot in met je eigen ondertekeningssleutels en configureer de ASUS ROG hardware-functies (fan curves, prestatieprofielen, GPU-switching).

→ [NVIDIA Driver: CachyOS]({{< relref "/docs/hardware/nvidia-cachyos" >}})
→ [Secure Boot op CachyOS]({{< relref "/docs/hardware/secure-boot-cachyos" >}})
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
