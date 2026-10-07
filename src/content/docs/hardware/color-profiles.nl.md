---
title: "Kleurprofielen voor het scherm"
weight: 2
prev: docs/hardware/asusctl-rog-control
next: docs/desktop/gnome-extensions
---

ASUS kalibreert het paneel van elke GA605WV in de fabriek en levert de profielen mee in het Windows-driverpakket. Ze staan in deze repository. Het [setup-venster]({{< relref "/docs/setup-script" >}}) installeert het fabrieksprofiel van jouw paneel en wisselt het scherm tussen **Native** en **sRGB**, de twee G-Helper-standen die op Linux iets betekenen.

## Waarom van profiel wisselen in Instellingen niets doet

In **Instellingen → Color** kun je een profiel aan het ingebouwde scherm toevoegen en er een kiezen. Dat bewaart de keuze in colord, en color-managed apps kunnen het gebruiken, maar GNOME past het profiel niet toe op het scherm. Het paneel is gemaakt voor gekalibreerde profielen van een colorimeter. Die bevatten een gammatabel (`vcgt`) die GNOME in het scherm laadt, en apps lezen de rest. De compositor leest verder niets uit een profiel, en geen van de ASUS-profielen heeft een `vcgt`: de algemene sRGB-, DCI-P3- en Display P3-bestanden zijn kale matrixprofielen van minder dan 700 bytes. Wisselen tussen die profielen verandert dus niets wat je kunt zien.

Dit is niet specifiek voor ASUS of deze laptop. Hetzelfde wordt upstream gemeld voor een wide gamut-monitor met een profiel zonder `vcgt`: [mutter issue 4597](https://gitlab.gnome.org/GNOME/mutter/-/issues/4597). GNOME 52 moet dat veranderen. De beeldschermconfiguratie krijgt dan een ICC-profiel en de compositor past het toe ([mutter merge request 5177](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/5177), op het moment van schrijven nog open). GNOME 51 blijft de softwarematige `sdr-native` kleurmodus gebruiken terwijl volledige ICC-profieltoepassing door de compositor gepland staat voor GNOME 52. Tot die release is de onderstaande kleurmodus hoe GNOME het hele scherm aanstuurt.

## Van stand wisselen

Open het setup-venster en ga naar **Display**. De schakelaar **Color mode** werkt meteen, er is geen toepassen-stap, en de keuze wordt bewaard, dus die blijft na een herstart. De knop **Undo** in de melding zet de vorige stand terug.

| Stand | Wat je ziet | Wat color-managed apps te horen krijgen |
|---|---|---|
| **Native** | Levendig. Het paneel zoals het is, met zijn hele brede gamut, zodat sRGB-inhoud erop wordt uitgerekt | Het fabrieksprofiel van jouw paneel |
| **sRGB** | Kleuren zoals sRGB-inhoud bedoeld is | Het ASUS sRGB-profiel |

**sRGB** heeft GNOME 50 of nieuwer op Wayland nodig. Het gebruikt GNOME's eigen kleurmodus `sdr-native`: GNOME leest de primaire kleuren, het witpunt en de gamma van het paneel uit de EDID en zet sRGB-inhoud daarop om. Dat is een omzetting in software, het paneel zelf verandert niet. Apps die Wayland color management ondersteunen kunnen er ook de hele gamut van het paneel mee gebruiken. GNOME biedt de modus alleen aan als de EDID alle drie heeft, en Instellingen heeft er geen schakelaar voor. De prijs is dat apps op volledig scherm de compositor meestal niet meer kunnen overslaan (direct scanout), dus een spel op volledig scherm kan wat meer vertraging krijgen. Schakel daarvoor terug naar Native als dat uitmaakt.

Om te zien dat het werkt, toont het venster vijf verzadigde kleuren onder **Compare the colors**. In sRGB horen de rode en groene er rustiger uit te zien dan in Native.

Verandert er niets, kijk dan bij **This screen** op dezelfde pagina. **GNOME color mode** toont wat GNOME nu gebruikt en **GNOME offers** noemt wat het voor dit scherm kan. `sdr-native` moet in die lijst staan. `gdctl show --properties` toont hetzelfde onder `supported-color-modes`. **Copy details** zet alles wat het venster weet op het klembord, en dat is wat een bugmelding nodig heeft.

### Waarom geen DCI-P3 of Display P3

Het fabrieksprofiel van het IPS-paneel zegt dat het uit zichzelf ongeveer 94% van DCI-P3 dekt (het OLED-paneel dekt alles), dus Native is al de wide gamut-stand. G-Helper toont DCI-P3 en Display P3 op Windows omdat het eigen hulpprogramma van ASUS erheen kan schakelen. G-Helper toont een stand alleen als het bijbehorende profielbestand bestaat, en vraagt dan `AsusSplendid.exe` om de omschakeling. De profielen beschrijven het paneel nadat die omschakeling is gedaan.

Op Linux doet niets die omschakeling. Een P3-stand zou hetzelfde beeld tonen als Native terwijl het color-managed apps vertelt dat het scherm DCI-P3 is, met een gamma van 2,6 waar het paneel ongeveer 2,15 heeft. Hun kleuren zouden verkeerd uitvallen. Daarom biedt het venster die twee standen niet aan, en installeert het alleen het profiel van jouw paneel en het sRGB-profiel.

### Hoe het de juiste profielen vindt

G-Helper haalt de modelcode uit de BIOS-versie (`GA605WV.309` is een GA605WV) en gebruikt die om het profielpakket voor dat model bij ASUS op te halen. Het setup-venster doet dezelfde opzoeking. Daarna kiest het het fabrieksprofiel dat bij jouw GPU en paneel past. Dat staat in de bestandsnaam: het model, de GPU (`1002` is AMD, `10DE` is NVIDIA) en de paneel-ID uit de EDID, bijvoorbeeld `GA605WV_1002_104D158E_CMDEF`. De profielen staan in deze repository, dus er wordt niets bij ASUS gedownload, en elk bestand wordt gecontroleerd met een SHA-256 die in het script zit.

Nadat je van GPU-modus wisselt (Hybrid, Integrated of Ultimate) hangt het scherm aan een andere GPU en krijgt het een eigen profiel. Pas **ASUS color profiles** in het setup-venster dan nog een keer toe.

### Wat Linux niet kan

Alles onder **Flicker-free Dimming / Visual Mode** in G-Helper is op Windows één ding: `AsusSplendid.exe`, met voor elk onderdeel een ander commando. De gamutlijst, de visual modes, de kleurtemperatuur en de dimschuif lopen er allemaal doorheen ([de broncode](https://raw.githubusercontent.com/seerge/g-helper/main/app/Display/VisualControl.cs)). Het komt mee met de eigen software van ASUS, dus de broncode van G-Helper laat niet zien wat het met het paneel doet. Ik vond op Linux niets dergelijks: `asusctl` en de `asus-armoury`-interface van de kernel hebben `panel_overdrive` en niets voor het scherm.

| G-Helper | Op GNOME |
|---|---|
| Gamut: Native | **Native** in het setup-venster |
| Gamut: sRGB, als jouw G-Helper het toont | **sRGB** in het setup-venster |
| Gamut: DCIP3 en DisplayP3 | Niet hier, zie hierboven |
| Visual mode (Vivid, Cinema, FPS en de rest) | Niets. Native is de levendige |
| Kleurtemperatuur | Night Light, in **Instellingen → Displays**. Het maakt het scherm warmer, op een schema dat je instelt |
| Flicker-free dimming | Niets dat ik gevonden heb |

Wat nog ontbreekt is dat de compositor het fabrieksprofiel zelf toepast. Daarmee zou het scherm nauwkeurig zijn op basis van de gemeten waarden van jouw paneel in plaats van die in de EDID. Dat is het GNOME 52-werk hierboven.

## Met de hand installeren

Het setup-venster doet dit allemaal. Dit is voor als je het zelf wilt doen. Niets hier is distributie-specifiek, behalve waar een profiel mag staan: `/usr/share` is beschrijfbaar op CachyOS en read-only op Bazzite. De locatie per gebruiker werkt op allebei hetzelfde, dus als je maar één account gebruikt, neem dan die.

{{< callout type="warning" >}}
Voeg alleen het bestand toe dat bij jouw GPU en paneel past. De algemene bestanden `ASUS_sRGB`, `ASUS_DCIP3` en `ASUS_DisplayP3` beschrijven de standen waar het Windows-hulpprogramma van ASUS naartoe schakelt. Op Linux actief gezet vertellen ze color-managed apps iets wat niet klopt over je scherm. `ASUS_sRGB` past alleen zolang het scherm in de sRGB-stand van het setup-venster staat.
{{< /callout >}}

{{< tabs >}}
{{< tab name="CachyOS" >}}

| Locatie | Bereik |
|---|---|
| `/usr/share/color/icc/colord/` | Systeembreed (alle gebruikers, root vereist) |
| `~/.local/share/icc/` | Alleen de huidige gebruiker |

{{< /tab >}}
{{< tab name="Bazzite" >}}

`/usr` hoort bij de image en is read-only, dus het systeembrede pad uit de CachyOS-tab bestaat hier niet. Gebruik de locatie per gebruiker:

| Locatie | Bereik |
|---|---|
| `~/.local/share/icc/` | Alleen de huidige gebruiker. **Gebruik deze** |
| `/usr/local/share/color/icc/` | Systeembreed. `/usr/local` is op een atomic systeem een symlink naar `/var/usrlocal`, dus het overleeft image-updates en is beschrijfbaar |

Een profiel met `rpm-ostree` in de image layeren zou werken, maar is het verkeerde gereedschap: dit zijn databestanden voor jouw account, geen onderdeel van het systeem.

{{< /tab >}}
{{< /tabs >}}

{{% details title="ASUS GameVisual kleurprofielen installeren voor GA605WV ingebouwd display" closed="true" %}}

De GA605WV wordt geleverd met een 16" 2560x1600 240Hz ROG Nebula Display. ASUS kalibreert elk paneel in de fabriek en levert kleurprofielen via hun ASUS System Control Interface. Op Windows worden deze automatisch toegepast door Armoury Crate/GameVisual. Op Linux moeten we deze handmatig installeren.

De GA605WV werd geleverd met verschillende panelen afhankelijk van het exemplaar. Het standaard model gebruikt een IPS-paneel (ROG Nebula Display); sommige configuraties worden geleverd met een OLED-paneel:

| Panel ID | Fabrikant | Model | Type |
|---|---|---|---|
| `104D158E` | Sharp | LQ160R1JW02 | IPS (ROG Nebula Display) |
| `834C41AE` | Samsung | ATNA60DL04-0 ([LaptopMedia](https://laptopmedia.com/screen/atna60dl04-0-sdc41ae/) · [Linux Hardware](https://linux-hardware.org/?id=eisa:samsung-sdc41ae)) | OLED |
| `E5090C19` | Onbekend | (aanwezig in ASUS driver package, nog niet publiek geïdentificeerd) | Onbekend |

Controleer welk paneel jouw exemplaar heeft:

```bash
cat /sys/class/drm/card*-eDP-*/edid | edid-decode 2>/dev/null | grep -i "manufacturer\|model\|product name"
```

Deze kleurprofielen zijn verkregen door het reverse engineeren van het ASUS Windows driver package. Door de structuur van de ASUS CDN en de inhoud van de driver ZIP-bestanden te analyseren, zijn alle fabrieksgekalibreerde profielen voor deze laptop gevonden. De bestanden houden de eigen technische namen van ASUS, bijvoorbeeld `ASUS_GA605WV_1002_104D158E_CMDEF`. Het setup-venster installeert ze onder leesbare namen.

**Installeer de kleurprofielen:**

De ICC kleurprofielen staan in de [`/icc-profiles/`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles) map van deze repository. Clone de repository of download de profielen handmatig en kopieer ze naar een van de locaties boven aan deze pagina. Per gebruiker werkt op beide distributies hetzelfde:

```bash
mkdir -p ~/.local/share/icc
cp GA605WV_1002_104D158E_CMDEF.icm ~/.local/share/icc/
```

**Activeer je profiel in GNOME:**

1. Open **Instellingen** → **Color Management**
2. Selecteer je display (bijv. **Built-In Screen**)
3. Klik **Add Profile**
4. Selecteer het profiel dat overeenkomt met jouw display en GPU-combinatie (bijv. **ASUS GA605WV 1002 104D158E CMDEF** voor AMD iGPU + Sharp LQ160R1JW02)
5. Klik **Add**

**Opmerking:** Met de hand gekopieerd verschijnen de profielen onder hun technische namen, zoals "ASUS GA605WV 1002 104D158E CMDEF". Ontbreekt een profiel dat je net hebt gekopieerd, sluit Settings dan af en heropen, of log uit en weer in om de color cache te verversen.

De bestandsnaam bevat je GPU (`1002` = AMD, `10DE` = NVIDIA) en paneel-ID. Koppel deze aan jouw exemplaar via de paneeltabel hierboven. Alle profielen staan in de [`/icc-profiles/`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles) map.

**Achtergrond:**

De profielen zijn gevonden door analyse van ASUS Windows driver packages. De ASUS CDN URL structuur:
```
https://dlcdn-rogboxbu1.asus.com/pub/ASUS/APService/Gaming/SYS/ROGS/{id}-{code}-{hash}.zip
```

Voor de GA605WV is dit: `20016-BWVQPK-01624c1cdd5a3c05252bad472fab1240.zip`

**Technische Details:**

De profielen in deze repository zijn de bestanden van ASUS zoals ze uit het driver package kwamen. Het setup-venster herschrijft tijdens het installeren alleen de description-tag (de naam die GNOME toont) en laat de kleurdata ongemoeid. [G-Helper](https://github.com/seerge/g-helper) doet de Windows-versie hiervan: het downloadt de zip voor jouw model van de ASUS CDN naar `C:\ProgramData\ASUS\GameVisual` en biedt de profielen daarin aan als Native, sRGB, DCIP3 en DisplayP3.

{{% /details %}}
