---
title: "Windows 11 VM Setup"
weight: 14
---

Some things simply don't run on Linux — Microsoft 365 being the obvious example. For those cases I set up a Windows 11 VM using KVM/QEMU with virt-manager. With VirtIO drivers and SPICE GL acceleration via the AMD iGPU, performance is good enough for everyday office work.

> **Want GPU passthrough?** If you want near-native GPU performance in your VM, see the [Looking Glass Attempt]({{< relref "/docs/virtualization/looking-glass-attempt" >}}). Spoiler: it doesn't work on this laptop due to hardware limitations, but the documentation may be useful for other hardware.


## Windows 11 Enterprise ISO

**Option 1: Evaluation (90-day trial)**

Download evaluation ISO (~6.6 GB) from Microsoft:
```
microsoft.com/en-us/evalcenter/download-windows-11-enterprise
```

90 days free, no bloatware, no mandatory Microsoft account.

**Option 2: Media Creation Tool + Activation Script**

Use the official Windows 11 Media Creation Tool with an activation method:

1. Download [Windows 11 Media Creation Tool](https://www.microsoft.com/software-download/windows11)
2. Create installation media on a USB drive or ISO file
3. Use [MAS (Microsoft Activation Scripts)](https://massgrave.dev/) for activation:
   - Open PowerShell as Administrator in Windows
   - Run: `irm https://get.activated.win | iex`
   - Select the appropriate activation method for your setup
   - No 90-day limit, full Windows 11 experience

**Option 3: AtlasOS (Optimized for Performance)**

[AtlasOS](https://atlasos.net/) creates a minified Windows 11 ISO with bloatware removed and unnecessary services disabled—resulting in significantly better performance in a VM.

**Creating an AtlasOS ISO:**

- **From a Windows machine:** Download the [AtlasOS Playbook](https://atlasos.net/) and run it on a Windows installation to create an optimized ISO
- **From inside the VM (OOBE):** You can run the AtlasOS Playbook directly during Windows 11's initial setup phase

**Important:** ISOs created with AtlasOS are for **personal use only**. Do not distribute or share these ISOs as they contain Microsoft software. Each user must create their own optimized copy using the official tools and AtlasOS Playbook.


## Installation

**1. Install packages:**
```bash
sudo pacman -S virt-manager qemu-full swtpm edk2-ovmf dnsmasq
```

**Note:** The `virtio-win` package is available from the AUR (`yay -S virtio-win`) or you can download the ISO directly in a later step.

**2. Add user to libvirt group:**
```bash
sudo usermod --append --groups libvirt $(whoami)
```
Log out and log back in (or reboot) before opening virt-manager.

**3. Start and enable libvirtd:**
```bash
sudo systemctl enable --now libvirtd
```

**4. Configure default network:**
```bash
sudo virsh net-start default
sudo virsh net-autostart default
```

Note: If you see "network is already active", it is already running.

**5. Download VirtIO drivers ISO:**
```bash
# Download the official stable VirtIO drivers ISO (~753 MB)
sudo curl -L -o /var/lib/libvirt/images/virtio-win.iso \
  https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso

# Verify the download (should be ~753 MB)
ls -lh /var/lib/libvirt/images/virtio-win.iso
```
Let the download finish; it is large.

**6. Verify your setup:**
```bash
# Check if you're in the libvirt group (after logging back in)
groups

# You should see "libvirt" in the output
# If not, log out and back in again

# Test if libvirt works
sudo virsh list --all
```

**7. Prepare Windows ISO:**

Download or copy your Windows 11 Enterprise ISO to `/var/lib/libvirt/images/`:
```bash
# If you already downloaded the ISO:
sudo cp ~/Downloads/Enterprise-25H2.iso /var/lib/libvirt/images/

# Or download directly to the correct location:
sudo curl -L -o /var/lib/libvirt/images/Enterprise-25H2.iso [ISO_URL]
```

Virt-manager can now directly select both ISOs from this directory.

**8. (Optional) Create a separate storage pool for VM disks:**

By default, virt-manager stores everything in `/var/lib/libvirt/images/`. If you want VM disks on a separate drive or partition:

1. Create the mount point and mount your drive (e.g. `/mnt/vmstore`)
2. In virt-manager: Edit → Connection Details → Storage
3. Click **+** to add a new pool
4. Name: `vmstore`, Type: dir, Target Path: `/mnt/vmstore`

This keeps large VM disk images off your root filesystem.

**9. Create VM in virt-manager:**
- File → New Virtual Machine → Local install media
- Select Windows 11 Enterprise ISO
- Memory: **8192 MB** (8 GB), CPUs: **8**, Storage: 200 GB (qcow2)
- **Check "Customize configuration before install"**

**10. Configure hardware:**

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

**11. Add VirtIO ISO:**
- Add Hardware → Storage → CDROM
- Select `/var/lib/libvirt/images/virtio-win.iso`
- Bus: SATA

Click **Begin Installation**.


## Windows Installation

**1. Load VirtIO storage driver:**

At "Where do you want to install Windows?":
- Load driver → Browse → `viostor\w11\amd64\` → Next

**2. Complete installation**

**3. Local account:**

If "I don't have internet" is not available:
- Shift+F10 → `start ms-cxh:localonly` → Enter

**4. Install VirtIO guest tools (during OOBE):**

Before finishing the OOBE setup, install the VirtIO guest drivers for better performance:
- Press **Shift+F10** to open a command prompt
- The VirtIO ISO is mounted as a CD-ROM drive (e.g. D: or E:)
- Run the installer: `D:\virtio-win-guest-tools.exe`
- After installation finishes, close the command prompt and continue the OOBE

This installs all VirtIO drivers (network, display, balloon, etc.) so Windows runs with optimal performance from the start.

**5. SPICE Guest Tools:**

Download and install for clipboard/file sharing:
```
spice-guest-tools-latest.exe (from spice-space.org)
```

Windows should now run with good performance.


## Post-install VM optimization

After Windows is installed and the guest tools are in place, you can fine-tune the VM configuration for better performance. Below is the optimized XML configuration and an explanation of the key settings.

### Key configuration choices explained

| Setting | What it does |
|---------|-------------|
| **Disk: `cache="writeback"` `io="threads"`** | Write-back caching with threaded I/O — significantly faster disk performance than the default. Safe for non-critical VMs |
| **Disk: `discard="unmap"`** | Passes TRIM/discard commands to the host — keeps the qcow2 file from growing unnecessarily |
| **Hyper-V enlightenments** | Windows-specific paravirtualization features (`vapic`, `synic`, `stimer`, `tlbflush`, `ipi`, `avic`, etc.) that dramatically improve guest performance |
| **CPU: `host-passthrough`** | Exposes the real CPU model to the guest — best performance, required for some applications |
| **CPU topology: 8 cores, 1 thread** | Presents 8 physical cores to Windows. Matches the actual allocation without SMT overhead |
| **SPICE with GL acceleration** | Uses `gl enable="yes"` with `rendernode` pointing to the AMD iGPU — hardware-accelerated display output |
| **VirtIO inputs** | VirtIO keyboard and tablet instead of PS/2 — lower latency input |
| **QEMU Guest Agent** | The `org.qemu.guest_agent.0` channel enables communication between host and guest (graceful shutdown, filesystem freeze for snapshots) |
| **USB redirection** | SPICE USB redirection devices allow passing USB devices from host to guest on-the-fly |
| **Watchdog (iTCO)** | Automatically resets the VM if the guest hangs |
| **Memory balloon** | Allows dynamic memory management between host and guest |

### Full VM XML reference

{{% details title="Click to expand the full optimized VM XML" closed="true" %}}

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

> This is a cleaned-up version without auto-generated PCI addresses and controller definitions — libvirt adds those automatically. You can export your own XML with `virsh dumpxml win11`.

{{% /details %}}

### Guest tools installation (inside Windows)

For the best VM performance, two sets of guest tools must be installed **inside the Windows guest**:

**VirtIO Guest Tools** (from the VirtIO ISO):
- Installs paravirtualized drivers for disk, network, display, memory balloon, serial, and input
- Also installs the QEMU Guest Agent for host-guest communication
- Without these drivers, disk and network performance will be significantly worse

**SPICE Guest Tools** (from [spice-space.org](https://www.spice-space.org/download.html)):
- Enables clipboard sharing between host and guest
- Enables drag-and-drop file transfer
- Enables dynamic display resolution (guest resolution follows the SPICE window size)
- Installs the SPICE WebDAV agent for folder sharing

Both are essential for a smooth VM experience.


## Snapshots

```bash
# Create snapshot (VM must be off)
virsh shutdown win11
qemu-img snapshot -c snapshot-name /mnt/vmstore/win11.qcow2

# List
qemu-img snapshot -l /mnt/vmstore/win11.qcow2

# Revert
qemu-img snapshot -a snapshot-name /mnt/vmstore/win11.qcow2
```


## Troubleshooting

**"Could not detect a default hypervisor" error in virt-manager:**

```bash
# 1. Start libvirtd
sudo systemctl start libvirtd

# 2. Check group membership
groups  # Must contain "libvirt"

# If "libvirt" is missing:
sudo usermod --append --groups libvirt $(whoami)
# Then log out and log back in
```

**Manually add connection in virt-manager:**
1. Open virt-manager
2. File → Add Connection
3. Hypervisor: **QEMU/KVM**
4. Connect to local hypervisor
5. Leave all other fields empty
6. Click **Connect**

**VirtIO ISO download is incomplete:**

The ISO must be exactly ~753 MB. If smaller:
```bash
# Remove incomplete download
sudo rm /var/lib/libvirt/images/virtio-win.iso

# Download again (don't cancel with Ctrl+C!)
sudo curl -L -o /var/lib/libvirt/images/virtio-win.iso \
  https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso

# Verify size
ls -lh /var/lib/libvirt/images/virtio-win.iso
```

**Permission denied when starting VM:**
```bash
sudo restorecon -Rv /var/lib/libvirt/images/
sudo restorecon -Rv /mnt/vmstore/
```

**Black screen:**
- Check that Video model is set to Virtio (not QXL)
- Install VirtIO guest tools from the VirtIO ISO
- Install SPICE Guest Tools

**Clipboard doesn't work:**
- SPICE Guest Tools installed?

