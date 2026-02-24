---
title: "YubiKey 5C NFC"
weight: 20
---

I wanted to use my YubiKey to unlock the LUKS-encrypted drive at boot — plug it in, touch it, and the desktop loads. This page documents what I tried, why it failed at first, and what actually works in the meantime.

> **Status:** LUKS unlock with FIDO2 has been unreliable on systemd 258. This page documents what was attempted, what the root cause is, and what to do instead. The situation may improve with systemd 259+.


## What Works Today

The YubiKey works reliably for everything **outside** of early boot:

- **OATH/TOTP** — Yubico Authenticator Flatpak 7.3.0 works perfectly for 2FA codes
- **SSH** — FIDO2-backed SSH keys
- **Bitwarden** — hardware-backed authentication
- **pam-u2f** — YubiKey touch for `sudo` and GDM screen unlock (see below)


## What Was Attempted: FIDO2 LUKS Unlock

The goal was: plug in YubiKey → touch at boot → LUKS unlocks → desktop. No LUKS password needed.

### What was done

**Packages installed:**
```bash
sudo dnf install libfido2 fido2-tools cryptsetup
```

**FIDO2 enrollment:**
```bash
sudo systemd-cryptenroll \
  --fido2-device=auto \
  --fido2-with-client-pin=no \
  --fido2-with-user-presence=yes \
  --fido2-with-user-verification=no \
  /dev/nvme1n1p3
```

**crypttab:**
```
luks-680fec4e-... UUID=680fec4e-... none discard,fido2-device=auto
```

**dracut config** (`/etc/dracut.conf.d/fido2.conf`):
```
add_dracutmodules+=" fido2 "
```

### What worked

- Enrollment succeeded (keyslot 1, touch-only, `fido2-clientPin-required: false`)
- FIDO2 libraries confirmed present in initramfs (`lsinitrd | grep fido`)
- Occasional successful boots when spamming the YubiKey touch at exactly the right moment

### What failed

1. **Touch window is ~1-2 seconds** — not enough time to react. There is no configurable `token-timeout=` in crypttab until systemd 259.

2. **No password fallback** — when FIDO2 fails, the system does not fall back to asking for a LUKS password. It drops into a dracut emergency shell with a locked root account. This is a confirmed regression introduced in **systemd 257** (issue [#35393](https://github.com/systemd/systemd/issues/35393)).

3. **dracut initqueue races the YubiKey** — the USB HID device is not ready within the 5-second dracut initqueue window on this hardware, so `systemd-cryptsetup` fails before it can even show the touch prompt.

4. **rhgb/plymouth swallows prompts** — even with verbose boot, the touch prompt is hidden behind Plymouth.

### Root cause

systemd 257/258 has a regression where FIDO2 authentication failure does not fall back to password. Combined with the short dracut initqueue window on this laptop's USB stack, the result is an unrecoverable boot loop when FIDO2 does not succeed on the first attempt.

### What was reverted

```bash
# Remove FIDO2 from LUKS
sudo systemd-cryptenroll --wipe-slot=fido2 /dev/nvme1n1p3

# Restore crypttab to passphrase-only
# discard only, no fido2-device=auto

# Remove dracut config
sudo rm /etc/dracut.conf.d/fido2.conf
sudo rm -r /etc/systemd/system/systemd-cryptsetup@.service.d/

# Rebuild initramfs
sudo dracut --force --regenerate-all
```


## When to Retry

Wait for **systemd 259+** to become available. Systemd 259 adds `token-timeout=` as a proper crypttab option, which gives a configurable wait window for the touch prompt. Combined with a fix for the fallback regression, FIDO2 LUKS unlock should become reliable on CachyOS as well.

When retrying, the enrollment procedure itself is correct — only the systemd version is the blocker.


## Using the YubiKey for sudo and Screen Unlock (pam-u2f)

A reliable alternative that works today: require a YubiKey touch for `sudo` and/or the GDM lock screen.

> **To be documented after testing.**


## Troubleshooting

{{% details title="System stuck in boot loop after FIDO2 enrollment" closed="true" %}}

If you enrolled FIDO2 and cannot boot, spam-tap the YubiKey immediately after the BIOS screen. The touch window is very short.

Once in the system, revert immediately:
```bash
sudo systemd-cryptenroll --wipe-slot=fido2 /dev/nvme1n1p3
sudo nano /etc/crypttab  # remove fido2-device=auto
sudo rm /etc/dracut.conf.d/fido2.conf
sudo dracut --force --regenerate-all
```

{{% /details %}}

{{% details title="Verify LUKS keyslots" closed="true" %}}

```bash
sudo cryptsetup luksDump /dev/nvme1n1p3 | grep -E "^\s+[0-9]+:"
```

Should show only `0: luks2` after reverting. If slot 1 is still present, FIDO2 is still enrolled.

{{% /details %}}
