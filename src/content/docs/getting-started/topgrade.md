---
title: "Topgrade"
weight: 3
prev: docs/getting-started/bazzite
next: docs/hardware/nvidia-cachyos
---

Updating this laptop is never one command. There's the system packages, the Flatpaks, whatever Homebrew put in your home directory, the distrobox containers, the firmware, and a handful of tools that update themselves. [Topgrade](https://github.com/topgrade-rs/topgrade) runs all of them in sequence and tells you what it did.

It's a convenience, not a package manager. Everything it does you could do by hand; the value is that you stop forgetting the Flatpaks for three weeks.

## What it actually runs here

Topgrade detects what's on the system rather than being told. On this laptop that means roughly:

{{< tabs >}}
{{< tab name="CachyOS" >}}

| Step | What it runs |
|---|---|
| System packages | `pacman` (through your AUR helper if you have one, so the AUR is included) |
| Flatpak | `flatpak update` |
| Firmware | `fwupdmgr` |
| Containers | pulls newer images for the containers you have |
| Distrobox | updates inside each container |
| Language tools | `cargo`, `rustup`, `npm`, `pipx` and friends, if present |

The system step is the one that matters most: it's a rolling distribution, so this is the update.

{{< /tab >}}
{{< tab name="Bazzite" >}}

| Step | What it runs |
|---|---|
| System image | `rpm-ostree upgrade`, and `bootc upgrade` where bootc is in use |
| Flatpak | `flatpak update` |
| Homebrew | `brew upgrade` |
| Distrobox | updates inside each container |
| Firmware | `fwupdmgr` |
| Language tools | `cargo`, `npm`, `pipx` and friends, if present |

Topgrade recognises Bazzite by name — it reads `VARIANT` from `/etc/os-release` and treats Bazzite, Bluefin, Aurora, Silverblue and Kinoite as one family — so it reaches for `rpm-ostree` rather than trying to `dnf` its way into a read-only `/usr`.

{{< callout type="warning" >}}
The system step here **stages an image and does not apply it**. Topgrade finishing is not the same as being up to date; you're up to date after the next reboot. That's `rpm-ostree`'s behaviour, not a Topgrade quirk, and it's the single most confusing thing about running Topgrade on an atomic system.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

## Install

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S topgrade
```

If it isn't in the repos on your install, the AUR has both `topgrade` and `topgrade-bin`.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Topgrade is a single command-line binary, so Homebrew — no layering, no reboot, and it updates itself along with everything else it manages:

```bash
brew install topgrade
```

Do **not** layer it with `rpm-ostree`. A tool whose whole job is to run updates has no business being part of the image it updates.

{{< /tab >}}
{{< /tabs >}}

## Running it

```bash
topgrade
```

That's the whole interface. Useful flags:

```bash
topgrade --dry-run          # show what would run, run nothing
topgrade --only system      # just the system packages
topgrade --disable firmware # skip a step for this run
topgrade -y                 # don't ask before each step
```

`--dry-run` is worth doing once on a new install. It prints the steps it detected, which is the quickest way to find out that it isn't picking something up.

## Configuration

The config file is created on first run at `~/.config/topgrade.toml`.

The setting worth having on this laptop is skipping firmware, because `fwupdmgr` on the G16 wants a reboot into the firmware updater and that is rarely what you want mid-update:

```toml
[misc]
disable = ["firmware"]
```

Other things that earn their place:

```toml
[misc]
# Keep going when one step fails instead of stopping the run
ignore_failures = ["containers"]

# Don't ask before each step
assume_yes = true
```

{{< tabs >}}
{{< tab name="CachyOS" >}}

Point it at your AUR helper so the AUR is included rather than skipped:

```toml
[linux]
arch_package_manager = "paru"
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Nothing distribution-specific is needed — the `rpm-ostree` step is picked up automatically.

If you'd rather Topgrade left the system image alone and only handled the layers above it (Flatpaks, Homebrew, containers), disable the system step and keep using `ujust update` for the image:

```toml
[misc]
disable = ["system"]
```

That's a reasonable split: the image updates itself in the background anyway.

{{< /tab >}}
{{< /tabs >}}

## Is it worth it?

{{< tabs >}}
{{< tab name="CachyOS" >}}

Yes, and it's where Topgrade earns the most. Updates are yours to run, they come from four or five different places, and forgetting one of them is how you end up with a Flatpak six months behind the system it's running on.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Less than on CachyOS, honestly. The image updates itself in the background, `ujust update` already covers the image plus Flatpaks plus distrobox, and the staged-not-applied behaviour above means Topgrade's output is easier to misread here.

It's still useful if you lean on Homebrew and containers, since those are outside what `ujust update` touches. If you don't, `ujust update` is enough and this page is optional.

{{< /tab >}}
{{< /tabs >}}

## References

- [Topgrade on GitHub](https://github.com/topgrade-rs/topgrade)
- [Topgrade: configuration reference](https://github.com/topgrade-rs/topgrade/blob/main/config.example.toml)
- [rpm-ostree documentation](https://coreos.github.io/rpm-ostree/)
