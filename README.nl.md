# Zephyrus-Linux

Nederlands | [English](README.md)

Mijn Linux-setup voor de ASUS ROG Zephyrus G16 GA605WV (2024), opgeschreven en gescript. Zo heb ik Linux het liefst, en zo krijg ik een verse installatie weer precies zoals ik hem wil: met een checklist-venster dat laat zien wat er op jouw machine al klaar is en bij elk onderdeel linkt naar de bijbehorende pagina in de handleiding. Je hebt niet precies deze laptop nodig. Alleen de pagina's en onderdelen van het script die de hardware van de laptop aansturen zijn specifiek voor de G16. Al het andere werkt op elke machine.

**Bekijk de handleidingen: [zephyrus-linux.thectic.nl](https://zephyrus-linux.thectic.nl/nl/)**


## Richt een machine in zoals de mijne

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/quicksetup.py
python3 quicksetup.py
```

Het script opent een venster: vink aan wat je wilt, lees het plan en pas het toe. Het laat zien wat er op jouw machine al klaar is en linkt elk onderdeel naar de handleiding. Er verandert niets totdat je het plan hebt gezien en op Apply hebt gedrukt, en elk onderdeel toont de exacte opdrachten die het draait en de weg terug, in het venster en in [de referentie](https://zephyrus-linux.thectic.nl/nl/docs/setup-script/reference/). Controleer de SHA-256 op [de pagina van het script](https://zephyrus-linux.thectic.nl/nl/docs/setup-script/) voordat je het draait. Het venster brengt alleen wijzigingen aan op CachyOS en andere Arch-systemen met GNOME. Overal elders is het alleen-lezen.


## Wat er in zit

- **Handleidingen** voor CachyOS en Bazzite: de instellingen en software die ik echt gebruik, en waarom. Pagina's over de hardware van de laptop zelf (de ASUS-tools, helderheid, de Wi-Fi-kaart, de kleurprofielen) zijn specifiek voor de G16. De pagina's over het GNOME-bureaublad, beveiliging, applicaties, virtualisatie en gaming werken op elke machine.
- **Een setup-venster** dat het grootste deel daarvan omzet in een checklist met per onderdeel een schakelaar en een link naar de handleiding.
- **Eigen scripts** voor de lastigere fixes (helderheid in elke GPU-modus, Wi-Fi-tuning, eduroam), die het setup-venster voor je draait, nadat het ze heeft gecontroleerd met de SHA-256 die het zelf bevat.


## Over dit project

Dit is mijn eigen setup, geen neutraal overzicht. Het is eigenzinnig: mijn favoriete instellingen en de software die ik echt gebruik, op de enige laptop die ik heb. Ik heb het opgeschreven zodat ik de machine snel opnieuw kan opbouwen, en zodat anderen die dezelfde dingen fijn vinden sneller bij hetzelfde resultaat uitkomen. Ik ben geen developer, gewoon iemand die naar Linux is overgestapt en daarna tegen van alles aanliep wat niet meteen werkte, en veel hiervan heb ik gaandeweg uitgezocht.

CachyOS (Arch) is mijn daily driver, vooral omdat een deel van wat ik doe wat directere controle over het systeem vraagt dan een atomic image je geeft. Vroeger draaide ik het in dualboot met Bazzite (Fedora Atomic) op dezelfde machine, en die handleidingen houd ik bij. De [Aan de slag](https://zephyrus-linux.thectic.nl/nl/docs/)-pagina legt de keuze uit, en met de schakelaar bovenaan elke pagina wissel je tussen de twee sets handleidingen.

Ik ben nog actief aan het testen en experimenteren: dingen kunnen veranderen, kapot gaan of achteraf onjuist blijken. Alles wat hier staat is gebaseerd op mijn eigen ervaring en is op eigen risico.

Ik ben niet gelieerd aan ASUS, NVIDIA, Microsoft, CachyOS, Universal Blue of enig ander bedrijf of project dat hier wordt genoemd, word er niet door goedgekeurd en spreek niet namens hen.

![Systeeminformatie-overzicht](src/static/images/system-info.avif)


## De site lokaal bouwen

Deze documentatiesite is gebouwd met [Hugo](https://gohugo.io/) en het [Hextra](https://imfing.github.io/hextra/)-thema. Het thema is opgenomen als Hugo module (via Go modules, geen git submodules).

**Vereisten:**
- [Hugo extended](https://gohugo.io/installation/) v0.160.0 (of hoger)
- [Go](https://go.dev/dl/) (vereist voor Hugo modules)
- Git
- VS Code

Op Arch Linux / CachyOS:
```bash
sudo pacman -S hugo go
```

**Repository klonen:**
```bash
git clone https://github.com/THectic-NL/Zephyrus-Linux.git
cd Zephyrus-Linux
```

Hugo downloadt de thema-module automatisch de eerste keer dat je het uitvoert.

**Ontwikkelserver starten:**
```bash
cd src
hugo server
```

De site is beschikbaar op `http://localhost:1313/`. Hugo detecteert wijzigingen en herlaadt automatisch.

**Bouwen voor productie:**
```bash
cd src
hugo --gc --minify
```

De output wordt geschreven naar `./src/public/`. Bij een push naar `main` bouwt GitHub Actions de site en deployt die naar Bunny.net (Storage-zone + Pull Zone) op [zephyrus-linux.thectic.nl](https://zephyrus-linux.thectic.nl/).


## Afbeeldingen

Alle afbeeldingen in deze repository gebruiken het [AVIF](https://en.wikipedia.org/wiki/AVIF)-formaat: open, royaltyvrij en efficiënter dan PNG of JPEG bij vergelijkbare kwaliteit. AVIF is de moderne standaard voor webafbeeldingen.

Installeer `avifenc` uit het `libavif`-pakket om PNG-screenshots om te zetten naar AVIF:

```bash
sudo pacman -S libavif
```

Batch-conversie van alle PNGs in `src/static/images/` (converteert en verwijdert de originelen):

```bash
cd src/static/images
for f in *.png; do avifenc -q 80 -s 6 "$f" "${f%.png}.avif" && rm "$f"; done
```

- `-q 80`: 80% kwaliteit (schaal 0-100, 100 = verliesvrij)
- `-s 6`: encodersnelheid (0 = beste compressie, 10 = snelst)


## Credits & bronnen

Dit project zou niet bestaan zonder het werk van deze mensen en communities:

- **[ASUS Linux community](https://asus-linux.org/)**: Het project achter `asusctl` en `rog-control-center`, tegenwoordig onderhouden onder het [Open Gaming Collective](https://github.com/OpenGamingCollective/asusctl). Luke Jones is hier een grote drijvende kracht achter geweest, en ook andere bijdragers hebben kernelpatches ingediend, waarvan er veel inmiddels in mainline Linux zijn opgenomen, waardoor moderne ASUS ROG-laptops echt bruikbaar zijn op Linux.
- **[WinUtil](https://github.com/ChrisTitusTech/winutil)**: De Windows-tool die voor elke tweak het exacte script toont dat hem toepast en het script dat hem terugdraait, gegenereerd uit hetzelfde bestand dat de tool draait. Het voorbeeld voor de setup-referentie.
- **[G-Helper](https://github.com/seerge/g-helper)**: De Windows-tool die per model een zip met ASUS-kleurprofielen van de ASUS CDN ophaalt en die aanbiedt als Native, sRGB, DCI-P3 en Display P3. De fabrieksprofielen in deze repository komen uit hetzelfde soort pakket, gevonden met reverse engineering. Je kunt er op Linux nog weinig mee, de [handleiding over kleurprofielen](https://zephyrus-linux.thectic.nl/nl/docs/hardware/color-profiles/) legt uit waarom.
- **[CachyOS](https://cachyos.org/)**: Een op Arch gebaseerde distributie met uitgebreide hardware-specifieke tuning: een verbeterde scheduler (BORE/EEVDF), beter energiebeheer, ondersteuning voor dynamische verversingsfrequentie, en ingebouwde drivers voor zowel de AMD iGPU als de NVIDIA dGPU, inclusief geïntegreerde GPU-switching. Een van de twee distributies die deze handleidingen dekken.
- **[Bazzite / Universal Blue](https://universal-blue.org/)**: De mensen die de atomic Fedora-images maken waarop deze laptop goed draait, en die veel van de patches hebben bijgedragen die hem beter laten presteren. De andere distributie die deze handleidingen dekken.
- **[Foxboron/sbctl](https://github.com/Foxboron/sbctl)**: Beheertool voor Secure Boot-sleutels, gebruikt voor het inschrijven van eigen sleutels en het ondertekenen van de kernel en EFI-binaries. Onmisbaar voor het actief houden van Secure Boot met een aangepaste kernel.
- **[sched-ext / scx_lavd](https://github.com/sched-ext/scx)**: Het Linux scheduler-extensibiliteitsframework achter de `scx_lavd` CPU-scheduler. Uitstekende latentie en responsiviteit voor desktop- en gamingworkloads.
- **[lz42/libinput-config](https://github.com/lz42/libinput-config)**: Kernel-niveau workaround voor de ontbrekende scroll speed-instelling in GNOME/Wayland, door libinput-events te onderscheppen vóór de compositor ze verwerkt.
- **[Yubico/pam-u2f](https://github.com/Yubico/pam-u2f)**: PAM-module waarmee een FIDO2-hardwaresleutel (een aanraking van de YubiKey) het wachtwoord vervangt bij sudo, de grafische sudo-prompt en het vergrendelscherm.
- **[Looking Glass](https://looking-glass.io/)**: Een project dat het beeld van een VM met GPU-passthrough met lage latentie op de host toont. Werkt niet op deze hardware, maar het project en de documentatie zijn uitstekend.
- **[Hugo](https://gohugo.io/)**: De statische sitegenerator waarmee de documentatiesite is gebouwd.
- **[Hextra](https://imfing.github.io/hextra/)**: Het Hugo-thema waarop de documentatiesite is gebouwd.


## Licentie

Dit project valt onder de [MIT-licentie](LICENSE).
