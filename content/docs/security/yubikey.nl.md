---
title: "YubiKey 5C NFC"
weight: 20
---

Ik wilde mijn YubiKey gebruiken om de LUKS-schijfversleuteling bij het opstarten te ontgrendelen — inpluggen, aanraken, en het bureaublad laadt. Op deze pagina staat wat ik geprobeerd heb, waarom het aanvankelijk niet werkte, en wat er in de tussentijd wél werkt.

> **Status:** LUKS ontgrendeling met FIDO2 is onbetrouwbaar geweest op systemd 258. Deze pagina documenteert wat geprobeerd is, wat de oorzaak is, en wat je in de tussentijd kunt doen. De situatie kan verbeteren met systemd 259+.


## Wat op dit moment werkt

De YubiKey werkt betrouwbaar voor alles **buiten** de vroege bootprocessen:

- **OATH/TOTP** — Yubico Authenticator Flatpak 7.3.0 werkt uitstekend voor 2FA codes
- **SSH** — FIDO2-backed SSH sleutels
- **Bitwarden** — hardware-backed authenticatie
- **pam-u2f** — YubiKey touch voor `sudo` en GDM-schermvergrendeling (zie hieronder)


## Wat Geprobeerd Is: FIDO2 LUKS Ontgrendeling

Het doel was: YubiKey inpluggen → aanraken bij boot → LUKS ontgrendelt → bureaublad. Geen LUKS-wachtwoord nodig dus.

### Wat gedaan is

**Packages geïnstalleerd:**
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

### Wat werkte

- Enrollment werkt (keyslot 1, touch-only, `fido2-clientPin-required: false`)
- FIDO2 libraries zijn aanwezig in initramfs (`lsinitrd | grep fido`)
- Incidentele succesvolle boots bij het snel aanraken (constant spammen) van de YubiKey op het juiste moment

### Wat niet werkte

1. **Touch venster is ~1-2 seconden** — niet genoeg tijd om te reageren. Er is geen configureerbare `token-timeout=` in crypttab tot systemd 259 uit is.

2. **Geen wachtwoord fallback** — als FIDO2 mislukt, vraagt het systeem niet om een LUKS-wachtwoord. Het valt terug in een dracut emergency shell met een vergrendeld root account. Dit is een bevestigde regressie geïntroduceerd in **systemd 257** (issue [#35393](https://github.com/systemd/systemd/issues/35393)). Dit wil je niet.

3. **dracut initqueue race met de YubiKey** — het USB HID apparaat is niet gereed binnen het 5-seconden dracut initqueue venster op deze hardware, waardoor `systemd-cryptsetup` mislukt voordat het de touch prompt kan tonen.

4. **rhgb/plymouth verbergt prompts** — zelfs met verbose boot is de touch prompt verborgen achter Plymouth.

### Oorzaak

systemd 257/258 heeft een regressie waarbij een mislukte FIDO2 authenticatie niet terugvalt op een wachtwoord. Gecombineerd met het korte dracut initqueue venster door de USB stack op deze laptop, resulteert dit in een onherstelbare boot loop als FIDO2 niet slaagt bij de eerste poging.

### Wat teruggedraaid is

```bash
# FIDO2 verwijderen uit LUKS
sudo systemd-cryptenroll --wipe-slot=fido2 /dev/nvme1n1p3

# crypttab herstellen naar alleen wachtwoord
# alleen discard, geen fido2-device=auto

# dracut config verwijderen
sudo rm /etc/dracut.conf.d/fido2.conf
sudo rm -r /etc/systemd/system/systemd-cryptsetup@.service.d/

# initramfs herbouwen
sudo dracut --force --regenerate-all
```


## Wanneer Opnieuw Proberen

Wachten op **systemd 259+**. Systemd 259 voegt `token-timeout=` toe als crypttab optie, wat een configureerbaar wachtvenster geeft voor de touch prompt. Gecombineerd met een fix voor de fallback regressie zou FIDO2 LUKS ontgrendeling ook op CachyOS betrouwbaar moeten worden.

Bij een nieuwe poging is de enrollment procedure zelf correct — alleen de systemd versie is het obstakel op dit moment.

## YubiKey Gebruiken voor sudo en Schermvergrendeling (pam-u2f)

Een betrouwbaar alternatief dat wel werkt: vereist een YubiKey touch voor `sudo` en/of het GDM-vergrendelscherm.

> **Nog te documenteren na testen.**

---

{{< callout type="info" >}}
Probleemoplossing voor YubiKey en LUKS staat op de pagina [Bekende Problemen]({{< relref "/docs/known-issues" >}}).
{{< /callout >}}
