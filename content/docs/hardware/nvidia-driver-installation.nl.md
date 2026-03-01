---
title: "NVIDIA Driver Installatie"
weight: 1
prev: docs/getting-started
---

De G16 heeft een NVIDIA RTX 4060 naast de AMD iGPU. De open-source Nouveau driver werkt niet goed op moderne NVIDIA-hardware, dus proprietary drivers zijn nodig.

**Driver die ik gebruik:**
- Versie: 590.48.01
- CUDA-versie: 13.1


## CachyOS (Arch)

CachyOS detecteert je hardware automatisch tijdens de installatie en installeert de NVIDIA-driver zonder handmatige stappen. Je hoeft zelf niets te selecteren; als de installer klaar is, is de driver al actief en volledig geconfigureerd.

Ga naar [Verificatie Na Installatie](#verificatie-na-installatie) om te bevestigen dat alles correct werkt.


## Fedora

De volgende stappen behandelen het volledige handmatige installatieproces. Ik liep tijdens de installatie tegen meerdere crashes en lockups aan die wat tijd kostten om op te sporen; die staan gedocumenteerd op de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}).

## Vereisten

### RPM Fusion inschakelen

RPM Fusion levert de NVIDIA drivers voor Fedora. Schakel beide repositories in voordat je installeert:

```bash
sudo dnf install \
  https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
  https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
```

### Systeem Verificatie

{{% details title="Controleer kernelversie" closed="true" %}}

Vereist: Kernel 6.19+ voor Ryzen AI 9 HX 370 ondersteuning.

```bash
uname -r
```

{{% /details %}}

{{% details title="Controleer Secure Boot-status" closed="true" %}}

```bash
mokutil --sb-state
```

{{% /details %}}

### Waarom Proprietary Driver

De open-source Nouveau driver heeft slechte prestaties op moderne NVIDIA GPU's. De proprietary driver is vereist voor:
- Gaming en graphics-intensieve applicaties
- CUDA workloads
- Goede Wayland-ondersteuning (beschikbaar sinds driver 555+)


## Installatiestappen

{{% steps %}}

### Systeem updaten

```bash
sudo dnf upgrade
```

Wacht tot de update voltooid is.

### Driver versie verifiëren

Controleer de beschikbare NVIDIA-driverversie:

```bash
dnf info akmod-nvidia
```

### NVIDIA driver installeren

Installeer de driver met CUDA-ondersteuning:

```bash
sudo dnf install akmod-nvidia xorg-x11-drv-nvidia-cuda xorg-x11-drv-nvidia-libs.i686
```

Dit installeert de driver, CUDA libraries en build dependencies (ongeveer 1 GB).
- `akmod-nvidia` - NVIDIA driver via akmods voor automatisch kernel module bouwen en signeren
- `xorg-x11-drv-nvidia-cuda` - CUDA-ondersteuning en driverutilities (inclusief Wayland ondersteuning)
- `xorg-x11-drv-nvidia-libs.i686` - 32-bit NVIDIA libraries (nodig voor Steam/Proton)

### Kernel modules bouwen

akmods bouwt en ondertekent kernelmodules automatisch tijdens installatie. Om handmatig te triggeren:

```bash
sudo akmods --force
sudo dracut --force
```

Dit proces kan 5-10 minuten duren.

### Kernel modules verifiëren

Controleer of de kernelmodules gebouwd zijn:

```bash
ls /lib/modules/$(uname -r)/kernel/drivers/video/
```

De NVIDIA modules moeten aanwezig zijn.

### MOK signing key enrollen

Als Secure Boot is ingeschakeld, importeer de akmods signing key en stel een wachtwoord in:

```bash
sudo mokutil --import /etc/pki/akmods/certs/public_key.der
```

### MOK enrollment bij volgende boot

```bash
sudo reboot
```

Tijdens boot verschijnt het MOK Management scherm (blauw scherm):
1. Selecteer "Enroll MOK"
2. Selecteer "Continue"
3. Selecteer "Yes"
4. Voer het wachtwoord in dat je in de vorige stap hebt ingesteld
5. Reboot

Het systeem boot normaal na MOK enrollment.

### Definitieve reboot

```bash
sudo reboot
```

De NVIDIA driver laadt nu correct.

### NVIDIA power management services activeren

Activeer NVIDIA power services voor beter suspend/resume-gedrag:

```bash
sudo systemctl enable nvidia-hibernate.service nvidia-suspend.service nvidia-resume.service
```

**Wat deze services doen:**
- `nvidia-hibernate.service` - Slaat GPU state correct op voor hibernation
- `nvidia-suspend.service` - Beheert GPU state tijdens system suspend
- `nvidia-resume.service` - Herstelt GPU state na resume

Deze services voorkomen GPU state problemen na suspend/resume cycli.

**Belangrijk: `nvidia-powerd` niet activeren; permanent masken**

De `nvidia-powerd.service` beheert NVIDIA Dynamic Boost, waarmee extra wattage (~5-15W) van de CPU naar de GPU geschoven wordt tijdens zware GPU-belasting. Hoewel nuttig op Intel-gebaseerde laptops, conflicteert het met AMD ATPX power management op de Zephyrus G16 en veroorzaakt soft lockups en "GPU has fallen off the bus" fouten.

Op deze laptop wordt GPU-vermogensbeheer geregeld via ATPX (AMD-gestuurd via ACPI). De NVIDIA suspend/hibernate/resume services en `supergfxctl` beheren power states correct zonder `nvidia-powerd`.

**Wat je verliest door het uit te zetten:** Minimaal. Een paar FPS minder bij zware GPU workloads. De ~5-15W Dynamic Boost is de instabiliteit niet waard op AMD ATPX hardware.

**Uitschakelen en permanent masken:**
```bash
sudo systemctl disable nvidia-powerd.service
sudo systemctl stop nvidia-powerd.service
sudo systemctl mask nvidia-powerd.service
```

Masken maakt een symlink naar `/dev/null`, waardoor geen enkel proces (ook geen NVIDIA driver updates via `dnf`) de service opnieuw kan activeren.

**Als je het later opnieuw wilt proberen** (bijv. na een kernel- of driver-update die het ATPX-conflict mogelijk verhelpt):
```bash
sudo systemctl unmask nvidia-powerd.service
sudo systemctl enable --now nvidia-powerd.service
```

**Referentie:**
- [NVIDIA Power Management Documentatie](https://download.nvidia.com/XFree86/Linux-x86_64/590.48.01/README/powermanagement.html)

{{% /steps %}}

## Verificatie Na Installatie

{{% steps %}}

### Verifieer NVIDIA driver

Na reboot, check driver status:

```bash
nvidia-smi
```

Je ziet de NVIDIA driver- en CUDA-versies in de output.

### Controleer geladen kernelmodules

```bash
lsmod | grep nvidia
```

De NVIDIA modules zijn geladen en de driver is functioneel.

{{% /steps %}}




## ICC Kleurprofielen

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

Deze kleurprofielen zijn verkregen door het reverse engineeren van het ASUS Windows driver package. Door de structuur van de ASUS CDN en de inhoud van de driver ZIP-bestanden te analyseren, zijn alle factory-gekalibreerde profielen voor deze laptop gevonden. De ICC metadata is vervolgens aangepast zodat de profielen direct met leesbare namen verschijnen in GNOME Color Management.

**Installeer de kleurprofielen:**

De ICC kleurprofielen staan in de [`/icc-profiles/`](https://github.com/Stensel8/Zephyrus-Linux/tree/main/static/icc-profiles) map van deze repository. Clone de repository of download de profielen handmatig en kopieer ze naar één van deze locaties:

| Locatie | Bereik |
|---|---|
| `/usr/share/color/icc/colord/` | Systeem-breed (alle gebruikers, vereist root) |
| `~/.local/share/icc/` | Alleen huidige gebruiker |

```bash
# Systeem-brede installatie:
sudo cp GA605WV_1002_104D158E_CMDEF.icm /usr/share/color/icc/colord/

# Of per-gebruiker installatie:
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

De bestandsnaam bevat je GPU (`1002` = AMD, `10DE` = NVIDIA) en paneel-ID. Match deze aan jouw exemplaar via de paneeltabel hierboven. Alle profielen staan in de [`/icc-profiles/`](https://github.com/Stensel8/Zephyrus-Linux/tree/main/static/icc-profiles) map.

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

Het profiel staat in de [`/icc-profiles/LS27B800TGUXEN - S80TB/`](https://github.com/Stensel8/Zephyrus-Linux/tree/main/static/icc-profiles/LS27B800TGUXEN%20-%20S80TB) map van deze repository.

**Installeer het kleurprofiel:**

Linux slaat ICC profielen op in één van twee locaties, afhankelijk van het bereik:

| Locatie | Bereik |
|---|---|
| `/usr/share/color/icc/colord/` | Systeem-breed (alle gebruikers, vereist root) |
| `~/.local/share/icc/` | Alleen huidige gebruiker |

```bash
# Systeem-brede installatie (aanbevolen):
sudo cp SxxB80xT.icm /usr/share/color/icc/colord/

# Of per-gebruiker installatie:
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


{{< callout type="info" >}}
Bekende problemen en probleemoplossing voor NVIDIA driver-installatie staan op de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}).
{{< /callout >}}


## Technische weetjes

### Package Naming
Het `akmod-nvidia` package is de aanbevolen NVIDIA driver voor Fedora. Het gebruikt het akmods framework om kernelmodules automatisch opnieuw te bouwen na kernelupdates.

### Secure Boot
akmods rebuildt en signeert kernelmodules automatisch na kernelupdates. Op Fedora kan `sbctl` ook worden gebruikt voor Secure Boot sleutelbeheer.


## Aanvullende Bronnen

- [CachyOS Wiki: NVIDIA](https://wiki.cachyos.org/configuration/nvidia/)
- [Arch Wiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA)
- [Ryzen AI 9 HX 370 Linux Support](https://forums.linuxmint.com/viewtopic.php?t=429052)
- [NVIDIA vs Nouveau Performance](https://machaddr.substack.com/p/nouveau-vs-nvidia-the-battle-between)
- [Zephyrus G16 2024 Linux Guide](https://www.ehmiiz.se/blog/linux_asus_g16_2024/)
- [Fedora Discussion: Zephyrus External Monitor Issues](https://discussion.fedoraproject.org/t/asus-zephyrus-g16-with-nvidia-and-external-monitor-crashes-every-few-minutes/147175)
