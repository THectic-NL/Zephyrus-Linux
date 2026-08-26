---
title: "NVIDIA Driver: Bazzite"
weight: 2
prev: docs/hardware/nvidia-cachyos
next: docs/hardware/secure-boot-cachyos
---

The G16 has an NVIDIA RTX 4060 alongside the AMD iGPU. On Bazzite the driver is not something you install — it is part of the image you booted. Which means the work here is picking the right image, enrolling one Secure Boot key, and two power settings this laptop needs.

{{< callout type="warning" >}}
If you came here looking for RPM Fusion, `akmod-nvidia`, `akmods --force` and a MOK enrollment screen: none of that applies. That is the procedure for conventional Fedora. On an atomic image it is at best redundant and at worst breaks your next update.
{{< /callout >}}

## Use an `-nvidia-open` image

The RTX 4060 is Ada, so it's covered by NVIDIA's open kernel modules, and that's what the `-nvidia-open` images ship. Check what you're currently on:

```bash
rpm-ostree status
```

The image ref is on the first line. If it doesn't contain `nvidia-open`, rebase:

```bash
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/ublue-os/bazzite-gnome-nvidia-open:stable
systemctl reboot
```

Swap `bazzite-gnome-nvidia-open` for `bazzite-nvidia-open` if you want KDE instead of GNOME. See [Bazzite]({{< relref "/docs/getting-started/bazzite" >}}) for the full image list and what a rebase does.

## Enroll the Secure Boot key first

The NVIDIA kernel modules are signed with Universal Blue's key. With Secure Boot on and that key not enrolled, the modules refuse to load and you land in a session without acceleration — which looks exactly like a broken driver.

```bash
ujust enroll-secure-boot-key
```

The password is `universalblue`. Full procedure, including the blue MokManager screen: [Secure Boot on Bazzite]({{< relref "/docs/hardware/secure-boot-bazzite" >}}).

## Post-Installation Verification

{{% steps %}}

### Verify NVIDIA driver

```bash
nvidia-smi
```

You should see the NVIDIA driver and CUDA versions listed.

### Check loaded kernel modules

```bash
lsmod | grep nvidia
```

If the modules are listed, the driver is loaded and functional. If they are not, and Secure Boot is on, enroll the key above before looking anywhere else.

### Confirm the open modules are in use

```bash
modinfo nvidia | grep -i license
```

The open kernel modules report a dual `MIT/GPL` license, where the proprietary module reports `NVIDIA`.

{{% /steps %}}

## Power Management

These two settings are about this laptop, not about the driver, so they apply here exactly as they do on CachyOS. `systemctl` writes to `/etc`, which is yours on an atomic system, so both survive image updates.

{{% steps %}}

### Enable the NVIDIA power services

```bash
sudo systemctl enable nvidia-hibernate.service nvidia-suspend.service nvidia-resume.service
```

**What these services do:**
- `nvidia-hibernate.service` - Properly saves GPU state before hibernation
- `nvidia-suspend.service` - Manages GPU state during system suspend
- `nvidia-resume.service` - Restores GPU state after resume

These services prevent GPU state issues after suspend/resume cycles. Check first whether the image already enabled them:

```bash
systemctl is-enabled nvidia-suspend.service nvidia-resume.service nvidia-hibernate.service
```

### Mask `nvidia-powerd` permanently

The `nvidia-powerd.service` manages NVIDIA Dynamic Boost, which shifts extra wattage (~5-15W) from the CPU to the GPU during heavy GPU loads. While useful on Intel-based laptops, it conflicts with AMD ATPX power management on the Zephyrus G16 and causes soft lockups and "GPU has fallen off the bus" errors.

On this laptop, GPU power is managed via ATPX (AMD-driven via ACPI). The NVIDIA suspend/hibernate/resume services handle power states correctly without `nvidia-powerd`.

**What you lose by disabling it:** Minimal. Slightly fewer FPS during heavy GPU workloads. The ~5-15W Dynamic Boost is not worth the instability on AMD ATPX hardware.

```bash
sudo systemctl disable nvidia-powerd.service
sudo systemctl stop nvidia-powerd.service
sudo systemctl mask nvidia-powerd.service
```

The mask is a symlink to `/dev/null` in `/etc/systemd/system`, so a new image can ship the unit enabled and it still won't start.

**If you want to try re-enabling it later** (e.g., after a kernel or driver update that may fix the ATPX conflict):

```bash
sudo systemctl unmask nvidia-powerd.service
sudo systemctl enable --now nvidia-powerd.service
```

**Reference:**
- [NVIDIA Power Management Documentation](https://download.nvidia.com/XFree86/Linux-x86_64/610.43.02/README/powermanagement.html)

{{% /steps %}}

## Kernel and driver updates

There is nothing to rebuild. The kernel and the NVIDIA modules are built into the image together and are tested against each other before it's published, which is the main reason this page is so much shorter than its CachyOS counterpart. You don't choose the driver version either — it moves when the image moves.

If an image update does break the GPU, the previous one is still on disk:

```bash
rpm-ostree rollback
systemctl reboot
```

{{< callout type="info" >}}
Known issues and troubleshooting for the NVIDIA driver are documented on the [Known Issues]({{< relref "/docs/known-issues" >}}) page.
{{< /callout >}}

## Additional Resources

- [Bazzite documentation](https://docs.bazzite.gg/)
- [Bazzite on GitHub](https://github.com/ublue-os/bazzite)
- [NVIDIA open kernel modules](https://github.com/NVIDIA/open-gpu-kernel-modules)
- [Ryzen AI 9 HX 370 Linux Support](https://forums.linuxmint.com/viewtopic.php?t=429052)
- [Fedora Discussion: Zephyrus External Monitor Issues](https://discussion.fedoraproject.org/t/asus-zephyrus-g16-with-nvidia-and-external-monitor-crashes-every-few-minutes/147175)
