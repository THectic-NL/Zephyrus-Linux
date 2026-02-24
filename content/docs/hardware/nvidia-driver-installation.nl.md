---
title: "NVIDIA Driver Installatie"
weight: 11
---

De G16 heeft een NVIDIA RTX 4060 naast de AMD iGPU. De open-source Nouveau driver werkt niet goed op moderne NVIDIA-hardware, dus proprietary drivers zijn nodig.

**Driver die ik gebruik:**
- Versie: 590.48.01
- CUDA-versie: 13.1
- Bron: CachyOS/Arch repos
- Installatiemethode: nvidia-dkms (DKMS-gebaseerd automatisch kernel module rebuilding)


## CachyOS (Arch)

CachyOS levert NVIDIA drivers standaard mee als onderdeel van de installer. Als je tijdens de installatie voor de NVIDIA-optie hebt gekozen, is de driver al aanwezig en volledig geconfigureerd — handmatige installatie is niet nodig.

Ga naar [Verificatie Na Installatie](#verificatie-na-installatie) om te bevestigen dat alles correct werkt.


## Fedora

De volgende stappen behandelen het volledige handmatige installatieproces. Ik liep tijdens de installatie tegen meerdere crashes en lockups aan die wat tijd kostten om op te sporen — die staan gedocumenteerd in het onderdeel [Bekende Problemen](#bekende-problemen).

## Vereisten

### RPM Fusion inschakelen

RPM Fusion levert de NVIDIA drivers voor Fedora. Schakel beide repositories in voordat je installeert:

```bash
sudo dnf install \
  https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
  https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
```

### Systeem Verificatie

{{% details title="Check kernel versie" closed="true" %}}

Vereist: Kernel 6.19+ voor Ryzen AI 9 HX 370 ondersteuning.

```bash
uname -r
```

{{% /details %}}

{{% details title="Check Secure Boot status" closed="true" %}}

```bash
mokutil --sb-state
```

{{% /details %}}

### Waarom Proprietary Driver

De open-source Nouveau driver heeft slechte prestaties op moderne NVIDIA GPU's. De proprietary driver is vereist voor:
- Gaming en graphics-intensieve applicaties
- CUDA workloads
- Goede Wayland ondersteuning (beschikbaar sinds driver 555+)


## Installatiestappen

{{% steps %}}

### Systeem updaten

```bash
sudo dnf upgrade
```

Wacht tot update voltooid is.

### Driver versie verifiëren

Check beschikbare NVIDIA driver versie:

```bash
dnf info akmod-nvidia
```

### NVIDIA driver installeren

Installeer driver met CUDA ondersteuning:

```bash
sudo dnf install akmod-nvidia xorg-x11-drv-nvidia-cuda xorg-x11-drv-nvidia-libs.i686
```

Dit installeert de driver, CUDA libraries en build dependencies (ongeveer 1 GB).
- `akmod-nvidia` - NVIDIA driver via akmods voor automatisch kernel module bouwen en signeren
- `xorg-x11-drv-nvidia-cuda` - CUDA ondersteuning en driver utilities (inclusief Wayland ondersteuning)
- `xorg-x11-drv-nvidia-libs.i686` - 32-bit NVIDIA libraries (nodig voor Steam/Proton)

### Kernel modules bouwen

akmods bouwt en signeert kernel modules automatisch bij installatie. Om handmatig te triggeren:

```bash
sudo akmods --force
sudo dracut --force
```

Dit proces kan 5-10 minuten duren.

### Kernel modules verifiëren

Check dat kernel modules gebouwd zijn:

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

Activeer NVIDIA power services voor beter suspend/resume gedrag:

```bash
sudo systemctl enable nvidia-hibernate.service nvidia-suspend.service nvidia-resume.service
```

**Wat deze services doen:**
- `nvidia-hibernate.service` - Slaat GPU state correct op voor hibernation
- `nvidia-suspend.service` - Beheert GPU state tijdens system suspend
- `nvidia-resume.service` - Herstelt GPU state na resume

Deze services voorkomen GPU state problemen na suspend/resume cycli.

**Belangrijk: `nvidia-powerd` niet activeren — permanent masken**

De `nvidia-powerd.service` beheert NVIDIA Dynamic Boost, waarmee extra wattage (~5-15W) van de CPU naar de GPU geschoven wordt tijdens zware GPU-belasting. Hoewel nuttig op Intel-gebaseerde laptops, conflicteert het met AMD ATPX power management op de Zephyrus G16 en veroorzaakt soft lockups en "GPU has fallen off the bus" fouten.

Op deze laptop wordt GPU-vermogensbeheer geregeld via ATPX (AMD-gestuurd via ACPI). De NVIDIA suspend/hibernate/resume services en `supergfxctl` beheren power states correct zonder `nvidia-powerd`.

**Wat je verliest door het uit te zetten:** Minimaal — een paar FPS minder bij zware GPU workloads. De ~5-15W Dynamic Boost is de instabiliteit niet waard op AMD ATPX hardware.

**Uitschakelen en permanent masken:**
```bash
sudo systemctl disable nvidia-powerd.service
sudo systemctl stop nvidia-powerd.service
sudo systemctl mask nvidia-powerd.service
```

Masken maakt een symlink naar `/dev/null`, waardoor geen enkel proces — ook geen NVIDIA driver updates via `dnf` — de service opnieuw kan activeren.

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

### Check geladen kernel modules

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
| `E5090C19` | Onbekend | — (aanwezig in ASUS driver package, nog niet publiek geïdentificeerd) | Onbekend |

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

De bestandsnaam bevat je GPU (`1002` = AMD, `10DE` = NVIDIA) en paneel-ID — match deze aan jouw exemplaar via de paneeltabel hierboven. Alle profielen staan in de [`/icc-profiles/`](https://github.com/Stensel8/Zephyrus-Linux/tree/main/static/icc-profiles) map.

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


## Bekende Problemen

{{% details title="Systeem crasht met externe monitoren (AMD GPU PSR bug)" closed="true" %}}

**Probleem:**
Systeem bevriest of crasht bij gebruik van externe monitoren via Thunderbolt/USB-C, vooral bij het (ont)koppelen van displays. Logs tonen AMD GPU errors:
```
amdgpu 0000:66:00.0: amdgpu: MES failed to respond to msg=RESET
amdgpu 0000:66:00.0: amdgpu: Ring gfx_0.0.0 reset failed
amdgpu 0000:66:00.0: amdgpu: GPU reset begin!
```

**Oorzaak:**
Deze laptop heeft dual GPUs (AMD Radeon 890M integrated + NVIDIA RTX 4060 discrete). De PSR (Panel Self Refresh) feature van de AMD GPU heeft een bug die crashes veroorzaakt met externe Thunderbolt monitoren.

**Oplossing:**
Disable AMD PSR door een kernel parameter toe te voegen. Bewerk `/etc/default/grub` en voeg `amdgpu.dcdebugmask=0x600` toe aan `GRUB_CMDLINE_LINUX_DEFAULT`, daarna regenereer:

```bash
sudo nano /etc/default/grub
sudo grub2-mkconfig -o /boot/efi/EFI/fedora/grub.cfg
```

Reboot:
```bash
sudo reboot
```

**Wat dit doet:**
- `amdgpu.dcdebugmask=0x600` schakelt PSR (Panel Self Refresh) uit op de AMD GPU
- PSR is een power-saving feature waarbij het display zichzelf refresht zonder GPU betrokkenheid
- De PSR implementatie heeft bugs met Thunderbolt/USB-C externe monitoren

**Trade-offs:**
- Pro: Stabiel systeem met externe monitoren
- Con: Iets hoger stroomverbruik (PSR uitgeschakeld)

**Verificatie:**
Monitor voor AMD GPU errors tijdens gebruik van externe displays:
```bash
sudo journalctl -f -k | grep -i amdgpu
```

Als er geen `amdgpu: [drm] *ERROR*` berichten verschijnen, werkt de fix.

**Referentie:**
- [Fedora Discussion: Zephyrus G16 External Monitor Crashes](https://discussion.fedoraproject.org/t/asus-zephyrus-g16-with-nvidia-and-external-monitor-crashes-every-few-minutes/147175)

{{% /details %}}

{{% details title="VS Code crasht systeem (AMD GPU page fault - Kernel 6.18.x bug)" closed="true" %}}

**Wat speelt er:**
Systeem bevriest volledig tijdens VS Code gebruik. Kernel 6.18.x/6.19.x hebben kritieke amdgpu driver bugs. VS Code hardware acceleratie triggert AMD Radeon 890M page fault → volledige freeze.

**Fix:**
Voeg toe aan `~/.config/Code/User/settings.json`:
```json
{
    "disable-hardware-acceleration": true
}
```

**Vervolg:**
Herstart VS Code. Systeem blijft nu stabiel, VS Code iets langzamer maar prima bruikbaar.

**Bronnen:**
- [VS Code Issue #238088](https://github.com/microsoft/vscode/issues/238088)
- [Framework: Critical amdgpu bugs kernel 6.18.x](https://community.frame.work/t/attn-critical-bugs-in-amdgpu-driver-included-with-kernel-6-18-x-6-19-x/79221)

{{% /details %}}

{{% details title="Brave Browser crasht systeem (AMD GPU page fault - Kernel 6.18.x bug)" closed="true" %}}

**Wat speelt er:**
Systeem bevriest of crasht tijdens Brave Browser gebruik, zelfs bij minimale workload (enkele tabs). Dit is hetzelfde onderliggende probleem als de VS Code crash: Chromium-gebaseerde applicaties met hardware acceleratie triggeren AMD Radeon 890M page faults op kernel 6.18.x/6.19.x.

Typische crash sequence in logs:
```
amdgpu: [gfxhub] page fault (src_id:0 ring:24 vmid:2)
amdgpu: Faulty UTCL2 client ID: SQC (data)
amdgpu: ring gfx_0.0.0 timeout, signaled seq=302899, emitted seq=302901
amdgpu: GPU reset begin!
```

Na GPU reset crasht gnome-shell (Signal 6 ABRT) omdat het een context reset detecteert.

**Fix:**
Open Brave Browser en ga naar `brave://settings/system`. Zet **"Use hardware acceleration when available"** uit.

Alternatief via terminal:
```bash
sed -i 's/"hardware_acceleration_mode_previous":true/"hardware_acceleration_mode_previous":false/' ~/.config/BraveSoftware/Brave-Browser/Local\ State
```

Of start Brave met de `--disable-gpu` flag:
```bash
brave-browser-stable --disable-gpu
```

**Vervolg:**
Herstart Brave. Verifieer via `brave://gpu` dat GPU acceleration uitgeschakeld is. Systeem blijft nu stabiel, Brave is iets langzamer bij zware pagina's maar prima bruikbaar.

**Achtergrond:**
Brave, VS Code, en andere Chromium-gebaseerde applicaties (Chrome, Edge, Electron apps) gebruiken GPU shader compilatie via Mesa. Op kernel 6.18.x heeft de amdgpu driver een bug in de Shader Queue Controller (SQC) memory access, waardoor page faults ontstaan die een volledige GPU reset triggeren. De fix is hardware acceleratie uitschakelen per applicatie totdat een kernel/Mesa update het probleem verhelpt.

**Bronnen:**
- [Framework: Critical amdgpu bugs kernel 6.18.x](https://community.frame.work/t/attn-critical-bugs-in-amdgpu-driver-included-with-kernel-6-18-x-6-19-x/79221)

{{% /details %}}

{{% details title="NVIDIA soft lockup bij minimale GPU load (hybrid GPU power management)" closed="true" %}}

**Wat speelt er:**
Systeem bevriest met een NVIDIA soft lockup, zelfs zonder actief GPU gebruik. Kernel logs tonen:
```
watchdog: BUG: soft lockup - CPU#23 stuck for 62s!
NVRM: Xid (PCI:0000:65:00): 79, pid=<...>, GPU has fallen off the bus
```

Dit kan optreden door een combinatie van factoren op hybrid GPU laptops:
- `nvidia-powerd` conflicteert met AMD ATPX power management
- NVIDIA dGPU power state transitions falen
- Corrupte VRAM na suspend/resume cycli

**Extra symptoom: Reboot hangt (zwart scherm, backlights blijven aan)**

Het systeem lijkt af te sluiten maar voltooit de hardware reset niet — het scherm wordt zwart maar toetsenbord- en schermverlichting blijven aan. Dit gebeurt wanneer `nvidia-powerd` interfereert met ACPI power state transitions tijdens shutdown/reboot.

**Oorzaak: `supergfxd` start `nvidia-powerd` achter je rug om**

Zelfs wanneer `nvidia-powerd` is uitgeschakeld via `systemctl disable`, roept `supergfxd` (de GPU switching daemon van asusctl) direct `systemctl start nvidia-powerd.service` aan tijdens GPU mode switches. Dit omzeilt de disabled status en activeert het conflict met ATPX opnieuw.

**Hoe dit is gediagnosticeerd:**

De logs van de vastgelopen boot tonen dat `supergfxd` nvidia-powerd opstartte:
```bash
journalctl -b -1 --no-pager | grep -iE "nvidia.*powerd|supergfxd"
```

Bewijsmateriaal:
```
supergfxd: [DEBUG supergfxctl] Did CommandArgs { inner: ["start", "nvidia-powerd.service"] }
nvidia-powerd: ERROR! Client (presumably SBIOS) has requested to disable Dynamic Boost DC controller
```

De SBIOS-fout bevestigt dat de firmware Dynamic Boost weigerde, maar `nvidia-powerd` draaide al en interfereerde met power state management. De shutdown-sequentie controleren:

```bash
journalctl -b -1 --reverse | head -20
```

Toont dat de hardware watchdog niet kon stoppen, wat bevestigt dat de ACPI reboot nooit voltooid is:
```
watchdog: watchdog0: watchdog did not stop!
```

**Fix:**

1. Disable en **mask** `nvidia-powerd` (masken is essentieel — `disable` alleen is niet genoeg omdat `supergfxd` het omzeilt):
```bash
sudo systemctl disable nvidia-powerd.service
sudo systemctl stop nvidia-powerd.service
sudo systemctl mask nvidia-powerd.service
```

2. Voeg kernel parameters toe voor stabielere NVIDIA power management (bewerk `/etc/default/grub`, voeg toe aan `GRUB_CMDLINE_LINUX_DEFAULT`, daarna `sudo grub-mkconfig -o /boot/grub/grub.cfg`):
```
nvidia-drm.fbdev=1 nvidia.NVreg_PreserveVideoMemoryAllocations=1
```

3. Reboot:
```bash
sudo reboot
```

**Vervolg:**
Systeem is stabieler na deze wijzigingen. De NVIDIA dGPU wordt nog steeds correct beheerd via ATPX (AMD-gestuurde power switching) zonder dat `nvidia-powerd` interfereert. De mask maakt een symlink naar `/dev/null`, waardoor geen enkel proces — inclusief `supergfxd` en NVIDIA driver updates — de service opnieuw kan activeren.

**Achtergrond:**
Op laptops met AMD iGPU + NVIDIA dGPU regelt het ATPX framework (via ACPI) welke GPU actief is. `nvidia-powerd` probeert zelfstandig power decisions te maken, wat conflicteert met ATPX. De `NVreg_PreserveVideoMemoryAllocations=1` parameter voorkomt dat VRAM verloren gaat tijdens power transitions, en `nvidia-drm.fbdev=1` zorgt voor een schonere framebuffer handoff.

{{% /details %}}


## Probleemoplossing

{{% details title="nvidia-smi command not found of faalt" closed="true" %}}

Check of NVIDIA modules geladen zijn:
```bash
lsmod | grep nvidia
```

Check system logs voor errors:
```bash
sudo journalctl -b | grep nvidia
```

Rebuild kernel modules:
```bash
sudo akmods --force
sudo dracut --force
sudo reboot
```

{{% /details %}}

{{% details title="MOK enrollment problemen of \"Key was rejected by service\" error" closed="true" %}}

Als je de error krijgt `modprobe: ERROR: could not insert 'nvidia': Key was rejected by service`, zijn de kernel modules gebouwd voordat MOK enrollment voltooid was.

Oplossing:
```bash
# Rebuild modules na MOK enrollment
sudo akmods --force
sudo dracut --force

# Reboot
sudo reboot
```

Om MOK te resetten indien nodig:
```bash
sudo mokutil --reset
```

Reboot en probeer enrollment opnieuw.

{{% /details %}}


{{% details title="Kernel module build failures" closed="true" %}}

Zorg dat kernel headers overeenkomen met draaiende kernel:
```bash
sudo dnf install kernel-devel
```

Forceer rebuild:
```bash
sudo akmods --force
sudo dracut --force
```

{{% /details %}}


## Technische weetjes

### Package Naming
Het `akmod-nvidia` package is de aanbevolen NVIDIA driver voor Fedora. Het gebruikt het akmods framework om kernel modules automatisch te rebuilden na kernel updates.

### Secure Boot
akmods rebuildt en signeert kernel modules automatisch na kernel updates. Op Fedora kan `sbctl` ook worden gebruikt voor Secure Boot sleutelbeheer.


## Aanvullende Bronnen

- [CachyOS Wiki: NVIDIA](https://wiki.cachyos.org/configuration/nvidia/)
- [Arch Wiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA)
- [Ryzen AI 9 HX 370 Linux Support](https://forums.linuxmint.com/viewtopic.php?t=429052)
- [NVIDIA vs Nouveau Performance](https://machaddr.substack.com/p/nouveau-vs-nvidia-the-battle-between)
- [Zephyrus G16 2024 Linux Guide](https://www.ehmiiz.se/blog/linux_asus_g16_2024/)
- [Fedora Discussion: Zephyrus External Monitor Issues](https://discussion.fedoraproject.org/t/asus-zephyrus-g16-with-nvidia-and-external-monitor-crashes-every-few-minutes/147175)
