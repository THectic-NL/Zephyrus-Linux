---
title: "NVIDIA Driver: CachyOS"
weight: 1
prev: docs/getting-started/topgrade
next: docs/hardware/nvidia-bazzite
---

The G16 has an NVIDIA RTX 4060 alongside the AMD iGPU. The open-source Nouveau driver doesn't perform well on modern NVIDIA hardware, so proprietary drivers are necessary.

**Driver I'm running (at the time of writing):**
- Version: 610.43.02
- CUDA Version: 13.3

## There is nothing to install

CachyOS automatically detects your hardware during installation and sets up the NVIDIA driver without any manual steps. No selection required; by the time the installer finishes, the driver is already active and fully configured.

That covers the driver itself. What's left is confirming it loaded, and two power management settings that are specific to this laptop and are *not* set for you.

## Post-Installation Verification

{{% steps %}}

### Verify NVIDIA driver

Check the driver status:

```bash
nvidia-smi
```

You should see the NVIDIA driver and CUDA versions listed.

### Check loaded kernel modules

```bash
lsmod | grep nvidia
```

If the modules are listed, the driver is loaded and functional.

{{% /steps %}}

## Power Management

{{% steps %}}

### Enable the NVIDIA power services

Enable NVIDIA power services for better suspend/resume behavior and power management:

```bash
sudo systemctl enable nvidia-hibernate.service nvidia-suspend.service nvidia-resume.service
```

**What these services do:**
- `nvidia-hibernate.service` - Properly saves GPU state before hibernation
- `nvidia-suspend.service` - Manages GPU state during system suspend
- `nvidia-resume.service` - Restores GPU state after resume

These services prevent GPU state issues after suspend/resume cycles.

### Mask `nvidia-powerd` permanently

The `nvidia-powerd.service` manages NVIDIA Dynamic Boost, which shifts extra wattage (~5-15W) from the CPU to the GPU during heavy GPU loads. While useful on Intel-based laptops, it conflicts with AMD ATPX power management on the Zephyrus G16 and causes soft lockups and "GPU has fallen off the bus" errors.

On this laptop, GPU power is managed via ATPX (AMD-driven via ACPI). The NVIDIA suspend/hibernate/resume services handle power states correctly without `nvidia-powerd`.

**What you lose by disabling it:** Minimal. Slightly fewer FPS during heavy GPU workloads. The ~5-15W Dynamic Boost is not worth the instability on AMD ATPX hardware.

```bash
sudo systemctl disable nvidia-powerd.service
sudo systemctl stop nvidia-powerd.service
sudo systemctl mask nvidia-powerd.service
```

Masking creates a symlink to `/dev/null`, preventing any process — including a driver update through `pacman` — from re-enabling the service.

**If you want to try re-enabling it later** (e.g., after a kernel or driver update that may fix the ATPX conflict):

```bash
sudo systemctl unmask nvidia-powerd.service
sudo systemctl enable --now nvidia-powerd.service
```

**Reference:**
- [NVIDIA Power Management Documentation](https://download.nvidia.com/XFree86/Linux-x86_64/610.43.02/README/powermanagement.html)

{{% /steps %}}

## Kernel Updates

The driver is a DKMS module, so a kernel update triggers two things through pacman hooks:

1. DKMS rebuilds the NVIDIA modules against the new kernel
2. If you set up Secure Boot, sbctl re-signs the new kernel EFI image

Neither needs manual intervention. What the kernel does *not* do is enforce module signatures, which is why the NVIDIA module keeps working while marking the kernel as tainted — see [Secure Boot on CachyOS]({{< relref "/docs/hardware/secure-boot-cachyos" >}}).

{{< callout type="info" >}}
Known issues and troubleshooting for the NVIDIA driver are documented on the [Known Issues]({{< relref "/docs/known-issues" >}}) page.
{{< /callout >}}

## Additional Resources

- [CachyOS Wiki: NVIDIA](https://wiki.cachyos.org/configuration/nvidia/)
- [Arch Wiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA)
- [Ryzen AI 9 HX 370 Linux Support](https://forums.linuxmint.com/viewtopic.php?t=429052)
- [NVIDIA vs Nouveau Performance](https://machaddr.substack.com/p/nouveau-vs-nvidia-the-battle-between)
- [Zephyrus G16 2024 Linux Guide](https://www.ehmiiz.se/blog/linux_asus_g16_2024/)
