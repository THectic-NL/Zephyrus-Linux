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
        self.gui_tool = self._detect_gui()
        
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
        text = re.sub(r'\b[a-zA-Z0-9._-]+@([a-zA-Z0-9-]+\.)*saxion\.nl\b', '[REDACTED]', text, flags=re.IGNORECASE)
        # Mask generic email addresses
        text = re.sub(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', '[REDACTED]', text, flags=re.IGNORECASE)
        # Mask passwords (generic pattern)
        text = re.sub(r'\bpassword[=: ]*[^\s]+', 'password=[REDACTED]', text, flags=re.IGNORECASE)
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
            print(f"\n{text}\n")
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

    def find_system_ca_bundle(self) -> str:
        candidates = [
            "/etc/pki/tls/certs/ca-bundle.crt",          # Fedora/RHEL
            "/etc/ssl/certs/ca-certificates.crt",        # Debian/Ubuntu
            "/var/lib/ca-certificates/ca-bundle.pem",    # openSUSE
            "/etc/ssl/ca-bundle.pem",                    # Other distros
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return ""

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
            self.show_message("NetworkManager failed to configure the connection.\nSee terminal output for details.", True)
            sys.exit(1)
        return True

    def install(self):
        if not self.silent:
            self.show_message(DESCRIPTION)

        if not shutil.which("nmcli"):
            self.show_message("NetworkManager (nmcli) is not installed.", True)
            sys.exit(1)

        self.get_credentials()
        
        ca_path = self.find_system_ca_bundle()
        
        # 1. Remove any existing eduroam connection
        subprocess.run(["nmcli", "connection", "delete", CON_NAME], 
                      capture_output=True)

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
            "wifi.cloned-mac-address", "permanent"
        ]

        # Try with CA bundle first (most secure option)
        success = False
        if ca_path:
            cmd_secure = cmd + ["802-1x.ca-cert", ca_path]
            success = self.run_nmcli(cmd_secure)
        
        # Fallback if CA fails or is not found (still secure via domain suffix validation)
        if not success:
            print("Note: Using system default trust store (implicit validation).")
            # Run nmcli without explicit ca-cert path (uses system trust store)
            self.run_nmcli(cmd)

        # Show explanation before attempting connection so the password prompt makes sense
        self.show_message(
            f"Username '{self.username}' added.\n\n"
            "Your password will now be requested by your desktop keyring (e.g. GNOME Keyring).\n"
            "This is normal and ensures your password is stored securely encrypted, never in plaintext.\n\n"
            "If you do not see a password prompt, open your network settings and connect to eduroam manually."
        )

        # Attempt to activate the connection and show only relevant output
        res = subprocess.run(["nmcli", "connection", "up", CON_NAME], capture_output=True, text=True)
        if res.returncode == 0:
            print("[INFO] Connection attempt started. If you entered your password, you should be connected to eduroam.")
        else:
            print("[ERROR] Could not activate eduroam connection:")
            print(res.stderr.strip() or res.stdout.strip())

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
