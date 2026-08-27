---
title: "SteamOS & Game Mode"
weight: 1
prev: docs/virtualization/vmware-workstation
next: docs/known-issues
---

De console-ervaring van de Steam Deck — direct opstarten in Steam, met een controller, geen bureaublad tenzij je erom vraagt — kun je op deze laptop hebben. Wat je niet kunt hebben is SteamOS zelf.

Deze pagina gaat over dat onderscheid, en over welke van de twee distributies je er het dichtst bij brengt.

## SteamOS kun je niet op de G16 installeren

Valves SteamOS is gebouwd voor hardware die Valve zelf uitbrengt. Twee dingen maken het hier kansloos:

- **Geen NVIDIA-ondersteuning.** SteamOS is in de praktijk AMD-only: de grafische stack is Mesa, en er zit geen proprietary NVIDIA-driver in de image. Op een laptop waarvan de discrete GPU een RTX 4060 is, houdt het gesprek daar op.
- **Het wordt niet als algemene installer uitgeleverd.** De recovery-images richten zich op Deck-hardware, en het werk dat Valve heeft gedaan om dat te verbreden mikt op andere handhelds, niet op laptops met hybride graphics.

Mensen krijgen SteamOS wel degelijk aan de praat op niet-Valve-hardware. Op deze machine zou dat betekenen dat je de discrete GPU opgeeft, en dan is de hele exercitie zinloos.

De vraag wordt dus: hoe dicht kom je bij een console-sessie op hardware waar SteamOS nooit voor bedoeld was?

{{< tabs >}}
{{< tab name="CachyOS" >}}

Dicht genoeg voor de meeste doelen, maar je zet het zelf in elkaar.

Je houdt een normaal bureaublad en krijgt de console-ervaring op afroep in plaats van bij het opstarten:

```bash
steam -gamepadui
```

Dat is Steams Game Mode-interface — dezelfde UI als op de Deck, in een venster of schermvullend. In combinatie met een controller dekt dat het meeste van wat mensen eigenlijk van SteamOS willen.

Voor het echte werk — een gamescope-sessie die je bureaubladsessie vervangt, zodat de machine in Steam opstart — kijk wat er in de CachyOS-repos zit in plaats van een verouderde gids te volgen:

```bash
pacman -Ss gamescope
```

CachyOS Hello heeft ook een gaming-sectie die de gebruikelijke stack in één keer installeert, en dat is een beter startpunt dan packagenamen uit een blogpost bij elkaar sprokkelen.

**Eerlijke samenvatting:** je krijgt Game Mode. Je krijgt niet het naadloze opstarten-in-Steam, slapen-en-terug-in-je-game, alles-werkt-gewoon; dat integratiewerk is precies het deel dat Valve bouwt en onderhoudt.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Zo dicht als het komt, en dit is Bazzites hele bestaansreden.

De `bazzite-deck`-images nemen Valves Game Mode-sessie en pakken die in voor hardware die geen Steam Deck is: direct opstarten in Steam, dezelfde gamescope-sessie, dezelfde controller-eerst-interface, met een bureaublad één menu-item verderop.

Overstappen is een rebase:

```bash
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/ublue-os/bazzite-deck-gnome:stable
systemctl reboot
```

`bazzite-deck-gnome` geeft GNOME als bureaublad om naar uit te stappen; `bazzite-deck` geeft KDE. Er zijn ook NVIDIA-varianten van de deck-images — controleer de [imagelijst](https://github.com/ublue-os/bazzite) op de actuele namen voordat je rebaset.

{{< callout type="warning" >}}
**Dit is op deze laptop de minst betreden route.** De deck-images mikken op handhelds, en die zijn AMD-only met één GPU. De G16 is een hybride machine waarbij het interne paneel aan de Radeon 890M hangt en de RTX 4060 rendert, en gamescope moet verteld worden wat wat is. Reken op ruwe randjes — externe schermen en de discrete GPU zijn waar ze opduiken.

Wil je een laptop die goed gamet, blijf dan op `bazzite-gnome-nvidia-open` en gebruik Big Picture. Wil je een console die toevallig een laptop is, dan is dit de route, en de vorige image staat er nog als het tegenvalt:

```bash
rpm-ostree rollback
systemctl reboot
```
{{< /callout >}}

Je hebt geen deck-image nodig om goed te kunnen gamen. De gewone desktop-images leveren Steam, Proton, gamescope, MangoHud en de controller-stack al geconfigureerd mee. De deck-images veranderen alleen hoe je *begint* — het gamen zelf is hetzelfde.

{{< /tab >}}
{{< /tabs >}}

## Game Mode op hybride graphics

Welke route je ook kiest, op deze laptop moet je begrijpen welke GPU wat doet.

Het interne scherm hangt aan de AMD Radeon 890M. De RTX 4060 rendert en geeft frames door. Dat is normaal voor een gaming-laptop en het is waar `asusctl armoury` tussen schakelt — zie [asusctl & ROG Control Center]({{< relref "/docs/hardware/asusctl-rog-control" >}}).

Voor een console-achtige sessie is dat belangrijk omdat gamescope composit, en dat op het juiste apparaat moet doen. Symptomen als het misgaat:

| Symptoom | Betekent meestal |
|---|---|
| Game draait, belabberde framerate | Rendert op de iGPU in plaats van op de RTX 4060 |
| Zwart scherm op een extern beeldscherm | Het scherm hangt aan de discrete GPU, de sessie composit op de iGPU |
| Game Mode start helemaal niet | gamescope krijgt het scherm niet dat hij verwacht |

Voordat je Game Mode de schuld geeft: controleer in een gewone bureaubladsessie of de driver gezond is:

```bash
nvidia-smi
```

Mislukt dat, los dat dan eerst op — [NVIDIA op CachyOS]({{< relref "/docs/hardware/nvidia-cachyos" >}}) of [NVIDIA op Bazzite]({{< relref "/docs/hardware/nvidia-bazzite" >}}) — want niets hiervan werkt bovenop een driver die niet laadt.

## Wat je in de praktijk moet nemen

| Je wilt | Doe dit |
|---|---|
| Een laptop die goed gamet | Beide distributies, gewoon bureaublad, Steam Big Picture wanneer je er zin in hebt |
| Een console die toevallig een laptop is | Bazzite, deck-image, en accepteer de ruwe randjes van hybride graphics |
| Écht SteamOS | Koop een Steam Deck |

De middelste regel is de eerlijke: het kan, het is leuk, en het is geen ondersteunde configuratie.

## Referenties

- [Bazzite](https://bazzite.gg/)
- [Bazzite op GitHub](https://github.com/ublue-os/bazzite) — actuele imagenamen
- [gamescope](https://github.com/ValveSoftware/gamescope)
- [SteamOS](https://store.steampowered.com/steamos)
