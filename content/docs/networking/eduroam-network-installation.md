---
title: "eduroam Network Installation"
weight: 1
prev: docs/applications
next: docs/virtualization/vm-setup
---

Getting eduroam to work on Linux is more painful than it should be. Every "official" method I tried failed; the connection would just hang during the TLS handshake and never connect. I eventually figured out a manual setup that works reliably and wrote a script around it. Sharing it here so you hopefully don't have to go through the same process.

## What doesn't work

{{% details title="cat.eduroam.org installer (official)" closed="true" %}}
The Python installer from [cat.eduroam.org](https://cat.eduroam.org/) provides a graphical interface and creates a connection profile. On some recent Linux distributions, the connection may hang during the TLS handshake due to changes in NetworkManager.

![cat.eduroam.org download portal for Saxion](/images/eduroam-cat-portal.avif)
{{% /details %}}

{{% details title="geteduroam Linux app (official)" closed="true" %}}

The [geteduroam Linux app](https://github.com/geteduroam/linux-app) (CLI and GUI RPM) may also experience connection issues on some recent distributions.
{{% /details %}}

{{% details title="easyroam-linux (community)" closed="true" %}}
[easyroam-linux](https://github.com/jahtz/easyroam-linux) by jahtz may not work on all distributions.
{{% /details %}}

{{% details title="UvA/HvA Linux eduroam guide" closed="true" %}}
The guide at [linux.datanose.nl](https://linux.datanose.nl/linux/eduroam/) (UvA/HvA) may not result in a working connection on all recent systems.
{{% /details %}}

## What does work

PEAP/MSCHAPv2 with CA validation via the system trust store and `domain-suffix-match` (the modern replacement for the deprecated `altsubject-matches`).

**Requirements:**
- Python 3.10+
- NetworkManager 1.8+ (`nmcli`)

### Connection settings

| Setting | Value |
|---------|-------|
| Security | WPA & WPA2 Enterprise |
| Authentication | Protected EAP (PEAP) |
| PEAP version | Automatic |
| Inner authentication | MSCHAPv2 |
| CA certificate | System CA bundle (`/etc/pki/tls/certs/ca-bundle.crt`) |
| Domain validation | `domain-suffix-match: ise.infra.saxion.net` |
| Phase2 domain validation | `phase2-domain-suffix-match: ise.infra.saxion.net` |
| Anonymous identity | `anonymous@saxion.nl` |
| Identity | `user@institution.tld` |

### Automated setup (recommended)

A Python script automates the full `nmcli` connection setup for Saxion:

```bash
curl -LO https://zephyrus-linux.stensel.nl/scripts/saxion-eduroam.py
python3 saxion-eduroam.py
```

The script removes any existing eduroam profile, prompts for your **username** via a GUI dialog (zenity, kdialog, or yad) or terminal fallback, and activates the connection. Your password is never asked by the script; it is requested by your GNOME Keyring at connection time and stored securely, never in plaintext.

{{< callout type="warning" >}}
You are downloading and running a script from the internet. If you want to be extra safe, verify the script source (or its checksum) before running it.
{{< /callout >}}

{{< callout type="info" >}}
This script is **Saxion-specific** and validates against Saxion's RADIUS server (`ise.infra.saxion.net`). For other institutions, use the official CAT script from [cat.eduroam.org](https://cat.eduroam.org/) as a starting point.
{{< /callout >}}

If everything goes well, you should see something like this:

![eduroam installer showing installation successful](/images/eduroam-installer-success.avif)

**Source:** [saxion-eduroam.py](/scripts/saxion-eduroam.py)

### Manual setup via nmcli

{{< callout type="info" >}}
This command stores the password directly in the connection profile. The automated script above uses `password-flags 1` instead, which stores the password securely in GNOME Keyring. Both approaches work; the script's method is more secure.
{{< /callout >}}

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
  802-1x.ca-cert file:///etc/pki/tls/certs/ca-bundle.crt \
  802-1x.domain-suffix-match "ise.infra.saxion.net" \
  802-1x.phase2-domain-suffix-match "ise.infra.saxion.net"
```

Then connect:

```bash
nmcli connection up eduroam
```

### Manual setup via GNOME Settings

1. Open **Settings → Wi-Fi**
2. Select **eduroam**
3. Go to the **Security** tab and fill in the settings from the table above
4. Enter your institutional credentials
5. Click **Apply**

Here's what the Security tab should look like:

![GNOME Settings eduroam Security tab](/images/eduroam-gnome-settings.avif)

### Removal

```bash
nmcli connection delete eduroam
```
