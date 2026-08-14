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

# Where the pinned CA is written. NetworkManager reads 802-1x.ca-cert every time
# it connects, so it has to survive the script exiting; a temporary file will not
# do. Under the user's config directory, so the script still needs no root.
CA_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
    "saxion-eduroam",
)
CA_FILE = os.path.join(CA_DIR, "saxion-eduroam-ca.pem")

# The certificate chain Saxion publishes for manual configuration, via the
# eduroam CAT profile ("eduroam CA certificate (PEM)"):
#
#   https://cat.eduroam.org/  ->  Saxion University of Applied Sciences
#
#   1. USERTrust RSA Certification Authority   (root,         expires 2038-01-18)
#      SHA-256 E7:93:C9:B0:2F:D8:AA:13:E2:1C:31:22:8A:CC:B0:81:
#              19:64:3B:74:9C:89:89:64:B1:74:6D:46:C3:D4:CB:D2
#   2. GEANT OV RSA CA 4                       (intermediate, expires 2033-05-01)
#      SHA-256 37:83:4F:A5:EA:40:FB:F7:B6:11:96:95:59:62:E1:CA:
#              05:58:87:24:35:E4:20:66:53:D3:F6:20:DD:8E:98:8E
#
# Both are shipped, as CAT does, so the chain still builds if GEANT rotates the
# intermediate under the same root.
#
# When Saxion changes RADIUS certificate authority this file stops working and
# the fix is to replace the block below from the URL above. That is the cost of
# pinning, and it is the point: without it any of the ~150 CAs in the system
# trust store could vouch for a server calling itself ise.infra.saxion.net.
SAXION_CA_PEM = """\
-----BEGIN CERTIFICATE-----
MIIF3jCCA8agAwIBAgIQAf1tMPyjylGoG7xkDjUDLTANBgkqhkiG9w0BAQwFADCB
iDELMAkGA1UEBhMCVVMxEzARBgNVBAgTCk5ldyBKZXJzZXkxFDASBgNVBAcTC0pl
cnNleSBDaXR5MR4wHAYDVQQKExVUaGUgVVNFUlRSVVNUIE5ldHdvcmsxLjAsBgNV
BAMTJVVTRVJUcnVzdCBSU0EgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkwHhcNMTAw
MjAxMDAwMDAwWhcNMzgwMTE4MjM1OTU5WjCBiDELMAkGA1UEBhMCVVMxEzARBgNV
BAgTCk5ldyBKZXJzZXkxFDASBgNVBAcTC0plcnNleSBDaXR5MR4wHAYDVQQKExVU
aGUgVVNFUlRSVVNUIE5ldHdvcmsxLjAsBgNVBAMTJVVTRVJUcnVzdCBSU0EgQ2Vy
dGlmaWNhdGlvbiBBdXRob3JpdHkwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIK
AoICAQCAEmUXNg7D2wiz0KxXDXbtzSfTTK1Qg2HiqiBNCS1kCdzOiZ/MPans9s/B
3PHTsdZ7NygRK0faOca8Ohm0X6a9fZ2jY0K2dvKpOyuR+OJv0OwWIJAJPuLodMkY
tJHUYmTbf6MG8YgYapAiPLz+E/CHFHv25B+O1ORRxhFnRghRy4YUVD+8M/5+bJz/
Fp0YvVGONaanZshyZ9shZrHUm3gDwFA66Mzw3LyeTP6vBZY1H1dat//O+T23LLb2
VN3I5xI6Ta5MirdcmrS3ID3KfyI0rn47aGYBROcBTkZTmzNg95S+UzeQc0PzMsNT
79uq/nROacdrjGCT3sTHDN/hMq7MkztReJVni+49Vv4M0GkPGw/zJSZrM233bkf6
c0Plfg6lZrEpfDKEY1WJxA3Bk1QwGROs0303p+tdOmw1XNtB1xLaqUkL39iAigmT
Yo61Zs8liM2EuLE/pDkP2QKe6xJMlXzzawWpXhaDzLhn4ugTncxbgtNMs+1b/97l
c6wjOy0AvzVVdAlJ2ElYGn+SNuZRkg7zJn0cTRe8yexDJtC/QV9AqURE9JnnV4ee
UB9XVKg+/XRjL7FQZQnmWEIuQxpMtPAlR1n6BB6T1CZGSlCBst6+eLf8ZxXhyVeE
Hg9j1uliutZfVS7qXMYoCAQlObgOK6nyTJccBz8NUvXt7y+CDwIDAQABo0IwQDAd
BgNVHQ4EFgQUU3m/WqorSs9UgOHYm8Cd8rIDZsswDgYDVR0PAQH/BAQDAgEGMA8G
A1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQEMBQADggIBAFzUfA3P9wF9QZllDHPF
Up/L+M+ZBn8b2kMVn54CVVeWFPFSPCeHlCjtHzoBN6J2/FNQwISbxmtOuowhT6KO
VWKR82kV2LyI48SqC/3vqOlLVSoGIG1VeCkZ7l8wXEskEVX/JJpuXior7gtNn3/3
ATiUFJVDBwn7YKnuHKsSjKCaXqeYalltiz8I+8jRRa8YFWSQEg9zKC7F4iRO/Fjs
8PRF/iKz6y+O0tlFYQXBl2+odnKPi4w2r78NBc5xjeambx9spnFixdjQg3IM8WcR
iQycE0xyNN+81XHfqnHd4blsjDwSXWXavVcStkNr/+XeTWYRUc+ZruwXtuhxkYze
Sf7dNXGiFSeUHM9h4ya7b6NnJSFd5t0dCy5oGzuCr+yDZ4XUmFF0sbmZgIn/f3gZ
XHlKYC6SQK5MNyosycdiyA5d9zZbyuAlJQG03RoHnHcAP9Dc1ew91Pq7P8yF1m9/
qS3fuQL39ZeatTXaw2ewh0qpKJ4jjv9cJ2vhsE/zB+4ALtRZh8tSQZXq9EfX7mRB
VXyNWQKV3WKdwrnuWih0hKWbt5DHDAff9Yk2dDLWKMGwsAvgnEzDHNb842m1R0aB
L6KCq9NjRHDEjf8tM7qtj3u1cIiuPhnPQCjY/MiQu12ZIvVS5ljFH4gxQ+6IHdfG
jjxDah2nGN59PRbxYvnKkKj9
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIG5TCCBM2gAwIBAgIRANpDvROb0li7TdYcrMTz2+AwDQYJKoZIhvcNAQEMBQAw
gYgxCzAJBgNVBAYTAlVTMRMwEQYDVQQIEwpOZXcgSmVyc2V5MRQwEgYDVQQHEwtK
ZXJzZXkgQ2l0eTEeMBwGA1UEChMVVGhlIFVTRVJUUlVTVCBOZXR3b3JrMS4wLAYD
VQQDEyVVU0VSVHJ1c3QgUlNBIENlcnRpZmljYXRpb24gQXV0aG9yaXR5MB4XDTIw
MDIxODAwMDAwMFoXDTMzMDUwMTIzNTk1OVowRDELMAkGA1UEBhMCTkwxGTAXBgNV
BAoTEEdFQU5UIFZlcmVuaWdpbmcxGjAYBgNVBAMTEUdFQU5UIE9WIFJTQSBDQSA0
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEApYhi1aEiPsg9ZKRMAw9Q
r8Mthsr6R20VSfFeh7TgwtLQi6RSRLOh4or4EMG/1th8lijv7xnBMVZkTysFiPmT
PiLOfvz+QwO1NwjvgY+Jrs7fSoVA/TQkXzcxu4Tl3WHi+qJmKLJVu/JOuHud6mOp
LWkIbhODSzOxANJ24IGPx9h4OXDyy6/342eE6UPXCtJ8AzeumTG6Dfv5KVx24lCF
TGUzHUB+j+g0lSKg/Sf1OzgCajJV9enmZ/84ydh48wPp6vbWf1H0O3Rd3LhpMSVn
TqFTLKZSbQeLcx/l9DOKZfBCC9ghWxsgTqW9gQ7v3T3aIfSaVC9rnwVxO0VjmDdP
FNbdoxnh0zYwf45nV1QQgpRwZJ93yWedhp4ch1a6Ajwqs+wv4mZzmBSjovtV0mKw
d+CQbSToalEUP4QeJq4Udz5WNmNMI4OYP6cgrnlJ50aa0DZPlJqrKQPGL69KQQz1
2WgxvhCuVU70y6ZWAPopBa1ykbsttpLxADZre5cH573lIuLHdjx7NjpYIXRx2+QJ
URnX2qx37eZIxYXz8ggM+wXH6RDbU3V2o5DP67hXPHSAbA+p0orjAocpk2osxHKo
NSE3LCjNx8WVdxnXvuQ28tKdaK69knfm3bB7xpdfsNNTPH9ElcjscWZxpeZ5Iij8
lyrCG1z0vSWtSBsgSnUyG/sCAwEAAaOCAYswggGHMB8GA1UdIwQYMBaAFFN5v1qq
K0rPVIDh2JvAnfKyA2bLMB0GA1UdDgQWBBRvHTVJEGwy+lmgnryK6B+VvnF6DDAO
BgNVHQ8BAf8EBAMCAYYwEgYDVR0TAQH/BAgwBgEB/wIBADAdBgNVHSUEFjAUBggr
BgEFBQcDAQYIKwYBBQUHAwIwOAYDVR0gBDEwLzAtBgRVHSAAMCUwIwYIKwYBBQUH
AgEWF2h0dHBzOi8vc2VjdGlnby5jb20vQ1BTMFAGA1UdHwRJMEcwRaBDoEGGP2h0
dHA6Ly9jcmwudXNlcnRydXN0LmNvbS9VU0VSVHJ1c3RSU0FDZXJ0aWZpY2F0aW9u
QXV0aG9yaXR5LmNybDB2BggrBgEFBQcBAQRqMGgwPwYIKwYBBQUHMAKGM2h0dHA6
Ly9jcnQudXNlcnRydXN0LmNvbS9VU0VSVHJ1c3RSU0FBZGRUcnVzdENBLmNydDAl
BggrBgEFBQcwAYYZaHR0cDovL29jc3AudXNlcnRydXN0LmNvbTANBgkqhkiG9w0B
AQwFAAOCAgEAUtlC3e0xj/1BMfPhdQhUXeLjb0xp8UE28kzWE5xDzGKbfGgnrT2R
lw5gLIx+/cNVrad//+MrpTppMlxq59AsXYZW3xRasrvkjGfNR3vt/1RAl8iI31lG
hIg6dfIX5N4esLkrQeN8HiyHKH6khm4966IkVVtnxz5CgUPqEYn4eQ+4eeESrWBh
AqXaiv7HRvpsdwLYekAhnrlGpioZ/CJIT2PTTxf+GHM6cuUnNqdUzfvrQgA8kt1/
ASXx2od/M+c8nlJqrGz29lrJveJOSEMX0c/ts02WhsfMhkYa6XujUZLmvR1Eq08r
48/EZ4l+t5L4wt0DV8VaPbsEBF1EOFpz/YS2H6mSwcFaNJbnYqqJHIvm3PLJHkFm
EoLXRVrQXdCT+3wgBfgU6heCV5CYBz/YkrdWES7tiiT8sVUDqXmVlTsbiRNiyLs2
bmEWWFUl76jViIJog5fongEqN3jLIGTG/mXrJT1UyymIcobnIGrbwwRVz/mpFQo0
vBYIi1k2ThVh0Dx88BbF9YiP84dd8Fkn5wbE6FxXYJ287qfRTgmhePecPc73Yrzt
apdRcsKVGkOpaTIJP/l+lAHRLZxk/dUtyN95G++bOSQqnOCpVPabUGl2E/OEyFrp
Ipwgu2L/WJclvd6g+ZA/iWkLSMcpnFb+uX6QBqvD6+RNxul1FaB5iHY=
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

    def __init__(self, silent: bool = False, username: str = ""):
        self.silent = silent
        self.username = username
        # --silent means no GUI, and that has to hold for prompts too. Deciding
        # it once here keeps show_message and prompt_input from disagreeing:
        # previously only show_message honoured the flag, so a --silent run on a
        # desktop still opened a zenity box asking for the username.
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
        # Mask passwords. The separator is required: with it optional this also
        # matched "password" followed by a space and swallowed the next word, so
        # ordinary prose came out as "Your password=[REDACTED] now be requested
        # by your desktop keyring".
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

    def install_ca_bundle(self) -> str:
        """
        Write the pinned Saxion chain to a stable path and return it.

        This replaces pointing 802-1x.ca-cert at the system trust store. That
        made any of the roughly 150 public CAs a valid signer for something
        calling itself ise.infra.saxion.net; now only the chain Saxion actually
        publishes is accepted. It is what eduroam CAT does, and the reason CAT
        exists.
        """
        try:
            os.makedirs(CA_DIR, mode=0o755, exist_ok=True)
            with open(CA_FILE, "w", encoding="ascii") as handle:
                handle.write(SAXION_CA_PEM)
            os.chmod(CA_FILE, 0o644)
        except OSError as error:
            self.show_message(
                f"Could not write the CA certificate to {CA_FILE}: {error}", True
            )
            sys.exit(1)
        return CA_FILE

    def run_nmcli(self, cmd: list[str]) -> bool:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            # Check for a specific error to allow fallback
            if "Failed to recognize certificate" in res.stderr:
                return False

            # Log full nmcli error to stderr (terminal only — never into GUI subprocess args).
            sanitized_error = self._sanitize_for_log(res.stderr.strip())
            print(f"NetworkManager error:\n{sanitized_error}", file=sys.stderr)

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
            # Saxion does not register devices by MAC, but it does block one
            # temporarily when it looks like it is scanning or flooding. A
            # randomised address would let that block be shrugged off by
            # reconnecting, so the real one is used deliberately.
            "wifi.cloned-mac-address", "permanent",
            # The pinned chain, not the system trust store.
            "802-1x.ca-cert", ca_path,
        ]

        # No unvalidated fallback. There used to be one, for when no CA bundle
        # could be found on the system; with the chain shipped inside this
        # script that situation no longer exists. If nmcli will not accept this
        # configuration, connecting anyway would mean handing a Saxion password
        # to whatever access point answered, which is not a trade worth making
        # on the user's behalf.
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

        # Attempt to activate the connection (best-effort; profile is already saved).
        res = subprocess.run(
            ["nmcli", "connection", "up", CON_NAME],
            capture_output=True,
            text=True
        )
        output = res.stderr.strip() or res.stdout.strip()

        if res.returncode == 0:
            print("[INFO] Connected to eduroam successfully.")
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

    installer = Installer(args.silent, initial_username)
    installer.install()


if __name__ == "__main__":
    main()
