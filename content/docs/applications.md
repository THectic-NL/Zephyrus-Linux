---
title: "Applications"
weight: 25
---

Everything I installed after the initial CachyOS setup. Organized loosely by category. Most of this is personal preference, but the Brave and libinput-config sections include non-obvious workarounds that aren't documented elsewhere.

## Initial System Setup

### Set the hostname

Nothing special — just set the hostname via System Settings so the machine has a proper name on the network.

![Set hostname](/images/system-info.avif)

### GNOME window buttons — adding minimize & maximize back

By default, GNOME 49 only shows the close button. One command fixes it:

```bash
gsettings set org.gnome.desktop.wm.preferences button-layout 'appmenu:minimize,maximize,close'
```

![Example of how the new GNOME windows look](/images/window-controls.avif)

### GNOME keyboard shortcuts — making it feel more like Windows

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

GNOME doesn't have a built-in shortcut for the file manager, so this one needs to be created manually.

### Touchpad scroll speed — no native GNOME setting (yet)

As of GNOME 49, there is simply **no native setting** for touchpad scroll speed anywhere in the Settings panel. KDE Plasma has had this for years. There are merge requests open in [mutter](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/1840) and [GNOME Control Center](https://gitlab.gnome.org/GNOME/gnome-control-center/-/merge_requests/991) to add it, but they've been sitting there for years. See the [GNOME Discourse thread](https://discourse.gnome.org/t/adding-scroll-speed-setting-in-gnome/25893) for context.

[libinput-config](https://github.com/lz42/libinput-config) by lz42 is a third-party workaround that intercepts libinput events and applies a scroll multiplier.

**Install (one-time):**

```bash
# 1. Install dependencies
sudo pacman -S meson ninja libinput git

# 2. Clone libinput-config
git clone https://github.com/lz42/libinput-config.git
cd libinput-config

# 3. Build
meson setup build
ninja -C build

# 4. Install system-wide
sudo ninja -C build install

# 5. Cleanup (optional)
cd ..
rm -rf libinput-config
```

**Configuration for slower touchpad scroll:**

```bash
sudo tee /etc/libinput.conf >/dev/null << 'EOF'
# libinput-config configuration
override-compositor=enabled

# Make touchpad scroll slower (lower = slower)
# Default: 1.0, tested value: 0.25
scroll-factor=0.25

# Keep mouse wheel behavior normal
discrete-scroll-factor=1.0
EOF
```

Log out and back in (or reboot), then adjust `scroll-factor` to your liking.

**Rollback:**

```bash
sudo rm /etc/libinput.conf
```

---

## Browser

### Brave

I use Brave as my main browser. I started with the Flatpak version but switched to the native package — the RPM version feels more native and offers better performance. There's a catch though: Brave 1.82+ has two crash bugs on GNOME Wayland that need workarounds before it's actually stable.

- **Native (pacman):** More native feel, better performance. This is what I use.
- **Flatpak:** Might work better in some situations, but feels a bit more isolated.

**Installation**

{{< callout type="warning" >}}
On CachyOS/Arch with GNOME + Wayland, Brave 1.82+ has two known crash bugs that require workarounds. The first is applied via the desktop entry; the second requires a setting in `brave://flags`.
{{< /callout >}}

```bash
sudo pacman -S brave-bin
```

![Brave install instructions](/images/brave-install.avif)

**Workaround 1: patch the desktop entry**

Copy the system desktop entry to your user directory so it doesn't get overwritten by updates:
```bash
sudo cp /usr/share/applications/brave-browser.desktop ~/.local/share/applications/
```

Patch all three `Exec=` lines with the flag:
```bash
sed -i \
  's|Exec=/usr/bin/brave-browser-stable %U|Exec=/usr/bin/brave-browser-stable --disable-features=WaylandWpColorManagerV1 %U|' \
  ~/.local/share/applications/brave-browser.desktop

sed -i \
  's|Exec=/usr/bin/brave-browser-stable$|Exec=/usr/bin/brave-browser-stable --disable-features=WaylandWpColorManagerV1|' \
  ~/.local/share/applications/brave-browser.desktop

sed -i \
  's|Exec=/usr/bin/brave-browser-stable --incognito$|Exec=/usr/bin/brave-browser-stable --incognito --disable-features=WaylandWpColorManagerV1|' \
  ~/.local/share/applications/brave-browser.desktop
```

Verify it worked — you should see exactly three `Exec=` lines:
```bash
grep "^Exec" ~/.local/share/applications/brave-browser.desktop
```

**What this flag actually does (as far as I understand it):**

`--disable-features=WaylandWpColorManagerV1` — Brave 1.82+ introduced some Wayland color management extension that apparently conflicts with the AMD amdgpu driver on GNOME Wayland. Without this flag, Brave triggers GPU ring timeouts that crash the entire GNOME Shell session.

**A note on `--ozone-platform=x11`:** I tried this flag as a workaround for a crash when opening or downloading Bitwarden attachments. It turned out to cause a worse problem: gnome-shell crashing with `SIGABRT` (`g_assertion_message_expr` in `meta_window_unmanage`), triggered during Picture-in-Picture video — the same underlying mutter crash documented in [gnome-mutter issue #4625](https://gitlab.gnome.org/GNOME/mutter/-/issues/4625). That takes down the entire desktop session and requires a hard reboot. The flag is gone. Brave now runs on native Wayland. The Bitwarden attachment crash still exists, but a Brave crash is preferable to losing the whole session.

**Workaround 2: disable hardware video decode in `brave://flags`**

{{< callout type="warning" >}}
Hardware video decode still causes crashes even with the flag above. As long as the AMD VCN decoder is active, GNOME Shell crashes with SIGABRT — reproducible during Picture-in-Picture video. See [gnome-mutter issue #4625](https://gitlab.gnome.org/GNOME/mutter/-/issues/4625). Hardware video decode is **not yet stable** on the AMD Radeon 890M with GNOME Wayland.
{{< /callout >}}

Go to `brave://flags` and disable:

- **Hardware-accelerated video decode** → `Disabled`

![Brave flags — hardware video decode disabled](/images/brave-flags.avif)

Video now decodes in software. After this, `brave://gpu` will show:

- `Video Decode: Software only. Hardware acceleration disabled`
- `Video Encode: Software only. Hardware acceleration disabled`

![Brave hardware acceleration config](/images/brave-gpu-config.avif)

**Flatpak alternative**

If the native package gives you trouble:

```bash
flatpak install flathub com.brave.Browser
```

![Brave Flatpak in Flathub](/images/brave-flathub.avif)

---

## Communication & Productivity

### Bitwarden

Password manager. Available via Flathub and works well.

![Bitwarden desktop app in Flathub](/images/bitwarden-flathub.avif)

### Signal Messenger

Signal is my main messaging app. Officially only supported on Debian/Ubuntu, but the Flatpak version works fine on CachyOS.

![Signal Messenger app in Flathub](/images/signal-flathub.avif)

### Proton Mail

Proton Mail desktop app is a wrapper around the web app rather than a native client. Works fine and shows up in the app launcher like any other app.

![Proton Mail app in Flathub](/images/protonmail-flathub.avif)

---

## Development

### Git & GitHub CLI

```bash
sudo pacman -S git github-cli
```

### Visual Studio Code

```bash
sudo pacman -S code
```

{{< callout type="warning" >}}
On kernel 6.18.x/6.19.x, VS Code hardware acceleration can trigger an amdgpu page fault causing a full system freeze. Disable hardware acceleration by adding to `~/.config/Code/User/settings.json`:
```json
{
    "disable-hardware-acceleration": true
}
```
See the [NVIDIA Driver Installation Guide]({{< relref "/docs/hardware/nvidia-driver-installation" >}}) Known Issues section for details.
{{< /callout >}}

### Kleopatra & GPG commit signing

I sign my Git commits and tags with a GPG key. Kleopatra makes generating and managing keys straightforward via a GUI instead of having to figure out the GPG command line.

After installing VS Code and Git, install Kleopatra and create your keys there. Then configure Git to use them:

```bash
git config --global user.name "YOUR_NAME"
git config --global user.email "YOUR_EMAIL"
git config --global user.signingkey YOUR_GPG_KEY_ID
git config --global commit.gpgsign true
git config --global tag.gpgsign true
git config --global gpg.program gpg
```

To find your key ID:
```bash
gpg --list-secret-keys --keyid-format=long
```
Use the ID from the `sec` line (e.g., `rsa4096/YOUR_GPG_KEY_ID`).

### Archi (ArchiMate modeling tool)

[Archi](https://www.archimatetool.com/) is a free ArchiMate modeling tool. The Linux package is a portable archive — no installer. To make it show up in GNOME with an icon, you have to place the files yourself and create a desktop entry manually.

{{< callout type="info" >}}
Archi's download page warns about possible UI issues on Wayland. In my experience it runs fine on GNOME 49 Wayland.
{{< /callout >}}

![Archi download page — Linux version with Wayland note](/images/archi-download.avif)

```bash
# Download and extract
cd /tmp
curl -L https://github.com/archimatetool/archi.io/releases/download/5.7.0/Archi-Linux64-5.7.0.tgz | tar -xz

# Move to /opt
sudo mv Archi-Linux64-5.7.0/Archi /opt/

# Cleanup
rm -rf Archi-Linux64-5.7.0
cd ~

# Create symlink so you can run 'archi' from the terminal
sudo ln -s /opt/Archi/Archi /usr/local/bin/archi
```

Create a desktop entry so Archi shows up in GNOME:
```bash
sudo nano /usr/share/applications/archi.desktop
```

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Archi
Comment=ArchiMate Modelling Tool
Exec=/opt/Archi/Archi
Icon=/opt/Archi/plugins/com.archimatetool.editor_5.7.0.202509230807/img/app-128.png
Terminal=false
Categories=Development;IDE;
StartupWMClass=Archi
```

After saving, Archi appears in the GNOME app launcher:

![Archi in the GNOME application launcher](/images/archi-launcher.avif)

![Archi running on Wayland with GNOME 49](/images/archi-running.avif)

---

## Gaming & Media

### Steam

On CachyOS, Steam is available directly from the `multilib` repository — no extra repos needed.

```bash
sudo pacman -S steam
```

![Steam in GNOME Software](/images/steam-gnome-software.avif)

Reboot after installing. Steam includes Proton out of the box for running Windows games on Linux.

{{< callout type="info" >}}
If Steam won't launch, try running it from the terminal with:
```bash
__GL_CONSTANT_FRAME_RATE_HINT=3 steam
```
{{< /callout >}}

### Tidal Hi-Fi

There's no official Tidal client for Linux. [Tidal Hi-Fi](https://github.com/Mastermindzh/tidal-hifi) by Rick van Lieshout is a community-made Electron wrapper around the Tidal web player, with Hi-Fi and Max quality support.

![Tidal Hi-Fi in the Flathub store](/images/tidal-hifi-flathub.avif)

---

## Utilities

### Bottles — running Windows software

[Bottles](https://usebottles.com/) lets you run Windows software via Wine. Install from Flathub — version 61 or newer.

- Open GNOME Software Center, search for "Bottles", select the **Flathub** source

For anything that doesn't work under Wine — like Microsoft 365 — I use a Windows VM instead. See [Windows 11 VM Setup]({{< relref "/docs/virtualization/vm-setup" >}}).

![Bottles in the Flathub store](/images/bottles-flathub.avif)

### Solaar for Logitech devices

[Solaar](https://github.com/pwr-Solaar/Solaar) manages Logitech keyboards, mice, and other peripherals. Version 1.1.19 or newer.

```bash
sudo pacman -S solaar
```

![Solaar in GNOME Software](/images/solaar-flathub.avif)

Runs in the system tray with battery notifications. You can also configure DPI, polling rate, and buttons from there.

![Solaar about screen — version 1.1.19](/images/solaar-about.avif)
