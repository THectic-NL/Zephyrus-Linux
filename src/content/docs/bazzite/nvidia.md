---
title: "NVIDIA Driver"
weight: 3
prev: docs/bazzite/updates
next: docs/bazzite/secure-boot
distro: bazzite
---

The G16 has an NVIDIA RTX 4060 alongside the AMD iGPU. On Bazzite the driver is not something you install. It is part of the image you booted, so the work here is picking the right image, enrolling one Secure Boot key, and checking that suspend is already taken care of.

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

See [Bazzite]({{< relref "/docs/bazzite/getting-started" >}}) for the full image list and what a rebase does. These guides assume a `-gnome-` image.

## Enroll the Secure Boot key first

The NVIDIA kernel modules are signed with Universal Blue's key. With Secure Boot on and that key not enrolled, the modules refuse to load and you land in a session without acceleration, which looks exactly like a broken driver.

```bash
ujust enroll-secure-boot-key
```

The password is `universalblue`. Full procedure, including the blue MokManager screen: [Secure Boot on Bazzite]({{< relref "/docs/bazzite/secure-boot" >}}).

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

### Confirm the open module is in use

```bash
cat /proc/driver/nvidia/version
```

The first line reads `NVIDIA UNIX Open Kernel Module` on an `-nvidia-open` image. `modinfo nvidia | grep -i license` is another way to tell: the open module reports a dual `MIT/GPL` license, the closed one reports `NVIDIA`.

{{% /steps %}}

## Power Management

The CachyOS page has a manual step here: Arch's `nvidia-utils` package ships suspend and resume handling as separate systemd units, and that page enables them by hand. Bazzite's driver is packaged by negativo17 and set up differently. With the open kernel modules, `NVreg_UseKernelSuspendNotifiers=1` lets the driver save and restore video memory on its own, so those units aren't shipped at all. It's already on. There is nothing here for you to turn on.

{{< callout type="warning" >}}
If you enable `nvidia-suspend.service` here, a step you may see in other guides including the CachyOS page in this repo, it fails with `Unit nvidia-suspend.service could not be found`. The unit isn't on this image at all. It wasn't just disabled.
{{< /callout >}}

{{% steps %}}

### Confirm the suspend override is in place

```bash
systemctl show systemd-suspend.service -p Environment
```

You should see `Environment=SYSTEMD_SLEEP_FREEZE_USER_SESSIONS=false`. That comes from `nvidia-suspend-nofreeze.conf`, a drop-in the `nvidia-driver` package installs on `systemd-suspend.service` (and the hibernate and suspend-then-hibernate units) to avoid a VT-switch deadlock during suspend.

### Confirm the driver's suspend settings

```bash
grep -E "UseKernelSuspendNotifiers|PreserveVideoMemoryAllocations|EnableS0ixPowerManagement" /proc/driver/nvidia/params
```

Expect:

```
PreserveVideoMemoryAllocations: 1
UseKernelSuspendNotifiers: 1
EnableS0ixPowerManagement: 1
```

This reads what the loaded driver actually uses, which is more reliable than a config file: newer images no longer list `NVreg_UseKernelSuspendNotifiers` in `/usr/lib/modprobe.d/nvidia.conf`, yet it's still on. The file only exists while the NVIDIA module is loaded, so check in Hybrid or Ultimate mode. In Integrated mode the dGPU is off the bus.

`NVreg_UseKernelSuspendNotifiers=1` is what replaces the separate suspend and resume units. With the open kernel modules, the driver preserves video memory through the kernel's own suspend and resume notifiers, instead of a systemd unit calling `nvidia-sleep.sh`.

{{% /steps %}}

## Kernel and driver updates

There is nothing to rebuild. The kernel and the NVIDIA modules are built into the image together and are tested against each other before it's published, which is the main reason this page is so much shorter than its CachyOS counterpart. You don't choose the driver version either; it moves when the image moves.

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
