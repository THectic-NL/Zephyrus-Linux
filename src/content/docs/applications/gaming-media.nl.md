---
title: "Gaming & Media"
weight: 4
prev: docs/applications/development
next: docs/applications/utilities
---

### Steam

{{< tabs >}}
{{< tab name="CachyOS" >}}

Steam zit in Arch's [multilib-repository](https://archlinux.org/packages/multilib/x86_64/steam/), die CachyOS standaard aanzet, dus je hebt geen extra repos nodig.

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

Steam downloadt Proton zelf zodra een Windows-game het nodig heeft, zie [Proton en de Steam Linux Runtime]({{< relref "/docs/gaming/proton-slr" >}}).

### Tidal

Er bestaat geen officiële Tidal client voor Linux. Twee community-alternatieven bestaan.

#### High Tide (aanbevolen)

[High Tide](https://flathub.org/apps/io.github.nokse22.high-tide) is een native GTK4 frontend voor Tidal, niet een Electron wrapper, maar een werkelijke applicatie gebouwd met proper Linux toolkit. Het ziet er schoon uit, integreert goed met GNOME, en ondersteunt Hi-Fi quality.

```bash
flatpak install flathub io.github.nokse22.high-tide
```

Het komt op beide distributies van Flathub. De AUR heeft ook een `high-tide`-pakket, maar de Flatpak doet hetzelfde zonder community-buildscript.

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
