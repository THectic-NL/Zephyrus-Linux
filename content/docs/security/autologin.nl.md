---
title: "GDM Autologin"
weight: 19
---

Na het ontgrendelen van de schijf met LUKS bij het opstarten wilde ik niet nog een keer een wachtwoord invoeren om in te loggen. Dit slaat het GDM-inlogscherm volledig over — je voert je schijfwachtwoord één keer in en het bureaublad laadt direct. De schermvergrendeling vraagt gewoon nog steeds om je wachtwoord.

**Bootgedrag:**
- Opstarten → LUKS wachtwoord prompt → bureaublad (geen tweede inlog)
- Slaapstand / schermvergrendeling → wachtwoord vereist zoals normaal


## Configuratie

Bewerk de GDM configuratie:

```bash
sudo nano /etc/gdm/custom.conf
```

Voeg `AutomaticLoginEnable` en `AutomaticLogin` toe onder `[daemon]`:

```ini
[daemon]
AutomaticLoginEnable=True
AutomaticLogin=sten
```

Volledig bestand ter referentie:

```ini
# GDM configuration storage
[daemon]
AutomaticLoginEnable=True
AutomaticLogin=sten

[security]

[xdmcp]

[chooser]

[debug]
```

Opslaan met `Ctrl+X`, `y` en dan herstarten:

```bash
sudo reboot
```


## Verificatie

Na herstart vraagt LUKS om een wachtwoord. Eenmaal ingevoerd laadt het bureaublad direct zonder GDM inlogscherm.

Bevestig dat autologin actief is:

```bash
sudo cat /etc/gdm/custom.conf | grep -i auto
```

Verwachte output:
```
AutomaticLoginEnable=True
AutomaticLogin=sten
```

## Opmerkingen

- Autologin geldt alleen voor de **initiële bootsessie**. GDM wordt niet geactiveerd bij hervatten na slaapstand.
- De GNOME **schermvergrendeling** (Super+L, deksel sluiten, time-out bij inactiviteit) wordt beheerd door `gnome-screensaver` / `gnome-shell`, niet door GDM. Deze vraagt altijd om je gebruikerswachtwoord, ongeacht de autologin-instellingen.
- Als er een tweede gebruikersaccount op het systeem staat, krijgt alleen de geconfigureerde gebruiker autologin. Andere accounts krijgen altijd een GDM-prompt.


## Probleemoplossing


{{% details title="Autologin werkt niet na config wijziging" closed="true" %}}

Verifieer dat het configuratiebestand correct is:

```bash
sudo cat /etc/gdm/custom.conf
```

Zorg dat `AutomaticLoginEnable=True` onder `[daemon]` staat en dat de gebruikersnaam exact overeenkomt:

```bash
whoami
```

Check ook dat GDM de actieve display manager is:

```bash
systemctl status gdm
```

{{% /details %}}

{{% details title="Autologin uitschakelen" closed="true" %}}

```bash
sudo nano /etc/gdm/custom.conf
```

Verwijder of becommentarieer de twee regels:

```ini
#AutomaticLoginEnable=True
#AutomaticLogin=sten
```

Herstart om toe te passen.

{{% /details %}}
