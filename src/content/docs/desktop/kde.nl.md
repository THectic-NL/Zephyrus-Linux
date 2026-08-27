---
title: "KDE Plasma"
weight: 1
prev: docs/hardware/color-profiles
next: docs/desktop/astra-monitor
---

De rest van deze site is voor GNOME geschreven. Deze pagina is de uitzondering: wat er verandert als je liever KDE Plasma op de G16 draait, en — belangrijker — welke van de andere handleidingen dan niet meer opgaan.

Plasma is een prima keuze op deze laptop. Fractionele schaling op het 2560x1600-paneel wordt beter afgehandeld dan op GNOME, de knop voor variabele verversingsfrequentie zit gewoon in Instellingen in plaats van achter een experimentele vlag, en de scrollsnelheid van de touchpad is een schuifregelaar in plaats van [een tool van derden die je zelf bouwt]({{< relref "/docs/applications" >}}).

## Naar Plasma toe

Hier verschillen de twee distributies het meest, en dat is meteen een mooie illustratie van het verschil in het algemeen.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Een bureaubladomgeving is een verzameling packages, dus die installeer je:

```bash
sudo pacman -S plasma-meta kde-applications-meta sddm
```

`plasma-meta` is het bureaublad, `kde-applications-meta` is de KDE-applicatieset (laat die weg als je alleen het bureaublad wilt) en `sddm` is de displaymanager van Plasma.

Zet de displaymanager om:

```bash
sudo systemctl disable gdm
sudo systemctl enable sddm
sudo reboot
```

GNOME staat er nog en blijft in de sessielijst op het inlogscherm staan, dus je kunt per sessie terugschakelen zonder iets te verwijderen. Dat is het voordeel; het nadeel is twee bureaubladen aan packages en twee sets standaardapplicaties op één systeem.

{{< callout type="info" >}}
CachyOS publiceert ook een KDE-editie van de ISO. Bij een schone installatie is dat netter dan Plasma over een GNOME-installatie heen leggen — je krijgt hun Plasma-configuratie en -thema in plaats van de kale Arch-versie.
{{< /callout >}}

{{< /tab >}}
{{< tab name="Bazzite" >}}

Hier installeer je geen bureaublad. Het bureaublad zit in de image, en KDE is de *standaard* — de GNOME-images zijn juist de varianten met `-gnome` in de naam.

Overstappen naar Plasma is dus een rebase:

```bash
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/ublue-os/bazzite-nvidia-open:stable
systemctl reboot
```

Dat is `bazzite-gnome-nvidia-open` → `bazzite-nvidia-open`: dezelfde NVIDIA-opzet, KDE in plaats van GNOME.

{{< callout type="info" >}}
Dit is het atomic-model zoals het bedoeld is. Je voegt geen tweede bureaublad aan je systeem toe, je vervangt het systeem door een systeem met een ander bureaublad — en de oude image blijft op schijf staan, dus `rpm-ostree rollback` zet GNOME terug als het je niet bevalt. Je home-map wordt hoe dan ook niet aangeraakt.
{{< /callout >}}

`plasma-workspace` bovenop een GNOME-image layeren zou technisch werken en is de verkeerde zet: je sleept dan bij elke image-update een bureaublad aan packages mee, voor iets wat een rebase netjes doet.

{{< /tab >}}
{{< /tabs >}}

## Wat er niet meer opgaat

Een aantal handleidingen op deze site configureert specifiek GNOME. Op Plasma:

| Handleiding | Op KDE Plasma |
|---|---|
| [GDM Autologin]({{< relref "/docs/security/autologin" >}}) | Gaat niet op. SDDM is de displaymanager; autologin stel je in via `/etc/sddm.conf.d/` of via **Systeeminstellingen → Opstarten en afsluiten → Aanmeldscherm (SDDM)** |
| [YubiKey]({{< relref "/docs/security/yubikey" >}}) | Het `sudo`- en polkit-deel geldt ongewijzigd. Het schermvergrendelingsdeel niet: bewerk `/etc/pam.d/kde` in plaats van `/etc/pam.d/gdm-password` |
| Scrollsnelheid touchpad | Niet nodig. **Systeeminstellingen → Muis & touchpad** heeft een schuifregelaar voor scrollsnelheid, en dat is precies waarom die sectie op de applicatiepagina bestaat |
| GNOME-vensterknoppen, -focus, -sneltoetsen | Niet van toepassing. Het zit allemaal in Systeeminstellingen, en de Windows-achtige standaarden waar die secties naar zoeken zijn grotendeels al Plasma's standaarden |
| Smile (emoji-kiezer) | Niet nodig. `Meta+.` opent de ingebouwde emoji-kiezer van Plasma |
| Astra Monitor | GNOME Shell-extensie, dus nee. Plasma heeft ingebouwde systeemmonitor-widgets |

De rest — de NVIDIA-driver, Secure Boot, `asusctl`, eduroam, de virtualisatiepagina's, en de applicaties die geen GNOME-aanpassing zijn — verandert niet. Niets daarvan maakt het uit welk bureaublad de vensters tekent.

## Specifiek voor de G16

- **Fractionele schaling** werkt op Wayland zonder experimentele vlag. **Systeeminstellingen → Beeldscherm en monitor**; 125% of 150% is het verstandige bereik op een 16"-scherm van 2560x1600.
- **Variabele verversingsfrequentie** is een instelling per beeldscherm onder Beeldscherm en monitor, niet iets wat je globaal aanzet.
- **De Slash LED, fan curves en GPU-switching** zijn `asusctl` en `asusd`, en die staan los van het bureaublad. `rog-control-center` is een Qt-applicatie, dus die voelt hier hooguit meer op zijn plek.
- **Hybride graphics** gedraagt zich hetzelfde. Plasma's programmastarter biedt in het rechtermuisknopmenu "Starten met discrete videokaart", wat een prettigere voorkant is voor hetzelfde `prime-run`-gedrag.

## Referenties

- [KDE Plasma](https://kde.org/plasma-desktop/)
- [Arch Wiki: KDE](https://wiki.archlinux.org/title/KDE)
- [Arch Wiki: SDDM](https://wiki.archlinux.org/title/SDDM)
- [Bazzite-documentatie](https://docs.bazzite.gg/)
