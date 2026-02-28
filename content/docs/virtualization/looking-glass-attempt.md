---
title: "Looking Glass B7: GPU Passthrough Attempt"
weight: 2
next: docs/virtualization/winboat
---

I wanted to try GPU passthrough with Looking Glass: running Windows in a VM but with the real NVIDIA GPU assigned to it, getting near-native performance. Spent a good few hours on it. It doesn't work on this laptop, and the reason is a hardware limitation that Looking Glass can't work around. I'm documenting the full attempt here so others can save themselves the time.

> **Prerequisite:** This assumes you already have a working Windows 11 VM set up with virt-manager. If not, follow the [VM Setup Guide]({{< relref "/docs/virtualization/vm-setup" >}}) first.

> **TL;DR:** Looking Glass does **not** work on the ASUS ROG Zephyrus G16 GA605WV. The RTX 4060 has no physical display outputs; all ports (HDMI, USB-C) are routed through the AMD iGPU. Windows can't find a "valid output device" for frame capture, so the host application fails immediately. This document describes everything that was tried and why it failed.


## What is Looking Glass?

[Looking Glass](https://looking-glass.io) is an open-source project that allows you to use a GPU-passthrough Windows VM **without a physical monitor** attached to the dGPU. The Windows VM gets the real GPU assigned and the rendered image is streamed to the Linux host via shared memory (IVSHMEM). The result is near-native GPU performance in a VM, visible in a window on your Linux desktop.

**Requirements for operation:**
- dGPU with direct display output (DisplayPort, HDMI), or a virtual display dongle
- IOMMU isolation of the dGPU from the rest of the system
- KVMFR kernel module on the host
- Looking Glass host application in the Windows VM


## Phase 1: Setting up IOMMU and VFIO

### Checking IOMMU groups

```bash
for d in /sys/kernel/iommu_groups/*/devices/*; do
    n=${d#*/iommu_groups/*}; n=${n%%/*}
    printf 'IOMMU Group %s ' "$n"
    lspci -nns "${d##*/}"
done | grep -E "NVIDIA|AMD|10de|1002" | head -20
```

The RTX 4060 was in a clean separate group:
```
IOMMU Group 20: 65:00.0 VGA [10de:28e0] NVIDIA GeForce RTX 4060 Max-Q
IOMMU Group 20: 65:00.1 Audio [10de:22be] NVIDIA HD Audio
IOMMU Group 21: 66:00.0 Display [1002:150e] AMD Radeon 890M
```

### Setting VFIO kernel parameters

```bash
sudo grubby --update-kernel=ALL \
  --args="vfio-pci.ids=10de:28e0,10de:22be \
          rd.driver.pre=vfio-pci \
          iommu=1 \
          rd.driver.blacklist=nouveau,nova_core \
          modprobe.blacklist=nouveau,nova_core \
          amdgpu.dcdebugmask=0x600"
```

### Creating VFIO configuration files

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

### Disabling nvidia-fallback.service

With VFIO, `vfio-pci` claims the GPU before the NVIDIA driver, causing `nvidia-fallback.service` to produce errors:

```bash
sudo systemctl disable nvidia-fallback.service
sudo systemctl mask nvidia-fallback.service
```

### Rebuilding initramfs and rebooting

```bash
sudo dracut --force
sudo reboot
```

### Verification after reboot

```bash
lspci -nnk -d 10de:28e0
# Expected: Kernel driver in use: vfio-pci

lspci -nnk -d 1002:150e
# Expected: Kernel driver in use: amdgpu

nvidia-smi
# Expected: NVIDIA-SMI has failed because... (normal with VFIO)
```


## Phase 2: Installing KVMFR kernel module

The KVMFR module provides the `/dev/kvmfr0` interface for the IVSHMEM shared memory buffer.

### Building and installing the module via DKMS

```bash
cd ~/source/looking-glass-B7/module
sudo dkms install .
```

### MOK enrollment for Secure Boot

```bash
sudo mokutil --import /var/lib/dkms/mok.pub
# Set a temporary password
sudo reboot
# At reboot: Enroll MOK → Continue → Yes → password → reboot
```

### Automatically loading and configuring the module

```bash
echo "kvmfr" | sudo tee /etc/modules-load.d/kvmfr.conf

echo "options kvmfr static_size_mb=128" | sudo tee /etc/modprobe.d/kvmfr.conf
```

### Setting udev permissions

```bash
echo 'SUBSYSTEM=="kvmfr", OWNER="sten", GROUP="kvm", MODE="0660"' | \
  sudo tee /etc/udev/rules.d/99-kvmfr.rules

sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Manually loading and testing the module

```bash
sudo modprobe -r kvmfr
sudo modprobe kvmfr

ls -la /dev/kvmfr0
# Expected: crw-rw---- 1 sten kvm 508, 0 ...

# If permissions are still incorrect after udev:
sudo chown sten:kvm /dev/kvmfr0
sudo chmod 660 /dev/kvmfr0
```


## Phase 3: Building the Looking Glass client

### Downloading the source

```bash
mkdir -p ~/source
cd ~/source
git clone https://github.com/gnif/LookingGlass.git looking-glass-B7
cd looking-glass-B7
git submodule update --init --recursive
```

### Installing dependencies

The dependencies had to be discovered one by one. The complete list on CachyOS:

```bash
sudo pacman -S cmake gcc libglvnd fontconfig \
  spice-protocol wayland wayland-protocols pipewire \
  libxkbcommon libsamplerate systemd nettle \
  desktop-file-utils libxi libxfixes libxss \
  libxinerama libxcursor libxpresent libxrandr \
  libdecor libpulse binutils
```

Missing packages per build error:

| Error | Missing package |
|-------|-----------------|
| `wayland-client.h: No such file` | `wayland-devel` |
| `xkbcommon.h: No such file` | `libxkbcommon-devel` |
| `samplerate.h: No such file` | `libsamplerate-devel` |
| `Xi.h: No such file` | `libXi-devel` |
| `Xfixes.h: No such file` | `libXfixes-devel` |
| `bfd.h: No such file` | `binutils-devel` |
| `Xrandr.h: No such file` | `libXrandr-devel` |

### Building and installing

```bash
cd ~/source/looking-glass-B7/client
mkdir build && cd build
cmake ../
make -j$(nproc)
sudo make install
# Installs to /usr/local/bin/looking-glass-client
```

### Verification

```bash
which looking-glass-client
looking-glass-client --version
# Output: Looking Glass (B7), CPU: AMD Ryzen AI 9 HX 370 w/ Radeon 890M
```


## Phase 4: Modifying the VM XML

Changes via `sudo virsh edit win11`:

**SPICE: Disable GL (input/clipboard only):**
```xml
<graphics type="spice">
  <listen type="none"/>
  <image compression="off"/>
  <streaming mode="filter"/>
  <gl enable="no"/>
</graphics>
```

**Video: Looking Glass replaces the display:**
```xml
<video>
  <model type="none"/>
</video>
```

> **Note:** With `type="none"`, virt-manager shows a blank screen. This is expected. Temporarily switch back to `type="vga"` if you need Windows access during setup.

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


## Phase 5: Installing the Looking Glass host in Windows

### Temporarily restoring VGA access

```bash
sudo virsh edit win11
# Change: <model type="none"/> to <model type="vga"/>
sudo virsh destroy win11
sudo virsh start win11
```

### Host installer in Windows

- Download `looking-glass-host-setup.exe` from **https://looking-glass.io/downloads** (B7)
- Right-click → **Run as administrator**
- Next → Agree → Next → Install → Close

This automatically installs the IVSHMEM driver and the Looking Glass Host service.

### Installing the NVIDIA driver in Windows

The RTX 4060 showed up as "Microsoft Basic Display Adapter". Download the driver from **https://www.nvidia.com/drivers** and install it.

### Setting video back to none

```bash
sudo virsh edit win11
# Change: <model type="vga"/> back to <model type="none"/>
sudo virsh destroy win11
sudo virsh start win11
```


## Phase 6: Connecting the client

### Checking shared memory permissions

```bash
ls -la /dev/kvmfr0

# QEMU fallback:
ls -la /dev/shm/looking-glass
sudo chown sten:kvm /dev/shm/looking-glass  # if permissions are incorrect
```

### Starting the client

```bash
looking-glass-client -s
```

Result: **"Host Application Not Running"**; shared memory works, but the host is not sending frames.


## Why it failed

### Host application log

`C:\ProgramData\Looking Glass (host)\looking-glass-host.txt`:

```
[I] d12.c | Not using unsupported adapter: Microsoft Basic Render Driver
[E] d12.c | Failed to locate a valid output device
[I] dxgi.c | Not using unsupported adapter: Microsoft Basic Render Driver
[E] dxgi.c | Failed to locate a valid output device
[E] app.c | Failed to find a supported capture interface
```

### Diagnosis via PowerShell in Windows

```powershell
Get-PnpDevice | Where-Object {
    $_.FriendlyName -like "*NVIDIA*" -or $_.FriendlyName -like "*display*"
} | Format-Table FriendlyName, Status, Class

# Result:
# NVIDIA GeForce RTX 4060 Laptop GPU  OK  Display
# Microsoft Basic Display Adapter     OK  Display
```

The RTX 4060 was recognized and the driver was installed, but the host could not use it because there is no display output.

### The fundamental hardware limitation

Confirmed via `ls /sys/class/drm/`:

```
card0-HDMI-A-1      ← HDMI is on AMD iGPU (card0)
card0-eDP-2         ← internal display via AMD (Dynamic MUX mode)
card1-DP-1 to DP-8  ← NVIDIA virtual outputs (no physical connectors)
card1-eDP-1         ← internal display via NVIDIA (dGPU MUX mode)
```

**All physical ports on this laptop are on the AMD iGPU.** The RTX 4060 has no physical display connectors whatsoever. DirectX 12 and DXGI require an active display output for frame capture, which is physically impossible on this laptop.


## Additional findings

### nvidia-fallback.service

Produces errors when VFIO is active. Solution: mask it (see Phase 1). When reverting, restore it:
```bash
sudo systemctl unmask nvidia-fallback.service
sudo systemctl enable nvidia-fallback.service
```

### QEMU shared memory fallback

If `/dev/kvmfr0` is not available, QEMU uses `/dev/shm/looking-glass` (128MB, owned by `qemu:qemu`). The client falls back to this automatically.


## Reverting everything

```bash
# Restore kernel parameters
sudo grubby --update-kernel=ALL \
  --remove-args="vfio-pci.ids=10de:28e0,10de:22be rd.driver.pre=vfio-pci \
                 rd.driver.blacklist=nouveau,nova_core modprobe.blacklist=nouveau,nova_core" \
  --args="nvidia-drm.modeset=1 nvidia-drm.fbdev=1 \
          nvidia.NVreg_PreserveVideoMemoryAllocations=1 iommu=pt"

# Remove VFIO config
sudo rm /etc/modprobe.d/vfio.conf
sudo rm /etc/dracut.conf.d/vfio.conf
sudo rm /etc/modules-load.d/kvmfr.conf
sudo rm /etc/udev/rules.d/99-kvmfr.rules
sudo rm /etc/modprobe.d/kvmfr.conf

# Restore nvidia-fallback
sudo systemctl unmask nvidia-fallback.service
sudo systemctl enable nvidia-fallback.service

# Remove KVMFR DKMS module
sudo dkms remove kvmfr/0.0.12 --all

# Remove DKMS MOK key (optional)
sudo mokutil --delete /var/lib/dkms/mok.pub
# Set password for the MOK prompt at reboot

# Rebuild initramfs
sudo akmods --force
sudo dracut --force

sudo reboot
# At reboot: blue MOK screen → Delete MOK → password → reboot
```

Restore VM XML via `sudo virsh edit win11`: remove the two `<hostdev>` blocks and the `<shmem>` block, set video back to `type="virtio"` with `accel3d="yes"`, and set SPICE back to `gl enable="yes" rendernode="/dev/dri/by-path/pci-0000:66:00.0-render"`.


## Conclusion

Looking Glass is an impressive project but requires hardware that is simply not present on the Zephyrus G16. For Windows applications on this laptop, the best options are:

- **[virt-manager with VirtIO + SPICE GL]({{< relref "/docs/virtualization/vm-setup" >}})**: good performance for office/productivity (see the [VM Setup Guide]({{< relref "/docs/virtualization/vm-setup" >}}) for configuration details)
- **Bottles/Wine**: for compatible Windows applications
- **Native Linux alternatives**: when available


## References

- [Looking Glass official documentation B7](https://looking-glass.io/docs/B7/)
- [Looking Glass GitHub](https://github.com/gnif/LookingGlass)
- [VFIO GPU Passthrough Guide - Arch Wiki](https://wiki.archlinux.org/title/PCI_passthrough_via_OVMF)
- [GA605WV display routing - Arch Linux Forums](https://bbs.archlinux.org/viewtopic.php?id=299932)


