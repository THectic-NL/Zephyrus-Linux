---
title: "Gaming & Media"
weight: 4
prev: docs/applications/development
next: docs/applications/utilities
---

### Steam

{{< tabs >}}
{{< tab name="CachyOS" >}}

Steam is direct beschikbaar uit de [CachyOS repository](https://packages.cachyos.org/package/cachyos/x86_64/steam), geen extra repos nodig.

```bash
sudo pacman -S steam
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Niets te installeren. Steam is deel van de image. Gaming is waar Bazzite rond is gebouwd, en het levert geconfigureerd, met de Proton en controller pieces al in plaats.

```bash
which steam
```

{{< /tab >}}
{{< /tabs >}}

![Steam in GNOME Software](/images/steam-website.avif)

Herstart na installatie. Steam inclusief Proton out of the box voor het draaien van Windows games op Linux.

### Tidal

Er bestaat geen officiële Tidal client voor Linux. Twee community-alternatieven bestaan.

#### High Tide (aanbevolen)

[High Tide](https://aur.archlinux.org/packages/high-tide) is een native GTK4 frontend voor Tidal, niet een Electron wrapper, maar een werkelijke applicatie gebouwd met proper Linux toolkit. Het ziet er schoon uit, integreert goed met GNOME, en ondersteunt Hi-Fi quality.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
paru -S high-tide
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub io.github.nokse22.high-tide
```

{{< /tab >}}
{{< /tabs >}}

![High Tide op GNOME](/images/high-tide.avif)

#### Tidal Hi-Fi

[Tidal Hi-Fi](https://github.com/Mastermindzh/tidal-hifi) van Rick van Lieshout is een Electron wrapper rond de Tidal web player. Werkt, maar het is eigenlijk de web app verpakt als desktop app.

![Tidal Hi-Fi in de Flathub store](/images/tidal-hifi-flathub.avif)

### Bottles: Windows-software draaien

[Bottles](https://usebottles.com/) laat je Windows-software via Wine draaien. Bottles is **alleen officieel beschikbaar via Flatpak**; negeer andere versies die je in de AUR of elders kunt vinden, omdat die niet officieel zijn en niet door de Bottles developers worden ondersteund.

```bash
flatpak install flathub com.usebottles.bottles
```

U kunt ook GNOME Software Center openen, naar "Bottles" zoeken en ervoor zorgen dat u de **Flathub**-bron selecteert.

Voor alles wat niet onder Wine werkt (zoals Microsoft 365), gebruik ik in plaats daarvan een Windows VM. Zie [Virt-Manager / KVM]({{< relref "/docs/virtualization/vm-setup" >}}).

![Bottles in de Flathub store](/images/bottles-flathub.avif)
