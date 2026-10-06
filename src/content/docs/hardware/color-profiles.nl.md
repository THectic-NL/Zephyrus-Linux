---
title: "Kleurprofielen voor het scherm"
weight: 2
prev: docs/hardware/asusctl-rog-control
next: docs/desktop/gnome-extensions
---

ASUS kalibreert het paneel van elke GA605WV in de fabriek en levert de profielen mee in het Windows-driverpakket. Op Linux past niets ze uit zichzelf toe, dus het ingebouwde scherm blijft op de standaardinstelling staan totdat je ze installeert. Het [setup-venster]({{< relref "/docs/setup-script" >}}) installeert ze voor je en wisselt tussen de standen, zoals G-Helper dat op Windows doet.

## Van stand wisselen

Open het setup-venster en ga naar **Display**. De schakelaar **Color mode** werkt meteen, er is geen toepassen-stap, en de keuze wordt bewaard, dus die blijft na een herstart. De knop **Undo** in de melding zet de vorige stand terug.

| Stand | Wat je ziet | Wat color-managed apps te horen krijgen |
|---|---|---|
| **Native** | Het paneel zoals het is, met zijn hele brede gamut. sRGB-inhoud ziet er levendig en een beetje oververzadigd uit | Het fabrieksprofiel van jouw paneel |
| **sRGB** | Kleuren zoals sRGB-inhoud bedoeld is | Het ASUS sRGB-profiel |
| **DCI-P3** | Hetzelfde beeld als Native | Het ASUS DCI-P3-profiel |
| **Display P3** | Hetzelfde beeld als Native | Het ASUS Display P3-profiel |

Alleen **sRGB** verandert het beeld, en het heeft GNOME 50 of nieuwer op Wayland nodig. Het gebruikt GNOME's eigen kleurmodus `sdr-native`: GNOME leest de echte primaire kleuren van het paneel uit de EDID en zet sRGB-inhoud daarop om. Dat is een omzetting in software, het paneel zelf verandert niet. Op een oudere GNOME verandert de schakelaar alleen het profiel.

De twee P3-standen vertellen alleen aan color-managed apps, zoals beeldbewerking, wat ze van het scherm kunnen verwachten. Voor het bureaublad zelf zien ze eruit als Native. Een snelle controle: open een kleurrijke afbeelding en wissel tussen Native en sRGB. Native hoort de meest verzadigde te zijn.

De Display-pagina van het venster toont ook het model, het paneel, de GPU waar het scherm aan hangt en hoeveel van sRGB en DCI-P3 het paneel dekt, voor zover de EDID dat zegt.

### Hoe het de juiste profielen vindt

G-Helper haalt de modelcode uit de BIOS-versie (`GA605WV.309` is een GA605WV) en gebruikt die om het profielpakket voor dat model bij ASUS op te halen. Het setup-venster doet dezelfde opzoeking. Daarna kiest het het fabrieksprofiel dat bij jouw GPU en paneel past. Dat staat in de bestandsnaam: het model, de GPU (`1002` is AMD, `10DE` is NVIDIA) en de paneel-ID uit de EDID, bijvoorbeeld `GA605WV_1002_104D158E_CMDEF`. De profielen staan in deze repository, dus er wordt niets bij ASUS gedownload, en elk bestand wordt gecontroleerd met een SHA-256 die in het script zit. De drie algemene (sRGB, DCI-P3, Display P3) zijn voor elk paneel hetzelfde.

Nadat je van GPU-modus wisselt (Hybrid, Integrated of Ultimate) hangt het scherm aan een andere GPU en krijgt het een eigen profiel. Pas **ASUS color profiles** in het setup-venster dan nog een keer toe.

### Wat Linux niet kan

Op Windows wisselt G-Helper de gamut van het paneel met ASUS's eigen software. Het draait `AsusSplendid.exe` met een `GamutMode`-commando, en dat praat via het `ATKWMIACPIIO`-stuurprogramma met de firmware ([de broncode](https://raw.githubusercontent.com/seerge/g-helper/main/app/Display/VisualControl.cs)). Ik vond op Linux niets dergelijks: `asusctl` en de `asus-armoury`-interface van de kernel hebben `panel_overdrive` en niets voor gamut. De andere ASUS Visual-standen, bijvoorbeeld Vivid, zijn ook firmware, dus die zijn er ook niet. Native is de levendige.

Een profiel op zich verandert het beeld niet. GNOME leest er alleen de gammatabel (`vcgt`) uit, en dat is wat Night Light verandert, en geen van de vier ASUS-profielen heeft er een: de sRGB-, DCI-P3- en Display P3-bestanden zijn kale matrixprofielen van ongeveer 640 bytes. Ik heb alle vier in Instellingen geprobeerd zonder iets anders om te zetten. Er veranderde niets, terwijl Night Light wel iets veranderde. Daarom gebruikt de sRGB-stand GNOME's kleurmodus en is het profiel er alleen voor de apps.

De sRGB-, DCI-P3- en Display P3-profielen beschrijven het paneel *nadat* ASUS's hardware-schakelaar is omgezet. Zonder die schakelaar vertellen ze color-managed apps iets wat niet klopt voor DCI-P3 en Display P3, dus **Native** is de veiligste om actief te laten.

## Met de hand installeren

Het setup-venster doet dit allemaal. Dit is voor als je het zelf wilt doen. Niets hier is distributie-specifiek, behalve waar een profiel mag staan: `/usr/share` is beschrijfbaar op CachyOS en read-only op Bazzite. De locatie per gebruiker werkt op allebei hetzelfde, dus als je maar één account gebruikt, neem dan die.

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
