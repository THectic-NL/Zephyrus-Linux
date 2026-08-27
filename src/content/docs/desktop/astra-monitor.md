---
title: "Astra Monitor"
weight: 2
prev: docs/desktop/kde
next: docs/security/autologin
---

[Astra Monitor](https://github.com/AstraExt/astra-monitor) is a GNOME Shell extension that puts CPU, memory, disk, network and GPU readouts in the top panel, with a dropdown for the details. On a laptop with two GPUs and a fan curve you actually care about, having the numbers permanently visible is more useful than it sounds.

The reason it's worth a page rather than a line on the applications page is that it monitors **both** GPUs on this machine — the Radeon 890M and the RTX 4060 — side by side, which is exactly what you want when you're trying to work out whether something is actually running on the discrete card.

## Requirements

GNOME Shell 45 or newer, so both distributions as documented here are fine.

The extension works with no dependencies at all. Everything below is optional and each one unlocks a specific readout — decide which you want before installing, particularly on Bazzite where each one costs a reboot.

| Dependency | Gives you | Worth it on the G16? |
|---|---|---|
| **Libgtop** | More accurate CPU, memory and process data | Yes — this is the one to install |
| **amdgpu_top** | Radeon 890M monitoring | Yes, if you want iGPU numbers |
| **nvidia-smi** | RTX 4060 monitoring | Already present with the NVIDIA driver |
| **Nethogs** | Network usage per process | Only if you want per-process network |

## Install the extension

{{< tabs >}}
{{< tab name="CachyOS" >}}

Through Extension Manager, either from the repos or from Flathub:

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
GNOME extensions live in `~/.local/share/gnome-shell/extensions/`, which is your home directory, not the image. So the extension itself survives image updates and rebases without any layering — it's only the optional dependencies below that touch the system.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

## Optional dependencies

### Libgtop

The one to install. Without it the extension falls back to reading `/proc` directly, which works but gives it less to go on.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S libgtop
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Check first — GNOME itself uses libgtop, so it's often already in the image:

```bash
rpm -q libgtop2
```

If it isn't there, this is a system library that the extension loads through GObject introspection, so it has to be layered:

```bash
rpm-ostree install libgtop2-devel
systemctl reboot
```

The `-devel` package is what upstream documents: it carries the introspection typelib the extension needs, not just headers.

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

Nothing to do. `nvidia-smi` ships with the driver on both — it's what the [NVIDIA]({{< relref "/docs/hardware/nvidia-cachyos" >}}) pages have you run to check the driver loaded. If Astra Monitor shows no NVIDIA section, the driver isn't loaded, and that's a driver problem rather than an extension one.

### Nethogs

Per-process network figures. It needs elevated privileges to inspect traffic, which is worth knowing before you install it.

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

## Configuration worth changing

Open the extension's settings from Extension Manager, or from the dropdown's gear icon.

- **Turn off what you don't watch.** The default enables most sensors. On a laptop panel there isn't room for all of them, and each one is a poll interval.
- **Set the update interval per sensor.** The default is frequent enough to show up in `powertop`. Slowing the disk and network sensors to a few seconds costs nothing you'll notice.
- **Pick which GPU is primary** under the GPU section. With two of them the panel readout has to choose; the RTX 4060 is the more interesting one when you're checking whether a game or a CUDA job actually landed there.
- **Compact mode** if you run other extensions in the panel — the default layout is wide.

{{< callout type="warning" >}}
A panel monitor polls continuously by definition, so it is not free on battery. If you're chasing idle drain, this is one of the first things to check with `powertop`, alongside the [`asusctl` power profile]({{< relref "/docs/hardware/asusctl-rog-control" >}}).
{{< /callout >}}

## On KDE Plasma

Not applicable — it's a GNOME Shell extension. Plasma has system monitor widgets built in; add one to the panel from the widget list. See [KDE Plasma]({{< relref "/docs/desktop/kde" >}}).

## References

- [Astra Monitor on GitHub](https://github.com/AstraExt/astra-monitor)
- [Astra Monitor on extensions.gnome.org](https://extensions.gnome.org/extension/6682/astra-monitor/)
- [amdgpu_top](https://github.com/Umio-Yasuno/amdgpu_top)
