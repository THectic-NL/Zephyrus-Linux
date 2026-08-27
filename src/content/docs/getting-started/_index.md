---
title: "Getting Started"
weight: 1
next: docs/getting-started/cachyos
---

This is my personal setup documentation for the ROG Zephyrus G16 (GA605WV). I'm not a software engineer or developer, just someone who switched to Linux and ran into a lot of things that didn't work out of the box. I figured I'd write it all down so others don't have to go through the same trial and error.

If something here helps you, great. If you run into something I haven't covered, feel free to reach out; I'm happy to think along.

## Which of the two should you run?

I've run both on this laptop for real, not as a weekend experiment, and this is the honest version of the advice I'd give in person. Decide this first — it's the one choice the rest of these guides hang off.

### Run CachyOS if you want the machine in your hands

You like knowing how the system fits together, and you'd rather have the option to change something than be protected from breaking it. You'll pick your own kernel, tune the scheduler, and install from `pacman` or the AUR without asking anyone's permission. In exchange you own the maintenance: updates are deliberate, and when one goes wrong you fix it by hand.

This is what I run day to day.

### Run Bazzite if you game, or if you'd rather not tinker at all

Bazzite is built for gaming — Steam, Proton and the controller stack are in the image, configured, before you log in for the first time. It's also the better answer if tweaking your OS is not the hobby: the system is read-only, updates arrive as a whole image, and a bad one is undone from the boot menu. It's genuinely hard to break, and that is the point.

The trade is real. You don't pick the kernel, installing anything system-level means layering and a reboot, and habits from a normal distribution have to be unlearned. If that sounds annoying rather than reassuring, you want CachyOS.

### The differences that actually show up

| | CachyOS | Bazzite |
|---|---|---|
| **Base** | Arch, rolling release | Fedora Atomic, built by [Universal Blue](https://universal-blue.org/) |
| **System files** | Writable | `/usr` is read-only; the system updates as one image |
| **Installing software** | `pacman` and the AUR, immediately | Flatpak first, then Homebrew and distrobox; `rpm-ostree` layering as a last resort, and that needs a reboot |
| **Kernel** | You pick one (CachyOS Kernel Manager) | Comes with the image |
| **Home directory** | `/home` | `/var/home`, with `/home` as a symlink to it |
| **NVIDIA driver** | Configured by the installer | Baked into the `-nvidia-open` image |
| **Gaming** | Works well, set it up yourself | The reason the distribution exists |
| **Undoing a bad update** | Downgrade packages by hand | `rpm-ostree rollback`, or pick the previous image at boot |

Both run this laptop well. Everything that matters on the G16 — the Radeon 890M, the RTX 4060, the ROG Nebula Display, `asusctl` — works on either. You are not choosing between a good option and a bad one; you're choosing how much of the machine you want to be responsible for.

{{< callout type="info" >}}
Kernel 6.19 or newer is the one thing both need. That is where the `asus-armoury` driver landed in mainline, and it is what the Ryzen AI 9 HX 370 wants. CachyOS is well past it; Bazzite carries a recent kernel in the image.
{{< /callout >}}

### What about plain Fedora?

It works fine on this laptop — nothing here is a warning against it. It's just that after testing several distributions on this specific machine, these two came out clearly ahead, so they're the two I can document from experience rather than from reading. Worth knowing that Bazzite *is* Fedora underneath, the atomic edition with the gaming and hardware pieces already assembled, so choosing it isn't really leaving Fedora behind.

These guides give commands for CachyOS and Bazzite only. There's no third set to keep correct.

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

→ [CachyOS]({{< relref "/docs/getting-started/cachyos" >}}) — you want control, and you don't mind maintaining it.
→ [Bazzite]({{< relref "/docs/getting-started/bazzite" >}}) — you game, or you'd rather the OS just stayed out of your way.

Each of those ends with the setup order I'd follow on that distribution.
