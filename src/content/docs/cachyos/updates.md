---
title: "Updating"
weight: 2
prev: docs/cachyos/getting-started
next: docs/cachyos/nvidia
distro: cachyos
---

The system update is one command:

```bash
sudo pacman -Syu
```

It's a rolling distribution, so that *is* the update — there is no release to move to. Everything `pacman` installs into `/usr` is usable the moment it finishes; only a new kernel needs a reboot.

If an update breaks something, you roll back by hand: reinstall the previous package from the cache in `/var/cache/pacman/pkg/`, or pull it from the [Arch Linux Archive](https://archive.archlinux.org/). Worth knowing before you need it.

## The kernel

CachyOS ships the **CachyOS Kernel Manager** as a pre-installed GUI. It manages installed kernels and configures the `sched-ext` scheduler — the kernel's framework for swapping in a userspace CPU scheduler.

I run `scx_lavd` with the profile set to **Auto**. LAVD (Latency-criticality Aware Virtual Deadline) is built for mixed interactive and compute workloads, which fits a laptop used for both daily work and gaming. The scheduler can be changed at any time without a reboot.

![CachyOS Kernel Manager - Configure sched-ext with scx_lavd](/images/cachyos-kernel-manager-sched-ext.avif)

## Everything else, in one go

The system is only part of it. There are also the Flatpaks, whatever Homebrew put in your home directory, the distrobox containers, the firmware, and a handful of tools that update themselves. [Topgrade](https://github.com/topgrade-rs/topgrade) runs all of them in sequence and tells you what it did.

It's a convenience, not a package manager. Everything it does you could do by hand; the value is that you stop forgetting the Flatpaks for three weeks.

### What it runs here

Topgrade detects what's on the system rather than being told. On this laptop that's roughly:

| Step | What it runs |
|---|---|
| System packages | `pacman`, through your AUR helper if you have one, so the AUR is included |
| Flatpak | `flatpak update` |
| Firmware | `fwupdmgr` |
| Containers | pulls newer images for the containers you have |
| Distrobox | updates inside each container |
| Language tools | `cargo`, `rustup`, `npm`, `pipx` and friends, if present |

### Install

```bash
sudo pacman -S topgrade
```

If it isn't in the repos on your install, the AUR has both `topgrade` and `topgrade-bin`.

### Running it

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

`--dry-run` is worth doing once on a new install — it prints the steps it detected, which is the quickest way to find out that it isn't picking something up.

### Configuration

The config file is created on first run at `~/.config/topgrade.toml`.

The setting worth having on this laptop is skipping firmware, because `fwupdmgr` on the G16 wants a reboot into the firmware updater and that is rarely what you want mid-update:

```toml
[misc]
disable = ["firmware"]

# Keep going when one step fails instead of stopping the run
ignore_failures = ["containers"]

# Don't ask before each step
assume_yes = true
```

Point it at your AUR helper so the AUR is included rather than skipped:

```toml
[linux]
arch_package_manager = "paru"
```

## References

- [Topgrade on GitHub](https://github.com/topgrade-rs/topgrade)
- [Topgrade: configuration reference](https://github.com/topgrade-rs/topgrade/blob/main/config.example.toml)
- [Arch Linux Archive](https://archive.archlinux.org/)
