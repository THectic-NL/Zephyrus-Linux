---
title: "Distrobox"
weight: 5
prev: docs/virtualization/podman
next: docs/virtualization/vmware-workstation
---

[Distrobox](https://distrobox.it/) runs another distribution's userspace in a container that is tightly integrated with your session: same home directory, same user, same X/Wayland display, and applications can be exported into your host menu. It uses [Podman]({{< relref "/docs/virtualization/podman" >}}) underneath.

It is not a VM and not a sandbox. A distrobox container shares your home directory and runs as you — it's a way to get a *different distribution's packages*, not a way to isolate anything from yourself.

How much this matters depends entirely on which distribution you're on.

{{< tabs >}}
{{< tab name="CachyOS" >}}

A convenience. You already have `pacman` and the AUR, which covers nearly everything, so distrobox is for the exceptions: a tool that only ships a `.deb`, a project that needs an older toolchain than the rolling one, or a build environment you'd rather not have on the host.

Useful, occasionally. You can go months without it.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Core infrastructure. `/usr` is read-only, layering is a last resort and costs a reboot, and Homebrew only covers so much — so when you need a real package manager, distrobox *is* the answer. It's third in Bazzite's own order of preference, above layering, and in practice it carries most development work.

If you're coming from a conventional distribution, this is the habit to build. "I'll just install it on the host" is the instinct to unlearn.

{{< /tab >}}
{{< /tabs >}}

## Install

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S distrobox podman
```

Podman is covered in more detail on [its own page]({{< relref "/docs/virtualization/podman" >}}).

{{< /tab >}}
{{< tab name="Bazzite" >}}

Nothing to install. Distrobox and Podman are both in the image:

```bash
distrobox version
```

{{< /tab >}}
{{< /tabs >}}

## Creating a container

```bash
distrobox create --name arch --image archlinux:latest
distrobox enter arch
```

First entry takes a moment — it sets up your user inside the container and wires up the home directory. After that it's a shell.

Images worth having:

| Image | For |
|---|---|
| `archlinux:latest` | The AUR, and anything documented for Arch |
| `fedora:latest` | Matches Bazzite's base; the least surprising choice there |
| `ubuntu:24.04` | Software that only ever ships a `.deb` |
| `debian:stable` | Older, stable toolchains |

{{< tabs >}}
{{< tab name="CachyOS" >}}

An Arch container is mostly redundant here — you're already on Arch. Reach for Ubuntu or Debian instead, which is where distrobox actually earns its place on this distribution.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Bazzite ships preconfigured container definitions, which is less typing and gets you images that are already set up for this:

```bash
ujust distrobox-assemble
```

Pick from the list. An **Arch** container is the interesting one here: it gives you `pacman` and the AUR on an atomic Fedora system, which is a genuinely odd and genuinely useful thing to have.

{{< /tab >}}
{{< /tabs >}}

## Exporting applications

A container is only useful if you don't have to think about it. Exporting puts a launcher on the host that enters the container for you.

```bash
# From inside the container
distrobox-export --app <application>
distrobox-export --bin /usr/bin/<command>
```

`--app` adds the application to your desktop menu. `--bin` puts a wrapper in `~/.local/bin`, so the command works from a host terminal as if it were installed there.

To undo:

```bash
distrobox-export --delete --app <application>
```

This is what makes the arrangement liveable: after exporting, a tool installed in an Ubuntu container behaves like any other application in your launcher.

## Housekeeping

```bash
distrobox list
distrobox stop <name>
distrobox rm -f <name>
```

Containers are meant to be disposable. If one gets into a state you can't explain, delete it and make a new one — that's cheaper than debugging it, and your home directory is untouched either way.

{{< callout type="warning" >}}
Because the home directory is shared, a container can write your dotfiles. A container that rewrites `~/.bashrc`, or a language toolchain that installs into `~/.local`, affects the host and every other container too. It's the most common surprise with distrobox, and it's a consequence of the design rather than a bug.

Keep per-project state inside the project directory, and be deliberate about anything that writes to `~`.
{{< /callout >}}

## On Bazzite specifically

- **`/var/home`.** Your home directory is `/var/home/<user>` with `/home` a symlink to it. Distrobox handles this, but a script inside a container that hardcodes `/home/<user>` may not. If a path "doesn't exist" inside a container while clearly existing outside it, this is why.
- **What still belongs on the host.** Anything the kernel or the login session has to load — drivers, kernel modules, PAM modules, system services — cannot come from a container. That's what layering is for, and it's why [`asusctl`]({{< relref "/docs/hardware/asusctl-rog-control" >}}) and `pam-u2f` are layered rather than containerised.
- **Homebrew first for plain CLI tools.** If a tool is a single binary with no system integration, `brew install` is simpler than a container. Distrobox is for when you need a distribution's package manager, not for every command-line program.

## References

- [Distrobox](https://distrobox.it/)
- [Distrobox on GitHub](https://github.com/89luca89/distrobox)
- [Bazzite: Distrobox](https://docs.bazzite.gg/Installing_and_Managing_Software/Distrobox/)
