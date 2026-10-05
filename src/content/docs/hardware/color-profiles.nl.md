---
title: "Kleurprofielen voor het scherm"
weight: 2
prev: docs/hardware/asusctl-rog-control
next: docs/desktop/gnome-extensions
---

ASUS kalibreert het paneel van elke GA605WV in de fabriek en levert de profielen mee in het Windows-driverpakket. Op Linux past niets ze toe, dus het ingebouwde scherm blijft op de standaardinstelling staan totdat je de profielen met de hand installeert.

Niets op deze pagina is distributie-specifiek, behalve waar een profiel mag staan: `/usr/share` is beschrijfbaar op CachyOS en read-only op Bazzite. De locatie per gebruiker werkt op allebei hetzelfde, dus gebruik je maar één account, houd het daar dan op en sla die vraag over.

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

## De profielen

{{< callout type="info" >}}
**Eén opdracht in plaats van de stappen hieronder.** Het [setup-script]({{< relref "/docs/setup-script" >}}) installeert de vier profielen die G-Helper op Windows laat zien, **Native** (het fabrieksgekalibreerde profiel van jouw paneel), **sRGB**, **DCI-P3** en **Display P3**, onder leesbare namen in colord's eigen profielmap, en voegt ze toe aan het Ingebouwde scherm, zodat je er een kunt kiezen in Instellingen → Color Management. Wisselen vanuit de terminal kan met `python3 zephyrus-setup.py color set srgb`.

**Dit verandert niet hoe je scherm eruitziet.** Op Linux vertelt een profiel aan color-managed apps (browsers, beeldbewerking, videospelers) wat het paneel doet. Het schakelt niet de eigen gamut-modus van het paneel om zoals de Windows-software van ASUS dat doet. [G-Helper's broncode](https://raw.githubusercontent.com/seerge/g-helper/main/app/Display/VisualControl.cs) wisselt de gamut door ASUS's `AsusSplendid.exe` met een `GamutMode`-commando te draaien, dat via het `ATKWMIACPIIO`-stuurprogramma met de firmware praat; de `.icm`-bestanden staan daar alleen naast. Ik vond geen aanwijzing dat `asusctl` of de `asus-armoury`-interface van de kernel zo'n schakelaar aanbiedt: op deze laptop zitten er `panel_overdrive` en niets voor gamut tussen de attributen. GNOME zelf doet ook weinig. Het past de `vcgt`-gammatabel van een profiel toe (dat is wat Night Light verandert), en geen van deze vier profielen heeft er een: de sRGB-, DCI-P3- en Display P3-bestanden zijn kale matrixprofielen van ongeveer 640 bytes. Getest door tussen alle vier te wisselen terwijl ik naar het scherm keek: er verandert niets, terwijl Night Light wel iets verandert.

Nog een gevolg: de sRGB-, DCI-P3- en Display P3-profielen beschrijven het paneel *nadat* ASUS's hardware-schakelaar is omgezet. Zonder die schakelaar vertellen ze color-managed apps het verkeerde, dus laat **Native** actief.
{{< /callout >}}

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

Deze kleurprofielen zijn verkregen door het reverse engineeren van het ASUS Windows driver package. Door de structuur van de ASUS CDN en de inhoud van de driver ZIP-bestanden te analyseren, zijn alle fabrieksgekalibreerde profielen voor deze laptop gevonden. De bestanden houden de eigen technische namen van ASUS, bijvoorbeeld `ASUS_GA605WV_1002_104D158E_CMDEF`. Het setup-script installeert ze onder leesbare namen.

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

De profielen in deze repository zijn de bestanden van ASUS zoals ze uit het driver package kwamen. Het setup-script herschrijft tijdens het installeren alleen de description-tag (de naam die GNOME toont) en laat de kleurdata ongemoeid. [G-Helper](https://github.com/seerge/g-helper) doet de Windows-versie hiervan: het downloadt de zip voor jouw model van de ASUS CDN naar `C:\ProgramData\ASUS\GameVisual` en biedt de profielen daarin aan als Native, sRGB, DCIP3 en DisplayP3.

{{% /details %}}
