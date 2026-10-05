---
title: "NVIDIA Driver"
weight: 3
prev: docs/cachyos/updates
next: docs/cachyos/secure-boot
distro: cachyos
---

The G16 has an NVIDIA RTX 4060 alongside the AMD iGPU. The RTX 4060 is Ada, so it runs on NVIDIA's open kernel modules (`nvidia-open`), which CachyOS installs by default. This is not Nouveau, and it is not something you set up.

**Driver I'm running (at the time of writing):**
- Version: 615.71.09
- CUDA Version: 13.4

## There is nothing to install

CachyOS detects the card during installation and sets up `nvidia-open` with no manual steps. By the time the installer finishes, the driver is active and configured.

That covers the driver. What's left is confirming it loaded, enrolling a Secure Boot key if you run Secure Boot, and knowing which NVIDIA services you do and don't have to touch.

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

### Suspend and resume: nothing to enable

Other guides tell you to enable `nvidia-suspend.service`, `nvidia-resume.service` and `nvidia-hibernate.service`. On `nvidia-open` you don't have to. [NVIDIA's README](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/powermanagement.html) says those units are for the proprietary driver with `NVreg_PreserveVideoMemoryAllocations=1` (or advanced CUDA features), and that with the open kernel modules saving video memory "is handled automatically if `NVreg_UseKernelSuspendNotifiers=1` is enabled". Arch's `nvidia-utils` sets exactly that in `/usr/lib/modprobe.d/nvidia-utils.conf`, so CachyOS has it on already and the units stay disabled. GDM 50 doesn't look for the units either: I found no reference to them in the GDM 50.3 package.

Check it with the dGPU awake (Hybrid or Ultimate mode), or read the config file in any mode:

```bash
grep -E "UseKernelSuspendNotifiers|PreserveVideoMemoryAllocations" /proc/driver/nvidia/params
grep -r UseKernelSuspendNotifiers /usr/lib/modprobe.d /etc/modprobe.d
```

You want `UseKernelSuspendNotifiers: 1` in the first and `NVreg_UseKernelSuspendNotifiers=1` in the second.

{{< callout type="info" >}}
**Why other guides say otherwise.** The [asus-linux.org Arch guide](https://asus-linux.org/guides/arch-guide/) and the [Open Gaming Collective Arch guide](https://opengamingcollective.github.io/asusctl/distributions/arch.html) both tell you to run `systemctl enable nvidia-suspend.service nvidia-hibernate.service nvidia-resume.service`. They don't say which driver they assume, and those units are what the proprietary module needs, so follow them if you run `nvidia-dkms` or set `NVreg_PreserveVideoMemoryAllocations=1` yourself. I found nothing saying that enabling them on `nvidia-open` breaks anything, but nothing needs them there either. Both guides also say to leave `nvidia-suspend-then-hibernate.service` alone unless you use that sleep mode, so this page doesn't enable it.
{{< /callout >}}

### nvidia-powerd (Dynamic Boost)

`nvidia-powerd` is NVIDIA's Dynamic Boost daemon, which shifts the power budget between CPU and GPU. [NVIDIA's README](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/dynamicboost.html) lists what it needs: a notebook with an Ampere or newer GPU, an AMD Renoir (or newer) or Intel Comet Lake (or newer) platform, and SBIOS support. The firmware stays in charge: Dynamic Boost "will be enabled automatically when the system firmware notifies the driver that the conditions are favorable", and on battery it can occasionally cost performance. NVIDIA, the [asus-linux.org FAQ](https://asus-linux.org/faq/graphics-switching/nvidia-dynamic-boost/) and the [Open Gaming Collective Arch guide](https://opengamingcollective.github.io/asusctl/distributions/arch.html) all enable it with `systemctl enable --now nvidia-powerd`, and asus-linux.org adds that it wants the Performance profile.

asusd looks after the battery side by itself. `disable_nvidia_powerd_on_battery` in `/etc/asusd/asusd.ron` is on by default and shows up as **Disable nvidia-powerd on battery** on ROG Control Center's GPU Configuration tab. It stops the service when you unplug. The [asusctl changelog](https://github.com/OpenGamingCollective/asusctl/blob/main/CHANGELOG.md) dates that to 4.5.6: "nvidia-powerd.service will now enable or disable depending on the AC power state".

On this laptop the service is enabled. In Integrated mode it exits right at boot with `Allocate Root client failed 0x59`, which is most likely because the dGPU is off the PCI bus then. I have not checked what it does in Hybrid or Ultimate mode, or whether this model's firmware turns Dynamic Boost on at all. NVIDIA's README says `/proc/driver/nvidia/gpus/*/power` reports Dynamic Boost support, which you can read with the dGPU awake. Dynamic Boost isn't a fix for anything, so leaving it off is fine. One reply on a [CachyOS forum thread](https://discuss.cachyos.org/t/nvidia-dynamic-boost-setup-for-notebooks/3785) reports added stutter with it on, so judge it by your own frame times. The [soft-lockup entry in Known Issues]({{< relref "/docs/known-issues" >}}) explains why people used to mask the service, and why that is no longer needed.

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
- [NVIDIA driver README: Power Management](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/powermanagement.html)
- [NVIDIA driver README: Dynamic Boost](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/dynamicboost.html)
- [Ryzen AI 9 HX 370 Linux Support](https://forums.linuxmint.com/viewtopic.php?t=429052)
- [NVIDIA vs Nouveau Performance](https://machaddr.substack.com/p/nouveau-vs-nvidia-the-battle-between)
- [Zephyrus G16 2024 Linux Guide](https://www.ehmiiz.se/blog/linux_asus_g16_2024/)
