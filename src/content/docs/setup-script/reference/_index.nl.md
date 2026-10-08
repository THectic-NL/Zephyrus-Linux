---
title: "Referentie"
weight: 1
---

Elke rij in het [setup-script]({{< relref "/docs/setup-script" >}}) heeft hier een regel: de exacte opdrachten die aanvinken draait, de exacte opdrachten die uitvinken draait om alles terug te zetten, en een link naar de code erachter. Het venster toont dezelfde opdrachten voordat het iets toepast. Hier kun je ze lezen zonder iets te draaien.

De pagina's worden uit het script gegenereerd. [`quicksetup.py`](https://github.com/THectic-NL/Zephyrus-Linux/blob/main/src/static/scripts/quicksetup.py) wordt geïmporteerd en dezelfde functies die het venster draait worden voor elk onderdeel uitgevoerd, dus de pagina's kunnen niet afwijken van wat het venster doet. De kwaliteitscontroles falen als een wijziging in het script niet in de pagina's is overgenomen.

## De secties

Eén pagina per sectie van het venster, met een regel per onderdeel.

- [ASUS hardware]({{< relref "/docs/setup-script/reference/hardware" >}}): asusctl, acculimiet, energieprofielen, helderheid
- [Graphics]({{< relref "/docs/setup-script/reference/gpu" >}}): NVIDIA-services, PRIME offload, schermvastlopers
- [Display]({{< relref "/docs/setup-script/reference/display" >}}): kleurstanden en de kleurprofielen uit de fabriek
- [Network]({{< relref "/docs/setup-script/reference/network" >}}): Wi-Fi-tuning, eduroam
- [GNOME desktop]({{< relref "/docs/setup-script/reference/desktop" >}}): vensterknoppen, sneltoetsen, extensies, touchpad
- [Security and login]({{< relref "/docs/setup-script/reference/security" >}}): autologin, YubiKey, Secure Boot
- [Development]({{< relref "/docs/setup-script/reference/dev" >}}): git, ondertekenen, editors, cloudtools
- [Applications]({{< relref "/docs/setup-script/reference/apps" >}}): browser, berichten, kantoor, hulpprogramma's
- [Gaming]({{< relref "/docs/setup-script/reference/gaming" >}}): Steam, Proton-tools, overlays
- [Virtual machines and containers]({{< relref "/docs/setup-script/reference/virt" >}}): KVM, Podman, Distrobox, Windows-apps

## Zo lees je een regel

- **Aanzetten** en **Uitzetten (het terugdraaien)** tonen wat het venster draait, in de volgorde waarin het dat doet. De koppen in de code zeggen wie het draait: *As root* is één script achter één wachtwoordprompt, *As you* is je eigen gebruiker, en *In a terminal window* is voor de AUR, waar je elke PKGBUILD leest voordat hij wordt gebouwd.
- Een bestand dat wordt bewerkt heeft zijn diff erbij. De diffs hier zijn gemaakt op de bestanden die een verse Arch-installatie meelevert. Het venster maakt de diff tegen je eigen bestanden voordat het iets toepast, en toont hem in de controle.
- Een bestand dat het venster bewerkt wordt eerst voorbereid in je cachemap, zodat je de diff kunt zien. Root installeert het alleen zolang de SHA-256 nog klopt met wat is voorbereid (de `sha256sum -c`-regel), zodat niets het bestand kan vervangen terwijl de wachtwoordprompt openstaat.
- **Bron** linkt naar de exacte regels van het script op GitHub: de regel in de catalogus en de functies die hij gebruikt. De links volgen de `main`-branch, en dat is het script dat je downloadt.
- `your-username` staat voor je inlognaam, en `/home/your-username` voor je thuismap.
- Het venster laat weg wat al klaar is. Het installeert geen pakket dat al is geïnstalleerd, en een paar stappen bestaan alleen als ze van toepassing zijn, zoals de `ufw`-regels, die er zijn als ufw draait. Een regel toont alles wat een onderdeel kan draaien.
- Een pakket uit de AUR is een `paru`-regel, tenzij een repository die je gebruikt het pakket heeft. Dan is het de `pacman`-regel.
- De opdrachten en hun beschrijvingen zijn wat het venster toont, dus ze zijn op elke taal van deze site Engels.

## De weg terug

Een onderdeel uitvinken is de weg terug, en elke regel toont hem. Het haalt weg wat aanvinken installeerde, zet instellingen terug naar de GNOME-standaard (alleen zolang ze nog de waarde hebben die het script gaf) en zet een bewerkt bestand terug uit de back-up die gemaakt is.

Wat het niet aanraakt is van jou: je eigen bestanden en instellingen, zoals de instellingen van een extensie die je hebt verwijderd, je containers en virtuele machines, en een pakket dat iets anders nog nodig heeft. De notities onder een regel zeggen wat blijft staan.

Twee rijen hebben geen vinkje, omdat een fout in hun stappen ervoor kan zorgen dat de machine niet meer opstart: de AMD-fix tegen schermvastlopers en Secure Boot. Hun regels noemen de stappen om ze in te richten en om ze met de hand terug te draaien.

## De eigen scripts

Drie onderdelen draaien een eigen script: de helderheidsfix, de Wi-Fi-tuning en eduroam. De setup draait zo'n script alleen als zijn SHA-256 die is die in de setup zit, en die hash staat in de regel, met een samenvatting van wat het script wijzigt. De scripts staan naast het setup-script: [zephyrus-backlight.py](/scripts/zephyrus-backlight.py), [mt7925-tune.py](/scripts/mt7925-tune.py) en [saxion-eduroam.py](/scripts/saxion-eduroam.py). De eerste twee draaien hun stappen als root, als één script achter één wachtwoordprompt. Het eduroam-script draait als jij. Elk heeft een eigen handleiding.

## Bij de tijd houden

Draai na een wijziging in `quicksetup.py` eerst `.github/scripts/check-doc-checksums.sh --apply` en daarna `.github/scripts/generate-setup-reference.py`. Die tweede schrijft deze pagina's opnieuw uit het script, en met `--check` faalt hij in plaats daarvan, en dat doen de kwaliteitscontroles.
