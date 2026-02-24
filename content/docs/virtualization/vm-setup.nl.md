---
title: "Windows 11 VM Setup"
weight: 14
---

Sommige dingen draaien gewoon niet op Linux — Microsoft 365 is het meest voor de hand liggende voorbeeld. Daarvoor heb ik een Windows 11 VM opgezet met KVM/QEMU via virt-manager. Met VirtIO-drivers en SPICE GL-acceleratie via de AMD iGPU is de performance goed genoeg voor dagelijks kantoorwerk.

> **GPU passthrough gewenst?** Als je near-native GPU performance wilt in je VM, zie de [Looking Glass Poging]({{< relref "/docs/virtualization/looking-glass-attempt" >}}). Spoiler: het werkt niet op deze laptop door hardwarebeperkingen, maar de documentatie kan nuttig zijn voor andere hardware.


## Windows 11 Enterprise ISO

**Optie 1: Evaluatie (90-daagse trial)**

Download evaluatie ISO (~6,6 GB) van Microsoft:
```
microsoft.com/en-us/evalcenter/download-windows-11-enterprise
```

90 dagen gratis, geen bloatware, geen verplichte Microsoft-account.

**Optie 2: Media Creation Tool + Activatiescript**

Gebruik de officiële Windows 11 Media Creation Tool met een activatiemethode:

1. Download [Windows 11 Media Creation Tool](https://www.microsoft.com/software-download/windows11)
2. Maak installatiemedium aan op een USB-stick of ISO-bestand
3. Gebruik [MAS (Microsoft Activation Scripts)](https://massgrave.dev/) voor activatie:
   - Open PowerShell als Administrator in Windows
   - Voer uit: `irm https://get.activated.win | iex`
   - Selecteer de juiste activatiemethode voor je setup
   - Geen 90-daagse beperking, volledige Windows 11-ervaring

**Optie 3: AtlasOS (Geoptimaliseerd voor prestatie)**

[AtlasOS](https://atlasos.net/) creëert een uitgeklede Windows 11 ISO met bloatware verwijderd en onnodige services uitgeschakeld — wat zorgt voor aanzienlijk betere prestaties in een VM.

**Een AtlasOS ISO aanmaken:**

- **Vanaf een Windows machine:** Download de [AtlasOS Playbook](https://atlasos.net/) en voer deze uit op een Windows-installatie om een geoptimaliseerde ISO aan te maken
- **Vanuit de VM (OOBE):** Je kunt de AtlasOS Playbook rechtstreeks uitvoeren tijdens de initiële setup fase van Windows 11

**Belangrijk:** ISOs gemaakt met AtlasOS zijn **alleen voor persoonlijk gebruik**. Distribueer of deel deze ISOs niet, want ze bevatten Microsoft-software. Iedere gebruiker moet zijn eigen geoptimaliseerde kopie aanmaken met de officiële tools en AtlasOS Playbook.


## Installatie

**1. Packages installeren:**
```bash
sudo pacman -S virt-manager qemu-full swtpm edk2-ovmf dnsmasq
```

**Let op:** Het `virtio-win` pakket is beschikbaar vanuit de AUR (`yay -S virtio-win`) of je kunt de ISO direct downloaden in een latere stap.

**2. Gebruiker toevoegen aan libvirt groep:**
```bash
sudo usermod --append --groups libvirt $(whoami)
```
Log uit en weer in (of herstart) voordat je virt-manager opent.

**3. Libvirtd starten en enablen:**
```bash
sudo systemctl enable --now libvirtd
```

**4. Standaard netwerk configureren:**
```bash
sudo virsh net-start default
sudo virsh net-autostart default
```

Let op: Als je "network is already active" ziet, draait het netwerk al.

**5. VirtIO drivers ISO downloaden:**
```bash
# Download de officiële stable VirtIO drivers ISO (~753 MB)
sudo curl -L -o /var/lib/libvirt/images/virtio-win.iso \
  https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso

# Controleer de download (moet ~753 MB zijn)
ls -lh /var/lib/libvirt/images/virtio-win.iso
```
Laat de download volledig afronden; het is een groot bestand.

**6. Controleer je setup:**
```bash
# Check of je in de libvirt groep zit (na opnieuw inloggen)
groups

# Je zou "libvirt" in de output moeten zien
# Zo niet, log dan uit en weer in

# Test of libvirt werkt
sudo virsh list --all
```

**7. Windows ISO klaarzetten:**

Download of kopieer je Windows 11 Enterprise ISO naar `/var/lib/libvirt/images/`:
```bash
# Als je de ISO al hebt gedownload:
sudo cp ~/Downloads/Enterprise-25H2.iso /var/lib/libvirt/images/

# Of download direct naar de juiste locatie:
sudo curl -L -o /var/lib/libvirt/images/Enterprise-25H2.iso [ISO_URL]
```

Virt-manager kan nu beide ISO's direct selecteren uit deze directory.

**8. (Optioneel) Apart storage pool aanmaken voor VM disks:**

Standaard slaat virt-manager alles op in `/var/lib/libvirt/images/`. Als je VM disks op een aparte schijf of partitie wilt:

1. Maak het mountpoint aan en mount je schijf (bijv. `/mnt/vmstore`)
2. In virt-manager: Edit → Connection Details → Storage
3. Klik op **+** om een nieuw pool toe te voegen
4. Naam: `vmstore`, Type: dir, Target Path: `/mnt/vmstore`

Zo houd je grote VM disk images van je root-bestandssysteem af.

**9. VM aanmaken in virt-manager:**
- File → New Virtual Machine → Local install media
- Selecteer Windows 11 Enterprise ISO
- Memory: **8192 MB** (8 GB), CPUs: **8**, Storage: 200 GB (qcow2)
- **Vink "Customize configuration before install" aan**

**10. Hardware configureren:**

| Setting | Value |
|---------|-------|
| Chipset | Q35 |
| Firmware | UEFI x86_64: `/usr/share/edk2/ovmf/OVMF_CODE_4M.secboot.qcow2` |
| CPU | Copy host CPU configuration (host-passthrough) |
| TPM | Add Hardware → TPM: Type Emulated, Model CRB, Version 2.0 |
| Disk bus | VirtIO |
| Network | Device model: virtio |
| Display | SPICE |
| Video | Virtio (3D acceleration enabled) |

**11. VirtIO ISO toevoegen:**
- Add Hardware → Storage → CDROM
- Selecteer `/var/lib/libvirt/images/virtio-win.iso`
- Bus: SATA

Klik **Begin Installation**.


## Windows Installatie

**1. VirtIO storage driver laden:**

Op "Where do you want to install Windows?":
- Load driver → Browse → `viostor\w11\amd64\` → Next

**2. Installatie voltooien**

**3. Lokaal account:**

Als "I don't have internet" niet beschikbaar is:
- Shift+F10 → `start ms-cxh:localonly` → Enter

**4. VirtIO guest tools installeren (tijdens OOBE):**

Installeer de VirtIO guest drivers voor betere prestaties voordat je de OOBE afrondt:
- Druk op **Shift+F10** om een opdrachtprompt te openen
- De VirtIO ISO is gemount als CD-ROM station (bijv. D: of E:)
- Voer de installer uit: `D:\virtio-win-guest-tools.exe`
- Sluit na installatie de opdrachtprompt en ga verder met de OOBE

Dit installeert alle VirtIO drivers (netwerk, display, balloon, etc.) zodat Windows vanaf het begin met optimale prestaties draait.

**5. SPICE Guest Tools:**

Download en installeer voor klembord/bestandsdeling:
```
spice-guest-tools-latest.exe (van spice-space.org)
```

Windows draait nu met goede performance.


## Post-install VM optimalisatie

Nadat Windows is geïnstalleerd en de guest tools aanwezig zijn, kun je de VM-configuratie fine-tunen voor betere prestaties. Hieronder staat de geoptimaliseerde XML-configuratie met een uitleg van de belangrijkste instellingen.

### Belangrijkste configuratiekeuzes uitgelegd

| Instelling | Wat het doet |
|------------|-------------|
| **Disk: `cache="writeback"` `io="threads"`** | Write-back caching met threaded I/O — significant snellere diskprestaties dan de standaard. Veilig voor niet-kritieke VM's |
| **Disk: `discard="unmap"`** | Geeft TRIM/discard commando's door aan de host — voorkomt dat het qcow2-bestand onnodig groeit |
| **Hyper-V enlightenments** | Windows-specifieke paravirtualisatie-features (`vapic`, `synic`, `stimer`, `tlbflush`, `ipi`, `avic`, etc.) die de guest-prestaties aanzienlijk verbeteren |
| **CPU: `host-passthrough`** | Toont het echte CPU-model aan de guest — beste prestaties, vereist voor sommige applicaties |
| **CPU topologie: 8 cores, 1 thread** | Presenteert 8 fysieke cores aan Windows. Komt overeen met de werkelijke toewijzing zonder SMT-overhead |
| **SPICE met GL-acceleratie** | Gebruikt `gl enable="yes"` met `rendernode` naar de AMD iGPU — hardware-versnelde display-output |
| **VirtIO inputs** | VirtIO toetsenbord en tablet in plaats van PS/2 — lagere input-latentie |
| **QEMU Guest Agent** | Het `org.qemu.guest_agent.0` kanaal maakt communicatie mogelijk tussen host en guest (graceful shutdown, filesystem freeze voor snapshots) |
| **USB redirection** | SPICE USB-omleidingsapparaten maken het mogelijk om USB-apparaten on-the-fly van host naar guest door te geven |
| **Watchdog (iTCO)** | Reset de VM automatisch als de guest vastloopt |
| **Memory balloon** | Maakt dynamisch geheugenbeheer mogelijk tussen host en guest |

### Volledige VM XML referentie

{{% details title="Klik om de volledige geoptimaliseerde VM XML te zien" closed="true" %}}

```xml
<domain type="kvm">
  <name>win11</name>
  <uuid>2a2aa4b0-5f6e-4d0e-a422-de3d63b8966f</uuid>
  <title>win11</title>
  <metadata>
    <libosinfo:libosinfo xmlns:libosinfo="http://libosinfo.org/xmlns/libvirt/domain/1.0">
      <libosinfo:os id="http://microsoft.com/win/11"/>
    </libosinfo:libosinfo>
  </metadata>
  <memory unit="KiB">8388608</memory>
  <currentMemory unit="KiB">8388608</currentMemory>
  <vcpu placement="static">8</vcpu>
  <os firmware="efi">
    <type arch="x86_64" machine="pc-q35-10.1">hvm</type>
    <firmware>
      <feature enabled="yes" name="enrolled-keys"/>
      <feature enabled="yes" name="secure-boot"/>
    </firmware>
    <loader readonly="yes" secure="yes" type="pflash" format="qcow2">/usr/share/edk2/ovmf/OVMF_CODE_4M.secboot.qcow2</loader>
    <nvram template="/usr/share/edk2/ovmf/OVMF_VARS_4M.secboot.qcow2" templateFormat="qcow2" format="qcow2">/var/lib/libvirt/qemu/nvram/win11_VARS.qcow2</nvram>
    <boot dev="hd"/>
  </os>
  <features>
    <acpi/>
    <apic/>
    <hyperv mode="custom">
      <relaxed state="on"/>
      <vapic state="on"/>
      <spinlocks state="on" retries="8191"/>
      <vpindex state="on"/>
      <runtime state="on"/>
      <synic state="on"/>
      <stimer state="on"/>
      <frequencies state="on"/>
      <tlbflush state="on"/>
      <ipi state="on"/>
      <avic state="on"/>
    </hyperv>
    <vmport state="off"/>
    <smm state="on"/>
  </features>
  <cpu mode="host-passthrough" check="none" migratable="on">
    <topology sockets="1" dies="1" clusters="1" cores="8" threads="1"/>
  </cpu>
  <clock offset="localtime">
    <timer name="rtc" tickpolicy="catchup"/>
    <timer name="pit" tickpolicy="delay"/>
    <timer name="hpet" present="no"/>
    <timer name="hypervclock" present="yes"/>
  </clock>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>destroy</on_crash>
  <pm>
    <suspend-to-mem enabled="no"/>
    <suspend-to-disk enabled="no"/>
  </pm>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type="file" device="disk">
      <driver name="qemu" type="qcow2" cache="writeback" io="threads" discard="unmap"/>
      <source file="/mnt/vmstore/win11.qcow2"/>
      <target dev="vda" bus="virtio"/>
    </disk>
    <controller type="usb" index="0" model="qemu-xhci" ports="15"/>
    <controller type="pci" index="0" model="pcie-root"/>
    <controller type="virtio-serial" index="0"/>
    <interface type="network">
      <source network="default"/>
      <model type="virtio"/>
    </interface>
    <serial type="pty">
      <target type="isa-serial" port="0">
        <model name="isa-serial"/>
      </target>
    </serial>
    <console type="pty">
      <target type="serial" port="0"/>
    </console>
    <channel type="spicevmc">
      <target type="virtio" name="com.redhat.spice.0"/>
    </channel>
    <channel type="unix">
      <target type="virtio" name="org.qemu.guest_agent.0"/>
    </channel>
    <input type="keyboard" bus="virtio"/>
    <input type="tablet" bus="virtio"/>
    <input type="mouse" bus="ps2"/>
    <input type="keyboard" bus="ps2"/>
    <tpm model="tpm-crb">
      <backend type="emulator" version="2.0"/>
    </tpm>
    <graphics type="spice">
      <listen type="none"/>
      <image compression="off"/>
      <streaming mode="filter"/>
      <gl enable="yes" rendernode="/dev/dri/by-path/pci-0000:66:00.0-render"/>
    </graphics>
    <sound model="ich9"/>
    <audio id="1" type="spice"/>
    <video>
      <model type="virtio" heads="1" primary="yes">
        <acceleration accel3d="yes"/>
      </model>
    </video>
    <redirdev bus="usb" type="spicevmc"/>
    <redirdev bus="usb" type="spicevmc"/>
    <watchdog model="itco" action="reset"/>
    <memballoon model="virtio"/>
  </devices>
</domain>
```

> Dit is een opgeschoonde versie zonder automatisch gegenereerde PCI-adressen en controller-definities — libvirt voegt die zelf toe. Je kunt je eigen XML exporteren met `virsh dumpxml win11`.

{{% /details %}}

### Guest tools installatie (in Windows)

Voor de beste VM-prestaties moeten twee sets guest tools worden geïnstalleerd **in de Windows guest**:

**VirtIO Guest Tools** (van de VirtIO ISO):
- Installeert geparavirtualiseerde drivers voor disk, netwerk, display, memory balloon, serial en input
- Installeert ook de QEMU Guest Agent voor host-guest communicatie
- Zonder deze drivers zijn disk- en netwerkprestaties aanzienlijk slechter

**SPICE Guest Tools** (van [spice-space.org](https://www.spice-space.org/download.html)):
- Maakt klembord-deling mogelijk tussen host en guest
- Maakt drag-and-drop bestandsoverdracht mogelijk
- Maakt dynamische schermresolutie mogelijk (guest-resolutie volgt het SPICE-venster)
- Installeert de SPICE WebDAV-agent voor mapdeling

Beide zijn essentieel voor een soepele VM-ervaring.


## Snapshots

```bash
# Snapshot maken (VM moet uit)
virsh shutdown win11
qemu-img snapshot -c snapshot-naam /mnt/vmstore/win11.qcow2

# Lijst
qemu-img snapshot -l /mnt/vmstore/win11.qcow2

# Terugdraaien
qemu-img snapshot -a snapshot-naam /mnt/vmstore/win11.qcow2
```


## Troubleshooting

**"Could not detect a default hypervisor" error in virt-manager:**

```bash
# 1. Start libvirtd
sudo systemctl start libvirtd

# 2. Controleer groepslidmaatschap
groups  # Moet "libvirt" bevatten

# Als "libvirt" ontbreekt:
sudo usermod --append --groups libvirt $(whoami)
# Dan uitloggen en opnieuw inloggen
```

**Handmatig connectie toevoegen in virt-manager:**
1. Open virt-manager
2. File → Add Connection
3. Hypervisor: **QEMU/KVM**
4. Connect to local hypervisor
5. Laat alle andere velden leeg
6. Klik **Connect**

**VirtIO ISO download is incompleet:**

De ISO moet exact ~753 MB zijn. Als deze kleiner is:
```bash
# Verwijder incomplete download
sudo rm /var/lib/libvirt/images/virtio-win.iso

# Download opnieuw (annuleer niet met Ctrl+C!)
sudo curl -L -o /var/lib/libvirt/images/virtio-win.iso \
  https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso

# Controleer grootte
ls -lh /var/lib/libvirt/images/virtio-win.iso
```

**Permission denied bij VM start:**
```bash
sudo restorecon -Rv /var/lib/libvirt/images/
sudo restorecon -Rv /mnt/vmstore/
```

**Zwart scherm:**
- Controleer dat Video model op Virtio staat (niet QXL)
- Installeer VirtIO guest tools van de VirtIO ISO
- Installeer SPICE Guest Tools

**Klembord werkt niet:**
- SPICE Guest Tools geïnstalleerd?

