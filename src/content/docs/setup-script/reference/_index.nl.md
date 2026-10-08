---
title: "Referentie"
weight: 1
---

Elke rij in het [setup-script]({{< relref "/docs/setup-script" >}}) heeft hier een regel: de exacte opdrachten die aanvinken draait, de exacte opdrachten die uitvinken draait om alles terug te zetten, en een link naar de code erachter. Het venster toont dezelfde opdrachten voordat het iets toepast. Hier kun je ze lezen zonder iets te draaien.

De pagina's worden bij elke build van de site uit het script gegenereerd: [`quicksetup.py`](https://github.com/THectic-NL/Zephyrus-Linux/blob/main/src/static/scripts/quicksetup.py) wordt geïmporteerd en de functies die het venster draait worden voor elk onderdeel uitgevoerd, dus de pagina's kunnen niet afwijken van wat het venster doet. Wil je ze vanuit een checkout lezen, draai dan `.github/scripts/generate-setup-reference.py` voor `hugo server`.

## De secties

- [ASUS hardware](hardware/): asusctl, acculimiet, energieprofielen, helderheid
- [Graphics](gpu/): NVIDIA-services, PRIME offload, schermvastlopers
- [Display](display/): kleurstanden en de kleurprofielen uit de fabriek
- [Network](network/): Wi-Fi-tuning, eduroam
- [GNOME desktop](desktop/): vensterknoppen, sneltoetsen, extensies, touchpad
- [Security and login](security/): autologin, YubiKey, Secure Boot
- [Development](dev/): git, ondertekenen, editors, cloudtools
- [Applications](apps/): browser, berichten, kantoor, hulpprogramma's
- [Gaming](gaming/): Steam, Proton-tools, overlays
- [Virtual machines and containers](virt/): KVM, Podman, Distrobox, Windows-apps

## Zo lees je een regel

- **Aanzetten** en **Uitzetten (het terugdraaien)** tonen wat het venster draait, in de volgorde waarin het dat doet. De commentaarkoppen zeggen wie het draait: *As root* is één script achter één wachtwoordprompt, *As you* is je eigen gebruiker, en *As you, in a terminal window* is voor de AUR, waar je elke PKGBUILD leest voordat hij wordt gebouwd.
- Een bestaand bestand dat wordt gewijzigd heeft zijn diff erbij, gemaakt op het bestand dat een verse Arch-installatie meelevert. Het venster maakt hem tegen je eigen bestand en toont hem in de controle. Een bestand dat wordt aangemaakt staat in het commando zelf. Root installeert het voorbereide bestand alleen zolang de SHA-256 nog klopt (de `sha256sum -c`-regel), zodat niets het kan vervangen terwijl de wachtwoordprompt openstaat.
- **Bron** linkt naar de exacte regels van het script, op de commit waarmee deze site is gebouwd.
- `your-username` staat voor je inlognaam. Het venster laat weg wat al klaar is, terwijl een regel alles toont wat een onderdeel kan draaien. Een pakket uit de AUR is een `paru`-regel, tenzij een repository die je gebruikt het pakket heeft: dan is het de `pacman`-regel.
- De opdrachten en hun beschrijvingen zijn wat het venster toont, dus ze zijn op elke taal van deze site Engels.

## De weg terug

Een onderdeel uitvinken is de weg terug, en elke regel toont hem. Het haalt weg wat aanvinken installeerde, zet instellingen terug naar de GNOME-standaard (alleen zolang ze nog de waarde hebben die het script gaf) en zet een bewerkt bestand terug uit de back-up die gemaakt is. Wat van jou is blijft staan: je eigen bestanden en instellingen, je containers en virtuele machines, en een pakket dat iets anders nog nodig heeft. De notities onder een regel zeggen wat blijft staan.

Twee rijen hebben geen vinkje, omdat een fout in hun stappen ervoor kan zorgen dat de machine niet meer opstart: de AMD-fix tegen schermvastlopers en Secure Boot. Hun regels noemen de stappen om ze in te richten en om ze met de hand terug te draaien.

## De eigen scripts

Drie onderdelen draaien een eigen script: de helderheidsfix, de Wi-Fi-tuning en eduroam. De setup draait zo'n script alleen als zijn SHA-256 die is die in de setup zit. Die hash staat in de regel, met een link naar de handleiding die zegt wat het script wijzigt. De scripts staan naast het setup-script: [zephyrus-backlight.py](/scripts/zephyrus-backlight.py), [mt7925-tune.py](/scripts/mt7925-tune.py) en [saxion-eduroam.py](/scripts/saxion-eduroam.py).
