---
title: "GNOME-extensies"
weight: 1
prev: docs/hardware/color-profiles
next: docs/desktop/astra-monitor
---

GNOME Shell-extensies zijn hoe dit bureaublad de dingen doet die het standaard niet kan: picture-in-picture-vensters die echt bovenop blijven, een systeemmonitor in de balk, fixes voor venstergedrag. Deze pagina behandelt het installeren in het algemeen. Extensies met genoeg haken en ogen om eigen instructies te verdienen krijgen een eigen pagina, hieronder gelinkt.

## Extensies installeren

extensions.gnome.org wil een browserextensie plus een native-host-connector voordat je iets vanaf de website kunt installeren. Staat dat niet klaar, of heb je er geen zin in, sla het dan over en gebruik **Extension Manager**. Die praat rechtstreeks met GNOME Shell en heeft een eigen Bladeren-tabblad met dezelfde catalogus.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S extension-manager
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub com.mattjakeman.ExtensionManager
```

{{< /tab >}}
{{< /tabs >}}

Open Extension Manager vanuit je applicatiemenu, ga naar het tabblad **Bladeren**, zoek de extensie op naam en installeer.

{{< callout type="info" >}}
Extensies die je zo installeert staan in `~/.local/share/gnome-shell/extensions/`, dus in je home-map en niet in de image. Op Bazzite betekent dat dat ze image-updates en rebases overleven zonder dat je iets hoeft te layeren.
{{< /callout >}}

## Extensies die ik gebruik

### PiP on Top

[PiP on Top](https://extensions.gnome.org/extension/4691/pip-on-top/) van [Rafostar](https://github.com/Rafostar) houdt Picture-in-Picture-vensters bovenop alles, ook op Wayland, wat GNOME zelf niet doet. Hij is gebouwd voor Firefox maar werkt ook met een paar andere browsers. Ik gebruik deze constant, meestal om een video in de hoek te laten staan terwijl ik ergens anders in werk.

- [extensions.gnome.org](https://extensions.gnome.org/extension/4691/pip-on-top/)
- [Broncode op GitHub](https://github.com/Rafostar/gnome-shell-extension-pip-on-top)

### Astra Monitor

CPU, geheugen, schijf, netwerk en GPU in de bovenbalk, de Radeon 890M en de RTX 4060 naast elkaar. Hij heeft optionele dependencies afhankelijk van wat je wilt uitlezen, dus krijgt hij een eigen pagina: [Astra Monitor]({{< relref "/docs/desktop/astra-monitor" >}}).

## Extensies die elders staan

Een paar andere komen op andere pagina's voorbij omdat ze één specifiek probleem oplossen in plaats van een algemeen hulpmiddel te zijn:

| Extensie | Waarvoor | Waar |
|---|---|---|
| [Smile complementary extension](https://extensions.gnome.org/extension/6096/smile-complementary-extension/) | Automatisch plakken van emoji's voor de [Smile]({{< relref "/docs/applications/utilities#smile-emoji-picker" >}})-picker | [Utilities]({{< relref "/docs/applications/utilities#smile-emoji-picker" >}}) |
| [Just Perfection](https://gitlab.gnome.org/jrahmatzadeh/just-perfection) | Fix voor apps die op de achtergrond openen in plaats van focus te pakken | [Applicaties]({{< relref "/docs/applications#gnome-vensterfocus-apps-die-op-de-achtergrond-openen" >}}) |
