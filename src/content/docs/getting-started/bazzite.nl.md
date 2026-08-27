---
title: "Bazzite"
weight: 2
prev: docs/getting-started/cachyos
next: docs/getting-started/topgrade
---

Bazzite is een [Universal Blue](https://universal-blue.org/)-image gebouwd op Fedora Atomic — onderhuids gewoon Fedora, met de gaming-stack en de hardware-onderdelen al in elkaar gezet. Waar CachyOS je een systeem geeft dat je uit elkaar kunt halen, geeft Bazzite je een systeem dat bewust moeilijk uit elkaar te halen is, en daarmee ook moeilijk stuk te krijgen.

Daarmee is het de keuze voor twee soorten mensen: gamers, want Steam, Proton en de controller-stack zitten geconfigureerd in de image, en iedereen die zijn avonden liever niet aan het tweaken van een besturingssysteem besteedt.

Lees deze pagina voordat je installeert, want de dingen die anders zijn dan bij een gewone distributie zijn geen details. Ze veranderen hoe je software installeert en hoe je een fout terugdraait.

## Wat atomic in de praktijk betekent

{{% steps %}}

### `/usr` is read-only

Het systeem staat in een door OSTree beheerde image en is read-only gemount. Je kunt er niet met `dnf install` in installeren en je kunt geen bestand in `/usr/bin` neerzetten. Je configuratie in `/etc` en je data in `/var` zijn van jou; de rest hoort bij de image.

### Een update vervangt de hele image

Een update is geen verzameling packages maar een nieuwe image. Die wordt op de achtergrond opgehaald en gaat in bij de volgende start, waardoor een update je nooit halverwege kan achterlaten.

```bash
ujust update
```

Desktop-images werken zichzelf op de achtergrond bij, dus in de praktijk draai je dit zelden met de hand — vooral vanaf een TTY of via SSH. [Topgrade]({{< relref "/docs/getting-started/topgrade" >}}) kan dit samen met je Flatpaks, Homebrew en containers aansturen.

### De vorige image blijft op schijf staan

Gaat er iets stuk na een update, dan staat de versie die je draaide er nog:

```bash
rpm-ostree rollback
systemctl reboot
```

Hij staat ook in het bootmenu, en dat is wat je redt als je door het probleem geen terminal meer haalt. Dit is het grootste praktische verschil met een rolling distributie.

### Gelaagde packages vragen een herstart

Alles wat niet in de image zit, wordt er *bovenop gelaagd*:

```bash
rpm-ostree install <package>
systemctl reboot
```

Die herstart is niet optioneel — de laag wordt op de volgende image toegepast, niet op de draaiende. Precies daarom is layeren een laatste redmiddel en niet de standaard; zie [Software installeren](#software-installeren) hieronder.

### Home is `/var/home`

`/home` is een symlink naar `/var/home`. Bijna niets merkt het, maar een script met een hardgecodeerd `/home/<gebruiker>`-pad, een `fstab`-regel of een bind-mount van een container wel, en de foutmelding wijst zelden die kant op. Kan iets je home-map niet vinden, controleer dan of de symlink is gevolgd.

### De kernel hoort bij de image

Er is geen kernel om te kiezen en geen kernel om apart bij te werken. Dat is de ruil voor niets hoeven onderhouden: je krijgt de kernel die Bazzite levert, op het moment dat Bazzite hem levert. Kernelparameters kun je nog wel zetten, via `rpm-ostree kargs`:

```bash
rpm-ostree kargs --append=example=1
```

{{% /steps %}}

## Welke image

Bazzite publiceert een aparte image per desktop en per GPU-driver, en je kiest er een door ernaartoe te rebasen. Voor een G16 met de RTX 4060 is dit de relevante keuze:

| Image | Waarvoor |
|---|---|
| `bazzite-gnome-nvidia-open` | GNOME + de open NVIDIA-kernelmodules — **waar deze handleidingen van uitgaan** |
| `bazzite-nvidia-open` | Hetzelfde, maar met KDE Plasma in plaats van GNOME |
| `bazzite-gnome-nvidia` | GNOME + de proprietary driver, voor kaarten van vóór Turing |
| `bazzite-deck-gnome` | Start direct op in Steams Game Mode, voor handhelds en HTPC's |

De `-nvidia-open`-images gebruiken NVIDIA's open kernelmodules, die elke kaart vanaf Turing ondersteunen. De RTX 4060 is Ada en valt daar dus onder; open is hier de juiste standaard.

De rest van deze site is rond GNOME geschreven — de handleidingen voor [autologin]({{< relref "/docs/security/autologin" >}}) en de [YubiKey]({{< relref "/docs/security/yubikey" >}}) configureren GDM, en een aantal applicatie-aanpassingen zijn GNOME-extensies. KDE werkt prima, het is alleen niet wat deze pagina's beschrijven.

{{< callout type="info" >}}
De ISO die je downloadt bepaalt alleen waar je begint. Later van desktop of driver wisselen is een rebase, geen herinstallatie.
{{< /callout >}}

### Rebasen naar een andere image

```bash
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/ublue-os/bazzite-gnome-nvidia-open:stable
systemctl reboot
```

`ostree-image-signed:` controleert de handtekening van de image. Brengt een rebase je ergens waar je niet wilt zijn, dan staat de image waar je vandaan kwam er nog — `rpm-ostree rollback` en herstarten.

## Secure Boot

Anders dan CachyOS start Bazzite gewoon op met Secure Boot aan, want het gebruikt shim. Wel moet de sleutel van Universal Blue één keer worden ingeschreven, anders laden de NVIDIA-kernelmodules niet.

→ [Secure Boot op Bazzite]({{< relref "/docs/hardware/secure-boot-bazzite" >}})

## Software installeren

Hier moeten de gewoontes van een gewone distributie overboord. Dit is Bazzites eigen volgorde van voorkeur, van meest naar minst aanbevolen:

{{% steps %}}

### Flatpak

De belangrijkste manier om grafische applicaties te installeren. Sandboxed, los van de image, en apart van het systeem bijgewerkt.

```bash
flatpak install flathub org.example.App
```

Bazzite levert **Bazaar** mee als grafische store hiervoor.

### Homebrew

Voor commandline-tools. Installeert in `/home/linuxbrew`, dus zonder layering en zonder herstart, en het raakt de image niet aan.

```bash
brew install <tool>
```

### Distrobox

Voor alles wat een echte package manager nodig heeft, en voor ontwikkelomgevingen. Een distrobox-container deelt je home-map en kan applicaties naar het menu van de host exporteren, waardoor een tool die in een Arch- of Fedora-container staat zich gedraagt als lokaal geïnstalleerd.

```bash
distrobox enter <container>
distrobox-export --app <package>
```

Bazzite levert voorgeconfigureerde containers mee waar je uit kunt kiezen:

```bash
ujust distrobox-assemble
```

Dit is het onderdeel dat op een atomic systeem het meeste werk doet. Op CachyOS is distrobox een gemak; hier is het de manier om aan een CLI-toolchain te komen zonder de image aan te raken.

### rpm-ostree-layering

Laatste redmiddel, voor dingen die echt onderdeel van het systeem moeten zijn — een driver, een kernelmodule, een systeemdienst.

```bash
rpm-ostree install <package>
systemctl reboot
```

Elk gelaagd package wordt opnieuw toegepast op elke nieuwe image, dus een package dat niet meer bouwt tegen een nieuwere Fedora blokkeert je updates. Houd die lijst kort en kijk er af en toe naar:

```bash
rpm-ostree status
```

{{% /steps %}}

## `ujust`

Bazzite verpakt zijn gebruikelijke onderhoudstaken in `ujust`-recepten. Zo zie je wat de geïnstalleerde image aanbiedt:

```bash
ujust
```

In deze handleidingen komen `ujust update`, `ujust enroll-secure-boot-key` en `ujust distrobox-assemble` voorbij. De lijst hangt van de image af, dus kijk op je eigen installatie in plaats van aan te nemen dat een recept bestaat.

## Aanbevolen volgorde

{{% steps %}}

### Hardware & Drivers

De NVIDIA-driver zit al in de image, dus dit is controleren plus de Secure Boot-sleutel inschrijven. Daarna de ASUS ROG hardware-functies, waarvoor `asusctl` vanuit de Terra-repository gelaagd moet worden.

→ [NVIDIA Driver: Bazzite]({{< relref "/docs/hardware/nvidia-bazzite" >}})
→ [Secure Boot op Bazzite]({{< relref "/docs/hardware/secure-boot-bazzite" >}})
→ [asusctl & ROG Control Center]({{< relref "/docs/hardware/asusctl-rog-control" >}})
→ [Kleurprofielen voor het scherm]({{< relref "/docs/hardware/color-profiles" >}})

### Beveiliging & Privacy

Configureer optioneel GDM om het inlogscherm over te slaan na schijfontsluiting. Stel de YubiKey in voor `sudo` en de GNOME-schermvergrendeling via pam-u2f.

→ [GDM Autologin]({{< relref "/docs/security/autologin" >}})
→ [YubiKey]({{< relref "/docs/security/yubikey" >}})

### Applicaties

Installeer en configureer applicaties. De meeste zijn Flatpaks en installeren op beide distributies hetzelfde; de pagina markeert de uitzonderingen.

→ [Applicaties]({{< relref "/docs/applications" >}})

### Netwerk

eduroam werkend krijgen. NetworkManager is NetworkManager, dus deze pagina is op beide distributies hetzelfde.

→ [eduroam Netwerkinstallatie]({{< relref "/docs/networking/eduroam-network-installation" >}})

### Virtualisatie

Windows 11 VM opzetten voor software die niet op Linux draait. Podman zit hier al in de image, wat de container-opties de weg van de minste weerstand maakt.

→ [Virt-Manager / KVM]({{< relref "/docs/virtualization/vm-setup" >}})
→ [Podman & Podman Desktop]({{< relref "/docs/virtualization/podman" >}})

{{% /steps %}}

## Meer lezen

- [Bazzite-documentatie](https://docs.bazzite.gg/)
- [Bazzite op GitHub](https://github.com/ublue-os/bazzite)
- [Universal Blue](https://universal-blue.org/)
- [Documentatie van Fedora Atomic Desktops](https://docs.fedoraproject.org/en-US/fedora-silverblue/)
