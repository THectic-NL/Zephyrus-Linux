---
title: "Kleurprofielen voor het scherm"
weight: 2
prev: docs/hardware/asusctl-rog-control
next: docs/desktop/gnome-extensions
---

ASUS kalibreert het paneel van elke GA605WV in de fabriek en levert de profielen mee in het Windows-driverpakket. Ik vond geen andere manier om er op Linux aan te komen, dus heb ik ze met reverse engineering uit dat pakket gehaald en in deze repository gezet.

**Je kunt er nu nog weinig mee.** Standaard draait je scherm op Linux en GNOME al op zijn eigen, levendige kleuren, en GNOME past een kleurprofiel niet toe op het scherm zelf, dus een profiel toevoegen verandert niets wat je kunt zien. Ik deel ze omdat ze op een andere manier moeilijk te krijgen zijn, en omdat ze later nog van pas kunnen komen: ze zijn wat een GNOME dat een profiel op het beeldscherm toepast nodig heeft (zie hieronder). Color-managed apps kunnen een profiel nu al uit colord lezen.

## Waar ze vandaan komen

ASUS levert de fabrieksprofielen mee in een driverpakket per model voor Windows. [G-Helper](https://github.com/seerge/g-helper) werkt op Windows met dat pakket: het haalt de modelcode uit de BIOS-versie (`GA605WV.309` is een GA605WV), downloadt de zip voor dat model van de ASUS CDN naar `C:\ProgramData\ASUS\GameVisual` en biedt de profielen daarin aan als Native, sRGB, DCIP3 en DisplayP3.

De Linux-kopieën heb ik gevonden door de structuur van die CDN en de inhoud van de driver-zip te reverse engineeren. De URL ziet er zo uit:

```
https://dlcdn-rogboxbu1.asus.com/pub/ASUS/APService/Gaming/SYS/ROGS/{id}-{code}-{hash}.zip
```

Voor de GA605WV is dat `20016-BWVQPK-01624c1cdd5a3c05252bad472fab1240.zip`. De bestanden in deze repository zijn die van ASUS zelf, zoals ze uit het pakket kwamen, met de technische namen van ASUS. De naam zegt welke van jou is: het model, de GPU (`1002` is AMD, `10DE` is NVIDIA) en de paneel-ID uit de EDID, bijvoorbeeld `GA605WV_1002_104D158E_CMDEF`. Ze staan allemaal in de map [`icc-profiles`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles), met een README die ze opsomt.

## Waarom van profiel wisselen in Instellingen niets doet

In **Instellingen → Color** kun je een profiel aan het ingebouwde scherm toevoegen en er een kiezen. Dat bewaart de keuze in colord, en color-managed apps kunnen het gebruiken, maar GNOME past het profiel niet toe op het scherm. Het paneel is gemaakt voor gekalibreerde profielen van een colorimeter. Die bevatten een gammatabel (`vcgt`) die GNOME in het scherm laadt, en apps lezen de rest. De compositor leest verder niets uit een profiel, en geen van de ASUS-profielen heeft een `vcgt`: de algemene sRGB-, DCI-P3- en Display P3-bestanden zijn kale matrixprofielen van minder dan 700 bytes. Wisselen tussen die profielen verandert dus niets wat je kunt zien.

Dit is niet specifiek voor ASUS of deze laptop. Hetzelfde wordt upstream gemeld voor een wide gamut-monitor met een profiel zonder `vcgt`: [mutter issue 4597](https://gitlab.gnome.org/GNOME/mutter/-/issues/4597). GNOME 52 moet dat veranderen. De beeldschermconfiguratie krijgt dan een ICC-profiel en de compositor past het toe ([mutter merge request 5177](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/5177), op het moment van schrijven nog open). Tot die release toont het scherm de eigen kleuren van het paneel, en dat is de levendige weergave die je al hebt.

## Wat het setup-venster doet

Het [setup-venster]({{< relref "/docs/setup-script" >}}) heeft hiervoor één onderdeel, **ASUS factory color profile**, in de sectie Display. Het zet het fabrieksprofiel van jouw paneel in colord en maakt het daar het actieve profiel, voor color-managed apps. Dat is alles: het beeld op je scherm verandert niet. **Select recommended** laat het weg.

Het kiest het profiel dat bij jouw GPU en paneel past, aan de hand van de bestandsnaam die hierboven staat. De profielen staan in deze repository, dus er wordt niets bij ASUS gedownload, en elk bestand wordt gecontroleerd met een SHA-256 die in het script zit. Nadat je van GPU-modus wisselt (Hybrid, Integrated of Ultimate) hangt het scherm aan een andere GPU en krijgt het een eigen profiel. Pas het onderdeel dan nog een keer toe.

Een eerdere versie van het venster had ook een schakelaar tussen **Native** en **sRGB**. Die is weg: wisselen veranderde niets wat je kon zien, en Native is wat het scherm standaard al doet.

## Wat Windows kan en Linux niet

Alles onder **Flicker-free Dimming / Visual Mode** in G-Helper is op Windows één ding: `AsusSplendid.exe`, met voor elk onderdeel een ander commando. De gamutlijst, de visual modes, de kleurtemperatuur en de dimschuif lopen er allemaal doorheen ([de broncode](https://raw.githubusercontent.com/seerge/g-helper/main/app/Display/VisualControl.cs)). Het komt mee met de eigen software van ASUS, dus de broncode van G-Helper laat niet zien wat het met het paneel doet. De `.icm`-bestanden bepalen alleen welke standen G-Helper toont, en ze beschrijven het paneel nadat die omschakeling is gedaan. Ik vond op Linux niets dergelijks: `asusctl` en de `asus-armoury`-interface van de kernel hebben `panel_overdrive` en niets voor het scherm.

| G-Helper | Op GNOME |
|---|---|
| Gamut: Native | Wat het scherm al doet |
| Gamut: sRGB, DCIP3 en DisplayP3 | Nog niets. De profielen bestaan, niets past ze toe |
| Visual mode (Vivid, Cinema, FPS en de rest) | Niets. Native is de levendige |
| Kleurtemperatuur | Night Light, in **Instellingen → Displays**. Het maakt het scherm warmer, op een schema dat je instelt |
| Flicker-free dimming | Niets dat ik gevonden heb |

Wat nog ontbreekt is dat de compositor het fabrieksprofiel zelf toepast. Daarmee zou het scherm nauwkeurig zijn op basis van de gemeten waarden van jouw paneel in plaats van die in de EDID. Dat is het GNOME 52-werk hierboven, en de reden dat deze bestanden het bewaren waard zijn.

## Met de hand installeren

Het setup-venster doet het colord-deel voor je. Dit is voor als je het zelf wilt doen. Niets hier is distributie-specifiek, behalve waar een profiel mag staan: `/usr/share` is beschrijfbaar op CachyOS en read-only op Bazzite. De locatie per gebruiker werkt op allebei hetzelfde, dus als je maar één account gebruikt, neem dan die.

{{< callout type="warning" >}}
Voeg alleen het bestand toe dat bij jouw GPU en paneel past. De algemene bestanden `ASUS_sRGB`, `ASUS_DCIP3` en `ASUS_DisplayP3` beschrijven de standen waar het Windows-hulpprogramma van ASUS naartoe schakelt. Op Linux actief gezet vertellen ze color-managed apps iets wat niet klopt over je scherm.
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

**Installeer de kleurprofielen:**

De ICC kleurprofielen staan in de [`/icc-profiles/`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles) map van deze repository. Clone de repository of download de profielen handmatig en kopieer ze naar een van de locaties hierboven. Per gebruiker werkt op beide distributies hetzelfde:

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

**Technische Details:**

De profielen in deze repository zijn de bestanden van ASUS zoals ze uit het driver package kwamen. Het setup-venster herschrijft tijdens het installeren van het profiel alleen de description-tag (de naam die GNOME toont) en laat de kleurdata ongemoeid.

{{% /details %}}
