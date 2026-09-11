---
title: "Browser"
weight: 1
prev: docs/applications
next: docs/applications/productivity
---

### Brave

I use [Brave Origin](https://packages.cachyos.org/package/cachyos/x86_64/brave-origin-bin) as my main browser. I started out with regular Brave, then switched to Brave Origin. It feels noticeably lighter and faster, has fewer built-in features, and for most people it's probably the better starting point.

Brave Origin is the stripped-down version of Brave. On Windows it's a paid product ($60); on Linux it's free.

Brave themselves recommend a native package over the Flatpak where one exists; the Flatpak works but feels a bit isolated.

{{< tabs >}}
{{< tab name="CachyOS" >}}

Both Brave and Brave Origin are available from three sources: the CachyOS repositories, the AUR, and Flathub. The CachyOS native package gives the best integration.

**Install Brave Origin (recommended):**

```bash
sudo pacman -S brave-origin-bin
```

**Or regular Brave, if you want the full feature set:**

```bash
sudo pacman -S brave-bin
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

Brave Origin has no Fedora package, so on Bazzite it's regular Brave. Brave publishes its own RPM repository, but a browser doesn't need to be part of the system image, so take the Flatpak:

```bash
flatpak install flathub com.brave.Browser
```

{{< callout type="info" >}}
The Brave GPU workarounds on the [Known Issues]({{< relref "/docs/known-issues" >}}) page apply to the Flatpak too, but a Flatpak reads its launch flags from `~/.var/app/com.brave.Browser/config/brave-flags.conf` instead of `~/.config/brave-flags.conf`.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

![Brave official Linux install instructions](/images/brave-linux-install.avif)

Hardware acceleration works fine with current Brave and kernel versions. The crash bugs that affected Brave 1.82–1.86 are resolved. See [Known Issues]({{< relref "/docs/known-issues" >}}) for the history.
