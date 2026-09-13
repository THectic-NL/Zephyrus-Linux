#!/usr/bin/env python3
"""
MT7925 Wi-Fi Performance Tuning (Linux)
----------------------------------------
Applies (enable) or reverts (disable) a set of tweaks for the MediaTek
MT7925 Wi-Fi 7 card, aimed at raising real-world throughput on a
6GHz/160MHz link: disabling PCIe ASPM for the card, turning off
NetworkManager's Wi-Fi power saving, disabling Bluetooth (it shares the
combo chip's silicon and antenna paths), and raising the mac80211 AQL
Best Effort queue limit.

Built and measured on an ASUS ROG Zephyrus G16 GA605WV (CachyOS, kernel
7.2.4) against a local iperf3 server; your mileage will vary with AP,
signal strength, and kernel version.

Some tweaks are live (take effect immediately), others need a reboot
because they're kernel module parameters read only at module load time.
This script says which is which every time.

Author: Stensel8
Rewrite of the original mt7925-tune.sh shell script, structured like
saxion-eduroam.py: one class, standard library only, every privileged
step going through pkexec rather than requiring the script itself to
run as root.
"""

from __future__ import annotations
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Support policy, not a technical floor: the code itself runs on older Pythons.
# Pinned to the current stable release so nobody runs this on an
# already-unsupported interpreter.
MIN_PYTHON = (3, 14)

MODPROBE_CONF = Path("/etc/modprobe.d/mt7925e.conf")
NM_CONF = Path("/etc/NetworkManager/conf.d/wifi-powersave.conf")

# AQL Best Effort (AC=2) queue limits, in microseconds.
# Stock mac80211 default, used to revert.
AQL_STOCK = (5000, 12000)
# Tuned value -- raises the airtime budget so a single high-bitrate TCP
# stream doesn't starve between bursts. Trade-off: less headroom for
# low-latency traffic (calls, gaming) sharing the radio under load.
AQL_TUNED = (20000, 40000)


class Tuner:
    """Applies, reverts, and reports on the MT7925 tuning steps above."""

    def __init__(self):
        self._iface: str | None = None
        self._phy: str | None = None

    # --- hardware discovery ------------------------------------------------

    def iface(self) -> str:
        """The first wireless interface iw knows about."""
        if self._iface is None:
            res = subprocess.run(["iw", "dev"], capture_output=True, text=True)
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("Interface"):
                    self._iface = line.split()[1]
                    break
            else:
                print(
                    "No wireless interface found (is a Wi-Fi card present, "
                    "and is 'iw' able to see it?).",
                    file=sys.stderr,
                )
                sys.exit(1)
        return self._iface

    def phy(self) -> str:
        """The phy (e.g. 'phy0') backing the interface above."""
        if self._phy is None:
            res = subprocess.run(
                ["iw", "dev", self.iface(), "info"], capture_output=True, text=True
            )
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("wiphy"):
                    self._phy = f"phy{line.split()[1]}"
                    break
            else:
                print(f"Could not determine the phy for {self.iface()}.", file=sys.stderr)
                sys.exit(1)
        return self._phy

    def aql_path(self) -> Path:
        return Path(f"/sys/kernel/debug/ieee80211/{self.phy()}/aql_txq_limit")

    # --- privileged helpers --------------------------------------------------
    #
    # This script never needs to run as root itself: every step that touches
    # /etc, systemd, rfkill, or debugfs goes through pkexec individually, the
    # same way the original shell script did. That keeps the polkit prompt
    # scoped to one action at a time instead of the whole script.

    @staticmethod
    def require_pkexec():
        if not shutil.which("pkexec"):
            print(
                "pkexec not found -- this script needs it for the privileged steps.",
                file=sys.stderr,
            )
            sys.exit(1)

    @staticmethod
    def run_privileged(cmd: list[str], input_text: str | None = None) -> subprocess.CompletedProcess:
        """Run a command through pkexec, or exit with what it reported."""
        res = subprocess.run(
            ["pkexec", *cmd], input=input_text, capture_output=True, text=True
        )
        if res.returncode != 0:
            detail = res.stderr.strip() or res.stdout.strip() or f"exit code {res.returncode}"
            print(f"[ERROR] 'pkexec {' '.join(cmd)}' failed: {detail}", file=sys.stderr)
            sys.exit(1)
        return res

    @classmethod
    def write_root_file(cls, path: Path, content: str):
        """Write content to a root-owned file via 'pkexec tee'."""
        cls.run_privileged(["tee", str(path)], input_text=content)

    @staticmethod
    def root_path_exists(path: Path) -> bool:
        return subprocess.run(["pkexec", "test", "-e", str(path)]).returncode == 0

    @classmethod
    def read_root_file(cls, path: Path) -> str:
        return cls.run_privileged(["cat", str(path)]).stdout

    # --- enable ----------------------------------------------------------

    def enable(self):
        self.require_pkexec()
        print("=== Enabling MT7925 performance tuning ===")

        print("[1/4] PCIe ASPM disable (mt7925e module param)")
        self.write_root_file(MODPROBE_CONF, "options mt7925e disable_aspm=1\n")
        print(f"      -> written to {MODPROBE_CONF} (needs reboot to take effect)")

        print("[2/4] NetworkManager Wi-Fi power saving off")
        self.run_privileged(["mkdir", "-p", str(NM_CONF.parent)])
        self.write_root_file(NM_CONF, "[connection]\nwifi.powersave = 2\n")
        self.run_privileged(["systemctl", "restart", "NetworkManager"])
        print("      -> live")

        print("[3/4] Bluetooth off (shares the combo chip with Wi-Fi)")
        self.run_privileged(["rfkill", "block", "bluetooth"])
        print("      -> live")

        low, high = AQL_TUNED
        stock_low, stock_high = AQL_STOCK
        print(
            f"[4/4] AQL Best Effort queue limit: {stock_low}/{stock_high} -> "
            f"{low}/{high} us"
        )
        live_note = (
            "live (resets on reboot/module reload -- this script "
            "re-applies it every run)"
        )
        self._set_aql(low, high, live_note=live_note)

        print()
        print("Done. LIVE now: NM powersave, Bluetooth, AQL.")
        print("REBOOT REQUIRED for: PCIe ASPM disable.")
        print(f"Run 'python3 {Path(sys.argv[0]).name} status' any time to check what's actually active.")

    # --- disable ---------------------------------------------------------

    def disable(self):
        self.require_pkexec()
        print("=== Reverting to stock settings ===")

        print("[1/4] Removing PCIe ASPM override")
        self.run_privileged(["rm", "-f", str(MODPROBE_CONF)])
        print("      -> removed (needs reboot to fully revert; module is already loaded with the tuned param)")

        print("[2/4] Removing NetworkManager power saving override")
        self.run_privileged(["rm", "-f", str(NM_CONF)])
        self.run_privileged(["systemctl", "restart", "NetworkManager"])
        print("      -> live")

        print("[3/4] Bluetooth back on")
        self.run_privileged(["rfkill", "unblock", "bluetooth"])
        print("      -> live")

        low, high = AQL_STOCK
        print(f"[4/4] AQL Best Effort queue limit: back to stock {low}/{high} us")
        self._set_aql(low, high, live_note="live")

        print()
        print("Done. REBOOT REQUIRED to fully clear the PCIe ASPM module param.")

    def _set_aql(self, low: int, high: int, live_note: str):
        aql = self.aql_path()
        if self.root_path_exists(aql):
            self.write_root_file(aql, f"2 {low} {high}")
            print(f"      -> {live_note}")
        else:
            print(
                f"      -> {aql} not found, skipped (debugfs not mounted? "
                "try: pkexec mount -t debugfs none /sys/kernel/debug)"
            )

    # --- status ------------------------------------------------------------

    def status(self):
        self.require_pkexec()
        iface, phy, aql = self.iface(), self.phy(), self.aql_path()

        print(f"=== MT7925 tuning status (iface: {iface}, {phy}) ===\n")

        print("-- PCIe ASPM (module param, needs reboot to change) --")
        print(f"config file: {'present' if MODPROBE_CONF.exists() else 'absent'} ({MODPROBE_CONF})")
        self._print_dmesg_aspm_line()

        print()
        print("-- NetworkManager Wi-Fi power saving --")
        print(f"config file: {'present' if NM_CONF.exists() else 'absent'} ({NM_CONF})")
        res = subprocess.run(
            ["iw", "dev", iface, "get", "power_save"], capture_output=True, text=True
        )
        if res.returncode == 0 and res.stdout.strip():
            print(res.stdout.strip())

        print()
        print("-- Bluetooth --")
        self._print_bluetooth_status()

        print()
        print("-- AQL Best Effort queue limit --")
        if self.root_path_exists(aql):
            print(self.read_root_file(aql).strip())
        else:
            print(f"{aql} not found (debugfs not mounted?)")

        print()
        print("-- Current link --")
        res = subprocess.run(["iw", "dev", iface, "link"], capture_output=True, text=True)
        print(res.stdout.strip() or "(no output)")

    def _print_dmesg_aspm_line(self):
        res = self.run_privileged(["dmesg"])
        matches = [
            line for line in res.stdout.splitlines()
            if re.search(r"mt7925e.*aspm", line, re.IGNORECASE)
        ]
        print(matches[-1] if matches else "dmesg: no ASPM line found")

    @staticmethod
    def _print_bluetooth_status():
        res = subprocess.run(["rfkill", "list", "bluetooth"], capture_output=True, text=True)
        lines = [line for line in res.stdout.splitlines() if "blocked" in line.lower()]
        if lines:
            for line in lines:
                print(line)
        else:
            print("(no bluetooth device found by rfkill)")


def main():
    if sys.version_info < MIN_PYTHON:
        need = ".".join(str(n) for n in MIN_PYTHON)
        have = ".".join(str(n) for n in sys.version_info[:3])
        print(f"This script needs Python {need} or newer; this is {have}.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="MT7925 Wi-Fi performance tuning")
    parser.add_argument(
        "action",
        choices=["enable", "disable", "status"],
        help="enable: apply all tweaks. disable: revert everything to stock. "
             "status: show current state of each tweak.",
    )
    args = parser.parse_args()

    if not shutil.which("iw"):
        print("'iw' is required but not installed.", file=sys.stderr)
        sys.exit(1)

    tuner = Tuner()
    getattr(tuner, args.action)()


if __name__ == "__main__":
    main()
