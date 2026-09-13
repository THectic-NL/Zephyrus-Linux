---
title: "Touchpad Scroll Speed"
weight: 3
prev: docs/desktop/astra-monitor
next: docs/security/autologin
---

As of GNOME 50, there is still no way to natively change trackpad scroll speed on Linux. Not in Settings, not anywhere. KDE Plasma has had this for years. The community has been asking for it for a long time too, with merge requests open in [mutter](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/1840) and [GNOME Control Center](https://gitlab.gnome.org/GNOME/gnome-control-center/-/merge_requests/991) that have gone essentially nowhere. See the [GNOME Discourse thread](https://discourse.gnome.org/t/adding-scroll-speed-setting-in-gnome/25893) for the full history.

Two third-party tools fill this gap. **wayland-scroll-factor** is the recommended option; **libinput-config** is the older system-wide alternative that's more awkward to set up.

## wayland-scroll-factor (recommended)

[wayland-scroll-factor](https://github.com/daniel-g-carrasco/wayland-scroll-factor) by daniel-g-carrasco intercepts libinput function calls inside `gnome-shell` and applies a scroll multiplier. It has its own package for both distributions now, so building it from source by hand is no longer the easiest way to get it running.

**Install:**

{{< tabs >}}
{{< tab name="CachyOS" >}}

From the AUR:

```bash
paru -S wayland-scroll-factor
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Through the project's own COPR repo, layered with `rpm-ostree`:

```bash
fedora_version="$(rpm -E %fedora)"
sudo curl -fsSL -o /etc/yum.repos.d/daniel-g-carrasco-wayland-scroll-factor.repo \
  "https://copr.fedorainfracloud.org/coprs/daniel-g-carrasco/wayland-scroll-factor/repo/fedora-${fedora_version}/daniel-g-carrasco-wayland-scroll-factor-fedora-${fedora_version}.repo"
sudo rpm-ostree refresh-md
sudo rpm-ostree install wayland-scroll-factor
systemctl reboot
```

{{< /tab >}}
{{< /tabs >}}

{{< callout type="info" >}}
Building from source is still an option, for the `-git` build (`paru -S wayland-scroll-factor-git` on CachyOS) or on a distribution without a package. It needs a C compiler, `meson`, `ninja` and `pkgconf`, none of which are installed by default on either distribution here. The project's own [dependencies](https://github.com/daniel-g-carrasco/wayland-scroll-factor/blob/main/docs/dependencies.md) and [install](https://github.com/daniel-g-carrasco/wayland-scroll-factor/blob/main/docs/install.md) docs have the exact package names and build steps.
{{< /callout >}}

**Configure:**

```bash
wsf set 0.2     # 1.0 = default speed, lower = slower; I use 0.2
wsf enable      # requires one logout/login to take effect
wsf status      # check whether it is active
```

`wsf set 0.2` covers scroll sensitivity. Pinch zoom and pinch rotate have their own factors, tunable separately with `wsf set --pinch-zoom` and `wsf set --pinch-rotate` if the default feels off.

Settings are stored in `~/.config/wayland-scroll-factor/config`. After the first `wsf enable` and re-login, `wsf set` applies live without needing another logout.

`wsf status` reports whether the preload library is actually mapped into `gnome-shell`. The path it points at depends on how you installed it: `/usr/lib/wayland-scroll-factor/` for the package, `~/.local/lib/wayland-scroll-factor/` if you built it yourself. If it still isn't picking up after a logout/login, run `wsf doctor` for a diagnosis and `wsf repair` if it reports a stale preload setup, then log out and back in once more.

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

## libinput-config (alternative)

[libinput-config](https://github.com/lz42/libinput-config) by lz42 is a system-wide workaround that requires building from source and root access. Use this if wayland-scroll-factor does not work for your setup.

{{< callout type="warning" >}}
**CachyOS only.** This installs into `/usr`, which is read-only on Bazzite. There is no clean way to do it there. Use wayland-scroll-factor above instead, which has a working install path on both distributions.
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
