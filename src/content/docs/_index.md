---
title: ""
weight: 1
toc: false
---

# My Linux setup

This is how I like Linux, written down so I can rebuild it quickly and so you can build the same one. It is built around the one laptop I own, the ROG Zephyrus G16 (GA605WV), and covers the two distributions I'd recommend on it: **CachyOS** and **Bazzite**.

It is opinionated. These are my favorite settings and the software I actually use, not a survey of every option, and most of it is turned into a setup window. If something here helps you, good. If you run into something I haven't covered, get in touch.

## Set up a machine like mine

{{< cards >}}
  {{< card link="/docs/setup-script" title="Setup script" subtitle="A checklist that shows what is done and what is open on your machine, and sets up my recommended defaults, with a guide link for every step." >}}
{{< /cards >}}

## What is specific to this laptop

You don't need this exact model. Only the pages about the laptop's own hardware are specific to the G16. Everything else works on any machine.

| Specific to the Zephyrus G16 | Works on any machine |
|---|---|
| [asusctl & ROG Control Center]({{< relref "/docs/hardware/asusctl-rog-control" >}}), [display color profiles]({{< relref "/docs/hardware/color-profiles" >}}), [MT7925 Wi-Fi tuning]({{< relref "/docs/networking/mt7925-wifi-performance" >}}), the brightness fix in [Known Issues]({{< relref "/docs/known-issues" >}}) | [GNOME desktop]({{< relref "/docs/desktop" >}}), [security]({{< relref "/docs/security" >}}), [applications]({{< relref "/docs/applications" >}}), [virtualization]({{< relref "/docs/virtualization" >}}), [gaming]({{< relref "/docs/gaming" >}}), [eduroam]({{< relref "/docs/networking/eduroam-network-installation" >}}) |

## Pick a distribution first

The rest of these guides follow from this one choice. Each distribution has its own pages for installing it, the NVIDIA driver, Secure Boot and updating. The switcher at the top of every page moves you between the two.

{{< cards >}}
  {{< card link="/docs/cachyos/getting-started" title="CachyOS" subtitle="Arch, rolling. You want the machine in your hands and don't mind maintaining it." >}}
  {{< card link="/docs/bazzite/getting-started" title="Bazzite" subtitle="Fedora Atomic. You game, or you'd rather the OS stayed out of your way." >}}
{{< /cards >}}

Everything that doesn't depend on the distribution (eduroam, the YubiKey, GNOME tweaks, the VM setup, applications) is in the shared sections below and works on both.

## Which of the two should you run?

I've run both on this laptop for real, not as a weekend experiment. This is the version of the advice I'd give in person.

**Run CachyOS if you want the machine in your hands.** You like knowing how the system fits together, and you'd rather be able to change something than be protected from breaking it. You pick your own kernel, tune the scheduler, and install from `pacman` or the AUR without asking anyone. In exchange you own the maintenance. Updates are deliberate, and when one goes wrong you fix it by hand.

**Run Bazzite if you game, or if you'd rather not tinker.** Steam, Proton and the controller stack ship in the image, already configured, before you first log in. It's also the better answer if tweaking your OS is not the hobby: the system is read-only, updates arrive as a whole image, and a bad one is undone from the boot menu. It's hard to break, which is the point. The trade is real. You don't pick the kernel, installing anything system-level means layering and a reboot, and habits from a normal distribution have to be unlearned. If that sounds annoying rather than reassuring, you want CachyOS.

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

Both run this laptop well. Everything that matters on the G16 (the Radeon 890M, the RTX 4060, the ROG Nebula Display, `asusctl`) works on either. You're not choosing between a good option and a bad one. You're choosing how much of the machine you want to be responsible for.

{{< callout type="info" >}}
Kernel 6.19 or newer is the one thing both need. That's where the `asus-armoury` driver landed in mainline, and it's what the Ryzen AI 9 HX 370 wants. CachyOS is well past it; Bazzite carries a recent kernel in the image.
{{< /callout >}}

### What about plain Fedora?

It works fine on this laptop. Nothing here is a warning against it. After testing several distributions on this specific machine, these two came out clearly ahead, so they're the two I can document from experience rather than from reading. Bazzite *is* Fedora underneath, the atomic edition with the gaming and hardware pieces already assembled, so choosing it isn't really leaving Fedora behind.

## They trade places

I haven't picked one and stopped looking. I've daily-driven both on this laptop and switched back and forth more than once. These days CachyOS is my daily driver, mostly because some of what I do wants that bit of extra system control, but I used to dual-boot Bazzite on the same machine and went back to it out of curiosity now and then, running it for a while before switching back. Neither one stays ahead for long.

It comes in waves. One month Bazzite lands a kernel bump or a Mesa fix and it's the smoother of the two. A month later CachyOS ships a scheduler change or an `asusctl` update and the lead flips back. The gap is never large and it never lasts, because the parts that matter get backported either way. A fix that lands in one distribution's kernel, or in mainline, is usually in the other within a release or two. Give it a few weeks and they're level again.

So don't overthink it. Pick the one whose trade-offs fit how you want to use the machine, not the one that looks two patches ahead this week. If you decide later that you chose wrong, moving across is a reinstall and an afternoon, and everything in these guides covers both.
