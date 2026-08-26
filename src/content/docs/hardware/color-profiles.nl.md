---
title: "Kleurprofielen voor het scherm"
weight: 6
prev: docs/hardware/asusctl-rog-control
next: docs/security/autologin
---

ASUS kalibreert het paneel van elke GA605WV in de fabriek en levert de profielen mee in het Windows-driverpakket. Op Linux past niets ze toe, dus zowel het ingebouwde scherm als een externe Samsung ViewFinity blijft op de standaardinstelling staan totdat je de profielen met de hand installeert.

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
| `~/.local/share/icc/` | Alleen de huidige gebruiker — **gebruik deze** |
| `/usr/local/share/color/icc/` | Systeembreed. `/usr/local` is op een atomic systeem een symlink naar `/var/usrlocal`, dus het overleeft image-updates en is beschrijfbaar |

Een profiel met `rpm-ostree` in de image layeren zou werken, maar is het verkeerde gereedschap: dit zijn databestanden voor jouw account, geen onderdeel van het systeem.

{{< /tab >}}
{{< /tabs >}}

## De profielen

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

Deze kleurprofielen zijn verkregen door het reverse engineeren van het ASUS Windows driver package. Door de structuur van de ASUS CDN en de inhoud van de driver ZIP-bestanden te analyseren, zijn alle fabrieksgekalibreerde profielen voor deze laptop gevonden. De ICC metadata is vervolgens aangepast zodat de profielen direct met leesbare namen verschijnen in GNOME Color Management.

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
4. Selecteer het profiel dat overeenkomt met jouw display en GPU-combinatie (bijv. **Native** voor AMD iGPU + Sharp LQ160R1JW02)
5. Klik **Add**

**Opmerking:** Als GNOME Settings de oude technische namen toont (bijv. "ASUS GA605WV 1002 104D158E CMDEF" in plaats van "Native"), sluit Settings af en heropen, of log uit/in om de color cache te verversen.

De bestandsnaam bevat je GPU (`1002` = AMD, `10DE` = NVIDIA) en paneel-ID. Koppel deze aan jouw exemplaar via de paneeltabel hierboven. Alle profielen staan in de [`/icc-profiles/`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles) map.

**Achtergrond:**

De profielen zijn gevonden door analyse van ASUS Windows driver packages. De ASUS CDN URL structuur:
```
https://dlcdn-rogboxbu1.asus.com/pub/ASUS/APService/Gaming/SYS/ROGS/{id}-{code}-{hash}.zip
```

Voor de GA605WV is dit: `20016-BWVQPK-01624c1cdd5a3c05252bad472fab1240.zip`

**Technische Details:**

De profielen in deze repository zijn al voorbewerkt met aangepaste ICC metadata 'desc' tags, zodat ze direct met leesbare namen verschijnen in GNOME Color Management. Voor gebruikers die geïnteresseerd zijn in hoe deze modificaties werken, kun je zelf vergelijkbare ICC 'desc' tag manipulatie implementeren met Python's PIL/ImageCms.

{{% /details %}}

{{% details title="Samsung kleurprofiel installeren voor LS27B800TGUXEN (S80TB) Thunderbolt display" closed="true" %}}

De Samsung ViewFinity S8 Thunderbolt (LS27B800TGUXEN) wordt geleverd met een fabriekskleurprofiel (`SxxB80xT.icm`) dat is opgenomen in het Windows INF driver package. Op Linux moet dit profiel handmatig worden geïnstalleerd.

Het profiel staat in de [`/icc-profiles/LS27B800TGUXEN - S80TB/`](https://github.com/THectic-NL/Zephyrus-Linux/tree/main/src/static/icc-profiles/LS27B800TGUXEN%20-%20S80TB) map van deze repository.

**Installeer het kleurprofiel:**

Dezelfde locaties als hierboven:

```bash
mkdir -p ~/.local/share/icc
cp SxxB80xT.icm ~/.local/share/icc/
```

**Activeer in GNOME:**

1. Open **Instellingen** → **Color Management**
2. Selecteer het **Samsung display** (bijv. "LS27B800TGUXEN")
3. Klik **Add Profile**
4. Selecteer `SxxB80xT`
5. Klik **Add**

{{% /details %}}
