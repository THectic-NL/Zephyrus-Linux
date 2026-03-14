---
title: "YubiKey 5C NFC"
weight: 2
prev: docs/security/autologin
next: docs/applications
---

De YubiKey voor `sudo` en de GNOME-schermvergrendeling werkt betrouwbaar via `pam-u2f`. LUKS-ontgrendeling bij het opstarten werkte niet door een USB timing race condition op deze hardware; zie de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}) voor het volledige verslag van die poging.


## Wat werkt

- **OATH/TOTP**: Yubico Authenticator 7.3.1 werkt uitstekend voor 2FA codes
- **SSH**: FIDO2-backed SSH sleutels
- **Bitwarden**: hardware-backed authenticatie
- **pam-u2f**: YubiKey touch voor `sudo` en GNOME-schermvergrendeling


## Yubico Authenticator (OATH/TOTP)

Yubico Authenticator slaat TOTP-geheimen op de YubiKey zelf op in plaats van op het apparaat. Hiervoor is een smartcard-daemon nodig om met de key te communiceren.

```bash
sudo pacman -S ccid pcsclite
sudo systemctl enable --now pcscd.socket
```

Installeer vervolgens Yubico Authenticator via Flathub of de CachyOS-repository en sluit de YubiKey aan. De app leest de TOTP-credentials rechtstreeks van de key.


## pam-u2f

YubiKey touch vereisen voor `sudo` en de GNOME-schermvergrendeling. Geen initramfs, geen boot-timing problemen.

```bash
sudo pacman -S pam-u2f
```

**YubiKey registreren:**
```bash
mkdir -p ~/.config/Yubico
pamu2fcfg > ~/.config/Yubico/u2f_keys
```

Raak de YubiKey aan als hij knippert. Voor een reservesleutel: sluit de tweede YubiKey aan en voer uit:
```bash
pamu2fcfg -n >> ~/.config/Yubico/u2f_keys
```

Beide sleutels staan dan in hetzelfde bestand. Omdat zowel `sudo` als de GNOME-schermvergrendeling uit `~/.config/Yubico/u2f_keys` lezen, werkt de reservesleutel direct voor beiden zonder extra configuratie.

### sudo

Bewerk `/etc/pam.d/sudo`:
```
#%PAM-1.0
auth       sufficient   pam_u2f.so cue
auth       include      system-auth
account    include      system-auth
session    include      system-auth
```

![nano met /etc/pam.d/sudo geconfigureerd voor pam_u2f.so](/images/yubikey-sudo-config.avif)

Test eerst zonder de huidige terminal te sluiten:
```bash
sudo echo test
# "Please touch the FIDO authenticator." → aanraken → klaar
```

![sudo echo test output met de YubiKey touch-prompt](/images/yubikey-sudo-test.avif)

Zonder YubiKey ingeplugd valt het terug op wachtwoord.

### Grafische sudo (polkit)

De grafische authenticatiedialoog van GNOME gebruikt een aparte PAM-service: `polkit-1`. Dit bestand bestaat standaard niet op CachyOS, waardoor polkit terugvalt op alleen wachtwoord.

Maak `/etc/pam.d/polkit-1` aan:
```
#%PAM-1.0
auth       sufficient   pam_u2f.so cue
auth       include      system-auth
account    include      system-auth
session    include      system-auth
```

![GNOME polkit-dialoog met "Please touch the FIDO authenticator."](/images/yubikey-polkit.avif)

### GNOME-schermvergrendeling

Bewerk `/etc/pam.d/gdm-password`:
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

![nano met /etc/pam.d/gdm-password geconfigureerd voor pam_u2f.so](/images/yubikey-gdm-password-config.avif)

Vergrendel het scherm met `Super+L` en raak de YubiKey aan om te ontgrendelen.

![GNOME-vergrendelscherm met "Please touch the FIDO authenticator."](/images/yubikey-lockscreen.avif)

| Situatie | Gedrag |
|---|---|
| YubiKey ingeplugd | Aanraken vereist om te ontgrendelen |
| YubiKey niet aanwezig | Valt terug op wachtwoord |
| Boot / autologin | Ongewijzigd (LUKS-wachtwoord, dan direct naar bureaublad) |

`sufficient` betekent: als de YubiKey slaagt, sla de rest van de verificatiestappen over. Als hij niet aanwezig is of de aanraaktijd verstrijkt, gaat PAM door naar de volgende methode (wachtwoord). `cue` toont "Please touch the FIDO authenticator." als visuele hint.


## Bootflow

```
Opstarten → LUKS-wachtwoord → autologin → bureaublad
                                               ↓
                              Super+L → YubiKey touch (of wachtwoord)
```

LUKS blijft wachtwoord-only. De YubiKey speelt alleen een rol nadat het bureaublad al draait.


{{< callout type="info" >}}
Probleemoplossing voor YubiKey en LUKS staat op de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}).
{{< /callout >}}
