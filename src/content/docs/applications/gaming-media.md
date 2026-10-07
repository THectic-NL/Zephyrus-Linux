---
title: "Gaming & Media"
weight: 4
prev: docs/applications/development
next: docs/applications/utilities
---

### Steam

{{< tabs >}}
{{< tab name="CachyOS" >}}

Steam is in Arch's [multilib repository](https://archlinux.org/packages/multilib/x86_64/steam/), which CachyOS enables by default, so no extra repos are needed.

```bash
sudo pacman -S steam
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Nothing to install. Steam is part of the image. Gaming is what Bazzite is built around, and it ships configured, with the Proton and controller pieces already in place.

```bash
which steam
```

{{< /tab >}}
{{< /tabs >}}

![Steam in GNOME Software](/images/steam-website.avif)

Steam downloads Proton itself the first time a Windows game needs it, see [Proton & the Steam Linux Runtime]({{< relref "/docs/gaming/proton-slr" >}}).

### Tidal

There's no official Tidal client for Linux. Two community alternatives exist.

#### High Tide (recommended)

[High Tide](https://flathub.org/apps/io.github.nokse22.high-tide) is a native GTK4 frontend for Tidal, not an Electron wrapper, but an actual application built with proper Linux toolkit. It looks clean, integrates well with GNOME, and supports Hi-Fi quality.

```bash
flatpak install flathub io.github.nokse22.high-tide
```

It comes from Flathub on both distributions. The AUR has a `high-tide` package as well, but the Flatpak does the same job without a community build script.

![High Tide running on GNOME](/images/high-tide.avif)

#### Tidal Hi-Fi

[Tidal Hi-Fi](https://github.com/Mastermindzh/tidal-hifi) by Rick van Lieshout is an Electron wrapper around the Tidal web player. Works, but it's essentially the web app packaged as a desktop app.

![Tidal Hi-Fi in the Flathub store](/images/tidal-hifi-flathub.avif)

### Bottles: running Windows software

[Bottles](https://usebottles.com/) lets you run Windows software via Wine. Bottles is **only officially distributed via Flatpak**; ignore any other versions you may find in the AUR or elsewhere, as they are not official and not supported by the Bottles developers.

```bash
flatpak install flathub com.usebottles.bottles
```

Alternatively, open GNOME Software Center, search for "Bottles", and make sure to select the **Flathub** source.

For anything that doesn't work under Wine (like Microsoft 365), I use a Windows VM instead. See [Virt-Manager / KVM]({{< relref "/docs/virtualization/vm-setup" >}}).

![Bottles in the Flathub store](/images/bottles-flathub.avif)
