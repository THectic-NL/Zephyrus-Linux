---
title: "SteamOS & Game Mode"
weight: 1
prev: docs/virtualization/vmware-workstation
next: docs/gaming/proton-slr
---

The console experience on the Steam Deck — boot straight into Steam, controller-driven, no desktop unless you ask for one — is a thing you can have on this laptop. What you can't have is SteamOS itself.

This page is about that distinction, and about which of the two distributions gets you closest.

## You can't install SteamOS on the G16

Valve's SteamOS is built for hardware Valve ships. Two things make it a non-starter here:

- **No NVIDIA support.** SteamOS is AMD-only in practice: the graphics stack is Mesa, and there is no proprietary NVIDIA driver in the image. On a laptop whose discrete GPU is an RTX 4060, that's the end of the conversation.
- **It isn't distributed as a general-purpose installer.** The recovery images target Deck hardware, and the work Valve has done to widen that has been aimed at other handhelds, not at hybrid-graphics laptops.

People do get SteamOS booting on non-Valve hardware. On this machine it would mean giving up the discrete GPU, which defeats the point of the exercise.

So the question becomes: how close can you get to a console session on hardware SteamOS was never meant for?

{{< tabs >}}
{{< tab name="CachyOS" >}}

Close enough for most purposes, assembled yourself.

You keep a normal desktop and get the console experience on demand rather than at boot:

```bash
steam -gamepadui
```

That's Steam's Game Mode interface — the same UI as the Deck's, in a window or fullscreen. Combined with a controller it covers most of what people actually want from SteamOS.

For the real thing — a gamescope session that replaces your desktop session, so the machine boots into Steam — look at what's in the CachyOS repos rather than following an out-of-date guide:

```bash
pacman -Ss gamescope
```

CachyOS Hello also has a gaming section that installs the usual stack in one go, and is a better starting point than assembling package names from a blog post.

**Honest summary:** you'll get Game Mode. You won't get the seamless boot-to-Steam, suspend-resume-into-game, everything-just-works integration, because that integration is the part Valve builds and maintains.

{{< /tab >}}
{{< tab name="Bazzite" >}}

As close as it gets, and this is Bazzite's whole reason for existing.

The `bazzite-deck` images take Valve's Game Mode session and package it for hardware that isn't a Steam Deck: boot straight into Steam, the same gamescope session, the same controller-first UI, with a desktop one menu item away.

Switching to one is a rebase:

```bash
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/ublue-os/bazzite-deck-gnome:stable
systemctl reboot
```

`bazzite-deck-gnome` gives GNOME as the desktop you drop out to; `bazzite-deck` gives KDE. There are NVIDIA variants of the deck images as well — check the [image list](https://github.com/ublue-os/bazzite) for the current names before rebasing.

{{< callout type="warning" >}}
**This is the least-travelled path on this laptop.** The deck images are aimed at handhelds, which are AMD-only and single-GPU. The G16 is a hybrid machine where the internal panel hangs off the Radeon 890M and the RTX 4060 renders, and gamescope has to be told which is which. Expect rough edges — external displays and the discrete GPU are where they show up.

If you want a laptop that games well, stay on `bazzite-gnome-nvidia-open` and use Big Picture. If you want a console that happens to be a laptop, this is the route, and the previous image is still on disk when it doesn't work out:

```bash
rpm-ostree rollback
systemctl reboot
```
{{< /callout >}}

You do not need a deck image to game well. The regular desktop images already ship Steam, Proton, gamescope, MangoHud and the controller stack, configured. The deck images only change how you *start* — the gaming itself is the same.

{{< /tab >}}
{{< /tabs >}}

## Game Mode on hybrid graphics

Whichever route you take, the thing to understand on this laptop is which GPU is doing what.

The internal display is wired to the AMD Radeon 890M. The RTX 4060 renders and hands frames over. That's normal for a gaming laptop and it's what `asusctl armoury` is switching between — see [asusctl & ROG Control Center]({{< relref "/docs/hardware/asusctl-rog-control" >}}).

For a console-style session it matters because gamescope composites, and it needs to composite on the right device. Symptoms of getting it wrong:

| Symptom | Usually means |
|---|---|
| Game runs, terrible frame rate | Rendering on the iGPU instead of the RTX 4060 |
| Black screen on an external display | The display is on the discrete GPU, the session composites on the iGPU |
| Game Mode won't start at all | gamescope can't get the display it expects |

Before blaming Game Mode, confirm the driver is healthy in a normal desktop session:

```bash
nvidia-smi
```

If that fails, fix it first — [NVIDIA on CachyOS]({{< relref "/docs/hardware/nvidia-cachyos" >}}) or [NVIDIA on Bazzite]({{< relref "/docs/hardware/nvidia-bazzite" >}}) — because none of this works on top of a driver that isn't loading.

## Which to actually use

| You want | Do this |
|---|---|
| A laptop that games well | Either distribution, normal desktop, Steam Big Picture when you want it |
| A console that happens to be a laptop | Bazzite, deck image, and accept the hybrid-graphics rough edges |
| Actual SteamOS | Buy a Steam Deck |

The middle row is the honest one: it's achievable, it's fun, and it is not a supported configuration.

## References

- [Bazzite](https://bazzite.gg/)
- [Bazzite on GitHub](https://github.com/ublue-os/bazzite) — current image names
- [gamescope](https://github.com/ValveSoftware/gamescope)
- [SteamOS](https://store.steampowered.com/steamos)
