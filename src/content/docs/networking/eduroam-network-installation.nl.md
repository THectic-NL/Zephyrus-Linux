---
title: "eduroam Netwerkinstallatie"
weight: 1
prev: docs/applications
next: docs/networking/mt7925-wifi-performance
---

Elke officiële eduroam-installer die ik probeerde faalde op Saxion: de verbinding hangt tijdens de TLS-handshake en komt nooit door. De oorzaak is een certificaatmismatch. Saxion's gepubliceerde CAT-profiel legt nog de oude GÉANT/USERTrust-keten vast, terwijl de RADIUS-server inmiddels naar HARICA-roots ketent ([#109](https://github.com/THectic-NL/Zephyrus-Linux/issues/109)).

Dit is een Saxion-specifiek script dat de verbinding opzet met de juiste roots vastgelegd. Het gebruikt PEAP/MSCHAPv2 en `domain-suffix-match`, en heeft Python 3.11+ (alleen standaardbibliotheek) en NetworkManager 1.8+ nodig.

## Installatie

{{% steps %}}

### Downloaden en controleren

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/saxion-eduroam.py
echo "17cd13c629ce480ece1a7896aff7d4061347ea0082b32dfa6b23dac6b34882ad  saxion-eduroam.py" | sha256sum -c
```

### Uitvoeren

```bash
python3 saxion-eduroam.py
```

Het verwijdert een eventueel bestaand eduroam-profiel, vraagt je gebruikersnaam (een zenity-dialoog, of de terminal) en verbindt. Je wachtwoord gaat bij het verbinden naar GNOME Keyring en wordt versleuteld opgeslagen, nooit in het verbindingsprofiel.

{{% /steps %}}

![eduroam installer toont installatie geslaagd](/images/eduroam-installer-success.avif)

Bron: [saxion-eduroam.py](/scripts/saxion-eduroam.py). SHA-256 `17cd13c629ce480ece1a7896aff7d4061347ea0082b32dfa6b23dac6b34882ad`.

Handige vlaggen:

| Vlag | Doel |
|------|------|
| `-u`, `--username` | Geef de gebruikersnaam mee in plaats van hem te laten vragen |
| `--silent` | Geen dialogen; vragen en melden alleen op de terminal |
| `--ignore-certificate` | Sla validatie over en toon de keten die de server stuurde. Alleen om te debuggen, zie hieronder |

{{< callout type="info" >}}
Dit script is Saxion-specifiek en valideert tegen `ise.infra.saxion.net`. Voor een andere instelling: begin bij het officiële CAT-script op [cat.eduroam.org](https://cat.eduroam.org/).
{{< /callout >}}

{{< callout type="warning" >}}
Dit is een persoonlijke, reverse-engineerde herschrijving van de officiële installer. Ik beheer het eduroam-netwerk noch Saxion's infrastructuur, en ik geef geen garantie dat het blijft werken als Saxion iets aan hun configuratie wijzigt. Gebruik op eigen risico.
{{< /callout >}}

## Als de server niet gevalideerd kan worden

De vertrouwde keten ligt vast in het script, dus die breekt zodra Saxion van certificaatautoriteit wisselt. Dat is wat er in [#109](https://github.com/THectic-NL/Zephyrus-Linux/issues/109) gebeurde. Meldt het script `unknown CA` of lukt authenticatie niet:

```bash
python3 saxion-eduroam.py --ignore-certificate
```

Dit verbindt zonder validatie en toont de keten die de server werkelijk stuurde. Zet de root in `SAXION_CA_PEM`, meld hem in een issue, en verbind daarna opnieuw zonder de vlag.

{{< callout type="warning" >}}
Laat `--ignore-certificate` niet aanstaan. Zonder validatie wordt elk access point dat zich `eduroam` noemt vertrouwd, en dat kan de TLS-tunnel zelf afsluiten en de MSCHAPv2-uitwisseling opvangen, die offline te kraken is. Dat is je Saxion-wachtwoord. `domain-suffix-match` helpt hier niet: die controleert de naam op een certificaat dat niemand geverifieerd heeft.
{{< /callout >}}

## Handmatige setup

{{% details title="Via nmcli" closed="true" %}}

Dit slaat het wachtwoord direct op in het verbindingsprofiel, waar het script `password-flags 1` gebruikt om het aan de keyring over te dragen. Het heeft ook `~/.config/saxion-eduroam/saxion-eduroam-ca.pem` nodig, dat het script aanmaakt, dus draai eerst een keer het script of laat de regel `802-1x.ca-cert` weg en accepteer een niet-gevalideerde keten.

```bash
nmcli connection add \
  type wifi \
  con-name "eduroam" \
  ssid "eduroam" \
  wifi-sec.key-mgmt wpa-eap \
  802-1x.eap peap \
  802-1x.phase2-auth mschapv2 \
  802-1x.identity "gebruiker@instelling.nl" \
  802-1x.password "je-wachtwoord" \
  802-1x.anonymous-identity "anonymous@saxion.nl" \
  802-1x.ca-cert file://$HOME/.config/saxion-eduroam/saxion-eduroam-ca.pem \
  802-1x.domain-suffix-match "ise.infra.saxion.net" \
  802-1x.phase2-domain-suffix-match "ise.infra.saxion.net"
```

```bash
nmcli connection up eduroam
```

{{% /details %}}

{{% details title="Via GNOME Instellingen" closed="true" %}}

**Instellingen → Wi-Fi → eduroam**, dan het **Beveiliging**-tabblad:

| Instelling | Waarde |
|------------|--------|
| Beveiliging | WPA & WPA2 Enterprise |
| Authenticatie | Protected EAP (PEAP) |
| PEAP-versie | Automatisch |
| Interne authenticatie | MSCHAPv2 |
| CA-certificaat | `~/.config/saxion-eduroam/saxion-eduroam-ca.pem` (het script schrijft het) |
| Domein | `ise.infra.saxion.net`, in zowel het Domein- als het Fase-2-domeinveld |
| Anonieme identiteit | `anonymous@saxion.nl` |
| Identiteit | `gebruiker@instelling.nl` |

![GNOME Instellingen eduroam Beveiliging-tabblad](/images/eduroam-gnome-settings.avif)

{{% /details %}}

## Verwijderen

```bash
nmcli connection delete eduroam
```

## Achtergrond

{{% details title="Waarom de officiële installers falen" closed="true" %}}

GÉANT heeft zijn Trusted Certificate Service naar HARICA verhuisd. Saxion's CAT-profiel legt nog steeds de oude USERTrust-keten vast, dus validatie tegen de huidige server kan niet slagen. Het profiel is op 2026-08-11 bewerkt, maar de CA is niet gecorrigeerd.

![cat.eduroam.org-portaal voor Saxion, item laatst bijgewerkt 2024-01-31](/images/eduroam-cat-portal.avif)

![Hetzelfde portaal op 2026-08-11, nog steeds met de verouderde CA](/images/eduroam-cat-portal-2026.avif)

Andere methoden die hier geen werkende verbinding gaven: de [geteduroam Linux app](https://github.com/geteduroam/linux-app), [easyroam-linux](https://github.com/jahtz/easyroam-linux), en de [UvA/HvA-handleiding](https://linux.datanose.nl/linux/eduroam/).

{{% /details %}}

{{% details title="De vastgelegde roots, en hoe je ze controleert" closed="true" %}}

Het script vertrouwt vier HARICA-roots en niets anders, in plaats van de ~150 publieke CA's die je distributie meelevert:

| Root | Sleutel | Verloopt |
|------|---------|----------|
| Hellenic Academic and Research Institutions RootCA 2015 | RSA | 2040 |
| HARICA TLS RSA Root CA 2021 | RSA | 2045 |
| Hellenic Academic and Research Institutions ECC RootCA 2015 | ECC | 2040 |
| HARICA TLS ECC Root CA 2021 | ECC | 2045 |

Het RSA-paar is wat de server vandaag stuurt. Het ketent via de cross-signed 2021-root door naar de 2015-root, maar HARICA publiceert dat cross-certificaat als geldig tot 2029-08-31, waarna de keten eindigt bij de self-signed 2021-root (al vastgelegd, en waar OpenSSL vandaag al op uitkomt). Het ECC-paar dekt een eventuele overstap weg van RSA.

| Datum | Wat er gebeurt |
|---|---|
| 2029-08-31 | Cross-certificaat verloopt; keten moet eindigen bij de self-signed 2021-root |
| 2040-06-30 | Beide 2015-roots verlopen |
| 2045-02-13 | Beide 2021-roots verlopen |

Controleer de fingerprints tegen HARICA's eigen repository op [repo.harica.gr](https://repo.harica.gr/rep_dyn.php):

| Entry in HARICA's repository | SHA-1 fingerprint |
|---|---|
| HARICA Root Certification Authority, 2015 | `01:0C:06:95:A6:98:19:14:FF:BF:5F:C6:B0:B6:95:EA:29:E9:12:A6` |
| HARICA TLS RSA Root CA 2021, 2021 | `02:2D:05:82:FA:88:CE:14:0C:06:79:DE:7F:14:10:E9:45:D7:A5:6D` |
| HARICA ECC Root Certification Authority, 2015 | `9F:F1:71:8D:92:D5:9A:F3:7D:74:97:B4:BC:6F:84:68:0B:BA:B6:66` |
| HARICA TLS ECC Root CA 2021, 2021 | `BC:B0:C1:9D:E9:98:92:70:19:38:57:E9:8D:A7:B4:5D:6E:EE:01:48` |

Nakijken wat het script op je machine heeft gezet:

```bash
awk '/BEGIN CERT/,/END CERT/' ~/.config/saxion-eduroam/saxion-eduroam-ca.pem |
  csplit -zs -f /tmp/root- -b '%d.pem' - '/BEGIN CERT/' '{*}'
for f in /tmp/root-*.pem; do
  openssl x509 -in "$f" -noout -subject -fingerprint -sha1
done
```

Elke fingerprint moet in de tabel hierboven staan. Zo niet: gebruik het script niet, maar open een issue. Fingerprints laatst gecontroleerd tegen HARICA's repository op 2026-08-31.

{{% /details %}}
