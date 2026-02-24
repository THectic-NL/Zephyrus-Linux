---
title: "News"
weight: 90
toc: false
---

## Moved to CachyOS (Arch) — the best distro for this hardware

After testing multiple distributions, I've settled on CachyOS (Arch) as my daily driver. CachyOS is an Arch-based distribution with deep hardware-specific optimizations that make it stand out for the Zephyrus G16:

- **BORE/EEVDF scheduler** — CachyOS ships with an improved CPU scheduler that provides better responsiveness and lower latency under mixed workloads
- **Improved power management** — Better handling of suspend/resume and ACPI power states on AMD+NVIDIA hybrid setups
- **Dynamic refresh rate support** — Out-of-the-box support for variable refresh rate on the ROG Nebula Display
- **Built-in iGPU and dGPU drivers** — The AMD Radeon 890M and NVIDIA RTX 4060 work correctly from a fresh install, including GPU switching via `supergfxctl`
- **ASUS Linux patches merged** — The work of [Luke Jones](https://asus-linux.org/) (asus-linux.org), including the `asus-armoury` driver and `asusctl` tooling, has been merged into CachyOS. This gives native support for ROG-specific features like fan curves, performance profiles, and the Slash LED panel

My first choice is CachyOS for this hardware. Fedora is a strong second — it came close and is also an excellent option if you prefer a more stable release cycle over rolling.

## Kernel 7.0: ASUS laptop quirks + newer AMDGPU enablement

Linus confirmed the next kernel will be 7.0, with the merge window now open and a stable release expected mid-April 2026. For this ASUS ROG G16, the headline is better graphics driver coverage: the DRM updates bring AMDGPU enablement for newer RDNA 3.5-class IP blocks (GFX11.5.4) plus ongoing NVIDIA Nova/Nouveau work, which should translate into better handling of both the iGPU and dGPU. Early expectations are that the Radeon 890M could see around a 20% uplift. CachyOS will pick this up as it ships.

**Sources:** [Linus confirms Linux 7.0](https://www.phoronix.com/news/Linux-7.0-Is-Next) · [HID laptop quirks for ASUS ROG models](https://www.phoronix.com/news/Linux-7.0-HID) · [Linux 7.0 DRM/AMDGPU updates](https://www.phoronix.com/news/Linux-7.0-Graphics-Drivers)

## Kernel 6.19: asus-armoury driver lands in mainline

The `asus-armoury` driver has been [merged into Linux 6.19](https://www.phoronix.com/news/ASUS-Armoury-Driver-Linux-6.19). This new `platform/x86` driver replaces parts of the older `asus-wmi` with a cleaner sysfs-based API, enabling panel mode switching, APU memory allocation, PPT tuning, and more directly from the kernel. The driver is entirely community-developed by [Luke Jones](https://asus-linux.org/) (ASUS Linux project), with no involvement from ASUS themselves. CachyOS ships kernel 6.19.3-2 which includes this driver and additional ASUS-specific patches.

**Before** — basic asusctl controls without Armoury settings:

![ROG Control before asus-armoury in mainline](/images/rog-control-armoury.avif)

**After** — full Armoury settings exposed, including PPT/power limit tuning:

![ROG Control System Control with Armoury settings and power limit tuning](/images/rog-control-system-control.png)

**Sources:** [Phoronix article](https://www.phoronix.com/news/ASUS-Armoury-Driver-Linux-6.19) · [Community discussion](https://www.phoronix.com/forums/forum/software/linux-gaming/1593500-asus-armoury-driver-set-to-be-introduced-in-linux-6-19) · [Patch series (lore.kernel.org)](https://lore.kernel.org/all/20251102215319.3126879-1-denis.benato@linux.dev/)
