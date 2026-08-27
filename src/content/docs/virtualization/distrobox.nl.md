---
title: "Distrobox"
weight: 5
prev: docs/virtualization/podman
next: docs/virtualization/vmware-workstation
---

[Distrobox](https://distrobox.it/) draait de userspace van een andere distributie in een container die strak met je sessie verweven is: dezelfde home-map, dezelfde gebruiker, hetzelfde X/Wayland-scherm, en applicaties kunnen naar het menu van je host geëxporteerd worden. Eronder zit [Podman]({{< relref "/docs/virtualization/podman" >}}).

Het is geen VM en geen sandbox. Een distrobox-container deelt je home-map en draait als jou — het is een manier om aan de *packages van een andere distributie* te komen, niet om iets van jezelf af te schermen.

Hoeveel dit uitmaakt hangt volledig af van welke distributie je draait.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Een gemak. Je hebt `pacman` en de AUR al, en die dekken vrijwel alles, dus distrobox is er voor de uitzonderingen: een tool die alleen als `.deb` wordt uitgeleverd, een project dat een oudere toolchain nodig heeft dan de rolling versie, of een buildomgeving die je liever niet op de host hebt.

Af en toe nuttig. Je kunt er maanden zonder.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Basisinfrastructuur. `/usr` is read-only, layeren is een laatste redmiddel en kost een herstart, en Homebrew dekt maar zoveel — dus als je een echte package manager nodig hebt, ís distrobox het antwoord. Het staat derde in Bazzites eigen voorkeursvolgorde, boven layeren, en in de praktijk draagt het het meeste ontwikkelwerk.

Kom je van een gewone distributie, dan is dit de gewoonte om aan te leren. "Ik installeer het gewoon even op de host" is het instinct om af te leren.

{{< /tab >}}
{{< /tabs >}}

## Installeren

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S distrobox podman
```

Podman staat uitgebreider op [zijn eigen pagina]({{< relref "/docs/virtualization/podman" >}}).

{{< /tab >}}
{{< tab name="Bazzite" >}}

Niets te installeren. Distrobox en Podman zitten allebei in de image:

```bash
distrobox version
```

{{< /tab >}}
{{< /tabs >}}

## Een container maken

```bash
distrobox create --name arch --image archlinux:latest
distrobox enter arch
```

De eerste keer binnenkomen duurt even — je gebruiker wordt in de container aangemaakt en de home-map wordt gekoppeld. Daarna is het gewoon een shell.

Images die de moeite waard zijn:

| Image | Waarvoor |
|---|---|
| `archlinux:latest` | De AUR, en alles wat voor Arch gedocumenteerd is |
| `fedora:latest` | Komt overeen met Bazzites basis; daar de minst verrassende keuze |
| `ubuntu:24.04` | Software die alleen ooit een `.deb` uitbrengt |
| `debian:stable` | Oudere, stabiele toolchains |

{{< tabs >}}
{{< tab name="CachyOS" >}}

Een Arch-container is hier grotendeels overbodig — je zit al op Arch. Grijp liever naar Ubuntu of Debian; dáár verdient distrobox op deze distributie zijn plek.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Bazzite levert voorgeconfigureerde containerdefinities mee, wat minder typen is en je images geeft die hier al op ingericht zijn:

```bash
ujust distrobox-assemble
```

Kies uit de lijst. De **Arch**-container is hier de interessante: die geeft je `pacman` en de AUR op een atomic Fedora-systeem, wat een even vreemd als nuttig bezit is.

{{< /tab >}}
{{< /tabs >}}

## Applicaties exporteren

Een container is pas nuttig als je er niet over hoeft na te denken. Exporteren zet een starter op de host die de container voor je binnengaat.

```bash
# Vanuit de container
distrobox-export --app <applicatie>
distrobox-export --bin /usr/bin/<commando>
```

`--app` zet de applicatie in je bureaubladmenu. `--bin` zet een wrapper in `~/.local/bin`, zodat het commando vanuit een terminal op de host werkt alsof het daar geïnstalleerd is.

Ongedaan maken:

```bash
distrobox-export --delete --app <applicatie>
```

Dit is wat de opzet leefbaar maakt: na het exporteren gedraagt een tool uit een Ubuntu-container zich als elke andere applicatie in je starter.

## Opruimen

```bash
distrobox list
distrobox stop <naam>
distrobox rm -f <naam>
```

Containers zijn bedoeld om weg te gooien. Komt er een in een toestand die je niet kunt verklaren, gooi hem dan weg en maak een nieuwe — dat is goedkoper dan debuggen, en je home-map blijft hoe dan ook ongemoeid.

{{< callout type="warning" >}}
Omdat de home-map gedeeld is, kan een container in je dotfiles schrijven. Een container die `~/.bashrc` herschrijft, of een taal-toolchain die in `~/.local` installeert, raakt daarmee ook de host en elke andere container. Het is de meest voorkomende verrassing bij distrobox, en een gevolg van het ontwerp, geen bug.

Houd projectstatus binnen de projectmap en wees bewust met alles wat naar `~` schrijft.
{{< /callout >}}

## Specifiek op Bazzite

- **`/var/home`.** Je home-map is `/var/home/<gebruiker>` met `/home` als symlink daarnaartoe. Distrobox gaat daar goed mee om, maar een script binnen een container dat `/home/<gebruiker>` hardcodeert misschien niet. "Bestaat niet" binnen een container terwijl het er buiten duidelijk wél is: dit is waarom.
- **Wat op de host hoort.** Alles wat de kernel of de inlogsessie moet laden — drivers, kernelmodules, PAM-modules, systeemdiensten — kan niet uit een container komen. Daar is layeren voor, en daarom zijn [`asusctl`]({{< relref "/docs/hardware/asusctl-rog-control" >}}) en `pam-u2f` gelaagd en niet gecontaineriseerd.
- **Eerst Homebrew voor kale CLI-tools.** Is een tool één binary zonder systeemintegratie, dan is `brew install` eenvoudiger dan een container. Distrobox is voor als je de package manager van een distributie nodig hebt, niet voor elk commandline-programma.

## Referenties

- [Distrobox](https://distrobox.it/)
- [Distrobox op GitHub](https://github.com/89luca89/distrobox)
- [Bazzite: Distrobox](https://docs.bazzite.gg/Installing_and_Managing_Software/Distrobox/)
