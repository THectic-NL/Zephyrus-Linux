#!/usr/bin/env python3
"""
Saxion Eduroam Installer (Linux)
-------------------------------
Configures eduroam Wi-Fi for Saxion University using NetworkManager (nmcli).
Uses secure PEAP/MSCHAPv2 with system CA certificates and domain validation.

Authors: Stensel8, GitHub Copilot
This rewrite is based on: https://cat.eduroam.org/
The original script was incompatible with Linux 6.19+ and outdated (last updated: 2024-01-31).
"""

from __future__ import annotations
import argparse
import getpass
import os
import re
import shutil
import subprocess
import sys

# --- Configuration ---
CON_NAME = "eduroam"
SSID = "eduroam"
REALM = "saxion.nl"
SERVER_DOMAIN = "ise.infra.saxion.net"
ANONYMOUS_ID = f"anonymous@{REALM}"

# nmcli's default is 90s of silence, which looks like a hang. Cut it short.
CONNECT_TIMEOUT = 45

# NetworkManager re-reads this on every connect, so it cannot be a temp file.
# In the user's config dir, so no root needed.
CA_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
    "saxion-eduroam",
)
CA_FILE = os.path.join(CA_DIR, "saxion-eduroam-ca.pem")

# The roots ise.infra.saxion.net chains to. GEANT moved its cert service to
# HARICA; this file used to pin the old USERTrust/"GEANT OV RSA CA 4" chain,
# which the server stopped sending, so every connect died on "unknown CA"
# (#109). Don't guess these -- read them off a real handshake:
#
#   nmcli connection modify eduroam 802-1x.ca-cert ""
#   nmcli connection up eduroam
#   journalctl -u wpa_supplicant -b | grep CTRL-EVENT-EAP-PEER-CERT
#
#   HARICA RootCA 2015              A0:40:92:9A:02:CE:53:B4... expires 2040
#   HARICA TLS RSA Root CA 2021     D9:5D:0E:8E:DA:79:52:5B... expires 2045
#
# The first is what the server currently chains to; the second keeps this
# working once GEANT drops the cross-signature. The GEANT TLS RSA 1
# intermediate is not pinned -- the server sends it, and intermediates rotate
# often enough to break us again.
#
# Yes, pinning breaks when Saxion switches CA. That is the trade: otherwise any
# of ~150 public CAs can impersonate the RADIUS server, and PEAP/MSCHAPv2 hands
# it a hash of the user's password.
SAXION_CA_PEM = """\
-----BEGIN CERTIFICATE-----
MIIGCzCCA/OgAwIBAgIBADANBgkqhkiG9w0BAQsFADCBpjELMAkGA1UEBhMCR1Ix
DzANBgNVBAcTBkF0aGVuczFEMEIGA1UEChM7SGVsbGVuaWMgQWNhZGVtaWMgYW5k
IFJlc2VhcmNoIEluc3RpdHV0aW9ucyBDZXJ0LiBBdXRob3JpdHkxQDA+BgNVBAMT
N0hlbGxlbmljIEFjYWRlbWljIGFuZCBSZXNlYXJjaCBJbnN0aXR1dGlvbnMgUm9v
dENBIDIwMTUwHhcNMTUwNzA3MTAxMTIxWhcNNDAwNjMwMTAxMTIxWjCBpjELMAkG
A1UEBhMCR1IxDzANBgNVBAcTBkF0aGVuczFEMEIGA1UEChM7SGVsbGVuaWMgQWNh
ZGVtaWMgYW5kIFJlc2VhcmNoIEluc3RpdHV0aW9ucyBDZXJ0LiBBdXRob3JpdHkx
QDA+BgNVBAMTN0hlbGxlbmljIEFjYWRlbWljIGFuZCBSZXNlYXJjaCBJbnN0aXR1
dGlvbnMgUm9vdENBIDIwMTUwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoIC
AQDC+Kk/G4n8PDwEXT2QNrCROnk8ZlrvbTkBSRq0t89/TSNTt5AA4xMqKKYx8ZEA
4yjsriFBzh/a/X0SWwGDD7mwX5nh8hKDgE0GPt+sr+ehiGsxr/CL0BgzuNtFajT0
AoAkKAoCFZVedioNmToUW/bLy1O8E00BiDeUJRtCvCLYjqOWXjrZMts+6PAQZe10
4S+nfK8nNLspfZu2zwnI5dMK/IhlZXQK3HMcXM1AsRzUtoSMTFDPaI6oWa7CJ06C
ojXdFPQf/7J31Ycvqm59JCfnxssm5uX+Zwdj2EUN3TpZZTlYepKZcj2chF6IIbjV
9Cz82XBST3i4vTwri5WY9bPRaM8gFH5MXF/ni+X1NYEZN9cRCLdmvtNKzoNXADrD
gfgXy5I2XdGj2HUb4Ysn6npIQf1FGQatJ5lOwXBH3bWfgVMS5bGMSF0xQxfjjMZ6
Y5ZLKTBOhE5iGV48zpeQpX8B653g+IuJ3SWYPZK2fu/Z8VFRfS0myGlZYeCsargq
NhEEelC9MoS+L9xy1dcdFkfkR2YgP/SWxa+OAXqlD3pk9Q0Yh9muiNX6hME6wGko
LfINaFGq46V3xqSQDqE3izEjR8EJCOtu93ib14L8hCCZSRm2Ekax+0VVFqmjZayc
Bw/qa9wfLgZy7IaIEuQt218FL+TwA9MmM+eAws1CoRc0CwIDAQABo0IwQDAPBgNV
HRMBAf8EBTADAQH/MA4GA1UdDwEB/wQEAwIBBjAdBgNVHQ4EFgQUcRVnyMjJvXVd
ctA4GGqd83EkVAswDQYJKoZIhvcNAQELBQADggIBAHW7bVRLqhBYRjTyYtcWNl0I
XtVsyIe9tC5G8jH4fOpCtZMWVdyhDBKg2mF+D1hYc2Ryx+hFjtyp8iY/xnmMsVMI
M4GwVhO+5lFc2JsKT0ucVlMC6U/2DWDqTUJV6HwbISHTGzrMd/K4kPFox/la/vot
9L/J9UUbzjgQKjeKeaO04wlshYaT/4mWJ3iBj2fjRnRUjtkNaeJK9E10A/+yd+2V
Z5fkscWrv2oj6NSU4kQoYsRL4vDY4ilrGnB+JGGTe08DMiUNRSQrlrRGar9KC/ea
j8GsGsVn82800vpzY4zvFrCopEYq+OsS7HK07/grfoxSwIuEVPkvPuNVqNxmsdnh
X9izjFk0WaSrT2y7HxjbdavYy5LNlDhhDgcGH0tGEPEVvo2FXDtKK4F5D7Rpn0lQ
l033DlZdwJVqwjbDG2jJ9SrcR5q+ss7FJej6A7na+RZukYT1HCjI/CbM1xyQVqdf
bzoEvM14iQuODy+jqk+iGxI9FghAD/FGTNeqewjBCvVtJ94Cj8rDtSvK6evIIVM4
pcw72Hc3MKJP2W/R8kCtQXoXxdZKNYm3QdV8hn9VTYNKpXMgwDqvkPGaJI7ZjnHK
e7iG2rKPmT4dEw0SEe7Uq/DpFXYC5ODfqiAeW2GFZECpkJcNrVPSWh2HagCXZWK0
vm9qp/UsQu0yrbYhnr68
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIFpDCCA4ygAwIBAgIQOcqTHO9D88aOk8f0ZIk4fjANBgkqhkiG9w0BAQsFADBs
MQswCQYDVQQGEwJHUjE3MDUGA1UECgwuSGVsbGVuaWMgQWNhZGVtaWMgYW5kIFJl
c2VhcmNoIEluc3RpdHV0aW9ucyBDQTEkMCIGA1UEAwwbSEFSSUNBIFRMUyBSU0Eg
Um9vdCBDQSAyMDIxMB4XDTIxMDIxOTEwNTUzOFoXDTQ1MDIxMzEwNTUzN1owbDEL
MAkGA1UEBhMCR1IxNzA1BgNVBAoMLkhlbGxlbmljIEFjYWRlbWljIGFuZCBSZXNl
YXJjaCBJbnN0aXR1dGlvbnMgQ0ExJDAiBgNVBAMMG0hBUklDQSBUTFMgUlNBIFJv
b3QgQ0EgMjAyMTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAIvC569l
mwVnlskNJLnQDmT8zuIkGCyEf3dRywQRNrhe7Wlxp57kJQmXZ8FHws+RFjZiPTgE
4VGC/6zStGndLuwRo0Xua2s7TL+MjaQenRG56Tj5eg4MmOIjHdFOY9TnuEFE+2uv
a9of08WRiFukiZLRgeaMOVig1mlDqa2YUlhu2wr7a89o+uOkXjpFc5gH6l8Cct4M
pbOfrqkdtx2z/IpZ525yZa31MJQjB/OCFks1mJxTuy/K5FrZx40d/JiZ+yykgmvw
Kh+OC19xXFyuQnspiYHLA6OZyoieC0AJQTPb5lh6/a6ZcMBaD9YThnEvdmn8kN3b
LW7R8pv1GmuebxWMevBLKKAiOIAkbDakO/IwkfN4E8/BPzWr8R0RI7VDIp4BkrcY
AuUR0YLbFQDMYTfBKnya4dC6s1BG7oKsnTH4+yPiAwBIcKMJJnkVU2DzOFytOOqB
AGMUuTNe3QvboEUHGjMJ+E20pwKmafTCWQWIZYVWrkvL4N48fS0ayOn7H6NhStYq
E613TBoYm5EPWNgGVMWX+Ko/IIqmhaZ39qb8HOLubpQzKoNQhArlT4b4UEV4AIHr
W2jjJo3Me1xR9BQsQL4aYB16cmEdH2MtiKrOokWQCPxrvrNQKlr9qEgYRtaQQJKQ
CoReaDH46+0N0x3GfZkYVVYnZS6NRcUk7M7jAgMBAAGjQjBAMA8GA1UdEwEB/wQF
MAMBAf8wHQYDVR0OBBYEFApII6ZgpJIKM+qTW8VX6iVNvRLuMA4GA1UdDwEB/wQE
AwIBhjANBgkqhkiG9w0BAQsFAAOCAgEAPpBIqm5iFSVmewzVjIuJndftTgfvnNAU
X15QvWiWkKQUEapobQk1OUAJ2vQJLDSle1mESSmXdMgHHkdt8s4cUCbjnj1AUz/3
f5Z2EMVGpdAgS1D0NTsY9FVqQRtHBmg8uwkIYtlfVUKqrFOFrJVWNlar5AWMxaja
H6NpvVMPxP/cyuN+8kyIhkdGGvMA9YCRotxDQpSbIPDRzbLrLFPCU3hKTwSUQZqP
JzLB5UkZv/HywouoCjkxKLR9YjYsTewfM7Z+d21+UPCfDtcRj88YxeMn/ibvBZ3P
zzfF0HvaO7AWhAw6k9a+F9sPPg4ZeAnHqQJyIkv3N3a6dcSFA1pj1bF1BcK5vZSt
jBWZp5N99sXzqnTPBIWUmAD04vnKJGW/4GKvyMX6ssmeVkjaef2WdhW+o45WxLM0
/L5H9MG0qPzVMIho7suuyWPEdr6sOBjhXlzPrjoiUevRi7PzKzMHVIf6tLITe7pT
BGIBnfHAT+7hOtSLIBD6Alfm78ELt5BGnBkpjNxvoEppaZS3JGWg/6w/zgH7IS79
aPib8qXPMThcFarmlwDB31qlpzmq6YR/PFGoOtmUW4y/Twhx5duoXNTSpv4Ao8YW
xw/ogM4cKGR0GQjTQuPOAF1/sdwTsOEFy9EgqoZ0njnnkf3/W9b3raYvAwtt41dU
63ZTGI0RmLo=
-----END CERTIFICATE-----
"""

# Strict allowlist for valid Saxion usernames (prevents argument injection into nmcli).
# Allows: number@student.saxion.nl  OR  name@saxion.nl  (staff accounts)
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]+@([a-zA-Z0-9-]+\.)*saxion\.nl$", re.IGNORECASE)

TITLE = "Saxion eduroam Installer"
DESCRIPTION = (
    "This installer configures eduroam for Saxion University.\n\n"
    "Rewritten by: Stensel8\n"
    "Based on: https://cat.eduroam.org/\n\n"
    "It uses secure PEAP/MSCHAPv2 with Domain Validation.\n"
    "Click OK to continue."
)


class Installer:

    def __init__(self, silent: bool = False, username: str = "",
                 ignore_certificate: bool = False):
        self.silent = silent
        self.username = username
        self.ignore_certificate = ignore_certificate
        # --silent means no GUI, prompts included. Decided once so show_message
        # and prompt_input cannot disagree.
        self.gui_tool = None if silent else self._detect_gui()

    def _detect_gui(self) -> str | None:
        """Detects available GUI tools (zenity, kdialog, yad)."""
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            return None

        for tool in ["zenity", "kdialog", "yad"]:
            if shutil.which(tool):
                return tool
        return None

    def _sanitize_for_log(self, text: str) -> str:
        """
        Sanitize text to remove potential sensitive information before logging.
        Masks usernames, passwords, and other sensitive data.
        """
        # Mask Saxion usernames (e.g., user@saxion.nl)
        text = re.sub(
            r'\b[a-zA-Z0-9._-]+@([a-zA-Z0-9-]+\.)*saxion\.nl\b',
            '[REDACTED]',
            text,
            flags=re.IGNORECASE
        )
        # Mask generic email addresses
        text = re.sub(
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
            '[REDACTED]',
            text,
            flags=re.IGNORECASE
        )
        # Separator is required. Without it this ate the word after "password"
        # and mangled ordinary prose.
        text = re.sub(
            r'\bpassword\s*[=:]\s*\S+',
            'password=[REDACTED]',
            text,
            flags=re.IGNORECASE
        )
        return text

    def show_message(self, text: str, is_error: bool = False):
        if self.silent:
            if is_error:
                sanitized_text = self._sanitize_for_log(text)
                print(f"Error: {sanitized_text}", file=sys.stderr)
            else:
                sanitized_text = self._sanitize_for_log(text)
                print(sanitized_text)
            return

        if not self.gui_tool:
            print(f"\n{self._sanitize_for_log(text)}\n")
            return

        cmd = []
        if self.gui_tool == "zenity":
            type_flag = "--error" if is_error else "--info"
            cmd = ["zenity", type_flag, "--width=500", f"--title={TITLE}", f"--text={text}"]
        elif self.gui_tool == "kdialog":
            type_flag = "--error" if is_error else "--msgbox"
            cmd = ["kdialog", type_flag, text, f"--title={TITLE}"]
        elif self.gui_tool == "yad":
            image = "dialog-error" if is_error else "dialog-information"
            cmd = ["yad", f"--image={image}", "--button=OK", "--width=500",
                   f"--title={TITLE}", f"--text={text}"]

        subprocess.run(cmd, stderr=subprocess.DEVNULL)

    def prompt_input(self, prompt: str, is_password: bool = False) -> str | None:
        if self.gui_tool == "zenity":
            cmd = ["zenity", "--entry", "--width=500", f"--title={TITLE}", f"--text={prompt}"]
            if is_password:
                cmd.append("--hide-text")
        elif self.gui_tool == "kdialog":
            flag = "--password" if is_password else "--inputbox"
            cmd = ["kdialog", flag, prompt, f"--title={TITLE}"]
        elif self.gui_tool == "yad":
            field = ":H" if is_password else ""
            cmd = ["yad", "--form", f"--field={prompt}{field}", f"--title={TITLE}"]
        else:
            # Terminal fallback if no GUI tool is available
            if is_password:
                return getpass.getpass(f"{prompt}: ")
            return input(f"{prompt}: ").strip()

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return None

        val = res.stdout.strip()
        # Yad sometimes adds a trailing separator
        if self.gui_tool == "yad" and val.endswith("|"):
            val = val[:-1]
        return val

    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate username format to prevent argument injection into nmcli.
        Accepts: number@student.saxion.nl  or  name@saxion.nl (staff)
        Rejects any value that doesn't match the strict allowlist pattern.
        """
        return bool(_USERNAME_RE.match(username.strip()))

    def get_credentials(self):
        # Only ask for username; password will be requested by the keyring at connection time
        while not self.username:
            val = self.prompt_input(f"Username (e.g. number@student.{REALM})")
            if val is None:
                sys.exit(1)
            if not self.validate_username(val):
                self.show_message(
                    f"Invalid username. Expected format: number@student.{REALM} or name@{REALM}",
                    True,
                )
                continue
            self.username = val.strip()

    def warn_insecure(self):
        """Say plainly what --ignore-certificate gives up."""
        warning = (
            "Certificate validation is OFF.\n\n"
            "Any access point calling itself 'eduroam' will be trusted. It can "
            "terminate the TLS tunnel itself and collect the MSCHAPv2 exchange, "
            "which is crackable offline -- that is your Saxion password.\n\n"
            "Use this to find out what the server is really serving, then fix the "
            "pinned chain and reconnect without this flag."
        )
        print("\n" + "!" * 70, file=sys.stderr)
        for line in warning.splitlines():
            print(line, file=sys.stderr)
        print("!" * 70 + "\n", file=sys.stderr)
        if not self.silent:
            self.show_message(warning, True)

    def report_server_chain(self):
        """Print the chain the server actually presented, to fix the pin with."""
        try:
            res = subprocess.run(
                ["journalctl", "-u", "wpa_supplicant", "-b", "--no-pager"],
                capture_output=True, text=True, timeout=15,
            )
            certs = [ln.split("wpa_supplicant", 1)[-1].strip()
                     for ln in res.stdout.splitlines() if "EAP-PEER-CERT" in ln]
        except (OSError, subprocess.SubprocessError):
            certs = []

        print("\n--- certificate chain the server presented ---")
        if certs:
            for line in certs[-8:]:
                print(f"  {line}")
            print("\nPut the root above into SAXION_CA_PEM and drop the flag.")
        else:
            print(
                "  Could not read the journal (needs root or the systemd-journal group).\n"
                "  Run this to see it:\n"
                "    journalctl -u wpa_supplicant -b | grep CTRL-EVENT-EAP-PEER-CERT"
            )

    def install_ca_bundle(self) -> str:
        """Write the pinned chain to a stable path and return it."""
        try:
            os.makedirs(CA_DIR, mode=0o755, exist_ok=True)
            with open(CA_FILE, "w", encoding="ascii") as handle:
                handle.write(SAXION_CA_PEM)
            # NetworkManager reads this as root, so the mode does not matter to
            # it. Keep it tight anyway.
            os.chmod(CA_FILE, 0o600)
        except OSError as error:
            self.show_message(
                f"Could not write the CA certificate to {CA_FILE}: {error}", True
            )
            sys.exit(1)
        return CA_FILE

    def run_nmcli(self, cmd: list[str]) -> bool:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            # Log before the cert check below: the caller tells people to look at
            # "the terminal output above", and that path used to print nothing.
            # Never into GUI subprocess args.
            sanitized_error = self._sanitize_for_log(res.stderr.strip())
            print(f"NetworkManager error:\n{sanitized_error}", file=sys.stderr)

            # Cert failures get a better message from the caller.
            if "Failed to recognize certificate" in res.stderr:
                return False

            # Fatal error: show a static message to the GUI to avoid passing
            # nmcli output (which may echo user input) into a subprocess argument
            # (CWE-78 / CodeQL py/command-line-injection).
            self.show_message(
                "NetworkManager failed to configure the connection.\n"
                "See terminal output for details.", True
            )
            sys.exit(1)
        return True

    def install(self):
        if not self.silent:
            self.show_message(DESCRIPTION)

        if not shutil.which("nmcli"):
            self.show_message("NetworkManager (nmcli) is not installed.", True)
            sys.exit(1)

        self.get_credentials()

        if self.ignore_certificate:
            self.warn_insecure()
            ca_path = ""
        else:
            ca_path = self.install_ca_bundle()

        # 1. Remove any existing eduroam connection
        subprocess.run(
            ["nmcli", "connection", "delete", CON_NAME],
            capture_output=True
        )

        # 2. Build nmcli command for new connection
        cmd = [
            "nmcli", "connection", "add",
            "type", "wifi",
            "con-name", CON_NAME,
            "ssid", SSID,
            "wifi-sec.key-mgmt", "wpa-eap",
            "802-1x.eap", "peap",
            "802-1x.phase2-auth", "mschapv2",
            "802-1x.identity", self.username,
            "802-1x.anonymous-identity", ANONYMOUS_ID,
            "802-1x.domain-suffix-match", SERVER_DOMAIN,
            "802-1x.phase2-domain-suffix-match", SERVER_DOMAIN,
            "802-1x.password-flags", "1",
            # Real MAC on purpose: Saxion blocks a MAC that looks like it is
            # scanning, and randomising would let that block be shrugged off.
            "wifi.cloned-mac-address", "permanent",
        ]
        if ca_path:
            cmd += ["802-1x.ca-cert", ca_path]

        # No unvalidated fallback. Connecting anyway would hand a Saxion
        # password to whatever access point answered.
        if not self.run_nmcli(cmd):
            self.show_message(
                "NetworkManager rejected the certificate configuration, so no eduroam "
                "profile was created.\n\n"
                f"The pinned CA is at {CA_FILE}. If Saxion has changed its RADIUS "
                "certificate authority, fetch the current one from cat.eduroam.org and "
                "report it, so this script can be updated.\n"
                "See the terminal output above for what nmcli reported.",
                True,
            )
            sys.exit(1)

        # Show explanation before attempting connection so the password prompt makes sense
        self.show_message(
            "eduroam profile created successfully.\n\n"
            "Your password will now be requested by your desktop keyring "
            "(GNOME Keyring on GNOME, KWallet on KDE).\n"
            "This is normal and ensures your password is stored securely encrypted, never in plaintext.\n\n"
            "If you do not see a password prompt, open your network settings and connect to eduroam manually."
        )

        # Best-effort; the profile is already saved. Output is captured, so
        # without the print below the script looks dead while nmcli waits.
        # --wait bounds nmcli, the subprocess timeout catches it ignoring that.
        print(f"[INFO] Connecting to {SSID} (up to {CONNECT_TIMEOUT}s)...", flush=True)
        try:
            res = subprocess.run(
                ["nmcli", "--wait", str(CONNECT_TIMEOUT), "connection", "up", CON_NAME],
                capture_output=True,
                text=True,
                timeout=CONNECT_TIMEOUT + 10,
            )
        except subprocess.TimeoutExpired:
            print(
                f"[WARN] eduroam profile saved, but activation did not finish within "
                f"{CONNECT_TIMEOUT}s.\n"
                "       This usually means the EAP handshake is failing and NetworkManager\n"
                "       is retrying. Check what it reported with:\n"
                "         journalctl -u NetworkManager -u wpa_supplicant -b --since '5 min ago'"
            )
            return

        output = res.stderr.strip() or res.stdout.strip()

        if res.returncode == 0:
            print("[INFO] Connected to eduroam successfully.")
            if self.ignore_certificate:
                self.report_server_chain()
        elif "network could not be found" in output or "No network with SSID" in output:
            # Not in range; the passwd-file warning is also present but not the root cause.
            print(
                "[INFO] eduroam profile saved, but the network could not be reached right now.\n"
                "       You are probably not in range of an eduroam access point.\n"
                "       The profile is stored — connect to eduroam from your network settings when nearby."
            )
        elif (
            "Secrets were required" in output
            or "Authentication rejected" in output
        ):
            print(
                "[ERROR] eduroam profile saved, but authentication failed.\n"
                "        Your credentials may be incorrect.\n"
                "        Re-run the script with the correct username, or update the profile in\n"
                "        your network settings (nmcli connection edit eduroam)."
            )
        elif "passwd-file" in output or "cannot ask without" in output:
            # nmcli was not invoked with --ask; keyring will prompt on first connect.
            print(
                "[INFO] eduroam profile saved. "
                "Enter your password when prompted by your desktop keyring upon connecting."
            )
        else:
            print(
                "[WARN] eduroam profile saved, but automatic activation failed.\n"
                "       You can connect manually via your network settings.\n"
                f"       nmcli: {output}"
            )


def main():

    parser = argparse.ArgumentParser(description="Saxion eduroam Installer")
    parser.add_argument("-u", "--username", help="Saxion username")
    parser.add_argument("--silent", action="store_true", help="Run without GUI")
    parser.add_argument(
        "--ignore-certificate",
        action="store_true",
        help="Skip CA validation and print what the server served. Debugging only: "
             "any access point named 'eduroam' is trusted and can harvest your password.",
    )
    args = parser.parse_args()

    # Validate CLI-provided username before it can reach subprocess args.
    # If invalid, fall back to interactive prompt in get_credentials().
    initial_username = args.username or ""
    if initial_username and not Installer.validate_username(initial_username):
        print(
            f"Warning: '{initial_username}' is not a valid Saxion username. You will be prompted.",
            file=sys.stderr,
        )
        initial_username = ""

    installer = Installer(args.silent, initial_username, args.ignore_certificate)
    installer.install()


if __name__ == "__main__":
    main()
