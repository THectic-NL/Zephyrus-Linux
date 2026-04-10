---
title: "eduroam Netwerkinstallatie"
weight: 1
prev: docs/applications
next: docs/virtualization/vm-setup
---

eduroam werkend krijgen op Linux is pijnlijker dan het zou moeten zijn. Elke "officiële" methode die ik probeerde faalde; de verbinding bleef gewoon hangen tijdens de TLS-handshake en lukte nooit. Uiteindelijk heb ik een handmatige setup gevonden die betrouwbaar werkt en daar een script omheen geschreven. Ik deel het hier zodat jij hopelijk niet hetzelfde proces hoeft door te maken.

## Wat niet werkt

{{% details title="cat.eduroam.org installer (officieel)" closed="true" %}}
De Python-installer van [cat.eduroam.org](https://cat.eduroam.org/) biedt een grafische interface en maakt een verbindingsprofiel aan. Op sommige recente Linux-distributies kan de verbinding blijven hangen tijdens de TLS-handshake door wijzigingen in NetworkManager.

![cat.eduroam.org downloadportaal voor Saxion](/images/eduroam-cat-portal.avif)
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

PEAP/MSCHAPv2 met CA-validatie via de systeem-truststore en `domain-suffix-match` (de moderne vervanging voor het verouderde `altsubject-matches`).

**Vereisten:**
- Python 3.10+
- NetworkManager 1.8+ (`nmcli`)

### Verbindingsinstellingen

| Instelling | Waarde |
|------------|--------|
| Beveiliging | WPA & WPA2 Enterprise |
| Authenticatie | Protected EAP (PEAP) |
| PEAP-versie | Automatisch |
| Interne authenticatie | MSCHAPv2 |
| CA-certificaat | Systeem-CA-bundel (`/etc/pki/tls/certs/ca-bundle.crt`) |
| Domeinvalidatie | `domain-suffix-match: ise.infra.saxion.net` |
| Fase-2-domeinvalidatie | `phase2-domain-suffix-match: ise.infra.saxion.net` |
| Anonieme identiteit | `anonymous@saxion.nl` |
| Identiteit | `gebruiker@instelling.nl` |

### Geautomatiseerde installatie (aanbevolen)

Een Python-script automatiseert de volledige `nmcli`-verbindingsconfiguratie voor Saxion:

```bash
# 1. Download
curl -LO https://zephyrus-linux.stensel.nl/scripts/saxion-eduroam.py

# 2. Controleer de checksum
echo "bb8c45e801fbd37bc7d8c12104ad3c525bc664571598344b90c5da0437631cf8  saxion-eduroam.py" | sha256sum -c

# 3. Uitvoeren
python3 saxion-eduroam.py
```

**SHA256:** `bb8c45e801fbd37bc7d8c12104ad3c525bc664571598344b90c5da0437631cf8`

Het script verwijdert een eventueel bestaand eduroam-profiel, vraagt je **gebruikersnaam** via een GUI-dialoog (zenity, kdialog of yad) of terminal-fallback, en activeert de verbinding. Je wachtwoord wordt nooit door het script gevraagd; dat wordt bij het verbinden opgevraagd door je GNOME Keyring en veilig opgeslagen, nooit in platte tekst.

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
Dit commando slaat het wachtwoord direct op in het verbindingsprofiel. Het geautomatiseerde script hierboven gebruikt `password-flags 1`, waardoor het wachtwoord veilig in de GNOME Keyring wordt opgeslagen. Beide methoden werken; de aanpak van het script is veiliger.
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
  802-1x.ca-cert file:///etc/pki/tls/certs/ca-bundle.crt \
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
