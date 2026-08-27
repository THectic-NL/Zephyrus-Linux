---
title: "Bazzite"
weight: 2
prev: docs/getting-started/cachyos
next: docs/getting-started/topgrade
---

Bazzite is a [Universal Blue](https://universal-blue.org/) image built on Fedora Atomic — plain Fedora underneath, with the gaming stack and the hardware pieces already assembled. Where CachyOS hands you a system you can take apart, Bazzite hands you a system that is deliberately hard to take apart, and correspondingly hard to break.

That makes it the one to pick for two kinds of people: gamers, because Steam, Proton and the controller stack ship configured in the image, and anyone who would rather not spend evenings tweaking an operating system.

It's worth reading this page before installing, because the parts that differ from a conventional distribution aren't cosmetic. They change how you install software and how you undo a mistake.

## What atomic actually means

{{% steps %}}

### `/usr` is read-only

The system lives on an OSTree-managed image and is mounted read-only. You cannot `dnf install` into it and you cannot drop a file into `/usr/bin`. Your configuration in `/etc` and your data in `/var` are yours; everything else belongs to the image.

### Updates replace the whole image

An update is not a set of packages, it's a new image. It's downloaded in the background and takes effect on the next boot, which means an update can never leave you halfway through.

```bash
ujust update
```

Desktop images update themselves in the background, so in practice you rarely run this by hand — mostly when you're on a TTY or over SSH. [Topgrade]({{< relref "/docs/getting-started/topgrade" >}}) can drive this together with your Flatpaks, Homebrew and containers.

### The previous image stays on disk

If an update breaks something, the version you were running is still there:

```bash
rpm-ostree rollback
systemctl reboot
```

It's also in the boot menu, which is what saves you when the problem stops you reaching a terminal. This is the single biggest practical difference with a rolling distribution.

### Layered packages need a reboot

Anything not in the image gets *layered* on top of it:

```bash
rpm-ostree install <package>
systemctl reboot
```

The reboot isn't optional — the layer is applied to the next image, not the running one. That's exactly why layering is a last resort rather than the default; see [Installing software](#installing-software) below.

### Home is `/var/home`

`/home` is a symlink to `/var/home`. Almost nothing notices, but a script with a hardcoded `/home/<user>` path, a `fstab` entry, or a container bind-mount might, and the error you get is rarely obvious. When something can't find your home directory, check whether it resolved the symlink.

### The kernel comes with the image

There's no kernel to pick and no kernel to update separately. This is the trade for not maintaining anything: you get the kernel Bazzite ships, on Bazzite's schedule. Kernel arguments still work, through `rpm-ostree kargs`:

```bash
rpm-ostree kargs --append=example=1
```

{{% /steps %}}

## Which image

Bazzite publishes a separate image per desktop and per GPU driver, and you pick one by rebasing onto it. For a G16 with the RTX 4060 the relevant choice is:

| Image | For |
|---|---|
| `bazzite-gnome-nvidia-open` | GNOME + the open NVIDIA kernel modules — **what these guides assume** |
| `bazzite-nvidia-open` | The same, with KDE Plasma instead of GNOME |
| `bazzite-gnome-nvidia` | GNOME + the proprietary driver, for pre-Turing cards |
| `bazzite-deck-gnome` | Boots straight into Steam's Game Mode, for handhelds and HTPCs |

The `-nvidia-open` images use NVIDIA's open kernel modules, which cover every card from Turing onwards. The RTX 4060 is Ada, so it qualifies, and open is the right default here.

The rest of this site is written around GNOME — the [autologin]({{< relref "/docs/security/autologin" >}}) and [YubiKey]({{< relref "/docs/security/yubikey" >}}) guides configure GDM, and several application tweaks are GNOME extensions. KDE works fine, it's just not what these pages describe.

{{< callout type="info" >}}
The ISO you download only decides where you start. Switching desktop or driver later is a rebase, not a reinstall.
{{< /callout >}}

### Rebasing onto another image

```bash
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/ublue-os/bazzite-gnome-nvidia-open:stable
systemctl reboot
```

`ostree-image-signed:` verifies the image signature. If a rebase leaves you somewhere you don't want to be, the image you came from is still on disk — `rpm-ostree rollback` and reboot.

## Secure Boot

Unlike CachyOS, Bazzite boots under Secure Boot without disabling it first, because it uses shim. It does need Universal Blue's key enrolled once, or the NVIDIA kernel modules won't load.

→ [Secure Boot on Bazzite]({{< relref "/docs/hardware/secure-boot-bazzite" >}})

## Installing software

This is where the habits from a conventional distribution have to go. Bazzite's own order of preference, most to least recommended:

{{% steps %}}

### Flatpak

The primary way to install graphical applications. Sandboxed, independent of the image, and updated separately from the system.

```bash
flatpak install flathub org.example.App
```

Bazzite ships **Bazaar** as its graphical store for these.

### Homebrew

For command-line tools. Installs into `/home/linuxbrew`, so it needs no layering and no reboot, and it doesn't touch the image at all.

```bash
brew install <tool>
```

### Distrobox

For anything that needs a real package manager, and for development environments. A distrobox container shares your home directory and can export applications to the host menu, so a tool installed in an Arch or Fedora container behaves like a locally installed one.

```bash
distrobox enter <container>
distrobox-export --app <package>
```

Bazzite ships preconfigured containers you can pick from:

```bash
ujust distrobox-assemble
```

This is the piece that does the most work on an atomic system. On CachyOS distrobox is a convenience; here it's how you get a CLI toolchain without touching the image.

### rpm-ostree layering

Last resort, for things that genuinely have to be part of the system — a driver, a kernel module, a system service.

```bash
rpm-ostree install <package>
systemctl reboot
```

Every layered package is re-applied on top of each new image, so a package that fails to build against a newer Fedora will block your updates. Keep this list short and check it now and then:

```bash
rpm-ostree status
```

{{% /steps %}}

## `ujust`

Bazzite wraps its common maintenance tasks in `ujust` recipes. To see what the installed image offers:

```bash
ujust
```

The ones that come up in these guides are `ujust update`, `ujust enroll-secure-boot-key` and `ujust distrobox-assemble`. The list depends on the image, so check it on your own install rather than assuming a recipe exists.

## Recommended setup order

{{% steps %}}

### Hardware & Drivers

The NVIDIA driver is already in the image, so this is verification plus enrolling the Secure Boot key. Then the ASUS ROG hardware features, which need `asusctl` layered from the Terra repository.

→ [NVIDIA Driver: Bazzite]({{< relref "/docs/hardware/nvidia-bazzite" >}})
→ [Secure Boot on Bazzite]({{< relref "/docs/hardware/secure-boot-bazzite" >}})
→ [asusctl & ROG Control Center]({{< relref "/docs/hardware/asusctl-rog-control" >}})
→ [Display Color Profiles]({{< relref "/docs/hardware/color-profiles" >}})

### Security & Privacy

Optionally configure GDM to skip the login screen after disk unlock. Set up the YubiKey for `sudo` and the GNOME lock screen via pam-u2f.

→ [GDM Autologin]({{< relref "/docs/security/autologin" >}})
→ [YubiKey]({{< relref "/docs/security/yubikey" >}})

### Applications

Install and configure applications. Most of them are Flatpaks and install identically on both distributions; the page marks the ones that don't.

→ [Applications]({{< relref "/docs/applications" >}})

### Networking

Get eduroam working. NetworkManager is NetworkManager, so this page is the same on both distributions.

→ [eduroam Network Installation]({{< relref "/docs/networking/eduroam-network-installation" >}})

### Virtualization

Set up a Windows 11 VM for software that doesn't run on Linux. Podman is already in the image here, which makes the container-based options the path of least resistance.

→ [Virt-Manager / KVM]({{< relref "/docs/virtualization/vm-setup" >}})
→ [Podman & Podman Desktop]({{< relref "/docs/virtualization/podman" >}})

{{% /steps %}}

## Additional Resources

- [Bazzite documentation](https://docs.bazzite.gg/)
- [Bazzite on GitHub](https://github.com/ublue-os/bazzite)
- [Universal Blue](https://universal-blue.org/)
- [Fedora Atomic Desktops documentation](https://docs.fedoraproject.org/en-US/fedora-silverblue/)
