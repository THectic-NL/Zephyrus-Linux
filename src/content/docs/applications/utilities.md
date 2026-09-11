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
