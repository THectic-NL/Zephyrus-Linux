---
title: "NVIDIA Driver Installation"
weight: 11
---

The G16 has an NVIDIA RTX 4060 alongside the AMD iGPU. The open-source Nouveau driver doesn't perform well on modern NVIDIA hardware, so proprietary drivers are necessary.

**Driver I'm running:**
- Version: 590.48.01
- CUDA Version: 13.1
- Source: CachyOS/Arch repos
- Installation Method: nvidia-dkms (DKMS-based automatic kernel module rebuilding)


## CachyOS (Arch)

CachyOS ships with NVIDIA drivers pre-installed as part of the installer. If you selected the NVIDIA option during setup, no manual driver installation is needed — the driver is already active and fully configured.

See [Post-Installation Verification](#post-installation-verification) to confirm everything is working correctly.


## Fedora

The following covers the full manual installation process. I ran into several crashes and lockups during setup that took some time to track down — those are documented in the [Known Issues](#known-issues) section.

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

**Important: Do NOT enable `nvidia-powerd` — mask it permanently**

The `nvidia-powerd.service` manages NVIDIA Dynamic Boost, which shifts extra wattage (~5-15W) from the CPU to the GPU during heavy GPU loads. While useful on Intel-based laptops, it conflicts with AMD ATPX power management on the Zephyrus G16 and causes soft lockups and "GPU has fallen off the bus" errors.

On this laptop, GPU power is managed via ATPX (AMD-driven via ACPI). The NVIDIA suspend/hibernate/resume services and `supergfxctl` handle power states correctly without `nvidia-powerd`.

**What you lose by disabling it:** Minimal — a few FPS less during heavy GPU workloads. The ~5-15W Dynamic Boost is not worth the instability on AMD ATPX hardware.

**Disable and mask permanently:**
```bash
sudo systemctl disable nvidia-powerd.service
sudo systemctl stop nvidia-powerd.service
sudo systemctl mask nvidia-powerd.service
```

Masking creates a symlink to `/dev/null`, preventing any process — including NVIDIA driver updates via `dnf` — from re-enabling the service.

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

The filename encodes your GPU (`1002` = AMD, `10DE` = NVIDIA) and panel ID — match these to your unit using the panel table above. All profiles are in the [`/icc-profiles/`](https://github.com/Stensel8/Zephyrus-Linux/tree/main/static/icc-profiles) directory.

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


## Known Issues

{{% details title="System crashes with external monitors (AMD GPU PSR bug)" closed="true" %}}

**Problem:**
System freezes or crashes when using external monitors via Thunderbolt/USB-C, especially when connecting/disconnecting displays. Logs show AMD GPU errors:
```
amdgpu 0000:66:00.0: amdgpu: MES failed to respond to msg=RESET
amdgpu 0000:66:00.0: amdgpu: Ring gfx_0.0.0 reset failed
amdgpu 0000:66:00.0: amdgpu: GPU reset begin!
```

**Cause:**
This laptop has dual GPUs (AMD Radeon 890M integrated + NVIDIA RTX 4060 discrete). The AMD GPU's PSR (Panel Self Refresh) feature has a bug causing crashes with external Thunderbolt monitors.

**Solution:**
Disable AMD PSR by adding a kernel parameter. Edit `/etc/default/grub` and add `amdgpu.dcdebugmask=0x600` to `GRUB_CMDLINE_LINUX_DEFAULT`, then regenerate:

```bash
sudo nano /etc/default/grub
sudo grub2-mkconfig -o /boot/efi/EFI/fedora/grub.cfg
```

Reboot:
```bash
sudo reboot
```

**What this does:**
- `amdgpu.dcdebugmask=0x600` disables PSR (Panel Self Refresh) on the AMD GPU
- PSR is a power-saving feature where the display refreshes itself without GPU involvement
- The PSR implementation has bugs with Thunderbolt/USB-C external monitors

**Trade-offs:**
- Pro: Stable system with external monitors
- Con: Slightly higher power consumption (PSR disabled)

**Verification:**
Monitor for AMD GPU errors while using external displays:
```bash
sudo journalctl -f -k | grep -i amdgpu
```

If no `amdgpu: [drm] *ERROR*` messages appear, the fix is working.

**Reference:**
- [Fedora Discussion: Zephyrus G16 External Monitor Crashes](https://discussion.fedoraproject.org/t/asus-zephyrus-g16-with-nvidia-and-external-monitor-crashes-every-few-minutes/147175)

{{% /details %}}

{{% details title="VS Code crashes system (AMD GPU page fault - Kernel 6.18.x bug)" closed="true" %}}

**What's happening:**
System freezes completely during VS Code use. Kernel 6.18.x/6.19.x have critical amdgpu driver bugs. VS Code hardware acceleration triggers AMD Radeon 890M page fault → complete freeze.

**Fix:**
Add to `~/.config/Code/User/settings.json`:
```json
{
    "disable-hardware-acceleration": true
}
```

**Next steps:**
Restart VS Code. System stays stable, VS Code slightly slower but perfectly usable.

**Sources:**
- [VS Code Issue #238088](https://github.com/microsoft/vscode/issues/238088)
- [Framework: Critical amdgpu bugs kernel 6.18.x](https://community.frame.work/t/attn-critical-bugs-in-amdgpu-driver-included-with-kernel-6-18-x-6-19-x/79221)

{{% /details %}}

{{% details title="Brave Browser crashes system (AMD GPU page fault - Kernel 6.18.x bug)" closed="true" %}}

**What's happening:**
System freezes or crashes during Brave Browser use, even with minimal workload (a few tabs). This is the same underlying issue as the VS Code crash: Chromium-based applications with hardware acceleration trigger AMD Radeon 890M page faults on kernel 6.18.x/6.19.x.

Typical crash sequence in logs:
```
amdgpu: [gfxhub] page fault (src_id:0 ring:24 vmid:2)
amdgpu: Faulty UTCL2 client ID: SQC (data)
amdgpu: ring gfx_0.0.0 timeout, signaled seq=302899, emitted seq=302901
amdgpu: GPU reset begin!
```

After GPU reset, gnome-shell crashes (Signal 6 ABRT) because it detects a context reset.

**Fix:**
Open Brave Browser and go to `brave://settings/system`. Turn off **"Use hardware acceleration when available"**.

Alternatively via terminal:
```bash
sed -i 's/"hardware_acceleration_mode_previous":true/"hardware_acceleration_mode_previous":false/' ~/.config/BraveSoftware/Brave-Browser/Local\ State
```

Or start Brave with the `--disable-gpu` flag:
```bash
brave-browser-stable --disable-gpu
```

**Next steps:**
Restart Brave. Verify via `brave://gpu` that GPU acceleration is disabled. System stays stable, Brave is slightly slower on heavy pages but perfectly usable.

**Background:**
Brave, VS Code, and other Chromium-based applications (Chrome, Edge, Electron apps) use GPU shader compilation via Mesa. On kernel 6.18.x, the amdgpu driver has a bug in the Shader Queue Controller (SQC) memory access, causing page faults that trigger a full GPU reset. The fix is to disable hardware acceleration per application until a kernel/Mesa update resolves the issue.

**Sources:**
- [Framework: Critical amdgpu bugs kernel 6.18.x](https://community.frame.work/t/attn-critical-bugs-in-amdgpu-driver-included-with-kernel-6-18-x-6-19-x/79221)

{{% /details %}}

{{% details title="NVIDIA soft lockup with minimal GPU load (hybrid GPU power management)" closed="true" %}}

**What's happening:**
System freezes with an NVIDIA soft lockup, even without active GPU use. Kernel logs show:
```
watchdog: BUG: soft lockup - CPU#23 stuck for 62s!
NVRM: Xid (PCI:0000:65:00): 79, pid=<...>, GPU has fallen off the bus
```

This can occur due to a combination of factors on hybrid GPU laptops:
- `nvidia-powerd` conflicts with AMD ATPX power management
- NVIDIA dGPU power state transitions fail
- Corrupted VRAM after suspend/resume cycles

**Additional symptom: Reboot hang (black screen, backlights stay on)**

The system appears to shut down but never completes the hardware reset — the screen goes black but keyboard and screen backlights remain on. This occurs when `nvidia-powerd` interferes with ACPI power state transitions during shutdown/reboot.

**Root cause: `supergfxd` starts `nvidia-powerd` behind your back**

Even when `nvidia-powerd` is disabled via `systemctl disable`, `supergfxd` (the GPU switching daemon from asusctl) directly calls `systemctl start nvidia-powerd.service` during GPU mode switches. This bypasses the disabled state and re-activates the conflict with ATPX.

**How this was diagnosed:**

Checking the logs of the hung boot reveals `supergfxd` starting `nvidia-powerd`:
```bash
journalctl -b -1 --no-pager | grep -iE "nvidia.*powerd|supergfxd"
```

Key evidence:
```
supergfxd: [DEBUG supergfxctl] Did CommandArgs { inner: ["start", "nvidia-powerd.service"] }
nvidia-powerd: ERROR! Client (presumably SBIOS) has requested to disable Dynamic Boost DC controller
```

The SBIOS error confirms the firmware rejected Dynamic Boost, but `nvidia-powerd` was already running and interfering with power state management. Checking the shutdown sequence:

```bash
journalctl -b -1 --reverse | head -20
```

Shows the hardware watchdog failed to stop, confirming the ACPI reboot never completed:
```
watchdog: watchdog0: watchdog did not stop!
```

**Fix:**

1. Disable and **mask** `nvidia-powerd` (masking is essential — `disable` alone is not enough because `supergfxd` bypasses it):
```bash
sudo systemctl disable nvidia-powerd.service
sudo systemctl stop nvidia-powerd.service
sudo systemctl mask nvidia-powerd.service
```

2. Add kernel parameters for more stable NVIDIA power management (edit `/etc/default/grub` and add to `GRUB_CMDLINE_LINUX_DEFAULT`, then `sudo grub-mkconfig -o /boot/grub/grub.cfg`):
```
nvidia-drm.fbdev=1 nvidia.NVreg_PreserveVideoMemoryAllocations=1
```

3. Reboot:
```bash
sudo reboot
```

**Next steps:**
System is more stable after these changes. The NVIDIA dGPU is still properly managed via ATPX (AMD-driven power switching) without `nvidia-powerd` interfering. The mask creates a symlink to `/dev/null`, ensuring no process — including `supergfxd` and NVIDIA driver updates — can re-enable the service.

**Background:**
On laptops with AMD iGPU + NVIDIA dGPU, the ATPX framework (via ACPI) controls which GPU is active. `nvidia-powerd` tries to make power decisions independently, which conflicts with ATPX. The `NVreg_PreserveVideoMemoryAllocations=1` parameter prevents VRAM from being lost during power transitions, and `nvidia-drm.fbdev=1` provides cleaner framebuffer handoff.

{{% /details %}}


## Troubleshooting

{{% details title="nvidia-smi command not found or fails" closed="true" %}}

Check if NVIDIA modules are loaded:
```bash
lsmod | grep nvidia
```

Check system logs for errors:
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

{{% details title="MOK enrollment issues or \"Key was rejected by service\" error" closed="true" %}}

If you receive the error `modprobe: ERROR: could not insert 'nvidia': Key was rejected by service`, the kernel modules were built before MOK enrollment completed.

Solution:
```bash
# Rebuild modules after MOK enrollment
sudo akmods --force
sudo dracut --force

# Reboot
sudo reboot
```

To reset MOK if needed:
```bash
sudo mokutil --reset
```

Reboot and attempt enrollment again.

{{% /details %}}


{{% details title="Kernel module build failures" closed="true" %}}

Ensure kernel headers match running kernel:
```bash
sudo dnf install kernel-devel
```

Force rebuild:
```bash
sudo akmods --force
sudo dracut --force
```

{{% /details %}}


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
