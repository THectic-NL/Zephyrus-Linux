---
title: "YubiKey 5C NFC"
weight: 2
prev: docs/security/autologin
next: docs/applications
---

Using the YubiKey for `sudo` and the GNOME lock screen works reliably via `pam-u2f`. LUKS unlock at boot did not work due to a USB timing race condition on this hardware; see the [Known Issues]({{< relref "/docs/known-issues" >}}) page for the full attempt log.


## What Works

- **OATH/TOTP**: Yubico Authenticator 7.3.1 works perfectly for 2FA codes
- **SSH**: FIDO2-backed SSH keys
- **Bitwarden**: hardware-backed authentication
- **pam-u2f**: YubiKey touch for `sudo` and GNOME screen unlock


## Yubico Authenticator (OATH/TOTP)

Yubico Authenticator stores TOTP secrets on the YubiKey itself rather than on the device. It requires a smartcard daemon to communicate with the key.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S ccid pcsclite
sudo systemctl enable --now pcscd.socket
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

`pcsc-lite` is generally already in the image. Check before layering anything:

```bash
rpm -q pcsc-lite pcsc-lite-ccid
```

If either is missing:

```bash
rpm-ostree install pcsc-lite pcsc-lite-ccid
systemctl reboot
```

Then enable the socket:

```bash
sudo systemctl enable --now pcscd.socket
```

{{< /tab >}}
{{< /tabs >}}

Then install Yubico Authenticator — the Flatpak works on both distributions — and plug in the YubiKey. The app reads the TOTP credentials directly from the key.

```bash
flatpak install flathub com.yubico.yubioath
```


## pam-u2f

Require YubiKey touch for `sudo` and the GNOME lock screen. No initramfs, no boot-timing issues.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S pam-u2f
```

**Register the YubiKey:**
```bash
mkdir -p ~/.config/Yubico
pamu2fcfg > ~/.config/Yubico/u2f_keys
```

Touch the YubiKey when it blinks. For a backup key, plug in the second YubiKey and run:
```bash
pamu2fcfg -n >> ~/.config/Yubico/u2f_keys
```

Both keys share one file. Since both `sudo` and the GNOME lock screen read from `~/.config/Yubico/u2f_keys`, the backup key works for both immediately without extra configuration.

{{< /tab >}}
{{< tab name="Bazzite" >}}

A PAM module has to be on the host, so this is a layered package:

```bash
rpm-ostree install pam-u2f
systemctl reboot
```

**Register the YubiKey.** Put the mapping in `/etc/u2f_mappings` rather than in your home directory:

```bash
pamu2fcfg | sudo tee -a /etc/u2f_mappings
```

Touch the YubiKey when it blinks. For a backup key, plug in the second one and run:

```bash
pamu2fcfg -n | sudo tee -a /etc/u2f_mappings
```

{{< callout type="warning" >}}
`~/.config/Yubico/u2f_keys` is where `pam_u2f` looks by default, and it's what the CachyOS tab uses. On Fedora-based systems SELinux confines what PAM may read out of a home directory, so a key file there tends to be silently ignored — the touch prompt never appears and you fall through to the password. `/etc/u2f_mappings` avoids the problem entirely.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

## Wiring it into PAM

This is where the two distributions genuinely part ways. On CachyOS you edit the PAM service files directly. On Bazzite you must not: they are generated.

{{< tabs >}}
{{< tab name="CachyOS" >}}

### sudo

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

### Graphical sudo (polkit)

GNOME's graphical authentication dialog uses a separate PAM service: `polkit-1`. This file doesn't exist by default on CachyOS, so polkit falls back to password-only.

Create `/etc/pam.d/polkit-1`:
```
#%PAM-1.0
auth       sufficient   pam_u2f.so cue
auth       include      system-auth
account    include      system-auth
session    include      system-auth
```

![GNOME polkit dialog showing "Please touch the FIDO authenticator."](/images/yubikey-polkit.avif)

### GNOME lock screen

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

| Situation | Behavior |
|---|---|
| YubiKey plugged in | Touch required to unlock |
| YubiKey absent | Falls back to password |
| Boot / autologin | Unaffected (LUKS password, then straight to desktop) |

`sufficient` means: if the YubiKey succeeds, skip remaining auth steps. If absent or touch times out, PAM continues to the next method (password). `cue` prints "Please touch the FIDO authenticator." as a visual hint.

{{< /tab >}}
{{< tab name="Bazzite" >}}

Do not hand-edit the files in `/etc/pam.d/` here. Fedora manages them with **authselect**, and the next `authselect apply-changes` — which an update can trigger on its own — puts back what it thinks should be there, taking your edits with it.

authselect ships a feature for exactly this:

```bash
sudo authselect enable-feature with-pam-u2f
```

That covers `sudo`, polkit and GDM in one go: the three separate files the CachyOS tab edits are all generated from the same profile.

Check what you ended up with:

```bash
authselect current
```

To require the YubiKey *in addition to* the password rather than instead of it, use `with-pam-u2f-2fa` instead of `with-pam-u2f`. To undo:

```bash
sudo authselect disable-feature with-pam-u2f
```

Then test it the same way, from a terminal you can afford to lose:

```bash
sudo echo test
# "Please touch the FIDO authenticator." → touch → done
```

{{< /tab >}}
{{< /tabs >}}


## Boot flow

```
Power on → LUKS password → autologin → desktop
                                           ↓
                              Super+L → YubiKey touch (or password)
```

LUKS stays password-only. The YubiKey only comes into play after the desktop is running.


{{< callout type="info" >}}
Troubleshooting for YubiKey and LUKS is documented on the [Known Issues]({{< relref "/docs/known-issues" >}}) page.
{{< /callout >}}
