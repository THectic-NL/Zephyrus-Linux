---
title: "Utilities"
weight: 5
prev: docs/applications/gaming-media
next: docs/networking/eduroam-network-installation
---

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

[Solaar](https://github.com/pwr-Solaar/Solaar) manages Logitech keyboards, mice, and other peripherals.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Available in the [CachyOS extra repository](https://packages.cachyos.org/package/extra/any/solaar).

```bash
sudo pacman -S solaar
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub io.github.pwr_solaar.solaar
```

Solaar talks to the receiver over HID, so the Flatpak needs the udev rules on the host to grant your user access to the device. Those rules ship with the image; if Solaar starts but sees no devices, that's the thing to check.

{{< /tab >}}
{{< /tabs >}}

![Solaar package page in the CachyOS repository](/images/solaar-docs.avif)

Runs in the system tray with battery notifications. You can also configure DPI, polling rate, and buttons from there.

![Solaar about screen - version 1.1.19](/images/solaar-about.avif)

### LocalSend

[LocalSend](https://localsend.org/) is an open-source, cross-platform file sharing app. I use it to transfer files between my Samsung S24 Ultra and the Zephyrus. If you're coming from Windows or Android, it's essentially the open-source equivalent of Quick Share: it discovers devices on the local network and transfers files directly, no cloud involved.

The one thing it can't do is transfer files across different networks. Quick Share could route transfers through Google/Samsung's cloud when sender and receiver were on separate networks, but that was mobile-only. Desktop Quick Share was unreliable enough that it was rarely worth using anyway. Speed-wise, LocalSend is slightly slower, but not noticeably so in practice.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Available natively in the [CachyOS package repository](https://packages.cachyos.org/package/cachyos/x86_64/localsend), built specifically for CachyOS. No AUR needed, which is a real plus.

```bash
sudo pacman -S localsend
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub org.localsend.localsend_app
```

{{< /tab >}}
{{< /tabs >}}

The app shows up in the GNOME launcher after installing. Open it and it auto-discovers other LocalSend instances on your network.

<img src="/images/localsend-desktop.avif" width="700" alt="LocalSend running on the desktop">

<img src="/images/localsend-cachyos-package.avif" width="600" alt="LocalSend in the CachyOS package repository">

**Firewall rules**

LocalSend uses port 53317 (TCP and UDP) for both device discovery and file transfer. If you have a firewall active, you need to open this port.

**ufw:**

```bash
sudo ufw allow 53317/tcp comment "LocalSend-App"
sudo ufw allow 53317/udp comment "LocalSend-App"
```

**firewalld:**

```bash
sudo firewall-cmd --permanent --add-port=53317/tcp
sudo firewall-cmd --permanent --add-port=53317/udp
sudo firewall-cmd --reload
```

The Android app works the same way. Open it on your phone and it immediately appears as a discovered device on the desktop side, and vice versa.

<img src="/images/localsend-android-1.avif" width="320" alt="LocalSend on Android (Samsung S24 Ultra)">

Selecting files is straightforward. Pick what you want to send, choose the target device, and the transfer starts.

<img src="/images/localsend-android-2.avif" width="320" alt="LocalSend on Android - selecting files to send">

<img src="/images/localsend-android-3.avif" width="320" alt="LocalSend on Android - transfer in progress">

### Mission Center: GNOME-native task manager

[Mission Center](https://missioncenter.io/) is a GNOME-native system monitor and task manager, built with Rust, GTK4 and Libadwaita. CPU, memory, disks, network and GPU on the left, a detail view with live graphs on the right, plus an Apps/Services view comparable to the Windows Task Manager's Processes tab.

```bash
flatpak install flathub io.missioncenter.MissionCenter
```

Open source under the GPLv3, source on [GitLab](https://gitlab.com/mission-center-devs/mission-center). Version 1.2.0 at the time of writing.

![Mission Center - CPU performance detail](/images/mission-center-cpu.avif)

On this hardware it reads both NVMe drives, all four fan sensors (`cpu_fan`, `gpu_fan`, `mid_fan`, plus one unlabeled), and both GPUs, with per-app GPU/GPU-memory usage broken out in the Apps view:

![Mission Center - Apps view](/images/mission-center-apps.avif)

{{< callout type="info" >}}
GPU monitoring is marked experimental upstream. NVIDIA is fully supported (including per-app VRAM and power draw); AMD is supported; Intel iGPUs older than Broadwell get no VRAM, power or temperature readout.
{{< /callout >}}

### TMOG: Dave Plummer's Task Manager

[Task Manager TMOG](https://tmog.org/) is a native Qt6 task manager for Windows, macOS and Linux by Dave Plummer, who wrote the original Windows Task Manager at Microsoft in the mid-1990s. Per [Tom's Hardware](https://www.tomshardware.com/software/windows/windows-veterans-vibe-coded-task-manager-now-also-runs-on-mac-and-linux-downloadable-app-is-the-result-of-a-107-page-spec-fed-to-claude-code), this rebuild was "vibe coded" from a 107-page spec fed to Claude Code. See also [Plummer's own video on it](https://youtu.be/c3EEs-O3bGE).

It's proprietary and closed-source, released under a beta license: personal use is fine, redistribution isn't. Most features are free; a handful (Power & Freq, Flight Recorder, Connections, Installed Apps, Drivers, Disk Space, Benchmarks) sit behind a **PRO** badge in the sidebar.

**Install (recommended: the official AppImage from [tmog.org](https://tmog.org/)):**

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S fuse2
```

Download the AppImage from tmog.org, then:

```bash
chmod +x TaskManagerOG-*.AppImage
./TaskManagerOG-*.AppImage
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Not tested on this hardware yet. AppImages generally need `libfuse2` at runtime; the cleanest way to get that on an atomic image (Homebrew, a distrobox, or otherwise) isn't confirmed here.

{{< /tab >}}
{{< /tabs >}}

{{< callout type="warning" >}}
Unofficial AUR packages (`tmog-bin`, `tmog-appimage`) exist too, but the official AppImage is the safer bet. Same general caveat as any AUR package: unaudited community build scripts. On top of that, at the time of writing `tmog-bin` was still packaging 0.1.1 while tmog.org itself had already moved on to 0.1.3. One more thing that can silently fall out of sync.
{{< /callout >}}

![Task Manager TMOG - Summary](/images/tmog-summary.avif)

Retro-styled, animates at 60 Hz instead of the usual once-a-second refresh, and gives a genuinely deep per-process breakdown, down to disk and network I/O per PID:

![Task Manager TMOG - Processes](/images/tmog-processes.avif)
