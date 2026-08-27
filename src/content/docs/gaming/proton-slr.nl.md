---
title: "Proton & de Steam Linux Runtime"
weight: 2
prev: docs/gaming/steamos
next: docs/known-issues
---

Windows-games draaien op deze laptop via twee lagen die stelselmatig door elkaar gehaald worden: **Proton**, dat de game vertaalt, en de **Steam Linux Runtime**, die de omgeving levert waarin Proton draait.

Weten wat wat is, is het verschil tussen een kapotte game in vijf minuten repareren en zonder reden je grafische driver herinstalleren.

## Proton

Proton is Valves build van Wine met hun eigen patches erbovenop, plus **DXVK** en **VKD3D-Proton** om Direct3D-aanroepen naar Vulkan te vertalen. Steam kiest per game een versie; die kun je overrulen.

De versies die je tegenkomt:

| Versie | Wat het is |
|---|---|
| **Proton 11** | De huidige stabiele major op het moment van schrijven. Prima standaard |
| **Proton Experimental** | Waar fixes als eerste landen. Probeer dit als een game zich misdraagt |
| **Proton Hotfix** | Gerichte fixes voor specifieke titels, meestal vlak nadat een game-update ze brak |
| **Proton-GE** | Een community-build met extra mediacodecs en patches die Valve niet gemerged heeft. Vaak het antwoord bij games met video-tussenfilmpjes |
| **Proton 8, 9, 10…** | Oudere majors, bewaard omdat sommige games alleen op één specifieke versie werken |

Er een instellen:

- **Per game:** rechtermuisknop op de game → **Eigenschappen** → **Compatibiliteit** → *Forceer het gebruik van een specifieke Steam Play-compatibiliteitstool*.
- **Alles:** **Steam → Instellingen → Compatibiliteit** → *Steam Play inschakelen voor alle overige titels*.

Per game is vrijwel altijd wat je wilt. Een globale override betekent dat één slechte versie je hele bibliotheek raakt.

{{< callout type="info" >}}
Kijk op [ProtonDB](https://www.protondb.com/) voordat je iets gaat uitzoeken. De meeste "deze game werkt niet"-problemen zijn een bekende launch-optie van één regel of een specifieke Proton-versie, en iemand heeft het al opgeschreven.
{{< /callout >}}

## De Steam Linux Runtime

Die "Steam Linux Runtime 3.0 (sniper)"-items die in je bibliotheek verschijnen, die je nooit geïnstalleerd hebt en niet kunt spelen — dat is de tweede laag, en het is geen vergissing.

Proton draait niet tegen de bibliotheken van jouw systeem. Het draait in een **container** met een vaste, bekende set daarvan. Valve bouwt en test Proton tegen die omgeving, zodat een game zich hetzelfde gedraagt op Debian, Arch of een atomic Fedora-image.

Dit is op allebei de distributies hier de moeite van het begrijpen waard, om tegenovergestelde redenen:

{{< tabs >}}
{{< tab name="CachyOS" >}}

Rolling betekent dat je systeembibliotheken continu bewegen. Zonder de runtime zou een game die vorige week werkte kunnen breken doordat er iets ongerelateerds onder hem vandaan bijgewerkt is.

De runtime is wat dat voorkomt. Proton is afgeschermd van je host, dus `pacman -Syu` zet je bibliotheek niet op het spel — een reëel voordeel op een distributie die zo vaak bijwerkt als deze.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Hier bewegen de systeembibliotheken juist nauwelijks — ze horen bij de image. Dat zou andersom een probleem kunnen zijn: een game die iets nieuwers nodig heeft dan de image meebrengt.

Ook dat vangt de runtime af. Proton neemt zijn eigen omgeving mee, dus de ouderdom van de image doet er niet toe voor de vraag of een game draait. Het is ook waarom gamen op een atomic systeem geen enkele layering vraagt: wat games nodig hebben komt sowieso niet uit `/usr`.

{{< /tab >}}
{{< /tabs >}}

**Verwijder de runtime-items niet**, en probeer ze niet te starten. Steam beheert ze, en er een weghalen breekt elke game die hem gebruikt.

## Proton-GE

Voor games waar Valves builds mee worstelen — meestal mediacodecs, soms anti-cheat. Installeer het met **ProtonUp-Qt**, dat op beide distributies hetzelfde werkt:

```bash
flatpak install flathub net.davidotek.pupgui2
```

Open hem, kies Steam, voeg de nieuwste GE-Proton toe. Het installeert in `~/.steam/root/compatibilitytools.d/` en verschijnt na een herstart van Steam in de compatibiliteitslijst per game.

Dat pad zit op beide distributies in je home-map, dus op Bazzite is er geen layering nodig en overleeft het image-updates en rebases zonder meer.

## Zorgen dat de RTX 4060 het werk doet

Dit is degene die op deze laptop echt bijt. Het interne paneel hangt aan de Radeon 890M, dus een game die niet expliciet naar de discrete GPU gewezen wordt kan stilletjes op de iGPU renderen — hij draait, alleen slecht.

Zet het als launch-optie (rechtermuisknop op de game → **Eigenschappen** → **Opstartopties**):

{{< tabs >}}
{{< tab name="CachyOS" >}}

```
prime-run %command%
```

`prime-run` is een wrapper die de NVIDIA-offloadvariabelen voor je zet. Hij komt met het `nvidia-prime`-package mee.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Hier bestaat `prime-run` niet, dus zet de variabelen zelf:

```
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia %command%
```

Hetzelfde, maar uitgeschreven — dit is precies wat `prime-run` in de andere tab doet.

{{< /tab >}}
{{< /tabs >}}

Controleer tijdens het spelen welke GPU gebruikt wordt:

```bash
nvidia-smi
```

De game hoort in de proceslijst te staan. Staat hij er niet, dan draait hij op de iGPU, wat de framerate ook suggereert.

## Launch-opties die je wilt kennen

Combineer ze op één regel, met `%command%` als laatste:

| Optie | Doet |
|---|---|
| `mangohud %command%` | Overlay met framerate en temperatuur |
| `gamemoderun %command%` | Past prestatie-instellingen toe zolang de game draait |
| `PROTON_LOG=1 %command%` | Schrijft `~/steam-<appid>.log` — het eerste om naar te kijken als een game niet start |
| `gamescope -f -- %command%` | Draait de game binnen gamescope; handig bij resolutie- en schalingsproblemen op het 2560x1600-paneel |

Voorbeeld, alles samen:

```
gamemoderun mangohud prime-run %command%
```

## Waar dingen staan

| | Pad |
|---|---|
| Proton-prefixes (de C:-schijf per game) | `~/.steam/steam/steamapps/compatdata/<appid>/pfx` |
| Eigen Proton-builds | `~/.steam/root/compatibilitytools.d/` |
| Proton-logs | `~/steam-<appid>.log` |

De `compatdata`-map van een game verwijderen zet zijn Windows-omgeving terug zonder de gamebestanden aan te raken. Het is het Proton-equivalent van een config wissen, en het repareert verrassend veel games die na een update niet meer starten.

Dit staat allemaal in je home-map, en die is op Bazzite `/var/home/<gebruiker>` met `/home` als symlink daarnaartoe — Steam gaat daar prima mee om, maar het is goed om te weten als je deze paden in een script opzoekt.

## Referenties

- [ProtonDB](https://www.protondb.com/) — rapporten en launch-opties per game
- [Proton op GitHub](https://github.com/ValveSoftware/Proton)
- [Steam Linux Runtime](https://gitlab.steamos.cloud/steamrt/steam-runtime-tools/-/blob/main/docs/container-runtime.md)
- [ProtonUp-Qt](https://davidotek.github.io/protonup-qt/)
- [GE-Proton](https://github.com/GloriousEggroll/proton-ge-custom)
