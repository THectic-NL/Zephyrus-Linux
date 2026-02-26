---
title: "NVIDIA Driver Installation"
weight: 1
prev: docs/getting-started
---

The G16 has an NVIDIA RTX 4060 alongside the AMD iGPU. The open-source Nouveau driver doesn't perform well on modern NVIDIA hardware, so proprietary drivers are necessary.

**Driver I'm running:**
- Version: 590.48.01
- CUDA Version: 13.1


## CachyOS (Arch)

CachyOS automatically detects your hardware during installation and sets up the NVIDIA driver without any manual steps. No selection required; by the time the installer finishes, the driver is already active and fully configured.

See [Post-Installation Verification](#post-installation-verification) to confirm everything is working correctly.


## Fedora

The following covers the full manual installation process. I ran into several crashes and lockups during setup that took some time to track down; those are documented on the [Known Issues]({{< relref "/docs/known-issues" >}}) page.

## Prerequisites

### Enable RPM Fusion

RPM Fusion provides the NVIDIA drivers for Fedora. Enable both repositories before installing:

```bash
sudo dnf install \
  https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
  https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
```

### System Verification

{{% details title="Check kernel version" closed="true" %}}

Required: Kernel 6.19+ for Ryzen AI 9 HX 370 support.

```bash
uname -r
```

{{% /details %}}

{{% details title="Check Secure Boot status" closed="true" %}}

```bash
mokutil --sb-state
```

{{% /details %}}

### Why Proprietary Driver

The open-source Nouveau driver has poor performance on modern NVIDIA GPUs. The proprietary driver is required for:
- Gaming and graphics-intensive applications
- CUDA workloads
- Proper Wayland support (available since driver 555+)


## Installation Steps

{{% steps %}}

### Update system

```bash
sudo dnf upgrade
```

Wait for update completion.

### Verify driver version

Check available NVIDIA driver version:

```bash
dnf info akmod-nvidia
```

### Install NVIDIA driver

Install driver with CUDA support:

```bash
sudo dnf install akmod-nvidia xorg-x11-drv-nvidia-cuda xorg-x11-drv-nvidia-libs.i686
```

This installs the driver, CUDA libraries, and build dependencies (about 1 GB).
- `akmod-nvidia` - NVIDIA driver using akmods for automatic kernel module building and signing
- `xorg-x11-drv-nvidia-cuda` - CUDA support and driver utilities (includes Wayland support)
- `xorg-x11-drv-nvidia-libs.i686` - 32-bit NVIDIA libraries (needed for Steam/Proton)

### Build kernel modules

akmods automatically builds and signs kernel modules on installation. To manually trigger a rebuild:

```bash
sudo akmods --force
sudo dracut --force
```

This process may take 5-10 minutes.

### Verify kernel modules

Check that kernel modules were built:

```bash
ls /lib/modules/$(uname -r)/kernel/drivers/video/
```

The NVIDIA modules should be present.

### Enroll MOK signing key

If Secure Boot is enabled, import the akmods signing key and set a password for the enrollment prompt:

```bash
sudo mokutil --import /etc/pki/akmods/certs/public_key.der
```

### MOK enrollment on next boot

```bash
sudo reboot
```

During boot, the MOK Management screen (blue screen) will appear:
1. Select "Enroll MOK"
2. Select "Continue"
3. Select "Yes"
4. Enter the password you set in the previous step
5. Reboot

The system will boot normally after MOK enrollment.

### Final reboot

```bash
sudo reboot
```

The NVIDIA driver will now load correctly.

### Enable NVIDIA power management services

Enable NVIDIA power services for better suspend/resume behavior and power management:

```bash
sudo systemctl enable nvidia-hibernate.service nvidia-suspend.service nvidia-resume.service
```

**What these services do:**
- `nvidia-hibernate.service` - Properly saves GPU state before hibernation
- `nvidia-suspend.service` - Manages GPU state during system suspend
- `nvidia-resume.service` - Restores GPU state after resume

These services prevent GPU state issues after suspend/resume cycles.

**Important: Do NOT enable `nvidia-powerd`; mask it permanently**

The `nvidia-powerd.service` manages NVIDIA Dynamic Boost, which shifts extra wattage (~5-15W) from the CPU to the GPU during heavy GPU loads. While useful on Intel-based laptops, it conflicts with AMD ATPX power management on the Zephyrus G16 and causes soft lockups and "GPU has fallen off the bus" errors.

On this laptop, GPU power is managed via ATPX (AMD-driven via ACPI). The NVIDIA suspend/hibernate/resume services and `supergfxctl` handle power states correctly without `nvidia-powerd`.

**What you lose by disabling it:** Minimal. A few FPS less during heavy GPU workloads. The ~5-15W Dynamic Boost is not worth the instability on AMD ATPX hardware.

**Disable and mask permanently:**
```bash
sudo systemctl disable nvidia-powerd.service
sudo systemctl stop nvidia-powerd.service
sudo systemctl mask nvidia-powerd.service
```

Masking creates a symlink to `/dev/null`, preventing any process (including NVIDIA driver updates via `dnf`) from re-enabling the service.

**If you want to try re-enabling it later** (e.g., after a kernel or driver update that may fix the ATPX conflict):
```bash
sudo systemctl unmask nvidia-powerd.service
sudo systemctl enable --now nvidia-powerd.service
```

**Reference:**
- [NVIDIA Power Management Documentation](https://download.nvidia.com/XFree86/Linux-x86_64/590.48.01/README/powermanagement.html)

{{% /steps %}}


## Post-Installation Verification

{{% steps %}}

### Verify NVIDIA driver

After reboot, check driver status:

```bash
nvidia-smi
```

You should see the NVIDIA driver and CUDA versions listed.

### Check loaded kernel modules

```bash
lsmod | grep nvidia
```

The NVIDIA modules are loaded and the driver is functional.

{{% /steps %}}




## ICC Color Profiles

{{% details title="Install ASUS GameVisual color profiles for GA605WV built-in display" closed="true" %}}

The GA605WV ships with a 16" 2560x1600 240Hz ROG Nebula Display. ASUS factory-calibrates each panel and provides color profiles via their ASUS System Control Interface. On Windows, these are automatically applied by Armoury Crate/GameVisual. On Linux, we must install them manually.

The GA605WV was shipped with different panels depending on the unit. The standard model uses an IPS panel (ROG Nebula Display); some configurations ship with an OLED panel instead:

| Panel ID | Manufacturer | Model | Type |
|---|---|---|---|
| `104D158E` | Sharp | LQ160R1JW02 | IPS (ROG Nebula Display) |
| `834C41AE` | Samsung | ATNA60DL04-0 ([LaptopMedia](https://laptopmedia.com/screen/atna60dl04-0-sdc41ae/) · [Linux Hardware](https://linux-hardware.org/?id=eisa:samsung-sdc41ae)) | OLED |
| `E5090C19` | Unknown | — (present in ASUS driver package, not yet publicly identified) | Unknown |

To check which panel your unit has:

```bash
cat /sys/class/drm/card*-eDP-*/edid | edid-decode 2>/dev/null | grep -i "manufacturer\|model\|product name"
```

These color profiles were obtained by reverse engineering the ASUS Windows driver package. By analyzing the ASUS CDN structure and the contents of the driver ZIP files, all factory-calibrated profiles for this laptop were recovered. The ICC metadata was then modified so the profiles appear with readable names directly in GNOME Color Management.

**Install the color profiles:**

The ICC color profiles are located in the [`/icc-profiles/`](https://github.com/Stensel8/Zephyrus-Linux/tree/main/static/icc-profiles) directory of this repository. Clone the repository or manually download the profiles and copy them to either location:

| Location | Scope |
|---|---|
| `/usr/share/color/icc/colord/` | System-wide (all users, requires root) |
| `~/.local/share/icc/` | Current user only |

```bash
# System-wide install:
sudo cp GA605WV_1002_104D158E_CMDEF.icm /usr/share/color/icc/colord/

# Or per-user install:
mkdir -p ~/.local/share/icc
cp GA605WV_1002_104D158E_CMDEF.icm ~/.local/share/icc/
```

**Activate your profile in GNOME:**

1. Open **Settings** → **Color Management**
2. Select your display (e.g. **Built-In Screen**)
3. Click **Add Profile**
4. Select the profile matching your display and GPU combination (e.g. **Native** for AMD iGPU + Sharp LQ160R1JW02)
5. Click **Add**

**Note:** If GNOME Settings shows old technical names (e.g., "ASUS GA605WV 1002 104D158E CMDEF" instead of "Native"), close Settings and reopen, or log out/in to refresh the color cache.

The filename encodes your GPU (`1002` = AMD, `10DE` = NVIDIA) and panel ID. Match these to your unit using the panel table above. All profiles are in the [`/icc-profiles/`](https://github.com/Stensel8/Zephyrus-Linux/tree/main/static/icc-profiles) directory.

**Background:**

The profiles were found through analysis of ASUS Windows driver packages. The ASUS CDN URL structure:
```
https://dlcdn-rogboxbu1.asus.com/pub/ASUS/APService/Gaming/SYS/ROGS/{id}-{code}-{hash}.zip
```

For the GA605WV, this is: `20016-BWVQPK-01624c1cdd5a3c05252bad472fab1240.zip`

**Technical Details:**

The profiles in this repository are pre-processed with custom ICC metadata 'desc' tags so they appear with readable names directly in GNOME Color Management. For users interested in how such modifications work, you can implement similar ICC 'desc' tag manipulation yourself using Python's PIL/ImageCms.

{{% /details %}}

{{% details title="Install Samsung color profile for LS27B800TGUXEN (S80TB) Thunderbolt display" closed="true" %}}

The Samsung ViewFinity S8 Thunderbolt (LS27B800TGUXEN) ships with a factory color profile (`SxxB80xT.icm`) included in the Windows INF driver package. On Linux this profile must be installed manually.

The profile is located in the [`/icc-profiles/LS27B800TGUXEN - S80TB/`](https://github.com/Stensel8/Zephyrus-Linux/tree/main/static/icc-profiles/LS27B800TGUXEN%20-%20S80TB) directory of this repository.

**Install the color profile:**

Linux stores ICC profiles in one of two locations depending on scope:

| Location | Scope |
|---|---|
| `/usr/share/color/icc/colord/` | System-wide (all users, requires root) |
| `~/.local/share/icc/` | Current user only |

```bash
# System-wide install (recommended):
sudo cp SxxB80xT.icm /usr/share/color/icc/colord/

# Or per-user install:
mkdir -p ~/.local/share/icc
cp SxxB80xT.icm ~/.local/share/icc/
```

**Activate in GNOME:**

1. Open **Settings** → **Color Management**
2. Select the **Samsung display** (e.g. "LS27B800TGUXEN")
3. Click **Add Profile**
4. Select `SxxB80xT`
5. Click **Add**

{{% /details %}}


{{< callout type="info" >}}
Known issues and troubleshooting for NVIDIA driver installation are documented on the [Known Issues]({{< relref "/docs/known-issues" >}}) page.
{{< /callout >}}


## Technical Notes

### Package Naming
The `akmod-nvidia` package is the recommended NVIDIA driver for Fedora. It uses the akmods framework to rebuild kernel modules automatically after kernel updates.

### Secure Boot
akmods rebuilds and re-signs kernel modules automatically after kernel updates. On Fedora, `sbctl` can also be used to manage Secure Boot keys.


## Additional Resources

- [CachyOS Wiki: NVIDIA](https://wiki.cachyos.org/configuration/nvidia/)
- [Arch Wiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA)
- [Ryzen AI 9 HX 370 Linux Support](https://forums.linuxmint.com/viewtopic.php?t=429052)
- [NVIDIA vs Nouveau Performance](https://machaddr.substack.com/p/nouveau-vs-nvidia-the-battle-between)
- [Zephyrus G16 2024 Linux Guide](https://www.ehmiiz.se/blog/linux_asus_g16_2024/)
- [Fedora Discussion: Zephyrus External Monitor Issues](https://discussion.fedoraproject.org/t/asus-zephyrus-g16-with-nvidia-and-external-monitor-crashes-every-few-minutes/147175)
