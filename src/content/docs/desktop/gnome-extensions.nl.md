---
title: "GNOME-extensies"
weight: 1
prev: docs/hardware/color-profiles
next: docs/desktop/astra-monitor
---

GNOME Shell-extensies zijn hoe dit bureaublad de dingen doet die het standaard niet kan: picture-in-picture-vensters die blijven staan waar jij ze neerzet, bovenop, een systeemmonitor in de balk, fixes voor venstergedrag. Deze pagina behandelt het installeren in het algemeen. Extensies met genoeg haken en ogen om eigen instructies te verdienen krijgen een eigen pagina, hieronder gelinkt.

## Extensies installeren

extensions.gnome.org wil een browserextensie plus een native-host-connector voordat je iets vanaf de website kunt installeren. Staat dat niet klaar, of heb je er geen zin in, sla het dan over en gebruik **Extension Manager**. Die praat rechtstreeks met GNOME Shell en heeft een eigen Bladeren-tabblad met dezelfde catalogus.

Het [setup-venster]({{< relref "/docs/setup-script" >}}) kan hetzelfde voor de extensies op deze pagina: het installeert ze van extensions.gnome.org, zet ze aan en uit, en meldt het als er nog geen build voor jouw GNOME-versie is.

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

### In Picture

[In Picture](https://extensions.gnome.org/extension/8692/in-picture/) van [Filip](https://codeberg.org/filiprund) verplaatst en schaalt Picture-in-Picture-vensters naar jouw voorkeur en kan ze bovenop alles houden, ook op Wayland, wat GNOME zelf niet doet. Hij is gebouwd voor PiP-vensters van webbrowsers en werkt goed met meerdere monitoren. Ik gebruik deze constant, meestal om een video in de hoek te laten staan terwijl ik ergens anders in werk. Er zijn builds voor GNOME 48 tot en met 51.

- [extensions.gnome.org](https://extensions.gnome.org/extension/8692/in-picture/)
- [Broncode op Codeberg](https://codeberg.org/filiprund/in-picture)

### Astra Monitor

CPU, geheugen, schijf, netwerk en GPU in de bovenbalk, de Radeon 890M en de RTX 4060 naast elkaar. Hij heeft optionele dependencies afhankelijk van wat je wilt uitlezen, dus krijgt hij een eigen pagina: [Astra Monitor]({{< relref "/docs/desktop/astra-monitor" >}}).

## Extensies die elders staan

Een paar andere komen op andere pagina's voorbij omdat ze één specifiek probleem oplossen in plaats van een algemeen hulpmiddel te zijn:

| Extensie | Waarvoor | Waar |
|---|---|---|
| [Smile complementary extension](https://extensions.gnome.org/extension/6096/smile-complementary-extension/) | Automatisch plakken van emoji's voor de [Smile]({{< relref "/docs/applications/utilities#smile-emoji-picker" >}})-picker | [Utilities]({{< relref "/docs/applications/utilities#smile-emoji-picker" >}}) |
| [Just Perfection](https://gitlab.gnome.org/jrahmatzadeh/just-perfection) | Fix voor apps die op de achtergrond openen in plaats van focus te pakken | [Applicaties]({{< relref "/docs/applications#gnome-vensterfocus-apps-die-op-de-achtergrond-openen" >}}) |


## GNOME 51 vernieuwingen en compatibiliteit

GNOME 51 ("A Coruña") introduceert diverse verbeteringen aan de desktopervaring op deze laptop:

- **Mutter frame scheduling:** Verbeterde frame delivery zorgt ervoor dat animaties en vensterbeheer soepel blijven draaien, zelfs onder zware systeembelasting.
- **Helderheid blijft bewaard:** Beeldschermhelderheid wordt nu correct onthouden na herstarts en bij het in- en uitschakelen van HDR.
- **Native GDM FIDO2- en passkey-ondersteuning:** GNOME Display Manager ondersteunt nu direct FIDO2-beveiligingssleutels voor inloggen.
- **Wayland achtergrondvervaging:** Ondersteuning voor het `ext-background-effect-v1`-protocol maakt native blur-effecten mogelijk.
- **Schermindeling en rotatie:** Schermindeling snapt nu netjes op het midden in Instellingen.

De meeste hieronder beschreven extensies (waaronder In Picture, Astra Monitor en Just Perfection) zijn geverifieerd compatibel met GNOME 51. De uitzondering hierop is de **Smile complementary extension**, die momenteel stopt bij GNOME 50 en door GNOME Shell als verouderd wordt geweigerd totdat de maker een build voor 51 uitbrengt (Smile zelf blijft gewoon werken om emoji's naar het klembord te kopiëren).