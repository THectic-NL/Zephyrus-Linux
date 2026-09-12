---
title: "eduroam Network Installation"
weight: 1
prev: docs/applications
next: docs/networking/mt7925-wifi-performance
---

Every official eduroam installer I tried failed on Saxion: the connection hangs during the TLS handshake and never completes. The cause is a certificate mismatch. Saxion's published CAT profile still pins the old GÉANT/USERTrust chain, while the RADIUS server now chains to HARICA roots ([#109](https://github.com/THectic-NL/Zephyrus-Linux/issues/109)).

This is a Saxion-specific script that sets up the connection with the right roots pinned. It uses PEAP/MSCHAPv2 and `domain-suffix-match`, needs Python 3.11+ (standard library only) and NetworkManager 1.8+.

## Setup

{{% steps %}}

### Download and verify

```bash
curl -LO https://zephyrus-linux.thectic.nl/scripts/saxion-eduroam.py
echo "17cd13c629ce480ece1a7896aff7d4061347ea0082b32dfa6b23dac6b34882ad  saxion-eduroam.py" | sha256sum -c
```

### Run

```bash
python3 saxion-eduroam.py
```

It removes any existing eduroam profile, asks for your username (a zenity dialog, or the terminal), and connects. Your password is handed to GNOME Keyring at connect time and stored encrypted, never in the connection profile.

{{% /steps %}}

![eduroam installer showing installation successful](/images/eduroam-installer-success.avif)

Source: [saxion-eduroam.py](/scripts/saxion-eduroam.py). SHA-256 `17cd13c629ce480ece1a7896aff7d4061347ea0082b32dfa6b23dac6b34882ad`.

Useful flags:

| Flag | Purpose |
|------|---------|
| `-u`, `--username` | Supply the username instead of being prompted |
| `--silent` | No dialogs; prompt and report on the terminal only |
| `--ignore-certificate` | Skip validation and print the chain the server served. Debugging only, see below |

{{< callout type="info" >}}
This script is Saxion-specific and validates against `ise.infra.saxion.net`. For another institution, start from the official CAT script at [cat.eduroam.org](https://cat.eduroam.org/).
{{< /callout >}}

{{< callout type="warning" >}}
This is a personal reverse-engineered rewrite of the official installer. I don't manage the eduroam network or Saxion's infrastructure, and I make no guarantee it keeps working if Saxion changes their setup. Use it at your own risk.
{{< /callout >}}

## If it can't validate the server

The trusted chain is pinned inside the script, so it breaks the day Saxion changes certificate authority. That is what happened in [#109](https://github.com/THectic-NL/Zephyrus-Linux/issues/109). If the script reports `unknown CA` or fails to authenticate:

```bash
python3 saxion-eduroam.py --ignore-certificate
```

This connects without validation and prints the chain the server actually served. Copy the root into `SAXION_CA_PEM`, open an issue with it, then reconnect without the flag.

{{< callout type="warning" >}}
Don't leave `--ignore-certificate` on. Without validation, any access point calling itself `eduroam` is trusted, and it can terminate the TLS tunnel itself and capture the MSCHAPv2 exchange, which is crackable offline. That is your Saxion password. `domain-suffix-match` does not help here: it checks the name on a certificate nobody verified.
{{< /callout >}}

## Manual setup

{{% details title="Via nmcli" closed="true" %}}

This stores the password directly in the connection profile, where the script uses `password-flags 1` to hand it to the keyring instead. It also needs `~/.config/saxion-eduroam/saxion-eduroam-ca.pem`, which the script creates, so run the script once first or drop the `802-1x.ca-cert` line and accept an unvalidated chain.

```bash
nmcli connection add \
  type wifi \
  con-name "eduroam" \
  ssid "eduroam" \
  wifi-sec.key-mgmt wpa-eap \
  802-1x.eap peap \
  802-1x.phase2-auth mschapv2 \
  802-1x.identity "user@institution.tld" \
  802-1x.password "your-password" \
  802-1x.anonymous-identity "anonymous@saxion.nl" \
  802-1x.ca-cert file://$HOME/.config/saxion-eduroam/saxion-eduroam-ca.pem \
  802-1x.domain-suffix-match "ise.infra.saxion.net" \
  802-1x.phase2-domain-suffix-match "ise.infra.saxion.net"
```

```bash
nmcli connection up eduroam
```

{{% /details %}}

{{% details title="Via GNOME Settings" closed="true" %}}

**Settings → Wi-Fi → eduroam**, then the **Security** tab:

| Setting | Value |
|---------|-------|
| Security | WPA & WPA2 Enterprise |
| Authentication | Protected EAP (PEAP) |
| PEAP version | Automatic |
| Inner authentication | MSCHAPv2 |
| CA certificate | `~/.config/saxion-eduroam/saxion-eduroam-ca.pem` (the script writes it) |
| Domain | `ise.infra.saxion.net`, in both the Domain and Phase2 domain fields |
| Anonymous identity | `anonymous@saxion.nl` |
| Identity | `user@institution.tld` |

![GNOME Settings eduroam Security tab](/images/eduroam-gnome-settings.avif)

{{% /details %}}

## Removal

```bash
nmcli connection delete eduroam
```

## Background

{{% details title="Why the official installers fail" closed="true" %}}

GÉANT moved its Trusted Certificate Service to HARICA. Saxion's CAT profile still pins the pre-migration USERTrust chain, so validation against the current server cannot succeed. The profile was edited on 2026-08-11, but the CA was not corrected.

![cat.eduroam.org portal for Saxion, entry last updated 2024-01-31](/images/eduroam-cat-portal.avif)

![The same portal on 2026-08-11, still serving the outdated CA](/images/eduroam-cat-portal-2026.avif)

Other methods that did not give a working connection here: the [geteduroam Linux app](https://github.com/geteduroam/linux-app), [easyroam-linux](https://github.com/jahtz/easyroam-linux), and the [UvA/HvA guide](https://linux.datanose.nl/linux/eduroam/).

{{% /details %}}

{{% details title="The pinned roots, and how to verify them" closed="true" %}}

The script trusts four HARICA roots and nothing else, rather than the ~150 public CAs your distribution ships:

| Root | Key | Expires |
|------|-----|---------|
| Hellenic Academic and Research Institutions RootCA 2015 | RSA | 2040 |
| HARICA TLS RSA Root CA 2021 | RSA | 2045 |
| Hellenic Academic and Research Institutions ECC RootCA 2015 | ECC | 2040 |
| HARICA TLS ECC Root CA 2021 | ECC | 2045 |

The RSA pair is what the server serves today. It chains through the cross-signed 2021 root up to the 2015 root, but HARICA publishes that cross certificate as valid only until 2029-08-31, after which the chain terminates at the self-signed 2021 root (already pinned, already what OpenSSL terminates on). The ECC pair covers an eventual move off RSA.

| Date | What happens |
|---|---|
| 2029-08-31 | Cross certificate expires; chain must terminate at the self-signed 2021 root |
| 2040-06-30 | Both 2015 roots expire |
| 2045-02-13 | Both 2021 roots expire |

Verify the fingerprints against HARICA's own repository at [repo.harica.gr](https://repo.harica.gr/rep_dyn.php):

| Entry in HARICA's repository | SHA-1 fingerprint |
|---|---|
| HARICA Root Certification Authority, 2015 | `01:0C:06:95:A6:98:19:14:FF:BF:5F:C6:B0:B6:95:EA:29:E9:12:A6` |
| HARICA TLS RSA Root CA 2021, 2021 | `02:2D:05:82:FA:88:CE:14:0C:06:79:DE:7F:14:10:E9:45:D7:A5:6D` |
| HARICA ECC Root Certification Authority, 2015 | `9F:F1:71:8D:92:D5:9A:F3:7D:74:97:B4:BC:6F:84:68:0B:BA:B6:66` |
| HARICA TLS ECC Root CA 2021, 2021 | `BC:B0:C1:9D:E9:98:92:70:19:38:57:E9:8D:A7:B4:5D:6E:EE:01:48` |

To check what the script installed on your machine:

```bash
awk '/BEGIN CERT/,/END CERT/' ~/.config/saxion-eduroam/saxion-eduroam-ca.pem |
  csplit -zs -f /tmp/root- -b '%d.pem' - '/BEGIN CERT/' '{*}'
for f in /tmp/root-*.pem; do
  openssl x509 -in "$f" -noout -subject -fingerprint -sha1
done
```

Every fingerprint must appear in the table above. If one does not, don't use the script; open an issue instead. Fingerprints last checked against HARICA's repository on 2026-08-31.

{{% /details %}}
