---
title: "eduroam Netwerkinstallatie"
weight: 1
prev: docs/applications
next: docs/virtualization/vm-setup
---

eduroam werkend krijgen op Linux is pijnlijker dan het zou moeten zijn. Elke "officiële" methode die ik probeerde faalde; de verbinding bleef gewoon hangen tijdens de TLS-handshake en lukte nooit. Uiteindelijk heb ik een handmatige setup gevonden die betrouwbaar werkt en daar een script omheen geschreven. Ik deel het hier zodat jij hopelijk niet hetzelfde proces hoeft door te maken.

## Wat niet werkt

{{% details title="cat.eduroam.org installer (officieel)" closed="true" %}}
De Python-installer van [cat.eduroam.org](https://cat.eduroam.org/) biedt een grafische interface en maakt een verbindingsprofiel aan. Hij meldt "Installation successful" zonder ooit een verbinding te proberen, waarna de verbinding eindeloos blijft hangen tijdens de TLS-handshake.

De oorzaak is niet NetworkManager: de CA in Saxion's CAT-profiel is de oude USERTrust / GEANT OV RSA CA 4 keten, terwijl de RADIUS-server inmiddels naar HARICA-roots ketent. Validatie kan dan niet slagen. Zie [#109](https://github.com/THectic-NL/Zephyrus-Linux/issues/109) voor de fingerprints en handshake-logs.

![cat.eduroam.org-portaal voor Saxion, item laatst bijgewerkt 2024-01-31](/images/eduroam-cat-portal.avif)

**Update, augustus 2026.** Het profiel is op 2026-08-11 aangeraakt, maar de CA is niet gecorrigeerd. De installer die je vanaf deze pagina downloadt draagt nog steeds de oude USERTrust-keten en kan de server dus nog altijd niet valideren. Beide screenshots blijven hier staan: de eerste laat zien dat het item sinds januari 2024 onaangeroerd was, de tweede laat een recente bewerking zien die het werkelijke probleem niet oploste.

![Hetzelfde portaal op 2026-08-11, nog steeds met de verouderde CA](/images/eduroam-cat-portal-2026.avif)
{{% /details %}}

{{% details title="geteduroam Linux app (officieel)" closed="true" %}}

De [geteduroam Linux app](https://github.com/geteduroam/linux-app) (CLI en GUI RPM) kan op sommige recente distributies ook verbindingsproblemen ondervinden.
{{% /details %}}

{{% details title="easyroam-linux (community)" closed="true" %}}
[easyroam-linux](https://github.com/jahtz/easyroam-linux) van jahtz werkt mogelijk niet op alle distributies.
{{% /details %}}

{{% details title="UvA/HvA Linux eduroam handleiding" closed="true" %}}
De handleiding op [linux.datanose.nl](https://linux.datanose.nl/linux/eduroam/) (UvA/HvA) levert mogelijk niet op alle recente systemen een werkende verbinding op.
{{% /details %}}

## Wat wel werkt

PEAP/MSCHAPv2, gevalideerd tegen Saxion's eigen certificaatautoriteit die in het script
is vastgelegd, plus `domain-suffix-match` (de moderne vervanging voor het verouderde
`altsubject-matches`).

Het script wees eerder naar de systeem-truststore. Daarmee kon elk van de ongeveer 150
publieke CA's die je distributie meelevert instaan voor een server die zich
`ise.infra.saxion.net` noemt. Nu worden alleen deze vier HARICA-roots vertrouwd:

| Root | Sleutel | Verloopt |
|------|---------|----------|
| Hellenic Academic and Research Institutions RootCA 2015 | RSA | 2040 |
| HARICA TLS RSA Root CA 2021 | RSA | 2045 |
| Hellenic Academic and Research Institutions ECC RootCA 2015 | ECC | 2040 |
| HARICA TLS ECC Root CA 2021 | ECC | 2045 |

Het RSA-paar is wat de server vandaag stuurt, en beide helften daarvan liggen niet voor
niets vast. De server ketent nu via de *cross-signed* 2021-root door naar de 2015-root,
maar HARICA publiceert dat cross-certificaat als geldig tot **2029-08-31**. Daarna moet
de keten eindigen bij de self-signed 2021-root. Die ligt hier al vast, en OpenSSL komt er
vandaag al op uit.

Het ECC-paar dekt een overstap weg van RSA. HARICA's repository noemt
`HARICA GEANT TLS ECC 1` (2025) al bij de intermediates, dus dat pad bestaat. Alle vier
zijn HARICA-roots, dus het blijft bij één CA-operator.

| Datum | Wat er gebeurt |
|---|---|
| 2029-08-31 | Cross-certificaat verloopt; keten moet eindigen bij de self-signed 2021-root |
| 2040-06-30 | Beide 2015-roots verlopen |
| 2045-02-13 | Beide 2021-roots verlopen |

Fingerprints laatst gecontroleerd tegen HARICA's repository op **2026-08-31**.

#### Controleer de vastgelegde roots zelf

Geloof deze pagina niet op haar woord. HARICA publiceert de fingerprints van hun eigen
roots op [repo.harica.gr](https://repo.harica.gr/rep_dyn.php). Kies de root in de
dropdown en vergelijk de SHA-1:

| Entry in HARICA's repository | SHA-1 fingerprint |
|---|---|
| HARICA Root Certification Authority, 2015 | `01:0C:06:95:A6:98:19:14:FF:BF:5F:C6:B0:B6:95:EA:29:E9:12:A6` |
| HARICA TLS RSA Root CA 2021, 2021 | `02:2D:05:82:FA:88:CE:14:0C:06:79:DE:7F:14:10:E9:45:D7:A5:6D` |
| HARICA ECC Root Certification Authority, 2015 | `9F:F1:71:8D:92:D5:9A:F3:7D:74:97:B4:BC:6F:84:68:0B:BA:B6:66` |
| HARICA TLS ECC Root CA 2021, 2021 | `BC:B0:C1:9D:E9:98:92:70:19:38:57:E9:8D:A7:B4:5D:6E:EE:01:48` |

Nakijken wat het script daadwerkelijk op je machine heeft gezet:

```bash
awk '/BEGIN CERT/,/END CERT/' ~/.config/saxion-eduroam/saxion-eduroam-ca.pem |
  csplit -zs -f /tmp/root- -b '%d.pem' - '/BEGIN CERT/' '{*}'
for f in /tmp/root-*.pem; do
  openssl x509 -in "$f" -noout -subject -fingerprint -sha1
done
```

Elke fingerprint die eruit komt moet in de tabel hierboven staan. Zo niet: gebruik het
script niet, maar open een issue.

Dit is dezelfde controle die wij doen: niets wordt vastgelegd omdat een handshake het
aanbood, alleen omdat de CA-operator het publiceert.

GÉANT heeft zijn Trusted Certificate Service naar HARICA verhuisd, en het officiële
CAT-profiel legt nog steeds de oude USERTrust-keten vast, en daarom faalt de officiële
installer. Wisselt Saxion opnieuw van CA-operator, dan breekt dit script ook, maar het
toont dan de keten die de server werkelijk stuurde in plaats van stil vast te lopen.

**Vereisten:**
- Python 3.11+ (alleen standaardbibliotheek, geen `pip install`, geen `dbus-python`)
- NetworkManager 1.8+ (`nmcli`)
- Optioneel: `zenity` (GNOME) of `kdialog` (KDE) voor grafische dialogen; anders de terminal
- Optioneel: toegang tot de systeemjournal, om certificaatfouten te kunnen verklaren

### Verbindingsinstellingen

| Instelling | Waarde |
|------------|--------|
| Beveiliging | WPA & WPA2 Enterprise |
| Authenticatie | Protected EAP (PEAP) |
| PEAP-versie | Automatisch |
| Interne authenticatie | MSCHAPv2 |
| CA-certificaat | De HARICA-roots waar de server naartoe ketent, geschreven naar `~/.config/saxion-eduroam/saxion-eduroam-ca.pem` |
| Domeinvalidatie | `domain-suffix-match: ise.infra.saxion.net` |
| Fase-2-domeinvalidatie | `phase2-domain-suffix-match: ise.infra.saxion.net` |
| Anonieme identiteit | `anonymous@saxion.nl` |
| Identiteit | `gebruiker@instelling.nl` |

### Geautomatiseerde installatie (aanbevolen)

Een Python-script automatiseert de volledige `nmcli`-verbindingsconfiguratie voor Saxion:

```bash
# 1. Download
curl -LO https://zephyrus-linux.thectic.nl/scripts/saxion-eduroam.py

# 2. Controleer de checksum
echo "17cd13c629ce480ece1a7896aff7d4061347ea0082b32dfa6b23dac6b34882ad  saxion-eduroam.py" | sha256sum -c

# 3. Uitvoeren
python3 saxion-eduroam.py
```

#### Als het certificaat niet meer klopt

De vertrouwde keten ligt vast in het script, dus die breekt zodra Saxion van
certificaatautoriteit wisselt. Precies wat er in
[#109](https://github.com/THectic-NL/Zephyrus-Linux/issues/109) gebeurde. Meldt
het script `unknown CA` of lukt authenticatie niet, dan verbindt
`--ignore-certificate` zonder te valideren en toont het welke keten de server
werkelijk stuurde:

```bash
python3 saxion-eduroam.py --ignore-certificate
```

Zet de root die eruit komt in `SAXION_CA_PEM`, meld hem in een issue, en verbind
daarna opnieuw zonder de vlag.

**Laat dit niet aanstaan.** Zonder validatie wordt elk access point dat zich
`eduroam` noemt vertrouwd. Dat kan de TLS-tunnel zelf afsluiten en de
MSCHAPv2-uitwisseling opvangen, die offline te kraken is. Dat is je
Saxion-wachtwoord. `domain-suffix-match` helpt hier niet: die controleert de naam
op een certificaat dat niemand geverifieerd heeft. Gebruik de vlag om te
diagnosticeren en verbind daarna netjes.

**SHA256:** `17cd13c629ce480ece1a7896aff7d4061347ea0082b32dfa6b23dac6b34882ad`

Het script verwijdert een eventueel bestaand eduroam-profiel, vraagt je **gebruikersnaam** via een GUI-dialoog (kdialog op KDE, zenity op GNOME) of een terminal-fallback, en activeert de verbinding. Je wachtwoord wordt nooit door het script gevraagd; dat wordt bij het verbinden opgevraagd door je keyring (GNOME Keyring of KWallet) en versleuteld opgeslagen, nooit in platte tekst.

Handige vlaggen:

| Vlag | Doel |
|------|------|
| `-u`, `--username` | Geef de gebruikersnaam mee in plaats van hem te laten vragen |
| `--silent` | Geen dialogen; vragen en melden alleen op de terminal |
| `--ignore-certificate` | Sla validatie over en toon de keten die de server stuurde. Alleen om te debuggen, zie de waarschuwing hierboven |

{{< callout type="info" >}}
Dit script is **Saxion-specifiek** en valideert tegen de Saxion RADIUS-server (`ise.infra.saxion.net`). Voor andere instellingen: gebruik het officiële CAT-script van [cat.eduroam.org](https://cat.eduroam.org/) als startpunt.
{{< /callout >}}

{{< callout type="warning" >}}
Dit is een persoonlijke, reverse-engineered herschrijving op basis van de officiële [cat.eduroam.org](https://cat.eduroam.org/) installer, die verouderd was en bij mij niet werkte. Ik beheer het eduroam-netwerk noch de Saxion-infrastructuur. Ik geef geen garanties over de werking, het onderhoud of de correctheid van dit script als Saxion iets aan hun configuratie wijzigt. Gebruik op eigen risico.
{{< /callout >}}

Als alles goed gaat, zie je zoiets als dit:

![eduroam installer toont installatie geslaagd](/images/eduroam-installer-success.avif)

**Bron:** [saxion-eduroam.py](/scripts/saxion-eduroam.py)

### Handmatige setup via nmcli

{{< callout type="info" >}}
Dit commando slaat het wachtwoord direct op in het verbindingsprofiel. Het geautomatiseerde script hierboven gebruikt `password-flags 1`, waardoor het wachtwoord aan je keyring wordt overgedragen. Beide methoden werken; de aanpak van het script is veiliger.

Het verwijst ook naar `~/.config/saxion-eduroam/saxion-eduroam-ca.pem`, dat pas bestaat nadat het script een keer gedraaid heeft. Draai dus eerst het script, of laat de regel `802-1x.ca-cert` weg en accepteer dat de keten dan niet gevalideerd wordt.
{{< /callout >}}

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

Maak daarna verbinding:

```bash
nmcli connection up eduroam
```

### Handmatige setup via GNOME Instellingen

1. Open **Instellingen → Wi-Fi**
2. Selecteer **eduroam**
3. Ga naar het **Beveiliging**-tabblad en vul de instellingen in uit de tabel hierboven
4. Voer je instellingsgegevens in
5. Klik op **Toepassen**

Zo hoort het Beveiliging-tabblad eruit te zien:

![GNOME Instellingen eduroam Beveiliging-tabblad](/images/eduroam-gnome-settings.avif)

### Verwijderen

```bash
nmcli connection delete eduroam
```
