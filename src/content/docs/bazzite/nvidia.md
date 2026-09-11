---
title: "NVIDIA Driver"
weight: 3
prev: docs/bazzite/updates
next: docs/bazzite/secure-boot
distro: bazzite
---

The G16 has an NVIDIA RTX 4060 alongside the AMD iGPU. On Bazzite the driver is not something you install. It is part of the image you booted, so the work here is picking the right image, enrolling one Secure Boot key, and two power settings this laptop needs.

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

### `nvidia-powerd`: no longer needs masking

The `nvidia-powerd.service` manages NVIDIA Dynamic Boost, which shifts extra wattage (~5-15W) from the CPU to the GPU during heavy GPU loads. For a while, on a kernel somewhere between 6.16 and 6.17, it conflicted with AMD's ATPX power management on this laptop's iGPU+dGPU combo: the two fought over GPU power state, which could turn either GPU off and caused soft lockups and "GPU has fallen off the bus" errors. Masking the service was the standing workaround; see the [full writeup]({{< relref "/docs/known-issues" >}}) on the Known Issues page for the original symptoms.

That conflict is fixed upstream now (exact commit not pinned down). `nvidia-powerd` has been running unmasked for months without a single lockup, so there's no reason to give up Dynamic Boost anymore.

**If you masked it following an older version of this guide, or you're still on an old kernel:**

```bash
sudo systemctl unmask nvidia-powerd.service
sudo systemctl enable --now nvidia-powerd.service
```

If that brings the soft lockups back, your kernel predates the fix; mask it again and update:

```bash
sudo systemctl mask --now nvidia-powerd.service
```

**Reference:**
- [NVIDIA Power Management Documentation](https://download.nvidia.com/XFree86/Linux-x86_64/610.57.04/README/powermanagement.html)

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
