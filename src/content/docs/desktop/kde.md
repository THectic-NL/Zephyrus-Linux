---
title: "KDE Plasma"
weight: 1
prev: docs/hardware/color-profiles
next: docs/desktop/astra-monitor
---

Everything else on this site is written for GNOME. This page is the exception: what changes if you'd rather run KDE Plasma on the G16, and — more importantly — which of the other guides stop applying if you do.

Plasma is a reasonable choice on this laptop. Fractional scaling on the 2560x1600 panel is better handled than on GNOME, the variable refresh rate toggle is in Settings rather than behind an experimental flag, and touchpad scroll speed is a slider instead of [a third-party tool you build yourself]({{< relref "/docs/applications" >}}).

## Getting to Plasma

This is where the two distributions differ most, and it's a good illustration of the difference between them generally.

{{< tabs >}}
{{< tab name="CachyOS" >}}

A desktop environment is a set of packages, so you install one:

```bash
sudo pacman -S plasma-meta kde-applications-meta sddm
```

`plasma-meta` is the desktop, `kde-applications-meta` is the KDE application set (drop it if you only want the desktop), and `sddm` is Plasma's display manager.

Switch the display manager over:

```bash
sudo systemctl disable gdm
sudo systemctl enable sddm
sudo reboot
```

GNOME is still installed and still on the session list at the login screen, so you can switch back per session without uninstalling anything. That's the upside; the downside is two desktops' worth of packages and two sets of default applications on one system.

{{< callout type="info" >}}
CachyOS also publishes a KDE edition of its ISO. On a fresh install that's cleaner than layering Plasma onto a GNOME install — you get their Plasma configuration and theming rather than the stock Arch one.
{{< /callout >}}

{{< /tab >}}
{{< tab name="Bazzite" >}}

You don't install a desktop here. The desktop is part of the image, and KDE is the *default* one — the GNOME images are the variants with `-gnome` in the name.

So switching to Plasma is a rebase:

```bash
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/ublue-os/bazzite-nvidia-open:stable
systemctl reboot
```

That's `bazzite-gnome-nvidia-open` → `bazzite-nvidia-open`: same NVIDIA setup, KDE instead of GNOME.

{{< callout type="info" >}}
This is the atomic model working the way it's meant to. You are not adding a second desktop to your system, you're replacing the system with one that has a different desktop — and the old image stays on disk, so `rpm-ostree rollback` puts GNOME back if you don't like it. Nothing in your home directory is touched either way.
{{< /callout >}}

Layering `plasma-workspace` on top of a GNOME image would technically work and is the wrong move: you'd carry a desktop's worth of packages through every image update, for something a rebase does cleanly.

{{< /tab >}}
{{< /tabs >}}

## What stops applying

Several guides on this site configure GNOME specifically. On Plasma:

| Guide | On KDE Plasma |
|---|---|
| [GDM Autologin]({{< relref "/docs/security/autologin" >}}) | Doesn't apply. SDDM is the display manager; autologin is configured in `/etc/sddm.conf.d/` or through **System Settings → Startup and Shutdown → Login Screen (SDDM)** |
| [YubiKey]({{< relref "/docs/security/yubikey" >}}) | The `sudo` and polkit parts apply unchanged. The lock screen part does not: edit `/etc/pam.d/kde` rather than `/etc/pam.d/gdm-password` |
| Touchpad scroll speed | Not needed. **System Settings → Mouse & Touchpad** has a scroll speed slider, which is the whole reason that section of the applications page exists |
| GNOME window buttons, focus, keyboard shortcuts | Not applicable. All of it is in System Settings, and the Windows-like defaults those sections chase are mostly Plasma's defaults already |
| Smile (emoji picker) | Not needed. `Meta+.` opens Plasma's built-in emoji picker |
| Astra Monitor | GNOME Shell extension, so no. Plasma has system monitor widgets built in |

Everything else — the NVIDIA driver, Secure Boot, `asusctl`, eduroam, the virtualization pages, the applications that aren't GNOME tweaks — is unaffected. None of it cares which desktop is drawing the windows.

## The G16 specifically

- **Fractional scaling** works on Wayland without an experimental flag. **System Settings → Display & Monitor**; 125% or 150% is the sane range on a 16" 2560x1600 panel.
- **Variable refresh rate** is a per-display setting under Display & Monitor rather than something you enable globally.
- **The Slash LED, fan curves and GPU switching** are `asusctl` and `asusd`, which are desktop-agnostic. `rog-control-center` is a Qt application, so if anything it looks more at home here.
- **Hybrid graphics** behaves the same. Plasma's Application Launcher offers "Launch using Discrete Graphics Card" on the right-click menu, which is a nicer front end for the same `prime-run` behaviour.

## References

- [KDE Plasma](https://kde.org/plasma-desktop/)
- [Arch Wiki: KDE](https://wiki.archlinux.org/title/KDE)
- [Arch Wiki: SDDM](https://wiki.archlinux.org/title/SDDM)
- [Bazzite documentation](https://docs.bazzite.gg/)
