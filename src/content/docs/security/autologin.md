---
title: "GDM Autologin"
weight: 1
prev: docs/desktop/touchpad-scroll-speed
next: docs/security/yubikey
---

After unlocking the disk with LUKS at boot, I didn't want to type a second password to log in to the desktop. This skips the GDM login screen entirely: you enter your disk password once, and the desktop loads straight away. The screen lock still requires your password as normal.

**Boot behavior:**
- Power on → LUKS password prompt → desktop (no second login)
- Suspend / screen lock → password required as normal


{{< callout type="info" >}}
Nothing on this page is distribution-specific. GDM reads the same `/etc/gdm/custom.conf` on both, and `/etc` is writable on Bazzite too, so no layering and no reboot beyond the one below.
{{< /callout >}}

## Configuration

Edit the GDM config:

```bash
sudo nano /etc/gdm/custom.conf
```

Add `AutomaticLoginEnable` and `AutomaticLogin` under `[daemon]`, as the [GNOME System Administrator's Guide](https://help.gnome.org/admin/system-admin-guide/stable/login-automatic.html.en) describes:

```ini
[daemon]
AutomaticLoginEnable=True
AutomaticLogin=your-username
```

Replace `your-username` with your own login name (`whoami` prints it).

Full example for reference:

```ini
# GDM configuration storage
[daemon]
AutomaticLoginEnable=True
AutomaticLogin=your-username

[security]

[xdmcp]

[chooser]

[debug]
```

Save with `Ctrl+X`, `y` then reboot:

```bash
sudo reboot
```


## Verification

After reboot, LUKS will prompt for a password. Once entered, the desktop should load immediately without a GDM login screen.

To confirm autologin is active:

```bash
sudo cat /etc/gdm/custom.conf | grep -i auto
```

Expected output:
```
AutomaticLoginEnable=True
AutomaticLogin=your-username
```

## Notes

- Autologin only applies to the **initial boot session**. GDM does not trigger when resuming from suspend.
- The GNOME **screen lock** (Super+L, lid close, idle timeout) is handled by GNOME Shell, not GDM. It always requires your user password regardless of autologin settings.
- If you have a second user account on the system, only the configured user gets autologin. Other accounts always get a GDM prompt.


{{< callout type="info" >}}
For troubleshooting autologin issues, see the [Known Issues]({{< relref "/docs/known-issues" >}}) page.
{{< /callout >}}

{{% details title="Disable autologin" closed="true" %}}

```bash
sudo nano /etc/gdm/custom.conf
```

Remove or comment out the two lines:

```ini
#AutomaticLoginEnable=True
#AutomaticLogin=your-username
```

Reboot to apply.

{{% /details %}}

## Sources

- [GNOME System Administrator's Guide: Enabling automatic login](https://help.gnome.org/admin/system-admin-guide/stable/login-automatic.html.en): the `/etc/gdm/custom.conf` syntax used above
