---
title: "Bekende Problemen"
weight: 7
prev: docs/virtualization/podman
---

Centrale referentie voor hardware- en softwareproblemen op de ASUS ROG Zephyrus G16 GA605WV. Actieve problemen staan bovenaan. Opgeloste problemen staan onderaan als naslagwerk.

## Actieve Problemen

### WinBoat: container start niet op

**Wat er gebeurt:**
WinBoat raakt regelmatig verstrikt in een eindeloze opstartronde. De Podman-container blijft proberen op te starten maar slaagt daar nooit in — ook niet na eindeloos wachten. De UI toont "WinBoat Guest API - Offline" en "Container - Exited". Dit is niet beperkt tot de eerste installatie — het treedt ook op bij latere starts.

**Workaround:**
WinBoat resetten en de initiële configuratie opnieuw doorlopen zorgt dat het weer werkt. Dit is geen duurzame oplossing.

**Status:**
Open. WinBoat is in beta en het project erkent de instabiliteit. Zie de [WinBoat-pagina]({{< relref "/docs/virtualization/winboat" >}}) voor meer context.

---

### WinBoat: applicatievensters verschuiven en krimpen willekeurig

**Wat er gebeurt:**
Wanneer WinBoat wel succesvol start en een Windows-applicatie (zoals Microsoft Word) wordt geopend, gedraagt het venster zich grillig: het schuift naar rechts over het scherm, schaalt willekeurig kleiner, en wordt steeds kleiner totdat het nauwelijks nog zichtbaar is. Dit maakt WinBoat in de praktijk onbruikbaar voor productiviteitsapplicaties.

**Workaround:**
Geen gevonden. De applicatie of WinBoat herstarten lost het niet betrouwbaar op.

**Status:**
Open. Beta-beperking.

---

### Brave Browser: touchpad scrollt te snel op Wayland

**Wat er gebeurt:**
Scrollen met het touchpad in Brave voelt aanzienlijk sneller aan dan in Firefox of native GTK-apps. Een korte veegbeweging stuurt de pagina al ver naar beneden. Dit treft alle Chromium-gebaseerde browsers op Wayland.

**Oorzaak:**
Upstream Chromium-probleem. Chromium ontvangt hoge-precisie scroll-events van libinput op Wayland, maar normaliseert deze niet zoals GTK dat doet. Firefox gebruikt de GTK-inputstack, die dit correct afhandelt. Chromium niet.

**Status:**
Open. Geen fix in Brave tot begin 2026. Het probleem wordt al gemeld sinds minimaal 2022.

**Geprobeerde workaround (afgebroken):**
Het verlagen van de globale `scroll-factor` in [libinput-config]({{< relref "/docs/applications#touchpad-scroll-speed-no-native-gnome-setting-yet" >}}) vermindert de scrollsnelheid in Brave, maar het is een systeembrede instelling die elke applicatie beïnvloedt, inclusief apps waar scrollen al prima werkte. Na ongeveer een week verwijderd. Het Brave-specifieke probleem rechtvaardigt niet dat alles trager scrollt.

**Bronnen:**
- [brave-browser #36569: native touchpad scrolling op Linux Wayland](https://github.com/brave/brave-browser/issues/36569)
- [Brave Community: hoge-resolutie touchpad scrolling op Linux Wayland](https://community.brave.app/t/scrolling-speed-is-way-too-fast/649357)

---

## Opgeloste Problemen

De volgende problemen zijn opgelost. Elk is ofwel verholpen door de Linux kernel-ontwikkelaars (met name de AMD GPU page fault-bugs in 6.18 en de asus-armoury driver die is samengevoegd in 6.19), of opgelost via een configuratiewijziging die ik zelf heb toegepast. Bewaard als naslagwerk.

## GPU & Beeldscherm

{{% details title="Systeem bevriest bij gebruik van externe monitoren (AMD GPU PSR bug)" closed="true" %}}

**Probleem:**
Systeem bevriest of crasht bij gebruik van externe monitoren via Thunderbolt/USB-C, met name bij het (ont)koppelen van displays. Logs tonen AMD GPU-fouten:
```
amdgpu 0000:66:00.0: amdgpu: MES failed to respond to msg=RESET
amdgpu 0000:66:00.0: amdgpu: Ring gfx_0.0.0 reset failed
amdgpu 0000:66:00.0: amdgpu: GPU reset begin!
```

**Oorzaak:**
Deze laptop heeft twee GPU's (AMD Radeon 890M geïntegreerd + NVIDIA RTX 4060 discreet). De PSR-functie (Panel Self Refresh) van de AMD GPU heeft een bug die crashes veroorzaakt met externe Thunderbolt-monitoren.

**Oplossing:**
Schakel AMD PSR uit door een kernelparameter toe te voegen. Bewerk `/etc/default/grub` en voeg `amdgpu.dcdebugmask=0x600` toe aan `GRUB_CMDLINE_LINUX_DEFAULT`, daarna opnieuw genereren:

```bash
sudo nano /etc/default/grub
sudo grub2-mkconfig -o /boot/efi/EFI/fedora/grub.cfg
```

Herstart:
```bash
sudo reboot
```

**Wat dit doet:**
- `amdgpu.dcdebugmask=0x600` schakelt PSR (Panel Self Refresh) uit op de AMD GPU
- PSR is een energiebesparingsfunctie waarbij het scherm zichzelf vernieuwt zonder GPU-betrokkenheid
- De PSR-implementatie heeft bugs met externe Thunderbolt/USB-C-monitoren

**Afwegingen:**
- Pro: Stabiel systeem met externe monitoren
- Con: Iets hoger stroomverbruik (PSR uitgeschakeld)

**Verificatie:**
```bash
sudo journalctl -f -k | grep -i amdgpu
```

Als er geen `amdgpu: [drm] *ERROR*`-berichten verschijnen, werkt de fix.

**Referentie:**
- [Fedora Discussion: Zephyrus G16 External Monitor Crashes](https://discussion.fedoraproject.org/t/asus-zephyrus-g16-with-nvidia-and-external-monitor-crashes-every-few-minutes/147175)

{{% /details %}}

{{% details title="Systeem bevriest tijdens gebruik van VS Code (AMD GPU page fault, Kernel 6.18.x)" closed="true" %}}

**Wat speelt er:**
Systeem bevriest volledig tijdens het gebruik van VS Code. Kernel 6.18.x/6.19.x hebben kritieke amdgpu-driverbugs. VS Code hardware-acceleratie triggert een AMD Radeon 890M page fault → volledige bevriezing.

**Fix:**
Voeg toe aan `~/.config/Code/User/settings.json`:
```json
{
    "disable-hardware-acceleration": true
}
```

Herstart VS Code. Systeem blijft nu stabiel, VS Code iets langzamer maar prima bruikbaar.

**Bronnen:**
- [VS Code Issue #238088](https://github.com/microsoft/vscode/issues/238088)
- [Framework: Critical amdgpu bugs kernel 6.18.x](https://community.frame.work/t/attn-critical-bugs-in-amdgpu-driver-included-with-kernel-6-18-x-6-19-x/79221)

{{% /details %}}

{{% details title="Systeem bevriest tijdens gebruik van Brave Browser (AMD GPU page fault, Kernel 6.18.x)" closed="true" %}}

**Wat speelt er:**
Systeem bevriest of crasht tijdens het gebruik van Brave Browser, zelfs bij minimale workload (enkele tabs). Chromium-gebaseerde applicaties met hardware-acceleratie triggeren AMD Radeon 890M page faults op kernel 6.18.x/6.19.x.

Typische crash-sequentie in de logs:
```
amdgpu: [gfxhub] page fault (src_id:0 ring:24 vmid:2)
amdgpu: Faulty UTCL2 client ID: SQC (data)
amdgpu: ring gfx_0.0.0 timeout, signaled seq=302899, emitted seq=302901
amdgpu: GPU reset begin!
```

Na GPU-reset crasht gnome-shell (Signal 6 ABRT) omdat het een context-reset detecteert.

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

Herstart Brave. Verifieer via `brave://gpu` dat GPU-acceleratie is uitgeschakeld.

**Achtergrond:**
Brave, VS Code en andere Chromium-gebaseerde applicaties (Chrome, Edge, Electron-apps) gebruiken GPU shader-compilatie via Mesa. Op kernel 6.18.x heeft de amdgpu-driver een bug in de Shader Queue Controller (SQC) geheugenaccess, waardoor page faults ontstaan die een volledige GPU-reset triggeren. De fix is hardware-acceleratie per applicatie uitschakelen totdat een kernel- of Mesa-update het probleem verhelpt.

**Bronnen:**
- [Framework: Critical amdgpu bugs kernel 6.18.x](https://community.frame.work/t/attn-critical-bugs-in-amdgpu-driver-included-with-kernel-6-18-x-6-19-x/79221)

{{% /details %}}

{{% details title="NVIDIA soft lockup / 'GPU has fallen off the bus'" closed="true" %}}

**Wat speelt er:**
Systeem bevriest met een NVIDIA soft lockup, zelfs zonder actief GPU-gebruik. Kernellogs tonen:
```
watchdog: BUG: soft lockup - CPU#23 stuck for 62s!
NVRM: Xid (PCI:0000:65:00): 79, pid=<...>, GPU has fallen off the bus
```

Dit kan optreden door een combinatie van factoren op hybrid GPU-laptops:
- `nvidia-powerd` conflicteert met AMD ATPX power management
- NVIDIA dGPU power state-overgangen mislukken
- Corrupte VRAM na suspend/resume-cycli

**Extra symptoom: Reboot hangt (zwart scherm, verlichting blijft aan)**

Het systeem lijkt af te sluiten maar voltooit de hardware-reset niet; het scherm wordt zwart maar toetsenbord- en schermverlichting blijven aan. Dit gebeurt wanneer `nvidia-powerd` interfereert met ACPI power state-overgangen tijdens afsluiten/herstarten.

**Oorzaak: `supergfxd` start `nvidia-powerd` achter je rug om**

Zelfs wanneer `nvidia-powerd` is uitgeschakeld via `systemctl disable`, roept `supergfxd` (de GPU-switchingdaemon van asusctl) direct `systemctl start nvidia-powerd.service` aan tijdens GPU-modusschakelingen. Dit omzeilt de uitgeschakelde status en activeert het conflict met ATPX opnieuw.

**Hoe dit gediagnosticeerd is:**
```bash
journalctl -b -1 --no-pager | grep -iE "nvidia.*powerd|supergfxd"
```

Bewijsmateriaal:
```
supergfxd: [DEBUG supergfxctl] Did CommandArgs { inner: ["start", "nvidia-powerd.service"] }
nvidia-powerd: ERROR! Client (presumably SBIOS) has requested to disable Dynamic Boost DC controller
```

De shutdown-sequentie controleren:
```bash
journalctl -b -1 --reverse | head -20
```

Toont dat de hardware watchdog niet kon stoppen, wat bevestigt dat de ACPI-reboot nooit is voltooid:
```
watchdog: watchdog0: watchdog did not stop!
```

**Fix:**

1. Disable én **mask** `nvidia-powerd` (masken is essentieel, `disable` alleen is niet genoeg omdat `supergfxd` het omzeilt):
```bash
sudo systemctl disable nvidia-powerd.service
sudo systemctl stop nvidia-powerd.service
sudo systemctl mask nvidia-powerd.service
```

2. Voeg kernelparameters toe voor stabielere NVIDIA power management (bewerk `/etc/default/grub`, voeg toe aan `GRUB_CMDLINE_LINUX_DEFAULT`, daarna `sudo grub-mkconfig -o /boot/grub/grub.cfg`):
```
nvidia-drm.fbdev=1 nvidia.NVreg_PreserveVideoMemoryAllocations=1
```

3. Herstart:
```bash
sudo reboot
```

**Achtergrond:**
Op laptops met AMD iGPU + NVIDIA dGPU regelt het ATPX-framework (via ACPI) welke GPU actief is. `nvidia-powerd` probeert zelfstandig power decisions te nemen, wat conflicteert met ATPX. De `NVreg_PreserveVideoMemoryAllocations=1`-parameter voorkomt dat VRAM verloren gaat tijdens power-overgangen, en `nvidia-drm.fbdev=1` zorgt voor een schonere framebuffer-overdracht.

{{% /details %}}


## NVIDIA Driver

> Deze onderdelen gelden voornamelijk voor de Fedora-installatieroute. CachyOS-gebruikers worden hier niet door getroffen; de driver is tijdens de installatie al vooraf geconfigureerd.

{{% details title="nvidia-smi: command not found of mislukt" closed="true" %}}

Controleer of NVIDIA-modules zijn geladen:
```bash
lsmod | grep nvidia
```

Controleer systeemlogboeken op fouten:
```bash
sudo journalctl -b | grep nvidia
```

Bouw kernelmodules opnieuw:
```bash
sudo akmods --force
sudo dracut --force
sudo reboot
```

{{% /details %}}

{{% details title="MOK enrollment: 'Key was rejected by service'" closed="true" %}}

Als je de foutmelding krijgt `modprobe: ERROR: could not insert 'nvidia': Key was rejected by service`, zijn de kernelmodules gebouwd voordat MOK enrollment was voltooid.

Oplossing:
```bash
# Modules opnieuw bouwen na MOK enrollment
sudo akmods --force
sudo dracut --force

# Herstart
sudo reboot
```

Om MOK te resetten indien nodig:
```bash
sudo mokutil --reset
```

Herstart en probeer de enrollment opnieuw.

{{% /details %}}

{{% details title="Kernelmodule build-fouten" closed="true" %}}

Zorg dat de kernelheaders overeenkomen met de draaiende kernel:
```bash
sudo dnf install kernel-devel
```

Forceer een rebuild:
```bash
sudo akmods --force
sudo dracut --force
```

{{% /details %}}


## Applicaties

{{% details title="Brave Browser crasht op GNOME Wayland (WaylandWpColorManagerV1)" closed="true" %}}

**Wat speelt er:**
Brave 1.82–1.86 crashte of veroorzaakte crashes van GNOME Shell op Wayland. De crash wordt veroorzaakt door een Wayland color management-extensie (`WaylandWpColorManagerV1`) die conflicteert met de AMD amdgpu-driver, wat GPU ring-timeouts veroorzaakt die de volledige desktopsessie neerhalen.

**Fix:**
Kopieer de systeemdesktop-entry naar je gebruikersmap zodat hij niet wordt overschreven bij updates:
```bash
sudo cp /usr/share/applications/brave-browser.desktop ~/.local/share/applications/
```

Patch alle drie de `Exec=`-regels met de flag:
```bash
sed -i \
  's|Exec=/usr/bin/brave-browser-stable %U|Exec=/usr/bin/brave-browser-stable --disable-features=WaylandWpColorManagerV1 %U|' \
  ~/.local/share/applications/brave-browser.desktop

sed -i \
  's|Exec=/usr/bin/brave-browser-stable$|Exec=/usr/bin/brave-browser-stable --disable-features=WaylandWpColorManagerV1|' \
  ~/.local/share/applications/brave-browser.desktop

sed -i \
  's|Exec=/usr/bin/brave-browser-stable --incognito$|Exec=/usr/bin/brave-browser-stable --incognito --disable-features=WaylandWpColorManagerV1|' \
  ~/.local/share/applications/brave-browser.desktop
```

Verifieer dit: je zou exact drie `Exec=`-regels moeten zien met de flag toegevoegd:
```bash
grep "^Exec" ~/.local/share/applications/brave-browser.desktop
```

{{% /details %}}

{{% details title="GNOME Shell crasht tijdens videoweergave in Brave (AMD VCN hardware decode)" closed="true" %}}

**Wat speelt er:**
GNOME Shell crasht met SIGABRT tijdens Picture-in-Picture video in Brave. De AMD VCN hardware decoder triggert een context-reset die gnome-shell neerlaat. Dit staat gedocumenteerd in [gnome-mutter issue #4625](https://gitlab.gnome.org/GNOME/mutter/-/issues/4625).

**Let op:** Deze crash treedt ook op met de `--disable-features=WaylandWpColorManagerV1`-flag actief. Beide workarounds zijn nodig.

**Fix:**
Ga naar `brave://flags` en schakel uit:

- **Hardware-accelerated video decode** → `Disabled`

![brave://flags - Hardware-accelerated video decode uitgeschakeld](/images/brave-flags.avif)

Daarna toont `brave://gpu`:
- `Video Decode: Software only. Hardware acceleration disabled`

![brave://gpu - Video Decode uitgeschakeld, software only](/images/brave-gpu-config.avif)

Brave is iets langzamer op video-intensieve pagina's maar stabiel. Hardware video decode is nog niet stabiel op de AMD Radeon 890M met GNOME Wayland.

{{% /details %}}

{{% details title="Steam wil niet starten" closed="true" %}}

**Wat er speelde:**
Steam startte op sommige systemen niet op, zonder zichtbare foutmelding.

**Workaround (niet meer nodig):**
```bash
__GL_CONSTANT_FRAME_RATE_HINT=3 steam
```

**Oplossing:**
Dit probleem heeft zichzelf opgelost. Steam start nu gewoon op; de `__GL_CONSTANT_FRAME_RATE_HINT` workaround is niet meer nodig. Installeer Steam vanuit de [CachyOS-repository](https://packages.cachyos.org/package/cachyos/x86_64/steam) via `sudo pacman -S steam`.

{{% /details %}}


## asusctl & ROG Control Center

{{% details title="ROG Control Center: 'The asus-armoury driver is not loaded'" closed="true" %}}

**Probleem:**
ROG Control Center toont een melding dat de `asus-armoury` kerneldriver niet is geladen. Geavanceerde functies (PPT-vermogensgrenzen, APU-geheugenallocatie, MUX-switchbesturing) zijn niet beschikbaar.

**Oorzaak:**
De `asus-armoury`-driver is samengevoegd in de Linux mainline-kernel in versie 6.19. CachyOS levert kernel 6.19.4-2 inclusief deze driver, dus hij zou beschikbaar moeten zijn.

**Fix:**
Verifieer dat de driver is geladen:
```bash
lsmod | grep asus_armoury
```

Als hij laadt, heropen ROG Control Center; de melding zou verdwenen moeten zijn en geavanceerde functies zijn beschikbaar.

{{% /details %}}


## Secure Boot

{{% details title="sbctl status toont nog steeds 'Setup Mode: Disabled' na het wissen van sleutels" closed="true" %}}

Sommige ASUS UEFI-versies vereisen dat de platformsleutel (PK) expliciet wordt verwijderd voordat Setup Mode wordt geactiveerd.

In de ASUS UEFI:
1. Ga naar **Security** → **Secure Boot** → **Key Management**
2. Selecteer **Platform Key (PK)** → **Delete**
3. Save & Exit en herstart

Na het herstarten moet `sudo sbctl status` Setup Mode: Enabled tonen.

{{% /details %}}

{{% details title="Systeem start niet op na het inschakelen van Secure Boot" closed="true" %}}

Als het systeem niet opstart na het inschakelen van Secure Boot, zijn een of meer EFI-bestanden niet ondertekend.

1. Herstart naar de ASUS UEFI en schakel Secure Boot tijdelijk uit
2. Start op in CachyOS
3. Controleer welke bestanden niet zijn ondertekend:
```bash
sudo sbctl verify
```
4. Onderteken ontbrekende bestanden:
```bash
sudo sbctl sign -s /pad/naar/bestand.efi
```
5. Of voer de batch-ondertekening opnieuw uit:
```bash
sudo sbctl-batch-sign
```
6. Herstart en schakel Secure Boot opnieuw in

{{% /details %}}


## YubiKey & LUKS

{{% details title="Systeem vast in boot loop na FIDO2 enrollment" closed="true" %}}

Als je FIDO2 hebt ingericht en niet kunt opstarten, tik dan snel op de YubiKey direct na het BIOS-scherm. Het touch-venster is erg kort.

Eenmaal in het systeem, direct terugdraaien:
```bash
sudo systemd-cryptenroll --wipe-slot=fido2 /dev/nvme1n1p3
sudo nano /etc/crypttab  # verwijder fido2-device=auto
sudo rm /etc/dracut.conf.d/fido2.conf
sudo dracut --force --regenerate-all
```

{{% /details %}}

{{% details title="LUKS keyslots verifiëren" closed="true" %}}

```bash
sudo cryptsetup luksDump /dev/nvme1n1p3 | grep -E "^\s+[0-9]+:"
```

Moet alleen `0: luks2` tonen na terugdraaien. Als slot 1 nog aanwezig is, is FIDO2 nog steeds ingeschreven.

{{% /details %}}


## GDM Autologin

{{% details title="Autologin werkt niet na een configuratiewijziging" closed="true" %}}

Verifieer dat het configuratiebestand correct is:

```bash
sudo cat /etc/gdm/custom.conf
```

Zorg dat `AutomaticLoginEnable=True` onder `[daemon]` staat en dat de gebruikersnaam exact overeenkomt:

```bash
whoami
```

Controleer ook dat GDM de actieve display manager is:

```bash
systemctl status gdm
```

{{% /details %}}


## Virtuele Machines

{{% details title="'Could not detect a default hypervisor' foutmelding in virt-manager" closed="true" %}}

```bash
# 1. Start libvirtd
sudo systemctl start libvirtd

# 2. Controleer groepslidmaatschap
groups  # Moet "libvirt" bevatten

# Als "libvirt" ontbreekt:
sudo usermod --append --groups libvirt $(whoami)
# Dan uitloggen en opnieuw inloggen
```

Als de foutmelding na opnieuw inloggen nog steeds verschijnt, voeg de verbinding handmatig toe:
1. Open virt-manager
2. File → Add Connection
3. Hypervisor: **QEMU/KVM**
4. Connect to local hypervisor
5. Laat alle andere velden leeg
6. Klik **Connect**

{{% /details %}}

{{% details title="VirtIO ISO-download is incompleet" closed="true" %}}

De ISO moet exact ~753 MB zijn. Als deze kleiner is:
```bash
# Verwijder de incomplete download
sudo rm /var/lib/libvirt/images/virtio-win.iso

# Download opnieuw (annuleer niet met Ctrl+C!)
sudo curl -L -o /var/lib/libvirt/images/virtio-win.iso \
  https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso

# Controleer de grootte
ls -lh /var/lib/libvirt/images/virtio-win.iso
```

{{% /details %}}

{{% details title="Permission denied bij het starten van de VM" closed="true" %}}

```bash
sudo restorecon -Rv /var/lib/libvirt/images/
sudo restorecon -Rv /mnt/vmstore/
```

{{% /details %}}

{{% details title="Zwart scherm in de VM" closed="true" %}}

- Controleer dat het videomodel is ingesteld op **Virtio** (niet QXL) in de hardware-instellingen van virt-manager
- Installeer VirtIO guest tools van de VirtIO ISO (in Windows)
- Installeer SPICE Guest Tools (in Windows)

{{% /details %}}

{{% details title="Klembord werkt niet tussen host en guest" closed="true" %}}

Installeer SPICE Guest Tools in de Windows-VM. Download van [spice-space.org](https://www.spice-space.org/download.html) en voer de installer uit. Klembord-deling, drag-and-drop en dynamische schermresolutie vereisen allemaal SPICE Guest Tools.

{{% /details %}}
