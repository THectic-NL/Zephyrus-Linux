# Zephyrus-Linux

Nederlands | [English](README.md)

Linux op de ASUS ROG Zephyrus G16 GA605WV (2024). Mijn persoonlijke setup-log voor de twee distributies die ik erop draai, CachyOS en Bazzite: wat werkte, wat niet, en hoe ik het heb opgelost.

**Bekijk de volledige documentatiesite: [zephyrus-linux.thectic.nl](https://zephyrus-linux.thectic.nl/nl/)**


## Over dit project

Dit is mijn persoonlijke setup-log voor deze laptop. Ik ben geen developer, gewoon iemand die naar Linux is overgestapt en daarna tegen van alles aanliep wat niet meteen werkte. Ik heb alles opgeschreven zodat anderen dat niet hoeven uitzoeken.

De handleidingen dekken CachyOS (Arch) en Bazzite (Fedora Atomic). Ik heb ze allebei als dagelijks systeem gedraaid en wissel ertussen; op dit moment zit ik op Bazzite. De [Aan de slag](https://zephyrus-linux.thectic.nl/nl/docs/)-pagina legt de keuze uit, en een switcher bovenaan elke pagina brengt je tussen de twee sets handleidingen.

Ik ben nog actief aan het testen en experimenteren: dingen kunnen veranderen, kapot gaan of achteraf onjuist blijken. Alles wat hier staat is gebaseerd op mijn eigen ervaring en is op eigen risico.

Ik ben niet gelieerd aan, goedgekeurd door, of handelend namens ASUS, NVIDIA, Microsoft, CachyOS, Universal Blue, of enig ander bedrijf of project dat hier wordt genoemd.

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

Hugo downloadt de thema-module automatisch bij de eerste keer uitvoeren.

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

Alle afbeeldingen in deze repository gebruiken het [AVIF](https://nl.wikipedia.org/wiki/AVIF)-formaat: open, royaltyvrij en efficiënter dan PNG of JPEG bij vergelijkbare kwaliteit. AVIF is de moderne standaard voor webafbeeldingen.

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

- **[ASUS Linux community](https://asus-linux.org/)**: Het project achter `asusctl` en `rog-control-center`, tegenwoordig onderhouden onder het [Open Gaming Collective](https://github.com/OpenGamingCollective/asusctl). Luke Jones is hier een grote drijvende kracht achter geweest, en ook andere bijdragers hebben kernel patches ingediend, waarvan velen inmiddels in mainline Linux zijn gemerged, waardoor moderne ASUS ROG laptops echt bruikbaar zijn op Linux.
- **[CachyOS](https://cachyos.org/)**: Een op Arch gebaseerde distributie met uitgebreide hardware-specifieke tuning: een verbeterde scheduler (BORE/EEVDF), beter energiebeheer, ondersteuning voor dynamische verversingsfrequentie, en ingebouwde drivers voor zowel de AMD iGPU als de NVIDIA dGPU, inclusief geïntegreerde GPU-switching. Een van de twee distributies die deze handleidingen dekken.
- **[Bazzite / Universal Blue](https://universal-blue.org/)**: De mensen die de atomic Fedora-images maken waarop deze laptop goed draait, en die veel van de patches hebben bijgedragen die hem beter laten presteren. De andere distributie die deze handleidingen dekken.
- **[Foxboron/sbctl](https://github.com/Foxboron/sbctl)**: Beheertool voor Secure Boot-sleutels, gebruikt voor het inschrijven van eigen sleutels en het ondertekenen van de kernel en EFI-binaries. Onmisbaar voor het actief houden van Secure Boot met een aangepaste kernel.
- **[sched-ext / scx_lavd](https://github.com/sched-ext/scx)**: Het Linux scheduler-extensibiliteitsframework achter de `scx_lavd` CPU-scheduler. Uitstekende latentie en responsiviteit voor desktop- en gamingworkloads.
- **[lz42/libinput-config](https://github.com/lz42/libinput-config)**: Kernel-niveau workaround voor de ontbrekende scroll speed-instelling in GNOME/Wayland, door libinput-events te onderscheppen vóór de compositor ze verwerkt.
- **[Yubico/pam-u2f](https://github.com/Yubico/pam-u2f)**: PAM-module voor FIDO2/WebAuthn hardware token-authenticatie bij sudo en het vergrendelscherm. Gebruikt samen met `systemd-cryptenroll` voor schijfversleuteling via YubiKey.
- **[Looking Glass](https://looking-glass.io/)**: Low-latency GPU passthrough display project. Werkt niet op deze hardware, maar het project en de documentatie zijn uitstekend.
- **[Hugo](https://gohugo.io/)**: De statische sitegenerator waarmee de documentatiesite is gebouwd.
- **[Hextra](https://imfing.github.io/hextra/)**: Het Hugo-thema waarop de documentatiesite is gebouwd.


## Licentie

Dit project valt onder de [MIT-licentie](LICENSE).
