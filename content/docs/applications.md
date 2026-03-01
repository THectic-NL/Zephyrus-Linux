---
title: "Applications"
weight: 4
prev: docs/security/yubikey
next: docs/networking/eduroam-network-installation
---

Everything I installed after the initial CachyOS setup. Organized loosely by category. Most of this is personal preference, but the Brave and libinput-config sections include non-obvious workarounds that aren't documented elsewhere.

## Package sources

On CachyOS there are three places to get software from. When looking for an application, check them in this order:

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

Native packages offer better performance and system integration. Flatpaks trade some efficiency for compatibility and sandboxing. The choice is yours per application; both work fine on CachyOS.

## Initial System Setup

### Set the hostname

Nothing special here, just set the hostname via System Settings so the machine has a proper name on the network.

![Set hostname](/images/system-info.avif)

### GNOME window buttons: adding minimize & maximize back

By default, GNOME 49 only shows the close button. One command fixes it:

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

GNOME doesn't have built-in shortcuts for the file manager or an emoji picker, so these need to be created manually. See [Smile](#smile-emoji-picker) for how the Copilot key is used.

### GNOME window focus: apps opening in the background

Apps like Signal and Discord sometimes open in the background, showing a "Your app is ready" notification instead of bringing the window to the front. Fix this with:

```bash
gsettings set org.gnome.desktop.wm.preferences focus-new-windows 'smart'
```

The default `strict` mode never focuses new windows automatically. `smart` lets GNOME decide; in practice this means newly launched apps come to the foreground as expected.

### Touchpad scroll speed: no native GNOME setting (yet)

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

I use Brave as my main browser. I started with the Flatpak version but switched to the native package, which integrates better with the system and offers better performance.

- **Native (pacman):** Better system integration, better performance. This is what I use.
- **Flatpak:** Might work better in some situations, but feels a bit more isolated.

**Installation**

[brave-bin on CachyOS packages](https://packages.cachyos.org/package/cachyos/x86_64/brave-bin): available directly in the CachyOS repo, no AUR helper needed.

```bash
sudo pacman -S brave-bin
```

![Brave official Linux install instructions](/images/brave-linux-install.avif)

Hardware acceleration works fine with current Brave and kernel versions. The crash bugs that affected Brave 1.82–1.86 are resolved. See [Known Issues]({{< relref "/docs/known-issues" >}}) for the history.

**Flatpak alternative**

If the native package causes issues:

```bash
flatpak install flathub com.brave.Browser
```


---

## Communication & Productivity

### Bitwarden

Password manager. Available via Flathub and works well.

![Bitwarden desktop app in Flathub](/images/bitwarden-flathub.avif)

### Signal Messenger

Signal is my main messaging app. The [CachyOS extra repository](https://packages.cachyos.org/package/extra/x86_64/signal-desktop) ships a native package, which is what I use and it works better than the Flatpak.

**CachyOS / Arch (recommended):**

```bash
sudo pacman -S signal-desktop
```

**Flatpak (alternative):**

```bash
flatpak install flathub org.signal.Signal
```

![Signal Messenger app in Flathub](/images/signal-flathub.avif)

### Proton Mail

Proton Mail desktop app is a wrapper around the web app rather than a native client. The [CachyOS repository](https://packages.cachyos.org/package/cachyos/any/proton-mail-bin) ships `proton-mail-bin`, which integrates more natively into the desktop than the Flatpak: better tray icon behavior, system notifications, and no Flatpak sandbox overhead.

**CachyOS / Arch (recommended):**

```bash
sudo pacman -S proton-mail-bin
```

**Flatpak (alternative):**

```bash
flatpak install flathub me.proton.Mail
```

![Proton Mail app in Flathub](/images/protonmail-flathub.avif)

### Office suites

No official Microsoft 365 client exists for Linux. Two solid alternatives cover most use cases.

#### OnlyOffice

[OnlyOffice](https://packages.cachyos.org/package/cachyos/x86_64/onlyoffice-bin) is the closest thing to Microsoft 365 on Linux. The UI is nearly identical, with Word, Excel, and PowerPoint equivalents that look and behave like the Microsoft originals. Good compatibility with `.docx`, `.xlsx`, and `.pptx` files.

```bash
sudo pacman -S onlyoffice-bin
```

![OnlyOffice running on GNOME](/images/only-office.avif)

**Missing: APA-style references**

One notable gap for academic work: OnlyOffice has no built-in citation manager or APA reference style support out of the box.

![OnlyOffice - references feature missing](/images/only-office-missing_references.avif)

There are workarounds via plugins. The [OnlyOffice help center documents reference management](https://helpcenter.onlyoffice.com/docs/userguides/plugins/InsertReferences.aspx) through integrations like Zotero or Mendeley, both citation managers that can hook into the editor. I haven't set this up myself yet, so I can't assess how well it actually works in practice.

#### LibreOffice

[LibreOffice Fresh](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/libreoffice-fresh) is the most actively developed open-source office suite and the most Linux-native option. More development effort goes into it than any alternative.

```bash
sudo pacman -S libreoffice-fresh
```

**APA references: built in**

Unlike OnlyOffice, LibreOffice has a built-in bibliography database and reference insertion. You can manage your sources and insert citations in APA format directly from the menus:

![LibreOffice bibliography manager](/images/libreoffice-bibliograpy.avif)

![LibreOffice - inserting references](/images/libreoffice-inserting_references.avif)

**Caveat: Microsoft format compatibility**

LibreOffice can open and save `.docx`/`.xlsx`/`.pptx` files, but there are known rendering differences with documents created in Microsoft Word. This comes down to how Microsoft and LibreOffice have each implemented the OpenXML standard, not always identically. For documents that stay within LibreOffice's own ODF format, there are no issues.

---

## Development

### Git & GitHub CLI

```bash
sudo pacman -S git github-cli
```

### Visual Studio Code

Two builds are available. The **Microsoft build** includes the full Microsoft extension marketplace and proprietary extensions like GitHub Copilot. The **open-source build** (`code`) removes Microsoft telemetry and branding, but proprietary extensions are not available.

**Microsoft build (recommended, full extension support):**

```bash
paru -S visual-studio-code-bin
```

Available in the [AUR](https://aur.archlinux.org/packages/visual-studio-code-bin).

**Open-source build (no Microsoft telemetry):**

```bash
sudo pacman -S code
```

Available in the [CachyOS extra repository](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/code).

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

[Archi](https://www.archimatetool.com/) is a free ArchiMate modeling tool. The Linux package is a portable archive with no installer. To make it show up in GNOME with an icon, you have to place the files yourself and create a desktop entry manually.

{{< callout type="info" >}}
Archi's download page warns about possible UI issues on Wayland. In my experience it runs fine on GNOME 49 Wayland.
{{< /callout >}}

![Archi download page - Linux version with Wayland note](/images/archi-download.avif)

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

### Podman & Podman Desktop

For container workloads I use Podman instead of Docker. Podman is daemonless, runs containers rootless by default, and ships a Docker-compatible CLI so existing workflows keep working. `podman-docker` replaces the `docker` package entirely.

All three packages are available in the CachyOS repositories: [podman](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/podman), [podman-docker](https://packages.cachyos.org/package/cachyos-extra-znver4/x86_64_v4/podman-docker), [podman-desktop](https://packages.cachyos.org/package/extra/x86_64/podman-desktop).

```bash
sudo pacman -S podman podman-docker podman-desktop
```

For the full setup — including registry configuration and connecting Docker Hub and GitHub — see [Podman & Podman Desktop]({{< relref "/docs/virtualization/podman" >}}) in the Virtualization section.

---

## Gaming & Media

### Steam

On CachyOS, Steam is available directly from the [CachyOS repository](https://packages.cachyos.org/package/cachyos/x86_64/steam), no extra repos needed.

```bash
sudo pacman -S steam
```

![Steam in GNOME Software](/images/steam-website.avif)

Reboot after installing. Steam includes Proton out of the box for running Windows games on Linux.

### Tidal

There's no official Tidal client for Linux. Two community alternatives exist.

#### High Tide (recommended)

[High Tide](https://aur.archlinux.org/packages/high-tide) is a native GTK4 frontend for Tidal, not an Electron wrapper, but an actual application built with proper Linux toolkit. It looks clean, integrates well with GNOME, and supports Hi-Fi quality.

```bash
paru -S high-tide
```

![High Tide running on GNOME](/images/high-tide.avif)

#### Tidal Hi-Fi

[Tidal Hi-Fi](https://github.com/Mastermindzh/tidal-hifi) by Rick van Lieshout is an Electron wrapper around the Tidal web player. Works, but it's essentially the web app packaged as a desktop app.

![Tidal Hi-Fi in the Flathub store](/images/tidal-hifi-flathub.avif)

---

## Utilities

### Bottles: running Windows software

[Bottles](https://usebottles.com/) lets you run Windows software via Wine. Bottles is **only officially distributed via Flatpak**; ignore any other versions you may find in the AUR or elsewhere, as they are not official and not supported by the Bottles developers.

```bash
flatpak install flathub com.usebottles.bottles
```

Alternatively, open GNOME Software Center, search for "Bottles", and make sure to select the **Flathub** source.

For anything that doesn't work under Wine (like Microsoft 365), I use a Windows VM instead. See [Windows 11 VM Setup]({{< relref "/docs/virtualization/vm-setup" >}}).

![Bottles in the Flathub store](/images/bottles-flathub.avif)

### Smile: emoji picker

[Smile](https://mijorus.it/projects/smile) by Lorenzo Paderi is a simple emoji picker for Linux with custom tags support. Available on Flathub.

```bash
flatpak install flathub it.mijorus.smile
```

![Smile emoji picker in Flathub](/images/smile-flathub.avif)

**Settings**

Enable "Run in the background" and "Minimize on exit" in Smile's settings. This keeps the picker instant and dismisses it cleanly after selecting an emoji:

![Smile settings - run in background, minimize on exit](/images/smile-settings.avif)

**GNOME extension**

Install the [Smile complementary extension](https://extensions.gnome.org/extension/6096/smile-complementary-extension/) to enable automatic emoji pasting on Wayland. Without it, Smile can only copy to clipboard.

{{< callout type="warning" >}}
In the Smile settings under "Paste emojis automatically", make sure the extension toggle is enabled after installing.
{{< /callout >}}

**Keyboard shortcut: repurposing the Copilot key**

The Copilot key on the Zephyrus G16 is otherwise useless on Linux. GNOME registers it as `Shift+Super+TouchpadOff`. Repurpose it as an emoji picker shortcut:

Go to **Settings → Keyboard → Custom Shortcuts** and add:

- **Name:** Emoji picker
- **Command:** `flatpak run it.mijorus.smile`
- **Shortcut:** press the Copilot key

![Custom shortcuts list showing Emoji picker entry](/images/smile-custom-shortcuts.avif)

![Custom shortcut dialog for Smile - Copilot key binding](/images/smile-shortcut-dialog.avif)

### Solaar for Logitech devices

[Solaar](https://github.com/pwr-Solaar/Solaar) manages Logitech keyboards, mice, and other peripherals. Available in the [CachyOS extra repository](https://packages.cachyos.org/package/extra/any/solaar).

```bash
sudo pacman -S solaar
```

![Solaar package page in the CachyOS repository](/images/solaar-docs.avif)

Runs in the system tray with battery notifications. You can also configure DPI, polling rate, and buttons from there.

![Solaar about screen - version 1.1.19](/images/solaar-about.avif)
