---
title: "Bekende Problemen"
weight: 7
prev: docs/virtualization/vmware-workstation
---

Centrale referentie voor hardware- en softwareproblemen op de ASUS ROG Zephyrus G16 GA605WV. Actieve problemen staan bovenaan. Opgeloste problemen staan onderaan als naslagwerk.

## Actieve Problemen

> Dit zijn problemen waar ik persoonlijk nog steeds tegenaan loop. In sommige gevallen is het mogelijk een echte bug; in andere gevallen doe ik misschien zelf iets fout of heb ik iets over het hoofd gezien. Ik deel wat ik heb waargenomen, niet wat ik definitief heb vastgesteld.

{{% details title="WinBoat: container start niet op" closed="true" %}}

**Wat er gebeurt:**
WinBoat raakt regelmatig verstrikt in een eindeloze opstartronde. De Podman-container blijft proberen op te starten maar slaagt daar nooit in, ook niet na eindeloos wachten. De UI toont "WinBoat Guest API - Offline" en "Container - Exited". Dit is niet beperkt tot de eerste installatie; het treedt ook op bij latere starts.

**Workaround:**
WinBoat resetten en de initiële configuratie opnieuw doorlopen zorgt dat het weer werkt. Dit is geen duurzame oplossing.

**Status:**
Open. WinBoat is in beta en het project erkent de instabiliteit. Zie de [WinBoat-pagina]({{< relref "/docs/virtualization/winboat" >}}) voor meer context.

{{% /details %}}

{{% details title="WinBoat: applicatievensters verschuiven en krimpen willekeurig" closed="true" %}}

**Wat er gebeurt:**
Als WinBoat wel opstart en je opent een Windows-app zoals Word, dan kruipt het venster langzaam naar rechts en wordt het steeds kleiner totdat het praktisch weg is. Herstarten helpt niet structureel.

**Workaround:**
Geen gevonden.

**Status:**
Open. Beta-beperking.

{{% /details %}}

{{% details title="YubiKey FIDO2 LUKS ontgrendeling: USB timing race" closed="true" %}}

**Wat er gebeurt:**
Het inschrijven van de YubiKey als FIDO2 LUKS-ontgrendelsleutel lukt, maar bij het opstarten geeft `systemd-cryptsetup` `FIDO_ERR_RX` terug. De key is fysiek aanwezig maar lijkt nog niet geïnitialiseerd te zijn door de USB HID-stack op het moment van de query. Dit lijkt met name op te treden bij warme reboots.

Geprobeerd met `token-timeout=30` in crypttab en `rd.udev.settle-timeout=10` als kernelparameter, beide op systemd 259. Geen van beide hielp.

**Status:**
Nog steeds onopgelost. Onduidelijk of dit een echt hardware/firmware timingprobleem is, iets specifiek voor dit apparaat, of een configuratiefout van mijn kant. Mogelijk later nog een keer opgepakt. Voorlopig gebruik ik de YubiKey voor `sudo` en de GNOME-schermvergrendeling.

Zie de sectie **Dingen die ik graag werkend had gezien** onderaan deze pagina voor de volledige context.

{{% /details %}}

## Opgeloste Problemen

De volgende problemen zijn opgelost. Sommige zijn verholpen door kernel- of driver-updates, andere via een configuratiewijziging, en eerlijk gezegd heb ik een aantal dingen misschien gewoon zelf fout gedaan. Ik heb ze hier toch bewaard, want misschien bespaar ik iemand anders dezelfde zoektocht.

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
Systeem bevriest volledig tijdens het gebruik van VS Code. Kernel 6.18.x/6.19.x hebben kritieke amdgpu-driverbugs. VS Code hardware-acceleratie veroorzaakt een AMD Radeon 890M page fault → volledige bevriezing.

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
Systeem bevriest of crasht tijdens het gebruik van Brave Browser, zelfs bij minimale workload (enkele tabs). Chromium-gebaseerde applicaties met hardware-acceleratie veroorzaken AMD Radeon 890M page faults op kernel 6.18.x/6.19.x.

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
Brave, VS Code en andere Chromium-gebaseerde applicaties (Chrome, Edge, Electron-apps) gebruiken GPU shader-compilatie via Mesa. Op kernel 6.18.x heeft de amdgpu-driver een bug in de Shader Queue Controller (SQC) geheugenaccess, waardoor page faults ontstaan die een volledige GPU-reset veroorzaken. De fix is hardware-acceleratie per applicatie uitschakelen totdat een kernel- of Mesa-update het probleem verhelpt.

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

1. Schakel `nvidia-powerd` uit en **maskeer** het (maskeren is essentieel, `disable` alleen is niet genoeg omdat `supergfxd` het omzeilt):
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

Forceer een herbouw:
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
GNOME Shell crasht met SIGABRT tijdens Picture-in-Picture video in Brave. De AMD VCN-harddecoder veroorzaakt een context-reset die gnome-shell neerlaat. Dit staat gedocumenteerd in [gnome-mutter issue #4625](https://gitlab.gnome.org/GNOME/mutter/-/issues/4625).

**Let op:** Deze crash treedt ook op met de `--disable-features=WaylandWpColorManagerV1`-flag actief. Beide workarounds zijn nodig.

**Fix:**
Ga naar `brave://flags` en schakel uit:

- **Hardware-accelerated video decode** → `Disabled`

![brave://flags - Hardware-accelerated video decode uitgeschakeld](/images/brave-flags.avif)

Daarna toont `brave://gpu`:
- `Video Decode: Software only. Hardware acceleration disabled`

![brave://gpu - Video Decode uitgeschakeld, software only](/images/brave-gpu-config.avif)

Deze workaround was van toepassing op kernel 6.18.x/6.19.x. Hardware video decode op de Radeon 890M is stabiel vanaf kernel 7.0 en deze vlag hoeft niet meer uitgeschakeld te worden.

{{% /details %}}

{{% details title="Touchpad scrollt te snel op Wayland (GNOME)" closed="true" %}}

**Wat er speelde:**
Scrollen met het touchpad voelde aanzienlijk sneller aan dan normaal in Brave en andere niet-GTK apps. Een korte veegbeweging stuurde de pagina al ver naar beneden.

**Oorzaak:**
Een GNOME/Wayland-probleem, niet specifiek aan Brave. GNOME normaliseert scroll-events niet zoals het zou moeten, waardoor apps die niet via GTK's inputstack gaan rauwe hoge-precisie events van libinput ontvangen. Firefox en native GTK-apps werken wel goed omdat zij via GTK gaan. Veel andere apps hadden hetzelfde probleem.

**Oplossing:**
[wayland-scroll-factor]({{< relref "/docs/applications#touchpad-scroll-speed-still-no-native-gnome-setting" >}}) lost dit op op GNOME-niveau door libinput-aanroepen binnen gnome-shell te onderscheppen en een scrollvermenigvuldiger toe te passen. Alles komt genormaliseerd uit. Het onderliggende GNOME-probleem staat nog steeds open upstream, maar WSF maakt het in de praktijk geen probleem meer.

**Bronnen:**
- [brave-browser #36569: native touchpad scrolling op Linux Wayland](https://github.com/brave/brave-browser/issues/36569)
- [Brave Community: hoge-resolutie touchpad scrolling op Linux Wayland](https://community.brave.app/t/scrolling-speed-is-way-too-fast/649357)

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
De `asus-armoury`-driver is toegevoegd aan de Linux mainline-kernel in versie 6.19. Deze driver zit in elke CachyOS-kernel vanaf 6.19; de huidige kernel op het moment van schrijven is 7.0.12-1-cachyos.

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


## Dingen die ik graag werkend had gezien

> Dit zijn dingen die ik écht werkend wilde krijgen, maar niet kon, door hardwarebeperkingen, hardnekkige bugs of omdat het project er nog niet klaar voor was.

{{% details title="Looking Glass B7: GPU passthrough op de Zephyrus G16" closed="true" %}}

Ik wilde GPU passthrough proberen met Looking Glass: Windows in een VM draaien maar met de echte NVIDIA GPU toegewezen, zodat je near-native performance hebt. Ik heb er een flink aantal uren aan besteed. Het werkt niet op deze laptop, en de reden is een hardwarebeperking waar Looking Glass niets aan kan doen. Ik documenteer de volledige poging hier zodat anderen die tijd kunnen besparen.

> **TL;DR:** Looking Glass werkt **niet** op de ASUS ROG Zephyrus G16 GA605WV. De RTX 4060 heeft geen fysieke display-outputs; alle poorten (HDMI, USB-C) lopen via de AMD iGPU. Windows kan daardoor geen "valid output device" vinden voor frame capture, waardoor de host-applicatie direct faalt.

### Wat is Looking Glass?

[Looking Glass](https://looking-glass.io) is een open-source project waarmee je een GPU-passthrough Windows VM kunt gebruiken **zonder fysiek scherm** aan de dGPU. De Windows VM krijgt de echte GPU toegewezen en het beeld wordt via gedeeld geheugen (IVSHMEM) naar de Linux host gestreamd. Het resultaat is near-native GPU performance in een VM, zichtbaar in een venster op je Linux desktop.

**Vereisten voor werking:**
- dGPU met directe display-output (DisplayPort, HDMI), of een virtuele display dongle
- IOMMU-isolatie van de dGPU van de rest van het systeem
- KVMFR kernel module op de host
- Looking Glass host application in de Windows VM


### Fase 1: IOMMU en VFIO instellen

#### IOMMU-groepen controleren

```bash
for d in /sys/kernel/iommu_groups/*/devices/*; do
    n=${d#*/iommu_groups/*}; n=${n%%/*}
    printf 'IOMMU Group %s ' "$n"
    lspci -nns "${d##*/}"
done | grep -E "NVIDIA|AMD|10de|1002" | head -20
```

De RTX 4060 zat in een schone eigen groep:
```
IOMMU Group 20: 65:00.0 VGA [10de:28e0] NVIDIA GeForce RTX 4060 Max-Q
IOMMU Group 20: 65:00.1 Audio [10de:22be] NVIDIA HD Audio
IOMMU Group 21: 66:00.0 Display [1002:150e] AMD Radeon 890M
```

#### VFIO kernel parameters instellen

```bash
sudo grubby --update-kernel=ALL \
  --args="vfio-pci.ids=10de:28e0,10de:22be \
          rd.driver.pre=vfio-pci \
          iommu=1 \
          rd.driver.blacklist=nouveau,nova_core \
          modprobe.blacklist=nouveau,nova_core \
          amdgpu.dcdebugmask=0x600"
```

#### VFIO configuratiebestanden aanmaken

**`/etc/modprobe.d/vfio.conf`:**
```
options vfio-pci ids=10de:28e0,10de:22be
softdep nvidia pre: vfio-pci
softdep nvidia_drm pre: vfio-pci
softdep nvidia_modeset pre: vfio-pci
softdep nouveau pre: vfio-pci
```

**`/etc/dracut.conf.d/vfio.conf`:**
```
add_drivers+=" vfio vfio_iommu_type1 vfio_pci "
```

#### nvidia-fallback.service uitschakelen

Bij VFIO claimt `vfio-pci` de GPU vóór de NVIDIA driver, waardoor `nvidia-fallback.service` foutmeldingen geeft:

```bash
sudo systemctl disable nvidia-fallback.service
sudo systemctl mask nvidia-fallback.service
```

#### Initramfs herbouwen en herstarten

```bash
sudo dracut --force
sudo reboot
```

#### Verificatie na de herstart

```bash
lspci -nnk -d 10de:28e0
# Verwacht: Kernel driver in use: vfio-pci

lspci -nnk -d 1002:150e
# Verwacht: Kernel driver in use: amdgpu

nvidia-smi
# Verwacht: NVIDIA-SMI has failed because... (normaal bij VFIO)
```


### Fase 2: KVMFR kernel module installeren

De KVMFR module levert de `/dev/kvmfr0` interface voor de IVSHMEM shared memory buffer.

#### Module bouwen en installeren via DKMS

```bash
cd ~/source/looking-glass-B7/module
sudo dkms install .
```

#### MOK enrollment voor Secure Boot

```bash
sudo mokutil --import /var/lib/dkms/mok.pub
# Stel een tijdelijk wachtwoord in
sudo reboot
# Bij reboot: Enroll MOK → Continue → Yes → wachtwoord → reboot
```

#### Module automatisch laden en configureren

```bash
echo "kvmfr" | sudo tee /etc/modules-load.d/kvmfr.conf
echo "options kvmfr static_size_mb=128" | sudo tee /etc/modprobe.d/kvmfr.conf
```

#### Udev-rechten instellen

```bash
echo 'SUBSYSTEM=="kvmfr", OWNER="sten", GROUP="kvm", MODE="0660"' | \
  sudo tee /etc/udev/rules.d/99-kvmfr.rules

sudo udevadm control --reload-rules
sudo udevadm trigger
```

#### Module handmatig laden en testen

```bash
sudo modprobe -r kvmfr
sudo modprobe kvmfr

ls -la /dev/kvmfr0
# Verwacht: crw-rw---- 1 sten kvm 508, 0 ...

# Als permissions nog niet kloppen na udev:
sudo chown sten:kvm /dev/kvmfr0
sudo chmod 660 /dev/kvmfr0
```


### Fase 3: Looking Glass client bouwen

#### Source downloaden

```bash
mkdir -p ~/source
cd ~/source
git clone https://github.com/gnif/LookingGlass.git looking-glass-B7
cd looking-glass-B7
git submodule update --init --recursive
```

#### Dependencies installeren

De dependencies moesten stuk voor stuk worden uitgezocht. De complete lijst op CachyOS:

```bash
sudo pacman -S cmake gcc libglvnd fontconfig \
  spice-protocol wayland wayland-protocols pipewire \
  libxkbcommon libsamplerate systemd nettle \
  desktop-file-utils libxi libxfixes libxss \
  libxinerama libxcursor libxpresent libxrandr \
  libdecor libpulse binutils
```

Ontbrekende packages per build-fout:

| Fout | Ontbrekende package |
|------|---------------------|
| `wayland-client.h: No such file` | `wayland-devel` |
| `xkbcommon.h: No such file` | `libxkbcommon-devel` |
| `samplerate.h: No such file` | `libsamplerate-devel` |
| `Xi.h: No such file` | `libXi-devel` |
| `Xfixes.h: No such file` | `libXfixes-devel` |
| `bfd.h: No such file` | `binutils-devel` |
| `Xrandr.h: No such file` | `libXrandr-devel` |

#### Bouwen en installeren

```bash
cd ~/source/looking-glass-B7/client
mkdir build && cd build
cmake ../
make -j$(nproc)
sudo make install
# Installeert naar /usr/local/bin/looking-glass-client
```

#### Verificatie

```bash
which looking-glass-client
looking-glass-client --version
# Output: Looking Glass (B7), CPU: AMD Ryzen AI 9 HX 370 w/ Radeon 890M
```


### Fase 4: VM XML aanpassen

Aanpassingen via `sudo virsh edit win11`:

**SPICE: GL uitschakelen (alleen input/clipboard):**
```xml
<graphics type="spice">
  <listen type="none"/>
  <image compression="off"/>
  <streaming mode="filter"/>
  <gl enable="no"/>
</graphics>
```

**Video: Looking Glass vervangt het display:**
```xml
<video>
  <model type="none"/>
</video>
```

> **Let op:** Met `type="none"` toont virt-manager een leeg scherm. Dat is verwacht. Tijdelijk terug naar `type="vga"` voor als je Windows-toegang nodig hebt tijdens setup.

**RTX 4060 PCI passthrough:**
```xml
<hostdev mode="subsystem" type="pci" managed="yes">
  <source>
    <address domain="0x0000" bus="0x65" slot="0x00" function="0x0"/>
  </source>
</hostdev>
<hostdev mode="subsystem" type="pci" managed="yes">
  <source>
    <address domain="0x0000" bus="0x65" slot="0x00" function="0x1"/>
  </source>
</hostdev>
```

**IVSHMEM buffer:**
```xml
<shmem name="looking-glass">
  <model type="ivshmem-plain"/>
  <size unit="M">128</size>
</shmem>
```


### Fase 5: Looking Glass host in Windows installeren

#### Tijdelijk VGA toegang herstellen

```bash
sudo virsh edit win11
# Verander: <model type="none"/> naar <model type="vga"/>
sudo virsh destroy win11
sudo virsh start win11
```

#### Host installer in Windows

- Download `looking-glass-host-setup.exe` van **https://looking-glass.io/downloads** (B7)
- Rechtsklik → **Run as administrator**
- Next → Agree → Next → Install → Close

Dit installeert automatisch de IVSHMEM driver en de Looking Glass Host service.

#### NVIDIA driver installeren in Windows

De RTX 4060 werd weergegeven als "Microsoft Basic Display Adapter". Download de driver via **https://www.nvidia.com/drivers** en installeer deze.

#### VGA terug naar none

```bash
sudo virsh edit win11
# Verander: <model type="vga"/> terug naar <model type="none"/>
sudo virsh destroy win11
sudo virsh start win11
```


### Fase 6: Client verbinden

#### Shared memory-permissies controleren

```bash
ls -la /dev/kvmfr0

# QEMU fallback:
ls -la /dev/shm/looking-glass
sudo chown sten:kvm /dev/shm/looking-glass  # als rechten niet kloppen
```

#### Client starten

```bash
looking-glass-client -s
```

Resultaat: **"Host Application Not Running"**; shared memory werkt, maar de host stuurt geen frames.


### Waarom het mislukt

**Host application log** (`C:\ProgramData\Looking Glass (host)\looking-glass-host.txt`):

```
[I] d12.c | Not using unsupported adapter: Microsoft Basic Render Driver
[E] d12.c | Failed to locate a valid output device
[I] dxgi.c | Not using unsupported adapter: Microsoft Basic Render Driver
[E] dxgi.c | Failed to locate a valid output device
[E] app.c | Failed to find a supported capture interface
```

**Diagnose via PowerShell in Windows:**

```powershell
Get-PnpDevice | Where-Object {
    $_.FriendlyName -like "*NVIDIA*" -or $_.FriendlyName -like "*display*"
} | Format-Table FriendlyName, Status, Class

# Resultaat:
# NVIDIA GeForce RTX 4060 Laptop GPU  OK  Display
# Microsoft Basic Display Adapter     OK  Display
```

De RTX 4060 was herkend en de driver was geïnstalleerd, maar de host kon hem niet gebruiken omdat er geen display-output is.

**De fundamentele hardwarebeperking**, bevestigd via `ls /sys/class/drm/`:

```
card0-HDMI-A-1      ← HDMI zit op AMD iGPU (card0)
card0-eDP-2         ← intern scherm via AMD (Dynamic MUX mode)
card1-DP-1 t/m DP-8 ← NVIDIA virtuele outputs (geen fysieke connectors)
card1-eDP-1         ← intern scherm via NVIDIA (dGPU MUX mode)
```

Alle fysieke poorten op deze laptop zitten op de AMD iGPU. De RTX 4060 heeft geen enkele fysieke display-aansluiting. DirectX 12 en DXGI vereisen een actieve display-output voor frame capture, wat hardwarematig onmogelijk is op deze laptop.


### Bijkomende bevindingen

**nvidia-fallback.service** geeft foutmeldingen wanneer VFIO actief is. Oplossing: maskeren (zie Fase 1). Bij terugdraaien herstellen:

```bash
sudo systemctl unmask nvidia-fallback.service
sudo systemctl enable nvidia-fallback.service
```

**QEMU shared memory fallback:** Als `/dev/kvmfr0` niet beschikbaar is, gebruikt QEMU `/dev/shm/looking-glass` (128MB, owned by `qemu:qemu`). De client valt hier automatisch op terug.


### Alles terugdraaien

```bash
# Kernel parameters herstellen
sudo grubby --update-kernel=ALL \
  --remove-args="vfio-pci.ids=10de:28e0,10de:22be rd.driver.pre=vfio-pci \
                 rd.driver.blacklist=nouveau,nova_core modprobe.blacklist=nouveau,nova_core" \
  --args="nvidia-drm.modeset=1 nvidia-drm.fbdev=1 \
          nvidia.NVreg_PreserveVideoMemoryAllocations=1 iommu=pt"

# VFIO config verwijderen
sudo rm /etc/modprobe.d/vfio.conf
sudo rm /etc/dracut.conf.d/vfio.conf
sudo rm /etc/modules-load.d/kvmfr.conf
sudo rm /etc/udev/rules.d/99-kvmfr.rules
sudo rm /etc/modprobe.d/kvmfr.conf

# nvidia-fallback herstellen
sudo systemctl unmask nvidia-fallback.service
sudo systemctl enable nvidia-fallback.service

# KVMFR DKMS module verwijderen
sudo dkms remove kvmfr/0.0.12 --all

# DKMS MOK key verwijderen (optioneel)
sudo mokutil --delete /var/lib/dkms/mok.pub
# Stel wachtwoord in voor de MOK prompt bij reboot

# Initramfs herbouwen
sudo akmods --force
sudo dracut --force

sudo reboot
# Bij reboot: blauw MOK scherm → Delete MOK → wachtwoord → reboot
```

VM XML herstellen via `sudo virsh edit win11`: verwijder de twee `<hostdev>` blokken en het `<shmem>` blok, zet video terug naar `type="virtio"` met `accel3d="yes"`, en zet SPICE terug naar `gl enable="yes" rendernode="/dev/dri/by-path/pci-0000:66:00.0-render"`.


### Referenties

- [Looking Glass officiële documentatie B7](https://looking-glass.io/docs/B7/)
- [Looking Glass GitHub](https://github.com/gnif/LookingGlass)
- [VFIO GPU Passthrough Guide - Arch Wiki](https://wiki.archlinux.org/title/PCI_passthrough_via_OVMF)
- [GA605WV display routing - Arch Linux Forums](https://bbs.archlinux.org/viewtopic.php?id=299932)

{{% /details %}}


{{% details title="YubiKey 5C NFC: FIDO2 LUKS-ontgrendeling" closed="true" %}}

Ik wilde het LUKS-versleutelde station bij het opstarten ontgrendelen door de YubiKey in te pluggen en aan te raken. Hier staat de poging en waarom het niet werkte. De YubiKey werkt prima voor alles buiten het vroege opstarten; zie de pagina [YubiKey]({{< relref "/docs/security/yubikey" >}}) voor de pam-u2f setup.


### Wat geprobeerd is: FIDO2 LUKS-ontgrendeling

**Packages geïnstalleerd:**
```bash
sudo pacman -S libfido2
```

**FIDO2 enrollment:**
```bash
sudo systemd-cryptenroll \
  --fido2-device=auto \
  --fido2-with-client-pin=no \
  --fido2-with-user-presence=yes \
  --fido2-with-user-verification=no \
  /dev/nvme1n1p2
```

**crypttab:**
```
luks-aaf424ea-... UUID=aaf424ea-... none fido2-device=auto,discard,token-timeout=30
```

**`/etc/sdboot-manage.conf`:**
```
LINUX_OPTIONS="... rd.luks.options=aaf424ea-...=fido2-device=auto,token-timeout=30 rd.udev.settle-timeout=10"
```

**Wat werkte:**
- Enrollment gelukt (keyslot 1, touch-only)
- FIDO2 libraries bevestigd aanwezig in initramfs
- systemd 259 bevestigd: `+FIDO2` aanwezig, `token-timeout=` beschikbaar als crypttab-optie
- Fallback-regressie uit systemd 257/258 is opgelost in 259

**Wat niet werkte:** Ondanks systemd 259 bleef de USB timing race condition bestaan:

```
systemd-cryptsetup: Failed to ask token for assertion: FIDO_ERR_RX
```

`FIDO_ERR_RX` betekent dat de YubiKey fysiek aanwezig is, maar nog niet volledig geïnitialiseerd door de USB HID-stack op het moment dat `systemd-cryptsetup` hem aanspreekt. Dit lijkt met name op te treden bij warme reboots. Geprobeerde workarounds: `token-timeout=30` in crypttab en `rd.udev.settle-timeout=10` als kernelparameter. Geen van beide was betrouwbaar genoeg.

**Wat teruggedraaid is:**
```bash
# FIDO2 verwijderen uit LUKS
sudo systemd-cryptenroll --wipe-slot=fido2 /dev/nvme1n1p2

# crypttab herstellen naar alleen wachtwoord (alleen discard, geen fido2-device=auto)

# /etc/sdboot-manage.conf herstellen naar originele LINUX_OPTIONS
sudo sdboot-manage gen
```

{{% /details %}}
