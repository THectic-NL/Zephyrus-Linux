---
title: "NVIDIA Driver"
weight: 3
prev: docs/cachyos/updates
next: docs/cachyos/secure-boot
distro: cachyos
---

The G16 has an NVIDIA RTX 4060 alongside the AMD iGPU. The RTX 4060 is Ada, so it runs on NVIDIA's open kernel modules (`nvidia-open`), which CachyOS installs by default. This is not Nouveau, and it is not something you set up.

**Driver I'm running (at the time of writing):**
- Version: 610.57.04
- CUDA Version: 13.3

## There is nothing to install

CachyOS detects the card during installation and sets up `nvidia-open` with no manual steps. By the time the installer finishes, the driver is active and configured.

That covers the driver. What's left is confirming it loaded, enrolling a Secure Boot key if you run Secure Boot, and two power settings that are specific to this laptop and are *not* set for you.

## Post-Installation Verification

{{% steps %}}

### Confirm the open module is loaded

```bash
cat /proc/driver/nvidia/version
```

The first line reads `NVIDIA UNIX Open Kernel Module` on `nvidia-open`. The closed module says `NVIDIA UNIX x86_64 Kernel Module` instead.

### Check the driver and CUDA version

```bash
nvidia-smi
```

Lists the driver and CUDA versions, and confirms the card is seen.

### Check loaded kernel modules

```bash
lsmod | grep nvidia
```

If the modules are listed, the driver is loaded. If they are not and Secure Boot is on, sort out [Secure Boot]({{< relref "/docs/cachyos/secure-boot" >}}) before looking anywhere else.

{{% /steps %}}

## Power Management

{{% steps %}}

### Enable the NVIDIA power services

Enable NVIDIA power services for better suspend/resume behavior and power management:

```bash
sudo systemctl enable nvidia-hibernate.service nvidia-suspend.service nvidia-resume.service nvidia-suspend-then-hibernate.service
```

**What these services do:**
- `nvidia-hibernate.service` - Properly saves GPU state before hibernation
- `nvidia-suspend.service` - Manages GPU state during system suspend
- `nvidia-resume.service` - Restores GPU state after resume
- `nvidia-suspend-then-hibernate.service` - Same as `nvidia-suspend.service`, but for the combined suspend-then-hibernate sleep action

These services prevent GPU state issues after suspend/resume cycles.

{{% /steps %}}

## Kernel Updates

The driver is a DKMS module, so a kernel update triggers two things through pacman hooks:

1. DKMS rebuilds the NVIDIA modules against the new kernel
2. If you set up Secure Boot, sbctl re-signs the new kernel EFI image

Neither needs manual intervention. What the kernel does *not* do is enforce module signatures, which is why the NVIDIA module keeps working while marking the kernel as tainted. See [Secure Boot on CachyOS]({{< relref "/docs/cachyos/secure-boot" >}}).

{{< callout type="info" >}}
Known issues and troubleshooting for the NVIDIA driver are documented on the [Known Issues]({{< relref "/docs/known-issues" >}}) page.
{{< /callout >}}

## Additional Resources

- [CachyOS Wiki: NVIDIA](https://wiki.cachyos.org/configuration/nvidia/)
- [Arch Wiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA)
- [Ryzen AI 9 HX 370 Linux Support](https://forums.linuxmint.com/viewtopic.php?t=429052)
- [NVIDIA vs Nouveau Performance](https://machaddr.substack.com/p/nouveau-vs-nvidia-the-battle-between)
- [Zephyrus G16 2024 Linux Guide](https://www.ehmiiz.se/blog/linux_asus_g16_2024/)
