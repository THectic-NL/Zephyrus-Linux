---
title: "Updating"
weight: 2
prev: docs/bazzite/getting-started
next: docs/bazzite/nvidia
distro: bazzite
---

An update on Bazzite is a whole new image, not a set of packages. It downloads in the background and takes effect on the next boot, so it can never leave you halfway through.

```bash
ujust update
```

Desktop images update themselves in the background, so in practice you rarely run this by hand. Mostly you run it from a TTY or over SSH. `ujust update` covers the image, the Flatpaks and the distrobox containers in one go.

If an update breaks something, the previous image is still on disk:

```bash
rpm-ostree rollback
systemctl reboot
```

It's in the boot menu too, which is what saves you when the problem stops you reaching a terminal. This is the biggest practical difference with a rolling distribution.

## Staged, not applied

```bash
rpm-ostree status
```

`rpm-ostree upgrade` (and `bootc upgrade`, where bootc is in use) stages the next image. You are not up to date when the command finishes. You are up to date after the next reboot. That is how `rpm-ostree` works, and it's the most confusing thing about updating an atomic system.

## Everything else, in one go

`ujust update` handles the image, Flatpaks and distrobox. What it doesn't touch is Homebrew and any containers you set up yourself. [Topgrade](https://github.com/topgrade-rs/topgrade) covers all of it in sequence and tells you what it did.

### What it runs here

| Step | What it runs |
|---|---|
| System image | `rpm-ostree upgrade`, and `bootc upgrade` where bootc is in use |
| Flatpak | `flatpak update` |
| Homebrew | `brew upgrade` |
| Distrobox | updates inside each container |
| Firmware | `fwupdmgr` |
| Language tools | `cargo`, `npm`, `pipx` and friends, if present |

Topgrade recognises Bazzite by name. It reads `VARIANT` from `/etc/os-release` and treats Bazzite, Bluefin, Aurora, Silverblue and Kinoite as one family, so it reaches for `rpm-ostree` rather than trying to `dnf` its way into a read-only `/usr`.

{{< callout type="warning" >}}
The system step stages an image and does not apply it. Topgrade finishing is not the same as being up to date. You're up to date after the next reboot.
{{< /callout >}}

### Install

Topgrade is a single command-line binary, so use Homebrew. No layering, no reboot, and it updates itself along with everything else it manages:

```bash
brew install topgrade
```

Don't layer it with `rpm-ostree`. A tool whose whole job is to run updates has no business being part of the image it updates.

### Running it

```bash
topgrade
```

Useful flags:

```bash
topgrade --dry-run          # show what would run, run nothing
topgrade --only system      # just the system image
topgrade --disable firmware # skip a step for this run
topgrade -y                 # don't ask before each step
```

### Configuration

The config file is created on first run at `~/.config/topgrade.toml`.

Skip firmware. `fwupdmgr` on the G16 wants a reboot into the firmware updater, which is rarely what you want mid-update:

```toml
[misc]
disable = ["firmware"]
ignore_failures = ["containers"]
assume_yes = true
```

If you'd rather Topgrade left the system image alone and only handled the layers above it (Flatpaks, Homebrew, containers), disable the system step and keep using `ujust update` for the image:

```toml
[misc]
disable = ["system", "firmware"]
```

That's a reasonable split. The image updates itself in the background anyway.

### Is it worth it?

Less than on CachyOS. The image updates itself, `ujust update` already covers image plus Flatpaks plus distrobox, and the staged-not-applied behaviour makes Topgrade's output easy to misread here. It earns its place if you lean on Homebrew and self-made containers. If you don't, `ujust update` is enough.

## References

- [Topgrade on GitHub](https://github.com/topgrade-rs/topgrade)
- [rpm-ostree documentation](https://coreos.github.io/rpm-ostree/)
- [Bazzite documentation](https://docs.bazzite.gg/)
