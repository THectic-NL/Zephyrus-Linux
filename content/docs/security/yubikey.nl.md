---
title: "YubiKey 5C NFC"
weight: 2
next: docs/applications
---

Ik wilde mijn YubiKey gebruiken om de LUKS-schijfversleuteling bij het opstarten te ontgrendelen: inpluggen, aanraken, en het bureaublad laadt. Op deze pagina staat wat ik geprobeerd heb, waarom het niet werkte, en wat ik nu gebruik.

> **Status:** LUKS ontgrendeling met FIDO2 is voorlopig afgebroken. Niet vanwege de systemd fallback-regressie (die is opgelost in systemd 259, wat ik draai), maar vanwege een hardnekkige USB timing race condition op deze hardware. De YubiKey wordt nu gebruikt voor `sudo` en de GNOME-schermvergrendeling via `pam-u2f`, wat wél betrouwbaar werkt.


## Wat op dit moment werkt

De YubiKey werkt betrouwbaar voor alles **buiten** de vroege bootprocessen:

- **OATH/TOTP**: Yubico Authenticator 7.3.1 werkt uitstekend voor 2FA codes
- **SSH**: FIDO2-backed SSH sleutels
- **Bitwarden**: hardware-backed authenticatie
- **pam-u2f**: YubiKey touch voor `sudo` en GNOME-schermvergrendeling


## Yubico Authenticator (OATH/TOTP)

Yubico Authenticator slaat TOTP-geheimen op de YubiKey zelf op in plaats van op het apparaat. Hiervoor is een smartcard-daemon nodig om met de key te communiceren.

### Installatie

```bash
sudo pacman -S ccid pcsclite
sudo systemctl enable --now pcscd.socket
```

Installeer vervolgens Yubico Authenticator via Flathub of de CachyOS-repository en sluit de YubiKey aan. De app leest de TOTP-credentials rechtstreeks van de key.


## Wat Geprobeerd Is: FIDO2 LUKS Ontgrendeling

Het doel was: YubiKey inpluggen → aanraken bij boot → LUKS ontgrendelt → bureaublad. Geen LUKS-wachtwoord nodig.

### Wat gedaan is

**Packages geïnstalleerd:**
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

### Wat werkte

- Enrollment gelukt (keyslot 1, touch-only)
- FIDO2 libraries bevestigd aanwezig in initramfs
- systemd 259 bevestigd: `+FIDO2` aanwezig, `token-timeout=` beschikbaar als crypttab-optie
- Fallback-regressie uit systemd 257/258 is opgelost in 259

### Wat niet werkte

Ondanks systemd 259 bleef de USB timing race condition bestaan:

```
systemd-cryptsetup: Failed to ask token for assertion: FIDO_ERR_RX
```

`FIDO_ERR_RX` betekent dat de YubiKey fysiek aanwezig is, maar nog niet volledig geïnitialiseerd door de USB HID-stack op het moment dat `systemd-cryptsetup` hem aanspreekt. Dit lijkt met name op te treden bij warme reboots. Er lijkt geen config-gebaseerde oplossing te bestaan; het ziet eruit als een hardware/firmware timingprobleem.

Geprobeerde workarounds:
- `token-timeout=30` in crypttab
- `rd.udev.settle-timeout=10` kernelparameter

Geen van beide was betrouwbaar genoeg.

### Wat teruggedraaid is

```bash
# FIDO2 verwijderen uit LUKS
sudo systemd-cryptenroll --wipe-slot=fido2 /dev/nvme1n1p2

# crypttab herstellen naar alleen wachtwoord
# alleen discard, geen fido2-device=auto

# /etc/sdboot-manage.conf herstellen naar originele LINUX_OPTIONS
sudo sdboot-manage gen
```


## Huidige aanpak: pam-u2f

Een betrouwbaar alternatief: YubiKey touch vereisen voor `sudo` en de GNOME-schermvergrendeling. Geen initramfs, geen boot-timing problemen.

### Installatie

```bash
sudo pacman -S pam-u2f
```

### YubiKey registreren

```bash
mkdir -p ~/.config/Yubico
pamu2fcfg > ~/.config/Yubico/u2f_keys
```

Raak de YubiKey aan als hij knippert. Voor een tweede key als backup: sluit de tweede YubiKey aan en voer uit:

```bash
pamu2fcfg -n >> ~/.config/Yubico/u2f_keys
```

Raak hem aan als hij knippert. Beide keys staan nu in hetzelfde bestand. Omdat zowel `sudo` als de GNOME-schermvergrendeling uit `~/.config/Yubico/u2f_keys` lezen, is geen extra configuratie nodig: de backup key werkt direct voor beiden.

### sudo configureren

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

### Grafische sudo configureren (polkit)

De grafische authenticatiedialoog van GNOME (verschijnt bij het wijzigen van systeeminstellingen, printerinstellingen, etc.) gebruikt een aparte PAM-service: `polkit-1`. Dit bestand bestaat standaard niet op CachyOS, waardoor polkit terugvalt op wachtwoord-only.

Maak `/etc/pam.d/polkit-1` aan:

```
#%PAM-1.0
auth       sufficient   pam_u2f.so cue
auth       include      system-auth
account    include      system-auth
session    include      system-auth
```

De `cue` tekstprompt verschijnt ook in de grafische dialoog. De YubiKey aanraken authenticeert zonder wachtwoord te hoeven typen. Zonder YubiKey ingeplugd valt hij terug op wachtwoord.

![GNOME polkit-dialoog met "Please touch the FIDO authenticator."](/images/yubikey-polkit.avif)

### GNOME-schermvergrendeling configureren

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

### Hoe het werkt

| Situatie | Gedrag |
|---|---|
| YubiKey ingeplugd | Aanraken vereist om te ontgrendelen |
| YubiKey niet aanwezig | Valt terug op wachtwoord |
| Boot / autologin | Ongewijzigd (LUKS-wachtwoord, dan direct naar bureaublad, zie [GDM autologin]({{< relref "/docs/security/autologin" >}})) |

`sufficient` betekent: als de YubiKey slaagt, sla de rest van de auth-stappen over. Als hij niet aanwezig is of de touch time-out optreedt, gaat PAM door naar de volgende methode (wachtwoord).

`cue` toont "Please touch the FIDO authenticator." als visuele hint.


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
