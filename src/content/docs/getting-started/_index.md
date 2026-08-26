---
title: "Getting Started"
weight: 1
next: docs/getting-started/cachyos
---

This is my personal setup documentation for the ROG Zephyrus G16 (GA605WV). I'm not a software engineer or developer, just someone who switched to Linux and ran into a lot of things that didn't work out of the box. I figured I'd write it all down so others don't have to go through the same trial and error.

If something here helps you, great. If you run into something I haven't covered, feel free to reach out; I'm happy to think along.

## Two distributions

After testing a number of distributions on this laptop, two are worth documenting: **CachyOS** and **Bazzite**. They take opposite approaches, and which one fits you depends on how you want to run the machine rather than on which one is better.

| | CachyOS | Bazzite |
|---|---|---|
| **Base** | Arch, rolling release | Fedora Atomic, built by [Universal Blue](https://universal-blue.org/) |
| **System files** | Writable | `/usr` is read-only; the system updates as one image |
| **Installing software** | `pacman` and the AUR, immediately | Flatpak first, then Homebrew and distrobox; `rpm-ostree` layering as a last resort, and that needs a reboot |
| **Kernel** | You pick one (CachyOS Kernel Manager) | Comes with the image |
| **Home directory** | `/home` | `/var/home`, with `/home` as a symlink to it |
| **NVIDIA driver** | Configured by the installer | Baked into the `-nvidia-open` image |
| **Undoing a bad update** | Downgrade packages by hand | `rpm-ostree rollback`, or pick the previous image at boot |
| **Fits you if** | You want to tune the machine and don't mind maintaining it | You want a machine that updates itself and is hard to break |

Both run this laptop well. Everything that matters on the G16 — the Radeon 890M, the RTX 4060, the ROG Nebula Display, `asusctl` — works on either.

{{< callout type="info" >}}
Kernel 6.19 or newer is the one thing both need. That is where the `asus-armoury` driver landed in mainline, and it is what the Ryzen AI 9 HX 370 wants. CachyOS is well past it; Bazzite carries a recent kernel in the image.
{{< /callout >}}

## How these guides are organised

Most of what follows applies to both distributions and lives on one page, with a tab around the parts that differ:

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S example
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub org.example.App
```

{{< /tab >}}
{{< /tabs >}}

The tabs are synced: pick your distribution once and every other tab on the page follows.

A few topics work so differently that a shared page would only obscure things. Those get a page per distribution — installing the system, the NVIDIA driver and Secure Boot. They are clearly labelled and listed side by side in the sidebar.

## Pick your starting point

→ [CachyOS]({{< relref "/docs/getting-started/cachyos" >}}) — Arch-based and rolling. Pick your own kernel and scheduler, tune what you like.
→ [Bazzite]({{< relref "/docs/getting-started/bazzite" >}}) — Fedora Atomic. Read-only system, image updates, rollback from the boot menu.

Each of those ends with the setup order I'd follow on that distribution.
