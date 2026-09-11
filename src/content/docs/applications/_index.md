---
title: "Applications"
weight: 6
prev: docs/security/yubikey
next: docs/applications/browser
---

Everything I installed after the initial system setup. Organized by category, with dedicated pages for each tool and workflow.

Most of these applications are Flatpaks and install identically on both distributions. Where an install command differs, both options are shown.

## Package sources

Where you get software from is the biggest day-to-day difference between the two distributions, so it's worth reading your tab before exploring the applications.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Three places, in this order:

1. **[CachyOS packages](https://packages.cachyos.org/)**: CachyOS's own repository, built on top of Arch. Packages here are optimized for modern CPUs (x86-64-v3/v4) and include CachyOS-specific patches. Install with `sudo pacman -S <package>`.

2. **[AUR](https://aur.archlinux.org/)** (Arch User Repository): community-maintained build scripts for software not in the official repos. Install with an AUR helper like `paru -S <package>`. Quality varies per package but the AUR covers almost everything.

3. **[Flathub](https://flathub.org/)**: Flatpak packages that bundle all their own dependencies. Install with `flatpak install flathub <app-id>`, run with `flatpak run <app-id>`.

**Native (pacman/paru) vs Flatpak: which to choose?**

| | Native (pacman/paru) | Flatpak |
|---|---|---|
| **Performance** | Better (uses shared system libraries) | Slightly worse (bundles own libraries) |
| **Integration** | Tight (full system access) | Sandboxed (more isolated) |
| **Size** | Smaller | Larger |
| **Compatibility** | Depends on distro | Consistent across distros |
| **Security** | Standard | Better sandboxing |

Native packages offer better performance and system integration. Flatpaks trade some efficiency for compatibility and sandboxing. The choice is yours per application; both work fine here.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Four places, and the order matters more than on CachyOS. It's Bazzite's own order of preference, from most to least recommended:

1. **[Flathub](https://flathub.org/)**: the primary way to install graphical applications. `flatpak install flathub <app-id>`. Bazzite ships **Bazaar** as the graphical store for these.

2. **[Homebrew](https://brew.sh/)**: for command-line tools. `brew install <tool>`. Installs into `/home/linuxbrew`, so no layering and no reboot.

3. **[Distrobox](https://distrobox.it/)**: for anything that needs a real package manager, and for development environments. `distrobox enter <container>`, then that container's own package manager. `distrobox-export --app <package>` puts a graphical app from the container in your host menu.

4. **`rpm-ostree` layering**: last resort, for things that must be part of the system: drivers, kernel modules, PAM modules, system services. Needs a reboot, and every layered package is re-applied on top of each new image.

**Which to choose?**

| | Flatpak | Homebrew | Distrobox | Layering |
|---|---|---|---|---|
| **Reboot needed** | No | No | No | Yes |
| **Survives image updates** | Yes | Yes | Yes | Re-applied each time |
| **Good for** | GUI apps | CLI tools | Toolchains, dev environments | System-level pieces |
| **Isolation** | Sandboxed | None | Container | None |
| **Can break an update** | No | No | No | Yes |

The last column is the one to keep in mind. A Flatpak that fails is a broken app; a layered package that fails to build against a newer Fedora blocks the whole system update. Keep `rpm-ostree status` short.

{{< /tab >}}
{{< /tabs >}}

## Initial System Setup

### Set the hostname

Nothing special here, just set the hostname via System Settings so the machine has a proper name on the network.

![Set hostname](/images/system-info.avif)

### GNOME window buttons: adding minimize & maximize back

By default, GNOME 50 only shows the close button. One command fixes it:

```bash
gsettings set org.gnome.desktop.wm.preferences button-layout 'appmenu:minimize,maximize,close'
```

![Example of how the new GNOME windows look](/images/window-controls.avif)

### GNOME keyboard shortcuts: making it feel more like Windows

Coming from Windows, some things feel off without the right shortcuts. These are the ones I set up to make the transition smoother.

**Built-in shortcuts (via Settings > Keyboard > Keyboard Shortcuts):**

| # | Action | Shortcut |
|---|--------|----------|
| 1 | Show desktop (hide all windows) | `Super+D` |
| 2 | Take a screenshot interactively | `Shift+Super+S` |
| 3 | Record a screencast interactively | `Shift+Super+R` |
| 4 | Open Settings | `Super+I` |

**Custom shortcut (via Settings > Keyboard > Keyboard Shortcuts > Custom Shortcuts):**

| # | Action | Command | Shortcut |
|---|--------|---------|----------|
| 5 | Open file manager | `nautilus` | `Super+E` |
| 6 | Emoji picker | `flatpak run it.mijorus.smile` | Copilot key |

GNOME doesn't have built-in shortcuts for the file manager or an emoji picker, so these need to be created manually. See [Smile](/docs/applications/utilities/#smile-emoji-picker) for how the Copilot key is used.

### GNOME window focus: apps opening in the background

By default, GNOME won't bring a newly opened window to the front. Instead, it queues it in the background and shows a notification saying the app is ready. The reasoning is fair: don't interrupt what you're already doing. In practice it's mostly just annoying.

There is a `gsettings` key that's supposed to control this:

```bash
gsettings set org.gnome.desktop.wm.preferences focus-new-windows 'smart'
```

The default is `strict` (never auto-focus new windows). `smart` is supposed to let GNOME decide and bring new windows to the front. In practice, **this alone is not reliable**. Windows still end up minimized in the background in many cases, because the underlying issue is that apps need to implement the [XDG Activation protocol](https://wayland.app/protocols/xdg-activation-v1) to properly request focus, and many don't. The GNOME Shell dev blog has [a thorough write-up](https://blogs.gnome.org/shell-dev/2024/09/20/understanding-gnome-shells-focus-stealing-prevention/) on why this is fundamentally broken for a large part of the app ecosystem.

The fix that actually works is applying **both** settings together: the `gsettings` key above, plus enabling **Window Demands Attention Focus** in the [Just Perfection](https://gitlab.gnome.org/jrahmatzadeh/just-perfection) GNOME Shell extension. In its **Behavior** tab:

![Just Perfection extension settings panel, Behavior tab](/images/just-perfection-panel.avif)

![Just Perfection: Window Demands Attention Focus setting enabled](/images/just-perfection-window-raise.avif)

Using Just Perfection alone without the `gsettings` change may still leave edge cases. Using only `gsettings` is not enough for apps that don't implement the activation protocol. Both together covers the vast majority of cases.

### Touchpad scroll speed: still no native GNOME setting

As of GNOME 50, there is still no way to natively change trackpad scroll speed on Linux. Not in Settings, not anywhere. KDE Plasma has had this for years. The community has been asking for it for a long time too, with merge requests open in [mutter](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/1840) and [GNOME Control Center](https://gitlab.gnome.org/GNOME/gnome-control-center/-/merge_requests/991) that have gone essentially nowhere. See the [GNOME Discourse thread](https://discourse.gnome.org/t/adding-scroll-speed-setting-in-gnome/25893) for the full history.

Two third-party tools fill this gap. **wayland-scroll-factor** is the recommended option; **libinput-config** is the older system-wide alternative that's more awkward to set up.

#### wayland-scroll-factor (recommended)

[wayland-scroll-factor](https://github.com/daniel-g-carrasco/wayland-scroll-factor) by daniel-g-carrasco is a user-level tool that intercepts libinput function calls inside `gnome-shell` and applies a scroll multiplier. No root access required; everything lives in your home directory.

**Install:**

```bash
git clone https://github.com/daniel-g-carrasco/wayland-scroll-factor.git
cd wayland-scroll-factor
meson setup build --prefix="$HOME/.local"
ninja -C build
meson install -C build
cd ..
rm -rf wayland-scroll-factor
```

{{< callout type="info" >}}
**On Bazzite:** the result lands in `$HOME/.local`, which is fine, but the build needs a toolchain and `libinput` headers, and the library it produces is preloaded into the *host's* `gnome-shell`. Build it in a Fedora distrobox of the same release as your image, or layer the build dependencies:

```bash
rpm-ostree install meson ninja-build gcc libinput-devel
systemctl reboot
```

A container built against a different Fedora release can produce a library `gnome-shell` refuses to load.
{{< /callout >}}

**Configure:**

```bash
wsf set 0.2     # 1.0 = default speed, lower = slower; I use 0.2
wsf enable      # requires one logout/login to take effect
wsf status      # check whether it is active
```

Settings are stored in `~/.config/wayland-scroll-factor/config`. After the first `wsf enable` and re-login, `wsf set` applies live without needing another logout.

When everything is working, `wsf status` confirms the library is injected into gnome-shell:

```
gnome-shell LD_PRELOAD: ~/.local/lib/wayland-scroll-factor/libwsf_preload.so (includes WSF)
gnome-shell library mapped: yes
runtime config reload: active (factor changes should apply live)
```

If the status shows the env file is present but systemd hasn't picked it up yet, run `systemctl --user daemon-reexec` and log out/in once.

**Optional GUI** (`wsf-gui`, requires libadwaita ≥ 1.4):

```bash
wsf-gui
```

Lets you adjust vertical and horizontal scroll speed separately, along with pinch zoom and pinch rotate. The System integration toggle maps to `wsf enable`/`wsf disable`.

![Wayland Scroll Factor GUI showing scroll sensitivity sliders](/images/wayland-scroll-factor-gui.avif)

**Rollback:**

```bash
wsf disable
```

#### libinput-config (alternative)

[libinput-config](https://github.com/lz42/libinput-config) by lz42 is a system-wide workaround that requires building from source and root access. Use this if wayland-scroll-factor does not work for your setup.

{{< callout type="warning" >}}
**CachyOS only.** This installs into `/usr`, which is read-only on Bazzite. There is no clean way to do it there. Use wayland-scroll-factor above, which stays inside your home directory.
{{< /callout >}}

**Install (one-time):**

```bash
sudo pacman -S meson ninja libinput git

git clone https://github.com/lz42/libinput-config.git
cd libinput-config
meson setup build
ninja -C build
sudo ninja -C build install
cd ..
rm -rf libinput-config
```

**Configuration:**

```bash
sudo tee /etc/libinput.conf >/dev/null << 'EOF'
override-compositor=enabled
scroll-factor=0.25
discrete-scroll-factor=1.0
EOF
```

Log out and back in, then adjust `scroll-factor` to your liking.

**Rollback:**

```bash
sudo rm /etc/libinput.conf
```
