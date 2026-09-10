---
title: "GNOME"
weight: 4
toc: false
---

This laptop runs GNOME on Wayland, versions 49 and 50 at the time of writing. That is the only desktop these guides cover.

If you run KDE Plasma instead (a Bazzite `-nvidia-open` image without `-gnome`, or Plasma installed on CachyOS), the hardware pages still apply as-is. The parts that assume GNOME are the [autologin]({{< relref "/docs/security/autologin" >}}) guide (GDM, not SDDM), the lock-screen half of the [YubiKey]({{< relref "/docs/security/yubikey" >}}) guide, the GNOME Shell extensions, and the touchpad and window-button tweaks on the [applications]({{< relref "/docs/applications" >}}) page. Plasma has settings for most of those built in.
