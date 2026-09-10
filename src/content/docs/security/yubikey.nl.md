---
title: "YubiKey 5C NFC"
weight: 2
prev: docs/security/autologin
next: docs/applications
---

De YubiKey voor `sudo` en de GNOME-schermvergrendeling werkt betrouwbaar via `pam-u2f`. LUKS-ontgrendeling bij het opstarten werkte niet door een USB timing race condition op deze hardware; zie de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}) voor het volledige verslag van die poging.


## Wat werkt

- **OATH/TOTP**: Yubico Authenticator 7.3.1 werkt uitstekend voor 2FA-codes
- **SSH**: FIDO2-ondersteunde SSH-sleutels
- **Bitwarden**: hardware-ondersteunde authenticatie
- **pam-u2f**: YubiKey touch voor `sudo` en GNOME-schermvergrendeling


## Yubico Authenticator (OATH/TOTP)

Yubico Authenticator slaat TOTP-geheimen op de YubiKey zelf op in plaats van op het apparaat. Hiervoor is een smartcard-daemon nodig om met de key te communiceren.

{{< tabs >}}
{{< tab name="CachyOS" >}}

```bash
sudo pacman -S ccid pcsclite
sudo systemctl enable --now pcscd.socket
```

{{< /tab >}}
{{< tab name="Bazzite" >}}

`pcsc-lite` zit meestal al in de image. Kijk eerst voordat je iets layert:

```bash
rpm -q pcsc-lite pcsc-lite-ccid
```

Ontbreekt er een:

```bash
rpm-ostree install pcsc-lite pcsc-lite-ccid
systemctl reboot
```

Zet daarna de socket aan:

```bash
sudo systemctl enable --now pcscd.socket
```

{{< /tab >}}
{{< /tabs >}}

Installeer vervolgens Yubico Authenticator — de Flatpak werkt op beide distributies — en sluit de YubiKey aan. De app leest de TOTP-credentials rechtstreeks van de key.

```bash
flatpak install flathub com.yubico.yubioath
```


## pam-u2f

YubiKey touch vereisen voor `sudo` en de GNOME-schermvergrendeling. Geen initramfs, geen boot-timingproblemen.

{{< tabs >}}
{{< tab name="CachyOS" >}}

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

{{< /tab >}}
{{< tab name="Bazzite" >}}

Een PAM-module hoort op de host, dus dit is een gelaagd package:

```bash
rpm-ostree install pam-u2f
systemctl reboot
```

**YubiKey registreren.** Zet de mapping in `/etc/u2f_mappings` en niet in je home-map:

```bash
pamu2fcfg | sudo tee -a /etc/u2f_mappings
```

Raak de YubiKey aan als hij knippert. Voor een reservesleutel: sluit de tweede aan en voer uit:

```bash
pamu2fcfg -n | sudo tee -a /etc/u2f_mappings
```

{{< callout type="warning" >}}
`~/.config/Yubico/u2f_keys` is waar `pam_u2f` standaard kijkt, en het is wat de CachyOS-tab gebruikt. Op Fedora-gebaseerde systemen beperkt SELinux wat PAM uit een home-map mag lezen, waardoor een sleutelbestand daar meestal stilzwijgend genegeerd wordt — de touch-prompt komt nooit en je valt terug op het wachtwoord. Met `/etc/u2f_mappings` speelt dat niet.
{{< /callout >}}

{{< /tab >}}
{{< /tabs >}}

## Aan PAM koppelen

Hier lopen de twee distributies echt uit elkaar. Op CachyOS bewerk je de PAM-servicebestanden rechtstreeks. Op Bazzite mag dat juist niet: die worden gegenereerd.

{{< tabs >}}
{{< tab name="CachyOS" >}}

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

{{< /tab >}}
{{< tab name="Bazzite" >}}

Bewerk hier niet met de hand de bestanden in `/etc/pam.d/`. Fedora beheert ze met **authselect**, en de eerstvolgende `authselect apply-changes` — die een update ook zelf kan aanroepen — zet terug wat er volgens het profiel hoort te staan, inclusief het weggooien van jouw aanpassingen.

authselect heeft hier een kant-en-klare feature voor:

```bash
sudo authselect enable-feature with-pam-u2f
```

Daarmee zijn `sudo`, polkit en GDM in één keer geregeld: de drie losse bestanden die de CachyOS-tab bewerkt komen allemaal uit hetzelfde profiel.

Controleer wat je hebt gekregen:

```bash
authselect current
```

Wil je de YubiKey *naast* het wachtwoord vereisen in plaats van in plaats daarvan, gebruik dan `with-pam-u2f-2fa` in plaats van `with-pam-u2f`. Terugdraaien:

```bash
sudo authselect disable-feature with-pam-u2f
```

Test daarna op dezelfde manier, vanuit een terminal die je kwijt mag:

```bash
sudo echo test
# "Please touch the FIDO authenticator." → aanraken → klaar
```

{{< /tab >}}
{{< /tabs >}}

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
