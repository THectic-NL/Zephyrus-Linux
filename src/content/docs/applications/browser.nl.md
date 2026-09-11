---
title: "Browser"
weight: 1
prev: docs/applications
next: docs/applications/productivity
---

### Brave

Ik gebruik [Brave Origin](https://packages.cachyos.org/package/cachyos/x86_64/brave-origin-bin) als mijn standaard browser. Ik ben begonnen met regular Brave en ben later overgegaan op Brave Origin. Het voelt opmerkelijk lichter en sneller, heeft minder ingebouwde features, en voor de meeste mensen is het waarschijnlijk het betere startpunt.

Brave Origin is de afgeslankte versie van Brave. Op Windows is het een betaald product ($60); op Linux is het gratis.

Brave zelf adviseert een native package boven de Flatpak waar die beschikbaar is; de Flatpak werkt maar voelt een beetje geïsoleerd.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Zowel Brave als Brave Origin zijn beschikbaar uit drie bronnen: de CachyOS-repositories, de AUR, en Flathub. Het CachyOS native package geeft de beste integratie.

**Brave Origin installeren (aanbevolen):**

```bash
sudo pacman -S brave-origin-bin
```

**Of regular Brave, als je het volledige feature-set wilt:**

```bash
sudo pacman -S brave-bin
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Brave Origin heeft geen Fedora-package, dus op Bazzite is het regular Brave. Brave publiceert zijn eigen RPM-repository, maar een browser hoeft geen onderdeel van de system image te zijn, dus neem de Flatpak:

```bash
flatpak install flathub com.brave.Browser
```

{{< callout type="info" >}}
De Brave GPU-workarounds op de [Known Issues]({{< relref "/docs/known-issues" >}}) pagina gelden ook voor de Flatpak, maar een Flatpak leest zijn launch flags uit `~/.var/app/com.brave.Browser/config/brave-flags.conf` in plaats van `~/.config/brave-flags.conf`.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

![Brave officiële Linux-installatie-instructies](/images/brave-linux-install.avif)

Hardware-acceleratie werkt prima met huidige Brave- en kernel-versies. De crash-bugs die Brave 1.82–1.86 troffen zijn opgelost. Zie [Known Issues]({{< relref "/docs/known-issues" >}}) voor de geschiedenis.
