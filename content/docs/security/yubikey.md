---
title: "YubiKey 5C NFC"
weight: 2
next: docs/applications
---

I wanted to use my YubiKey to unlock the LUKS-encrypted drive at boot: plug it in, touch it, and the desktop loads. This page documents what I tried, why it didn't work out, and what I'm actually using instead.

> **Status:** LUKS unlock with FIDO2 has been abandoned for now. Not because of the systemd fallback regression (fixed in systemd 259, which I'm running), but because of a persistent USB timing race condition on this hardware. The YubiKey is used instead for `sudo` and the GNOME lock screen via `pam-u2f`, which works reliably.


## What Works Today

The YubiKey works reliably for everything **outside** of early boot:

- **OATH/TOTP**: Yubico Authenticator 7.3.1 works perfectly for 2FA codes
- **SSH**: FIDO2-backed SSH keys
- **Bitwarden**: hardware-backed authentication
- **pam-u2f**: YubiKey touch for `sudo` and GNOME screen unlock


## Yubico Authenticator (OATH/TOTP)

Yubico Authenticator stores TOTP secrets on the YubiKey itself rather than on the device. It requires a smartcard daemon to communicate with the key.

### Install

```bash
sudo pacman -S ccid pcsclite
sudo systemctl enable --now pcscd.socket
```

Then install Yubico Authenticator from Flathub or the CachyOS repository and plug in the YubiKey. The app reads the TOTP credentials directly from the key.


## What Was Attempted: FIDO2 LUKS Unlock

The goal was: plug in YubiKey → touch at boot → LUKS unlocks → desktop. No LUKS password needed.

### What was done

**Packages installed:**
```bash
sudo pacman -S libfido2
```

**FIDO2 enrollment:**
```bash
sudo systemd-cryptenroll \
  --fido2-device=auto \
  --fido2-with-client-pin=no \
  --fido2-with-user-presence=yes \
  --fido2-with-user-verification=no \
  /dev/nvme1n1p2
```

**crypttab:**
```
luks-aaf424ea-... UUID=aaf424ea-... none fido2-device=auto,discard,token-timeout=30
```

**`/etc/sdboot-manage.conf`:**
```
LINUX_OPTIONS="... rd.luks.options=aaf424ea-...=fido2-device=auto,token-timeout=30 rd.udev.settle-timeout=10"
```

### What worked

- Enrollment succeeded (keyslot 1, touch-only)
- FIDO2 libraries confirmed present in initramfs
- systemd 259 confirmed: `+FIDO2` support present, `token-timeout=` available as a crypttab option
- Password fallback regression from systemd 257/258 is fixed in 259

### What failed

Despite running systemd 259, the USB timing race condition remained:

```
systemd-cryptsetup: Failed to ask token for assertion: FIDO_ERR_RX
```

`FIDO_ERR_RX` means the YubiKey is physically present but not fully initialized by the USB HID stack when `systemd-cryptsetup` queries it. This seems to affect warm reboots especially. No config-based fix seems to exist; this looks like a hardware/firmware timing issue.

Attempted workarounds:
- `token-timeout=30` in crypttab
- `rd.udev.settle-timeout=10` kernel parameter

Neither was reliable enough.

### What was reverted

```bash
# Remove FIDO2 from LUKS
sudo systemd-cryptenroll --wipe-slot=fido2 /dev/nvme1n1p2

# Restore crypttab to passphrase-only
# discard only, no fido2-device=auto

# Restore /etc/sdboot-manage.conf to original LINUX_OPTIONS
sudo sdboot-manage gen
```


## Current Approach: pam-u2f

A reliable alternative: require a YubiKey touch for `sudo` and the GNOME lock screen. No initramfs involvement, no boot-time timing issues.

### Install

```bash
sudo pacman -S pam-u2f
```

### Register the YubiKey

```bash
mkdir -p ~/.config/Yubico
pamu2fcfg > ~/.config/Yubico/u2f_keys
```

Touch the YubiKey when it blinks. To enroll a second key as backup, plug in the second YubiKey and run:

```bash
pamu2fcfg -n >> ~/.config/Yubico/u2f_keys
```

Touch it when it blinks. Both keys are now in the same file. Since both `sudo` and the GNOME lock screen read from `~/.config/Yubico/u2f_keys`, no extra configuration is needed: the backup key works for both immediately.

### Configure sudo

Edit `/etc/pam.d/sudo`:

```
#%PAM-1.0
auth       sufficient   pam_u2f.so cue
auth       include      system-auth
account    include      system-auth
session    include      system-auth
```

![nano editing /etc/pam.d/sudo with pam_u2f.so configured](/images/yubikey-sudo-config.avif)

Test without closing the current terminal first:

```bash
sudo echo test
# "Please touch the FIDO authenticator." → touch → done
```

![sudo echo test output showing the YubiKey touch prompt](/images/yubikey-sudo-test.avif)

Without the YubiKey plugged in, it falls through to password as normal.

### Configure graphical sudo (polkit)

GNOME's graphical authentication dialog (shown when changing system settings, printer config, etc.) uses a separate PAM service: `polkit-1`. This file doesn't exist by default on CachyOS, so polkit falls back to password-only.

Create `/etc/pam.d/polkit-1`:

```
#%PAM-1.0
auth       sufficient   pam_u2f.so cue
auth       include      system-auth
account    include      system-auth
session    include      system-auth
```

The `cue` text prompt does appear in the graphical dialog as well. Touching the YubiKey authenticates without needing to type a password. Without the key plugged in, it falls back to password as usual.

![GNOME polkit dialog showing "Please touch the FIDO authenticator."](/images/yubikey-polkit.avif)

### Configure GNOME lock screen

Edit `/etc/pam.d/gdm-password`:

```
#%PAM-1.0
auth       sufficient   pam_u2f.so cue
auth       include                     system-local-login
auth       optional                    pam_gnome_keyring.so
account    include                     system-local-login
password   include                     system-local-login
password   optional                    pam_gnome_keyring.so use_authtok
session    include                     system-local-login
session    optional                    pam_gnome_keyring.so auto_start
```

![nano editing /etc/pam.d/gdm-password with pam_u2f.so configured](/images/yubikey-gdm-password-config.avif)

Lock the screen with `Super+L` and touch the YubiKey to unlock.

![GNOME lock screen showing "Please touch the FIDO authenticator."](/images/yubikey-lockscreen.avif)

### How it works

| Situation | Behavior |
|---|---|
| YubiKey plugged in | Touch required to unlock |
| YubiKey absent | Falls back to password |
| Boot / autologin | Unaffected (LUKS password, then straight to desktop, see [GDM autologin]({{< relref "/docs/security/autologin" >}})) |

`sufficient` means: if the YubiKey succeeds, skip remaining auth steps. If absent or touch times out, PAM continues to the next method (password).

`cue` prints "Please touch the FIDO authenticator." as a visual hint.


## Boot Flow

```
Power on → LUKS password → autologin → desktop
                                           ↓
                              Super+L → YubiKey touch (or password)
```

LUKS stays password-only. The YubiKey only comes into play after the desktop is running.


{{< callout type="info" >}}
Troubleshooting for YubiKey and LUKS is documented on the [Known Issues]({{< relref "/docs/known-issues" >}}) page.
{{< /callout >}}
