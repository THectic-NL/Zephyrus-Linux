#!/usr/bin/env python3
"""
MT7925 Wi-Fi Performance Tuning (Linux)
----------------------------------------
Applies (enable) or reverts (disable) a set of tweaks for the MediaTek
MT7925 Wi-Fi 7 card, aimed at raising real-world throughput on a
6GHz/160MHz link: disabling PCIe ASPM for the card, turning off
NetworkManager's Wi-Fi power saving, and raising the mac80211 AQL Best
Effort queue limit. Disabling Bluetooth (it shares the combo chip's
silicon and antenna paths) is a separate, optional extra -- see
--bluetooth-off below -- not one of the measured fixes, so it is not
applied by default.

Built and measured on an ASUS ROG Zephyrus G16 GA605WV (CachyOS, kernel
7.2.4) against a local iperf3 server; your mileage will vary with AP,
signal strength, and kernel version.

Some tweaks are live (take effect immediately), others need a reboot
because they're kernel module parameters read only at module load time.
This script says which is which every time. 'status' also reports what
hardware and driver/firmware version is actually detected, and where to
check whether something newer has landed since.

Every privileged step for one action (enable/disable/status) runs as a
single script under one pkexec call, so you get one polkit password
prompt per command instead of one per step.

Author: Stensel8
Rewrite of the original mt7925-tune.sh shell script, structured like
saxion-eduroam.py: one class, standard library only.
"""

from __future__ import annotations
import argparse
import platform
import re
import shlex
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

# Where to check whether driver/firmware work has moved past what's
# reported below. Same sources as the write-up this script ships with.
DOC_URL = "https://zephyrus-linux.thectic.nl/docs/networking/mt7925-wifi-performance/"
REFERENCES = [
    ("Official patch mailing list, search \"mt7925\"", "https://lore.kernel.org/linux-wireless/"),
    ("Readable web archive of the same mailing list", "https://ratatoskr.run/"),
    ("Mirror of the driver source, easier to browse", "https://github.com/openwrt/mt76"),
]


class Tuner:
    """Applies, reverts, and reports on the MT7925 tuning steps above."""

    def __init__(self, bluetooth_off: bool = False):
        self._iface: str | None = None
        self._phy: str | None = None
        self.bluetooth_off = bluetooth_off

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

    @staticmethod
    def pci_device() -> str | None:
        """The lspci line for the MediaTek Wi-Fi card, if lspci is available."""
        if not shutil.which("lspci"):
            return None
        res = subprocess.run(["lspci"], capture_output=True, text=True)
        for line in res.stdout.splitlines():
            lowered = line.lower()
            if "mediatek" in lowered and ("network" in lowered or "wireless" in lowered):
                return line.strip()
        return None

    @staticmethod
    def firmware_package_version() -> str | None:
        """Best-effort: the linux-firmware-mediatek package version, on Arch-based distros."""
        if not shutil.which("pacman"):
            return None
        res = subprocess.run(
            ["pacman", "-Qi", "linux-firmware-mediatek"], capture_output=True, text=True
        )
        if res.returncode != 0:
            return None
        for line in res.stdout.splitlines():
            if line.lower().startswith("version"):
                return line.split(":", 1)[1].strip()
        return None

    # --- privileged helpers --------------------------------------------------
    #
    # This script never needs to run as root itself. Everything that touches
    # /etc, systemd, rfkill, or debugfs for one action is bundled into a
    # single bash script and run through one pkexec call, so a run asks for
    # your password once, not once per step.

    @staticmethod
    def require_pkexec():
        if not shutil.which("pkexec"):
            print(
                "pkexec not found -- this script needs it for the privileged steps.",
                file=sys.stderr,
            )
            sys.exit(1)

    @staticmethod
    def run_privileged_script(
        script: str, exit_on_failure: bool = True
    ) -> subprocess.CompletedProcess | None:
        """Run a bash script as root through one pkexec/polkit prompt."""
        res = subprocess.run(
            ["pkexec", "bash", "-c", script], capture_output=True, text=True
        )
        if res.returncode != 0:
            detail = res.stderr.strip() or res.stdout.strip() or f"exit code {res.returncode}"
            if exit_on_failure:
                print(f"[ERROR] privileged step failed: {detail}", file=sys.stderr)
                sys.exit(1)
            print(f"[WARN] could not read privileged details: {detail}", file=sys.stderr)
            return None
        return res

    # --- enable ------------------------------------------------------------

    def enable(self):
        self.require_pkexec()
        aql = self.aql_path()
        low, high = AQL_TUNED
        stock_low, stock_high = AQL_STOCK

        script = f"""
set -e
mkdir -p {shlex.quote(str(NM_CONF.parent))}
cat > {shlex.quote(str(MODPROBE_CONF))} <<'EOF'
options mt7925e disable_aspm=1
EOF
cat > {shlex.quote(str(NM_CONF))} <<'EOF'
[connection]
wifi.powersave = 2
EOF
systemctl restart NetworkManager
if [ -e {shlex.quote(str(aql))} ]; then
    printf '2 {low} {high}' > {shlex.quote(str(aql))}
    echo AQL_OK
else
    echo AQL_MISSING
fi
"""
        if self.bluetooth_off:
            script += "rfkill block bluetooth\n"

        print("=== Enabling MT7925 performance tuning ===")
        print("One polkit prompt covers every privileged step below.\n")

        res = self.run_privileged_script(script)

        print("[1/3] PCIe ASPM disable (mt7925e module param)")
        print(f"      -> written to {MODPROBE_CONF} (needs reboot to take effect)")

        print("[2/3] NetworkManager Wi-Fi power saving off")
        print("      -> live")

        print(f"[3/3] AQL Best Effort queue limit: {stock_low}/{stock_high} -> {low}/{high} us")
        if "AQL_OK" in res.stdout:
            print("      -> live (resets on reboot/module reload -- this script re-applies it every run)")
        else:
            print(
                f"      -> {aql} not found, skipped (debugfs not mounted? "
                "try: pkexec mount -t debugfs none /sys/kernel/debug)"
            )

        print()
        if self.bluetooth_off:
            print("-- Optional extra, applied: Bluetooth off --")
            print("      Shares the combo chip's silicon and antennas with Wi-Fi; off removes")
            print("      a source of variance, at the cost of Bluetooth. Undo any time with:")
            print("      rfkill unblock bluetooth")
        else:
            print("-- Optional extra, not applied: Bluetooth off --")
            print("      The MT7925 is a combo Wi-Fi+Bluetooth chip; turning Bluetooth off")
            print("      removes a source of radio contention, but costs you Bluetooth. Not")
            print("      one of the measured fixes above, so left alone by default. Opt in")
            print("      with --bluetooth-off.")

        print()
        live = f"NM powersave, AQL{', Bluetooth off' if self.bluetooth_off else ''}"
        print(f"Done. LIVE now: {live}.")
        print("REBOOT REQUIRED for: PCIe ASPM disable.")
        print(f"Run 'python3 {Path(sys.argv[0]).name} status' any time to check what's actually active.")

    # --- disable -------------------------------------------------------------

    def disable(self):
        self.require_pkexec()
        aql = self.aql_path()
        low, high = AQL_STOCK

        script = f"""
set -e
rm -f {shlex.quote(str(MODPROBE_CONF))}
rm -f {shlex.quote(str(NM_CONF))}
systemctl restart NetworkManager
rfkill unblock bluetooth
if [ -e {shlex.quote(str(aql))} ]; then
    printf '2 {low} {high}' > {shlex.quote(str(aql))}
    echo AQL_OK
else
    echo AQL_MISSING
fi
"""
        print("=== Reverting to stock settings ===")
        print("One polkit prompt covers every privileged step below.\n")

        res = self.run_privileged_script(script)

        print("[1/4] Removing PCIe ASPM override")
        print("      -> removed (needs reboot to fully revert; module is already loaded with the tuned param)")

        print("[2/4] Removing NetworkManager power saving override")
        print("      -> live")

        print("[3/4] Bluetooth back on (in case --bluetooth-off had switched it off)")
        print("      -> live")

        print(f"[4/4] AQL Best Effort queue limit: back to stock {low}/{high} us")
        if "AQL_OK" in res.stdout:
            print("      -> live")
        else:
            print(f"      -> {aql} not found, skipped")

        print()
        print("Done. REBOOT REQUIRED to fully clear the PCIe ASPM module param.")

    # --- status ------------------------------------------------------------

    def status(self):
        self.require_pkexec()
        iface, phy, aql = self.iface(), self.phy(), self.aql_path()
        priv = self._read_privileged_status(aql)

        print(f"=== MT7925 tuning status (iface: {iface}, {phy}) ===\n")

        print("-- Detected hardware --")
        pci = self.pci_device()
        if pci:
            print(pci)
        print(f"Kernel release (driver ships in-tree, so this is the driver version too): {platform.release()}")
        print(f"Kernel build: {platform.version()}")

        print()
        print("-- Firmware --")
        fw_lines = [
            line for line in priv["dmesg"].splitlines()
            if re.search(r"mt7925e.*(firmware|hw/sw|build time)", line, re.IGNORECASE)
        ]
        if fw_lines:
            for line in fw_lines[-4:]:
                print(line)
        else:
            print("(no firmware line in the current dmesg buffer -- it wraps, try again after a fresh boot)")
        pkg_version = self.firmware_package_version()
        if pkg_version:
            print(f"linux-firmware-mediatek package: {pkg_version}")

        print()
        print("-- Checking for something newer --")
        print(f"  Full write-up: {DOC_URL}")
        for label, url in REFERENCES:
            print(f"  {label}: {url}")

        print()
        print("-- PCIe ASPM (module param, needs reboot to change) --")
        print(f"config file: {'present' if MODPROBE_CONF.exists() else 'absent'} ({MODPROBE_CONF})")
        aspm_lines = [
            line for line in priv["dmesg"].splitlines()
            if re.search(r"mt7925e.*aspm", line, re.IGNORECASE)
        ]
        print(aspm_lines[-1] if aspm_lines else "dmesg: no ASPM line found")

        print()
        print("-- NetworkManager Wi-Fi power saving --")
        print(f"config file: {'present' if NM_CONF.exists() else 'absent'} ({NM_CONF})")
        res = subprocess.run(
            ["iw", "dev", iface, "get", "power_save"], capture_output=True, text=True
        )
        if res.returncode == 0 and res.stdout.strip():
            print(res.stdout.strip())

        print()
        print("-- Bluetooth (optional extra; off is not required for the throughput fixes) --")
        self._print_bluetooth_status()

        print()
        print("-- AQL Best Effort queue limit --")
        print(priv["aql_value"] if priv["aql_exists"] else f"{aql} not found (debugfs not mounted?)")

        print()
        print("-- Current link --")
        res = subprocess.run(["iw", "dev", iface, "link"], capture_output=True, text=True)
        print(res.stdout.strip() or "(no output)")

    def _read_privileged_status(self, aql: Path) -> dict[str, object]:
        """dmesg plus the AQL sysfs value, in one pkexec call."""
        marker = "---AQL---"
        script = f"""
dmesg
echo '{marker}'
if [ -e {shlex.quote(str(aql))} ]; then
    echo EXISTS
    cat {shlex.quote(str(aql))}
else
    echo MISSING
fi
"""
        res = self.run_privileged_script(script, exit_on_failure=False)
        if res is None:
            return {"dmesg": "", "aql_exists": False, "aql_value": ""}

        dmesg_part, _, aql_part = res.stdout.partition(marker + "\n")
        aql_lines = aql_part.splitlines()
        exists = bool(aql_lines) and aql_lines[0].strip() == "EXISTS"
        value = aql_lines[1].strip() if exists and len(aql_lines) > 1 else ""
        return {"dmesg": dmesg_part, "aql_exists": exists, "aql_value": value}

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
        help="enable: apply the throughput fixes. disable: revert everything to stock. "
             "status: show current state, detected hardware, and driver/firmware info.",
    )
    parser.add_argument(
        "--bluetooth-off",
        action="store_true",
        help="On 'enable', also disable Bluetooth (the MT7925 is a combo Wi-Fi+Bluetooth "
             "chip sharing the same silicon and antennas). Optional extra, not one of the "
             "measured throughput fixes, so off by default. Ignored for other actions.",
    )
    args = parser.parse_args()

    if not shutil.which("iw"):
        print("'iw' is required but not installed.", file=sys.stderr)
        sys.exit(1)

    tuner = Tuner(bluetooth_off=args.bluetooth_off)
    getattr(tuner, args.action)()


if __name__ == "__main__":
    main()
