---
title: "GNOME"
weight: 4
toc: false
---

This laptop runs GNOME on Wayland, versions 50 and 51 at the time of writing. That is the only desktop these guides cover.

If you run KDE Plasma instead (a Bazzite `-nvidia-open` image without `-gnome`, or Plasma installed on CachyOS), the hardware pages still apply as-is. The parts that assume GNOME are the [autologin]({{< relref "/docs/security/autologin" >}}) guide (GDM, not SDDM), the lock-screen half of the [YubiKey]({{< relref "/docs/security/yubikey" >}}) guide, the [GNOME Shell extensions]({{< relref "/docs/desktop/gnome-extensions" >}}), the [touchpad scroll speed]({{< relref "/docs/desktop/touchpad-scroll-speed" >}}) fix, and the window-button tweaks on the [applications]({{< relref "/docs/applications" >}}) page. Plasma has settings for most of those built in.

## GNOME 51

GNOME 51 came out in September 2026. What matters for these guides:

- **Extensions.** extensions.gnome.org lists per extension which GNOME versions it supports, and GNOME Shell ignores a build that does not list yours. At the time of writing, [Just Perfection]({{< relref "/docs/applications" >}}) and [Astra Monitor]({{< relref "/docs/desktop/astra-monitor" >}}) have a GNOME 51 build. [PiP on Top]({{< relref "/docs/desktop/gnome-extensions" >}}) and the [Smile complementary extension]({{< relref "/docs/applications/utilities" >}}) stop at GNOME 50, so on 51 they stay out of date until their authors publish an update. The setup window greys them out with "No build for GNOME 51 yet". Smile itself keeps working, it just cannot paste the emoji for you.
- **NVIDIA.** mutter 51 drops support for legacy NVIDIA drivers. The RTX 4060 runs the current open driver, so nothing changes here.
- **Brightness.** GNOME 51 remembers the screen brightness between sessions, and mutter 51 improves backlight detection. It is not known yet whether that makes the [brightness fix]({{< relref "/docs/known-issues" >}}) unnecessary.
- **Login.** GDM 51 closes an autologin hole where a compromised greeter could ask for autologin of any local account, and the fingerprint reader can only re-authenticate now, it no longer logs you in on its own. See the [autologin]({{< relref "/docs/security/autologin" >}}) and [YubiKey]({{< relref "/docs/security/yubikey" >}}) guides if you rely on those.
- **Color.** The `sdr-native` color mode behind the sRGB mode in the [setup window]({{< relref "/docs/hardware/color-profiles" >}}) arrived in GNOME 50 and is still there in 51.
