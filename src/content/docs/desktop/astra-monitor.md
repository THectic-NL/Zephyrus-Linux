---
title: "Astra Monitor"
weight: 1
prev: docs/hardware/color-profiles
next: docs/security/autologin
---

[Astra Monitor](https://github.com/AstraExt/astra-monitor) is a GNOME Shell extension that puts CPU, memory, disk, network and GPU readouts in the top panel, with a dropdown for the details.

It gets its own page because it monitors both GPUs on this machine, the Radeon 890M and the RTX 4060, side by side. That is what you want when you are checking whether something is actually running on the discrete card.

## Requirements

GNOME Shell 45 or newer, so both distributions here are fine.

The extension has no hard dependencies. Everything below is optional, and each one adds one readout. Decide which you want before installing, especially on Bazzite where each one costs a reboot.

| Dependency | Gives you | On the G16 |
|---|---|---|
| **Libgtop** | More accurate CPU, memory and process data | Install it |
| **amdgpu_top** | Radeon 890M monitoring | Install it if you want iGPU numbers |
| **nvidia-smi** | RTX 4060 monitoring | Already there with the NVIDIA driver |
| **Nethogs** | Network usage per process | Only if you need per-process network |

## Install the extension

{{< tabs >}}
{{< tab name="CachyOS" >}}

Through Extension Manager, from the repos or from Flathub:

```bash
sudo pacman -S extension-manager
```

```bash
flatpak install flathub com.mattjakeman.ExtensionManager
```

Open it, search for "Astra Monitor", install. Or install from [extensions.gnome.org](https://extensions.gnome.org/extension/6682/astra-monitor/) in a browser.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Extension Manager is a Flatpak, so nothing is layered for the extension itself:

```bash
flatpak install flathub com.mattjakeman.ExtensionManager
```

Open it, search for "Astra Monitor", install. Or install from [extensions.gnome.org](https://extensions.gnome.org/extension/6682/astra-monitor/) in a browser.

{{< callout type="info" >}}
GNOME extensions live in `~/.local/share/gnome-shell/extensions/`, which is your home directory, not the image. The extension itself survives image updates and rebases without layering. Only the optional dependencies below touch the system.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

## Optional dependencies

### Libgtop

Without it the extension reads `/proc` directly, which works but gives it less to go on.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S libgtop
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

GNOME itself uses libgtop, so check first:

```bash
rpm -q libgtop2
```

If it is not there, it has to be layered. The extension loads it through GObject introspection, so it needs the package that carries the typelib:

```bash
rpm-ostree install libgtop2-devel
systemctl reboot
```

The `-devel` package is what upstream documents. It carries the introspection typelib the extension needs, not just headers.

{{< /tab >}}
{{< /tabs >}}

### amdgpu_top (Radeon 890M)

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S amdgpu_top
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
rpm-ostree install amdgpu_top
systemctl reboot
```

{{< /tab >}}
{{< /tabs >}}

### nvidia-smi (RTX 4060)

Nothing to do. `nvidia-smi` ships with the driver on both distributions. If Astra Monitor shows no NVIDIA section, the driver is not loaded, which is a driver problem, not an extension one. See the [NVIDIA]({{< relref "/docs/cachyos/nvidia" >}}) page.

### Nethogs

Per-process network figures. It needs elevated privileges to inspect traffic.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S nethogs
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
rpm-ostree install nethogs
systemctl reboot
```

{{< /tab >}}
{{< /tabs >}}

## Settings worth changing

Open the extension's settings from Extension Manager, or from the dropdown's gear icon.

- **Turn off sensors you don't watch.** The default enables most of them. Each one is a poll interval, and a laptop panel has no room for all of them anyway.
- **Slow down the disk and network sensors.** A few seconds is fine for those and shows up less in `powertop`.
- **Pick the primary GPU** under the GPU section. With two of them the panel has to choose one. The RTX 4060 is usually the one you want to see.
- **Compact mode** if you run other panel extensions. The default layout is wide.

{{< callout type="warning" >}}
A panel monitor polls continuously, so it is not free on battery. If you are chasing idle drain, check this with `powertop` alongside the [`asusctl` power profile]({{< relref "/docs/hardware/asusctl-rog-control" >}}).
{{< /callout >}}

## References

- [Astra Monitor on GitHub](https://github.com/AstraExt/astra-monitor)
- [Astra Monitor on extensions.gnome.org](https://extensions.gnome.org/extension/6682/astra-monitor/)
- [amdgpu_top](https://github.com/Umio-Yasuno/amdgpu_top)
