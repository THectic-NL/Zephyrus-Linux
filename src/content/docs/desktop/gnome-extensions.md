---
title: "GNOME Extensions"
weight: 1
prev: docs/hardware/color-profiles
next: docs/desktop/astra-monitor
---

GNOME Shell extensions are how this desktop gets the things it doesn't do out of the box: picture-in-picture windows that stay where you put them, on top, a system monitor in the panel, window behaviour fixes. This page covers installing them in general. Extensions with enough moving parts to need their own instructions get a dedicated page, linked below.

## Installing extensions

extensions.gnome.org wants a browser add-on plus a native host connector before it lets you install anything from the website. If that's not set up, or you can't be bothered, skip it and use **Extension Manager** instead. It talks to GNOME Shell directly and has its own Browse tab with the same catalog.

The [setup window]({{< relref "/docs/setup-script" >}}) can do the same for the extensions on this page: it installs them from extensions.gnome.org, switches them on and off, and tells you when there is no build for your GNOME version yet.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S extension-manager
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

```bash
flatpak install flathub com.mattjakeman.ExtensionManager
```

{{< /tab >}}
{{< /tabs >}}

Open Extension Manager from your application menu, go to the **Browse** tab, search for the extension by name, and install.

{{< callout type="info" >}}
Extensions installed this way live in `~/.local/share/gnome-shell/extensions/`, your home directory, not the system image. On Bazzite that means they survive rebases and image updates without layering anything.
{{< /callout >}}

## Extensions I use

### In Picture

[In Picture](https://extensions.gnome.org/extension/8692/in-picture/) by [Filip](https://codeberg.org/filiprund) moves and resizes Picture-in-Picture windows to your preferences and can keep them on top of everything else, even on Wayland, which GNOME doesn't do on its own. It's built for web browser PiP windows and works well with multiple monitors. I use this one constantly, mostly to keep a video in the corner while I'm working in something else. It has builds for GNOME 48 through 51.

- [extensions.gnome.org](https://extensions.gnome.org/extension/8692/in-picture/)
- [Source on Codeberg](https://codeberg.org/filiprund/in-picture)

### Astra Monitor

CPU, memory, disk, network and GPU readouts in the panel, both the Radeon 890M and the RTX 4060 side by side. It has optional dependencies depending on what you want to monitor, so it gets its own page: [Astra Monitor]({{< relref "/docs/desktop/astra-monitor" >}}).

## Extensions covered elsewhere

A couple of others show up on other pages because they fix one specific problem rather than being a general tool:

| Extension | What it's for | Where |
|---|---|---|
| [Smile complementary extension](https://extensions.gnome.org/extension/6096/smile-complementary-extension/) | Automatic emoji pasting for the [Smile]({{< relref "/docs/applications/utilities#smile-emoji-picker" >}}) picker | [Utilities]({{< relref "/docs/applications/utilities#smile-emoji-picker" >}}) |
| [Just Perfection](https://gitlab.gnome.org/jrahmatzadeh/just-perfection) | Fixes apps opening in the background instead of taking focus | [Applications]({{< relref "/docs/applications#gnome-window-focus-apps-opening-in-the-background" >}}) |


## GNOME 51 features and compatibility

GNOME 51 ("A Coruña") brings several core desktop improvements that affect daily use on this laptop:

- **Mutter frame scheduling:** Reworked frame delivery keeps animations and window dragging fluid even when heavy background tasks or compilation are running.
- **Display brightness persistence:** Monitor brightness levels are now reliably retained across reboots and HDR toggles.
- **Native GDM FIDO2 & passkey support:** GDM now natively supports FIDO2 security keys and passkeys for login sessions.
- **Wayland background blur protocol:** Support for `ext-background-effect-v1` allows blur effects without custom compositor hacks.
- **Display auto-rotation and alignment:** Refined display layout snapping with center alignment in Settings.

Most extensions documented below (including In Picture, Astra Monitor, and Just Perfection) are confirmed compatible with GNOME 51. The notable exception is the **Smile complementary extension**, which currently stops at GNOME 50 and will be rejected as out of date by GNOME Shell until its upstream author publishes a 51 build (Smile itself remains functional for copying emojis to the clipboard).
