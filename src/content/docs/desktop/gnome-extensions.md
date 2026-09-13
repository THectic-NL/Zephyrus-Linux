---
title: "GNOME Extensions"
weight: 1
prev: docs/hardware/color-profiles
next: docs/desktop/astra-monitor
---

GNOME Shell extensions are how this desktop gets the things it doesn't do out of the box: picture-in-picture windows that actually stay on top, a system monitor in the panel, window behaviour fixes. This page covers installing them in general. Extensions with enough moving parts to need their own instructions get a dedicated page, linked below.

## Installing extensions

extensions.gnome.org wants a browser add-on plus a native host connector before it lets you install anything from the website. If that's not set up, or you can't be bothered, skip it and use **Extension Manager** instead. It talks to GNOME Shell directly and has its own Browse tab with the same catalog.

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

### PiP on Top

[PiP on Top](https://extensions.gnome.org/extension/4691/pip-on-top/) by [Rafostar](https://github.com/Rafostar) keeps Picture-in-Picture windows on top of everything else, even on Wayland, which GNOME doesn't do on its own. It's built for Firefox but works with a few other browsers too. I use this one constantly, mostly to keep a video in the corner while I'm working in something else.

- [extensions.gnome.org](https://extensions.gnome.org/extension/4691/pip-on-top/)
- [Source on GitHub](https://github.com/Rafostar/gnome-shell-extension-pip-on-top)

### Astra Monitor

CPU, memory, disk, network and GPU readouts in the panel, both the Radeon 890M and the RTX 4060 side by side. It has optional dependencies depending on what you want to monitor, so it gets its own page: [Astra Monitor]({{< relref "/docs/desktop/astra-monitor" >}}).

## Extensions covered elsewhere

A couple of others show up on other pages because they fix one specific problem rather than being a general tool:

| Extension | What it's for | Where |
|---|---|---|
| [Smile complementary extension](https://extensions.gnome.org/extension/6096/smile-complementary-extension/) | Automatic emoji pasting for the [Smile]({{< relref "/docs/applications/utilities#smile-emoji-picker" >}}) picker | [Utilities]({{< relref "/docs/applications/utilities#smile-emoji-picker" >}}) |
| [Just Perfection](https://gitlab.gnome.org/jrahmatzadeh/just-perfection) | Fixes apps opening in the background instead of taking focus | [Applications]({{< relref "/docs/applications#gnome-window-focus-apps-opening-in-the-background" >}}) |
