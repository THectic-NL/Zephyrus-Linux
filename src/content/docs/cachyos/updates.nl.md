---
title: "Bijwerken"
weight: 2
prev: docs/cachyos/getting-started
next: docs/cachyos/nvidia
distro: cachyos
---

De systeemupdate is één commando:

```bash
sudo pacman -Syu
```

Het is een rolling distributie, dus dat *is* de update — er is geen release om naartoe te gaan. Alles wat `pacman` in `/usr` installeert is bruikbaar zodra het klaar is; alleen een nieuwe kernel vraagt een herstart.

Breekt een update iets, dan draai je met de hand terug: herinstalleer het vorige package uit de cache in `/var/cache/pacman/pkg/`, of haal het uit het [Arch Linux Archive](https://archive.archlinux.org/). Goed om te weten voordat je het nodig hebt.

## De kernel

CachyOS levert de **CachyOS Kernel Manager** als voorgeïnstalleerde GUI. Die beheert geïnstalleerde kernels en configureert de `sched-ext`-scheduler — het framework van de kernel om er een userspace-CPU-scheduler in te wisselen.

Ik draai `scx_lavd` met het profiel op **Auto**. LAVD (Latency-criticality Aware Virtual Deadline) is gebouwd voor gemengde interactieve en compute-workloads, wat past bij een laptop voor zowel dagelijks werk als gaming. De scheduler kun je op elk moment wisselen zonder herstart.

![CachyOS Kernel Manager - sched-ext configureren met scx_lavd](/images/cachyos-kernel-manager-sched-ext.avif)

## De rest, in één keer

Het systeem is maar een deel. Er zijn ook de Flatpaks, wat Homebrew in je home-map heeft gezet, de distrobox-containers, de firmware, en een handvol tools die zichzelf bijwerken. [Topgrade](https://github.com/topgrade-rs/topgrade) draait ze allemaal achter elkaar en vertelt je wat het gedaan heeft.

Het is een gemak, geen package manager. Alles wat het doet kun je met de hand doen; de winst is dat je de Flatpaks niet meer drie weken vergeet.

### Wat het hier draait

| Stap | Wat het draait |
|---|---|
| Systeempackages | `pacman`, via je AUR-helper als je die hebt, dus inclusief de AUR |
| Flatpak | `flatpak update` |
| Firmware | `fwupdmgr` |
| Containers | haalt nieuwere images op voor de containers die je hebt |
| Distrobox | werkt bij binnen elke container |
| Taal-tools | `cargo`, `rustup`, `npm`, `pipx` en dergelijke, als ze er zijn |

### Installeren

```bash
sudo pacman -S topgrade
```

Zit hij niet in de repos op jouw installatie, dan heeft de AUR zowel `topgrade` als `topgrade-bin`.

### Draaien

```bash
topgrade
```

Dat is de hele interface. Handige vlaggen:

```bash
topgrade --dry-run          # laat zien wat er zou draaien, draait niets
topgrade --only system      # alleen de systeempackages
topgrade --disable firmware # sla een stap over voor deze run
topgrade -y                 # niet vragen voor elke stap
```

`--dry-run` is op een nieuwe installatie één keer de moeite waard — het print de gedetecteerde stappen, de snelste manier om te ontdekken dat het iets níét oppikt.

### Configuratie

Het configuratiebestand wordt bij de eerste run aangemaakt op `~/.config/topgrade.toml`.

De instelling die op deze laptop het meest oplevert is firmware overslaan, want `fwupdmgr` wil op de G16 herstarten naar de firmware-updater en dat is zelden wat je midden in een update wilt:

```toml
[misc]
disable = ["firmware"]

# Doorgaan als een stap faalt in plaats van de run stoppen
ignore_failures = ["containers"]

# Niet vragen voor elke stap
assume_yes = true
```

Wijs hem naar je AUR-helper zodat de AUR meegaat in plaats van overgeslagen wordt:

```toml
[linux]
arch_package_manager = "paru"
```

## Referenties

- [Topgrade op GitHub](https://github.com/topgrade-rs/topgrade)
- [Topgrade: configuratiereferentie](https://github.com/topgrade-rs/topgrade/blob/main/config.example.toml)
- [Arch Linux Archive](https://archive.archlinux.org/)
