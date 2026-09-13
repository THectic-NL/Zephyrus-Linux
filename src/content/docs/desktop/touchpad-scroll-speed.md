---
title: "Touchpad Scroll Speed"
weight: 3
prev: docs/desktop/astra-monitor
next: docs/security/autologin
---

As of GNOME 50, there is still no way to natively change trackpad scroll speed on Linux. Not in Settings, not anywhere. KDE Plasma has had this for years. The community has been asking for it for a long time too, with merge requests open in [mutter](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/1840) and [GNOME Control Center](https://gitlab.gnome.org/GNOME/gnome-control-center/-/merge_requests/991) that have gone essentially nowhere. See the [GNOME Discourse thread](https://discourse.gnome.org/t/adding-scroll-speed-setting-in-gnome/25893) for the full history.

Two third-party tools fill this gap. **wayland-scroll-factor** is the recommended option; **libinput-config** is the older system-wide alternative that's more awkward to set up.

## wayland-scroll-factor (recommended)

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

## libinput-config (alternative)

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
