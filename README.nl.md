# Zephyrus-Linux

Nederlands | [English](README.md)

CachyOS op de ASUS ROG Zephyrus G16 GA605WV (2024). Mijn persoonlijke setup-log — wat werkte, wat niet, en hoe ik het heb opgelost.

**Bekijk de volledige documentatiesite: [zephyrus-linux.stensel.nl](https://zephyrus-linux.stensel.nl/nl/)**


## Over dit project

Dit is mijn persoonlijke setup-log voor CachyOS op deze laptop. Ik ben geen software-engineer of developer — gewoon iemand die naar Linux is overgestapt en daarna tegen van alles aanliep wat niet meteen werkte. Ik heb alles opgeschreven zodat anderen niet hetzelfde hoeven uitzoeken als ik.

Ik ben nog actief aan het testen en experimenteren — dingen kunnen veranderen, kapot gaan of achteraf onjuist blijken. Alles wat hier staat is gebaseerd op mijn eigen ervaring en is op eigen risico.

Ik ben niet gelieerd aan, goedgekeurd door, of handelend namens ASUS, NVIDIA, Microsoft, CachyOS, of enig ander bedrijf of project dat hier wordt genoemd.


## Systeemspecificaties

| Onderdeel | Specificatie |
|-----------|--------------|
| **Model** | ASUS ROG Zephyrus G16 GA605WV (2024) |
| **CPU** | AMD Ryzen AI 9 HX 370 |
| **iGPU** | AMD Radeon 890M |
| **dGPU** | NVIDIA GeForce RTX 4060 Laptop (Max-Q) |
| **OS** | CachyOS |
| **Kernel** | 6.19.3-2-cachyos |
| **Desktop** | GNOME 49 / Wayland |
| **Secure Boot** | Ingeschakeld |


## De site lokaal bouwen

Deze documentatiesite is gebouwd met [Hugo](https://gohugo.io/) en het [Hextra](https://imfing.github.io/hextra/)-thema. Het thema is opgenomen als git submodule.

**Vereisten:**
- [Hugo extended](https://gohugo.io/installation/) v0.156.0 (gebouwd met deze versie)
- Git

Op Arch Linux / CachyOS:
```bash
sudo pacman -S hugo
```

**Clone met submodules:**
```bash
git clone --recurse-submodules https://github.com/Stensel8/Zephyrus-Linux.git
cd Zephyrus-Linux
```

Als je al gekloond hebt zonder `--recurse-submodules`:
```bash
git submodule update --init --recursive
```

**Ontwikkelserver starten:**
```bash
hugo server
```

De site is beschikbaar op `http://localhost:1313/`. Hugo detecteert wijzigingen en herlaadt automatisch.

**Bouwen voor productie:**
```bash
hugo --gc --minify
```

De output wordt geschreven naar `./public/`. Bij een push naar `main` bouwt GitHub Actions de site automatisch en deployt naar GitHub Pages.


## Afbeeldingen

Alle afbeeldingen in deze repository gebruiken het [AVIF](https://nl.wikipedia.org/wiki/AVIF)-formaat — open, royaltyvrij en efficiënter dan PNG of JPEG bij vergelijkbare kwaliteit. AVIF is de moderne standaard voor webafbeeldingen.

Installeer `avifenc` uit het `libavif`-pakket om PNG-screenshots om te zetten naar AVIF:

```bash
sudo pacman -S libavif
```

Batch-conversie van alle PNGs in `static/images/` (converteert en verwijdert de originelen):

```bash
cd static/images
for f in *.png; do avifenc -q 80 -s 6 "$f" "${f%.png}.avif" && rm "$f"; done
```

- `-q 80` — 80% kwaliteit (schaal 0–100, 100 = verliesvrij)
- `-s 6` — encodersnelheid (0 = beste compressie, 10 = snelst)


## Credits & bronnen

Dit project zou niet bestaan zonder het werk van deze mensen en communities:

- **[Luke Jones](https://asus-linux.org/)** — Maker van `asusctl`, `rog-control-center` en de `asus-armoury` kernel driver. Het ASUS Linux project is de reden dat moderne ASUS laptops goed werken op Linux. Zijn patches zijn gemerged in CachyOS, waardoor dit de best ondersteunde distributie is voor ASUS ROG hardware.
- **[CachyOS](https://cachyos.org/)** — De distributie die deze setup aandrijft. CachyOS is een op Arch gebaseerde distro met uitgebreide hardware-specifieke optimalisaties: een verbeterde scheduler (BORE/EEVDF), beter energiebeheer, ondersteuning voor dynamische verversingsfrequentie, en ingebouwde drivers voor zowel de AMD iGPU als de NVIDIA dGPU — inclusief geïntegreerde GPU-switching. Van alle distributies die ik getest heb (waaronder Fedora, dat dicht in de buurt kwam), is CachyOS veruit de sterkste op dit apparaat.
- **[lz42/libinput-config](https://github.com/lz42/libinput-config)** — Third-party workaround voor de ontbrekende scroll speed-instelling in GNOME/Wayland.
- **[Looking Glass](https://looking-glass.io/)** — Low-latency VM display project. Werkt niet op deze hardware, maar het project en de documentatie zijn uitstekend.
- **[Mastermindzh/tidal-hifi](https://github.com/Mastermindzh/tidal-hifi)** — Community Electron-client voor Tidal op Linux.
- **[Hextra](https://imfing.github.io/hextra/)** — Het Hugo-thema waarop de documentatiesite is gebouwd.


## Licentie

Dit project valt onder de [MIT-licentie](LICENSE).
