---
title: "Known Issues"
weight: 7
prev: docs/virtualization/vmware-workstation
---

Central reference for hardware and software issues on the ASUS ROG Zephyrus G16 GA605WV. Active issues are listed first. Resolved issues are kept as reference at the bottom.

## Active Issues

> These are issues I'm personally still running into. In some cases it might be a real bug; in others it might just be something I'm missing or doing wrong. I'm sharing what I observed, not what I've definitively diagnosed.

{{% details title="WinBoat: container fails to start" closed="true" %}}

**What's happening:**
WinBoat regularly gets stuck in an endless startup loop. The Podman container keeps trying to start but never succeeds, even after waiting indefinitely. The UI shows "WinBoat Guest API - Offline" and "Container - Exited". This is not limited to the first install; it happens on subsequent starts as well.

**Workaround:**
Resetting WinBoat and going through the initial configuration again gets it running again. This is not a sustainable fix.

**Status:**
Open. WinBoat is in beta and the project acknowledges instability. See the [WinBoat page]({{< relref "/docs/virtualization/winboat" >}}) for more context.

{{% /details %}}

{{% details title="WinBoat: application windows drift and shrink randomly" closed="true" %}}

**What's happening:**
When WinBoat does start successfully and a Windows application (such as Microsoft Word) is opened, the window behaves erratically: it drifts to the right across the screen, scales down randomly, and keeps getting smaller until it is barely visible. This makes WinBoat effectively unusable for productivity applications.

**Workaround:**
None found. Restarting the application or WinBoat does not reliably fix it.

**Status:**
Open. Beta limitation.

{{% /details %}}

{{% details title="Brave Browser: touchpad scrolling too fast on Wayland" closed="true" %}}

**What's happening:**
Touchpad scrolling in Brave feels significantly faster than in Firefox or native GTK apps. A short swipe sends the page flying. This affects all Chromium-based browsers on Wayland.

**Cause:**
Upstream Chromium issue. Chromium receives high-precision scroll events from libinput on Wayland but doesn't normalize them the way GTK does. Firefox uses GTK's input stack, which handles this correctly. Chromium does not.

**Status:**
Open. No fix in Brave as of early 2026. The issue has been reported since at least 2022.

**Attempted workaround (abandoned):**
Lowering the global `scroll-factor` in [libinput-config]({{< relref "/docs/applications#touchpad-scroll-speed-no-native-gnome-setting-yet" >}}) does reduce scrolling speed in Brave, but it's a system-wide change that affects every application, including ones where scrolling was already fine. After running with this for about a week I removed it. The Brave-specific problem doesn't justify slowing down everything else.

**Sources:**
- [brave-browser #36569: native touchpad scrolling on Linux Wayland](https://github.com/brave/brave-browser/issues/36569)
- [Brave Community: high-resolution touchpad scrolling on Linux Wayland](https://community.brave.app/t/scrolling-speed-is-way-too-fast/649357)

{{% /details %}}

{{% details title="YubiKey FIDO2 LUKS unlock: USB timing race" closed="true" %}}

**What's happening:**
Enrolling the YubiKey as a FIDO2 LUKS unlock key succeeds, but at boot `systemd-cryptsetup` fails with `FIDO_ERR_RX`. The key is physically present but seemingly not yet initialized by the USB HID stack when the query comes in. This seems to hit especially on warm reboots.

Tried with `token-timeout=30` in crypttab and `rd.udev.settle-timeout=10` as a kernel parameter, both on systemd 259. Neither helped.

**Status:**
Still unresolved. Not sure if this is a real hardware/firmware timing issue, something specific to this machine, or a misconfiguration on my end. Possibly revisiting later. For now, the YubiKey is used for `sudo` and the GNOME lock screen instead.

See the [YubiKey page]({{< relref "/docs/security/yubikey" >}}) for the full attempted setup and what was reverted.

{{% /details %}}

## Resolved Issues

The following issues are resolved. Each entry is either fixed by the Linux kernel developers (notably the AMD GPU page fault bugs in 6.18 and the asus-armoury driver merged in 6.19), or resolved through a configuration workaround I applied myself. Kept here as reference.

## GPU & Display

{{% details title="System freezes with external monitors (AMD GPU PSR bug)" closed="true" %}}

**Problem:**
System freezes or crashes when using external monitors via Thunderbolt/USB-C, especially when connecting/disconnecting displays. Logs show AMD GPU errors:
```
amdgpu 0000:66:00.0: amdgpu: MES failed to respond to msg=RESET
amdgpu 0000:66:00.0: amdgpu: Ring gfx_0.0.0 reset failed
amdgpu 0000:66:00.0: amdgpu: GPU reset begin!
```

**Cause:**
This laptop has dual GPUs (AMD Radeon 890M integrated + NVIDIA RTX 4060 discrete). The AMD GPU's PSR (Panel Self Refresh) feature has a bug causing crashes with external Thunderbolt monitors.

**Fix:**
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
```bash
sudo journalctl -f -k | grep -i amdgpu
```

If no `amdgpu: [drm] *ERROR*` messages appear, the fix is working.

**Reference:**
- [Fedora Discussion: Zephyrus G16 External Monitor Crashes](https://discussion.fedoraproject.org/t/asus-zephyrus-g16-with-nvidia-and-external-monitor-crashes-every-few-minutes/147175)

{{% /details %}}

{{% details title="System freezes during VS Code use (AMD GPU page fault, Kernel 6.18.x)" closed="true" %}}

**What's happening:**
System freezes completely during VS Code use. Kernel 6.18.x/6.19.x have critical amdgpu driver bugs. VS Code hardware acceleration triggers AMD Radeon 890M page fault → complete freeze.

**Fix:**
Add to `~/.config/Code/User/settings.json`:
```json
{
    "disable-hardware-acceleration": true
}
```

Restart VS Code. System stays stable, VS Code slightly slower but perfectly usable.

**Sources:**
- [VS Code Issue #238088](https://github.com/microsoft/vscode/issues/238088)
- [Framework: Critical amdgpu bugs kernel 6.18.x](https://community.frame.work/t/attn-critical-bugs-in-amdgpu-driver-included-with-kernel-6-18-x-6-19-x/79221)

{{% /details %}}

{{% details title="System freezes during Brave Browser use (AMD GPU page fault, Kernel 6.18.x)" closed="true" %}}

**What's happening:**
System freezes or crashes during Brave Browser use, even with minimal workload (a few tabs). Chromium-based applications with hardware acceleration trigger AMD Radeon 890M page faults on kernel 6.18.x/6.19.x.

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

Restart Brave. Verify via `brave://gpu` that GPU acceleration is disabled.

**Background:**
Brave, VS Code, and other Chromium-based applications (Chrome, Edge, Electron apps) use GPU shader compilation via Mesa. On kernel 6.18.x, the amdgpu driver has a bug in the Shader Queue Controller (SQC) memory access, causing page faults that trigger a full GPU reset. The fix is to disable hardware acceleration per application until a kernel/Mesa update resolves the issue.

**Sources:**
- [Framework: Critical amdgpu bugs kernel 6.18.x](https://community.frame.work/t/attn-critical-bugs-in-amdgpu-driver-included-with-kernel-6-18-x-6-19-x/79221)

{{% /details %}}

{{% details title="NVIDIA soft lockup / 'GPU has fallen off the bus'" closed="true" %}}

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

The system appears to shut down but never completes the hardware reset; the screen goes black but keyboard and screen backlights remain on. This occurs when `nvidia-powerd` interferes with ACPI power state transitions during shutdown/reboot.

**Root cause: `supergfxd` starts `nvidia-powerd` behind your back**

Even when `nvidia-powerd` is disabled via `systemctl disable`, `supergfxd` (the GPU switching daemon from asusctl) directly calls `systemctl start nvidia-powerd.service` during GPU mode switches. This bypasses the disabled state and re-activates the conflict with ATPX.

**How this was diagnosed:**
```bash
journalctl -b -1 --no-pager | grep -iE "nvidia.*powerd|supergfxd"
```

Key evidence:
```
supergfxd: [DEBUG supergfxctl] Did CommandArgs { inner: ["start", "nvidia-powerd.service"] }
nvidia-powerd: ERROR! Client (presumably SBIOS) has requested to disable Dynamic Boost DC controller
```

Checking the shutdown sequence:
```bash
journalctl -b -1 --reverse | head -20
```

Shows the hardware watchdog failed to stop, confirming the ACPI reboot never completed:
```
watchdog: watchdog0: watchdog did not stop!
```

**Fix:**

1. Disable and **mask** `nvidia-powerd` (masking is essential, `disable` alone is not enough because `supergfxd` bypasses it):
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

**Background:**
On laptops with AMD iGPU + NVIDIA dGPU, the ATPX framework (via ACPI) controls which GPU is active. `nvidia-powerd` tries to make power decisions independently, which conflicts with ATPX. The `NVreg_PreserveVideoMemoryAllocations=1` parameter prevents VRAM from being lost during power transitions, and `nvidia-drm.fbdev=1` provides cleaner framebuffer handoff.

{{% /details %}}


## NVIDIA Driver

> These entries apply primarily to the Fedora installation path. CachyOS users are not affected; the driver is pre-configured during installation.

{{% details title="nvidia-smi: command not found or fails" closed="true" %}}

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

{{% details title="MOK enrollment: 'Key was rejected by service'" closed="true" %}}

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


## Applications

{{% details title="Brave Browser crashes on GNOME Wayland (WaylandWpColorManagerV1)" closed="true" %}}

**What's happening:**
Brave 1.82–1.86 crashed or caused GNOME Shell to crash on Wayland. The crash is triggered by a Wayland color management extension (`WaylandWpColorManagerV1`) that conflicts with the AMD amdgpu driver, causing GPU ring timeouts that take down the entire desktop session.

**Fix:**
Copy the system desktop entry to your user directory so it doesn't get overwritten by updates:
```bash
sudo cp /usr/share/applications/brave-browser.desktop ~/.local/share/applications/
```

Patch all three `Exec=` lines with the flag:
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

Verify: you should see exactly three `Exec=` lines with the flag appended:
```bash
grep "^Exec" ~/.local/share/applications/brave-browser.desktop
```

{{% /details %}}

{{% details title="GNOME Shell crashes during video playback in Brave (AMD VCN hardware decode)" closed="true" %}}

**What's happening:**
GNOME Shell crashes with SIGABRT during Picture-in-Picture video in Brave. The AMD VCN hardware decoder triggers a context reset that crashes gnome-shell. This is documented in [gnome-mutter issue #4625](https://gitlab.gnome.org/GNOME/mutter/-/issues/4625).

**Note:** This crash occurs even with the `--disable-features=WaylandWpColorManagerV1` flag applied. Both workarounds are required.

**Fix:**
Go to `brave://flags` and disable:

- **Hardware-accelerated video decode** → `Disabled`

![brave://flags - Hardware-accelerated video decode disabled](/images/brave-flags.avif)

After this, `brave://gpu` will show:
- `Video Decode: Software only. Hardware acceleration disabled`

![brave://gpu - Video Decode disabled, software only](/images/brave-gpu-config.avif)

Brave is slightly slower on video-heavy pages but stable. Hardware video decode is not yet stable on the AMD Radeon 890M with GNOME Wayland.

{{% /details %}}

{{% details title="Steam won't launch" closed="true" %}}

**What was happening:**
Steam failed to launch on some setups, with no visible error output.

**Workaround (no longer needed):**
```bash
__GL_CONSTANT_FRAME_RATE_HINT=3 steam
```

**Resolution:**
This issue has since resolved itself. Steam now launches normally; the `__GL_CONSTANT_FRAME_RATE_HINT` workaround is no longer required. Install Steam from the [CachyOS repository](https://packages.cachyos.org/package/cachyos/x86_64/steam) via `sudo pacman -S steam`.

{{% /details %}}


## asusctl & ROG Control Center

{{% details title="ROG Control Center: 'The asus-armoury driver is not loaded'" closed="true" %}}

**Problem:**
ROG Control Center shows a warning that the `asus-armoury` kernel driver is not loaded. Some advanced features (PPT power limits, APU memory allocation, MUX switch control) are unavailable.

**Cause:**
The `asus-armoury` driver was merged into the Linux mainline kernel in version 6.19. CachyOS ships kernel 6.19.8-1-cachyos which includes this driver, so it should be available.

**Fix:**
Verify the driver is loaded:
```bash
lsmod | grep asus_armoury
```

If it loads, reopen ROG Control Center; the warning should be gone and advanced features will be available.

{{% /details %}}


## Secure Boot

{{% details title="sbctl status still shows 'Setup Mode: Disabled' after clearing keys" closed="true" %}}

Some ASUS UEFI versions require the platform key (PK) to be explicitly deleted before Setup Mode activates.

In the ASUS UEFI:
1. Go to **Security** → **Secure Boot** → **Key Management**
2. Select **Platform Key (PK)** → **Delete**
3. Save & Exit and reboot

After rebooting, `sudo sbctl status` should show Setup Mode: Enabled.

{{% /details %}}

{{% details title="System does not boot after enabling Secure Boot" closed="true" %}}

If the system doesn't boot after enabling Secure Boot, one or more EFI files weren't signed.

1. Reboot into the ASUS UEFI and temporarily disable Secure Boot
2. Boot into CachyOS
3. Check which files are unsigned:
```bash
sudo sbctl verify
```
4. Sign any missing files:
```bash
sudo sbctl sign -s /path/to/file.efi
```
5. Or re-run the batch sign:
```bash
sudo sbctl-batch-sign
```
6. Reboot and re-enable Secure Boot

{{% /details %}}


## YubiKey & LUKS

{{% details title="System stuck in boot loop after FIDO2 enrollment" closed="true" %}}

If you enrolled FIDO2 and cannot boot, spam-tap the YubiKey immediately after the BIOS screen. The touch window is very short.

Once in the system, revert immediately:
```bash
sudo systemd-cryptenroll --wipe-slot=fido2 /dev/nvme1n1p3
sudo nano /etc/crypttab  # remove fido2-device=auto
sudo rm /etc/dracut.conf.d/fido2.conf
sudo dracut --force --regenerate-all
```

{{% /details %}}

{{% details title="Verify LUKS keyslots" closed="true" %}}

```bash
sudo cryptsetup luksDump /dev/nvme1n1p3 | grep -E "^\s+[0-9]+:"
```

Should show only `0: luks2` after reverting. If slot 1 is still present, FIDO2 is still enrolled.

{{% /details %}}


## GDM Autologin

{{% details title="Autologin not working after config change" closed="true" %}}

Verify the config file is correct:

```bash
sudo cat /etc/gdm/custom.conf
```

Ensure `AutomaticLoginEnable=True` is under `[daemon]` and the username matches exactly:

```bash
whoami
```

Also check that GDM is the active display manager:

```bash
systemctl status gdm
```

{{% /details %}}


## Virtual Machines

{{% details title="'Could not detect a default hypervisor' error in virt-manager" closed="true" %}}

```bash
# 1. Start libvirtd
sudo systemctl start libvirtd

# 2. Check group membership
groups  # Must contain "libvirt"

# If "libvirt" is missing:
sudo usermod --append --groups libvirt $(whoami)
# Then log out and log back in
```

If you still see the error after logging back in, add the connection manually:
1. Open virt-manager
2. File → Add Connection
3. Hypervisor: **QEMU/KVM**
4. Connect to local hypervisor
5. Leave all other fields empty
6. Click **Connect**

{{% /details %}}

{{% details title="VirtIO ISO download is incomplete" closed="true" %}}

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

{{% /details %}}

{{% details title="Permission denied when starting VM" closed="true" %}}

```bash
sudo restorecon -Rv /var/lib/libvirt/images/
sudo restorecon -Rv /mnt/vmstore/
```

{{% /details %}}

{{% details title="Black screen in VM" closed="true" %}}

- Check that Video model is set to **Virtio** (not QXL) in virt-manager hardware settings
- Install VirtIO guest tools from the VirtIO ISO (inside Windows)
- Install SPICE Guest Tools (inside Windows)

{{% /details %}}

{{% details title="Clipboard doesn't work between host and guest" closed="true" %}}

Install SPICE Guest Tools inside the Windows VM. Download from [spice-space.org](https://www.spice-space.org/download.html) and run the installer. Clipboard sharing, drag-and-drop, and dynamic display resolution all require SPICE Guest Tools.

{{% /details %}}
