#!/usr/bin/env python3
"""
Zephyrus G16 Backlight Fix (Linux)
----------------------------------
Makes screen brightness work in every GPU mode on the ASUS ROG Zephyrus G16
GA605WV (AMD Radeon 890M iGPU, NVIDIA RTX 4060 dGPU, MUX switch).

Out of the box, brightness is dead in Integrated mode. The firmware tells
the kernel that brightness is handled by the embedded controller (EC), so
only nvidia_wmi_ec_backlight registers, and the EC ignores it while the
dGPU is off. The fix has two parts:

  1. Kernel parameter acpi_backlight=native, so amdgpu gets a backlight
     device of its own.
  2. A modprobe rule that still loads nvidia_wmi_ec_backlight, with
     force=1, in Hybrid mode: the NVIDIA GPU is on the PCI bus but isn't
     the boot display. Brightness goes through the EC there, and part 1 on
     its own would stop that driver from registering. In Ultimate mode the
     NVIDIA GPU is the boot display and its own nvidia_0 controls brightness,
     so the rule stays out of the way.

Both parts are read at boot, so enable and disable need a reboot. 'status'
shows what's configured, what's running, and which backlight device is in
use. 'test' dims the screen for a few seconds through that device, so you
can see whether brightness actually reaches the panel.

Three ways of storing that kernel parameter are handled: /etc/default/grub
plus grub-mkconfig on a conventional distribution, 'rpm-ostree kargs' on an
image-based one like Bazzite, and a Limine configuration file. Limine support
is early, untested, and may be unstable or not work. The right one is detected.
Other bootloaders, systemd-boot among them, are refused with a pointer to the
manual steps instead.

Built on CachyOS with GRUB (kernel 7.2.5), then extended to Bazzite with
rpm-ostree (kernel 7.2.4). Verified in all three GPU modes on both, with
GNOME. KDE is untested.

Every privileged step for one action runs as a single script under one
pkexec call, so there's one polkit password prompt per action. Dialogs use
zenity, kdialog or yad, whichever matches the desktop. Without any of those,
or with --silent, everything happens in the terminal.

Author: Stensel8
Structured like mt7925-tune.py and saxion-eduroam.py: one class, standard
library only.
"""

from __future__ import annotations
import argparse
import html
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn, TypedDict

# Pinned to the current stable release so nobody runs this on an
# already-unsupported interpreter.
MIN_PYTHON = (3, 14)

SUPPORTED_BOARD = "GA605WV"
DMI_DIR = Path("/sys/class/dmi/id")

GRUB_DEFAULT = Path("/etc/default/grub")
GRUB_CFG = Path("/boot/grub/grub.cfg")
GRUB_BACKUP = Path("/etc/default/grub.zephyrus-backlight.bak")
MODPROBE_CONF = Path("/etc/modprobe.d/nvidia-wmi-ec-backlight.conf")
# Backups live here, not next to the original: older kmod still reads files in
# /etc/modprobe.d that do not end in .conf, so a copy dropped there could end up
# active alongside the rule it backs up. /var is writable on ostree too.
MODPROBE_BACKUP = Path("/var/lib/zephyrus-backlight/nvidia-wmi-ec-backlight.conf.bak")

# Present on a booted ostree deployment, so on Bazzite and its siblings.
OSTREE_MARKER = Path("/run/ostree-booted")
EFI_VARIABLES = Path("/sys/firmware/efi/efivars")
LIMINE_CONFIG_CANDIDATES = tuple(Path(path) for path in (
    "/boot/EFI/BOOT/limine.conf",
    "/boot/EFI/limine/limine.conf",
    "/boot/EFI/Limine/limine.conf",
    "/boot/limine/limine.conf",
    "/boot/limine.conf",
    "/boot/efi/EFI/BOOT/limine.conf",
    "/boot/efi/EFI/limine/limine.conf",
    "/boot/efi/EFI/Limine/limine.conf",
    "/boot/efi/limine/limine.conf",
    "/boot/efi/limine.conf",
    "/efi/EFI/BOOT/limine.conf",
    "/efi/EFI/limine/limine.conf",
    "/efi/EFI/Limine/limine.conf",
    "/efi/limine/limine.conf",
    "/efi/limine.conf",
))

KERNEL_PARAMS = ("acpi_backlight=native",)

# Identical to the rule in the write-up, so a hand-installed copy counts as
# installed.
MODPROBE_RULE = (
    "# acpi_backlight=native stops this driver from binding, "
    "but in Hybrid mode the backlight goes through the EC.\n"
    "# Force it only for an NVIDIA GPU that isn't the boot display, which means Hybrid. "
    "In Integrated mode amdgpu\n"
    "# handles brightness, and in Ultimate mode (NVIDIA is the boot display) "
    "the NVIDIA driver's nvidia_0 does.\n"
    "install nvidia_wmi_ec_backlight for d in /sys/bus/pci/devices/*; do "
    '[ -e "$d/boot_vga" ] || continue; '
    'read -r vendor < "$d/vendor"; read -r boot_vga < "$d/boot_vga"; '
    'if [ "$vendor" = 0x10de ] && [ "$boot_vga" = 0 ]; '
    "then exec /sbin/modprobe --ignore-install nvidia_wmi_ec_backlight force=1; fi; done\n"
)

NVIDIA_VENDOR = "0x10de"
WMI_EC_MODULE = Path("/sys/module/nvidia_wmi_ec_backlight")

# GNOME prefers the most specific backlight type it can find.
TYPE_ORDER = ("firmware", "platform", "raw")

# 'test' dims to this fraction of max_brightness, for this long.
TEST_LEVEL = 0.3
TEST_SECONDS = 3

DOC_URL = "https://zephyrus-linux.thectic.nl/docs/known-issues/"
TITLE = "Zephyrus Backlight Fix"

ACTIONS = [
    ("status", "Show what's configured, what's running, and which backlight is in use"),
    ("test", f"Dim the screen for {TEST_SECONDS} seconds to check brightness reaches the panel"),
    ("enable", "Apply the fix (kernel parameter and modprobe rule), then reboot"),
    ("disable", "Remove the fix and go back to the default, then reboot"),
]

MODE_LABELS = {
    "Integrated": "Integrated (NVIDIA GPU off)",
    "Hybrid": "Hybrid",
    "Ultimate": "Ultimate (NVIDIA GPU drives the screen)",
    "unknown": "couldn't be detected",
}

# The one conclusion about brightness on this boot, keyed by diagnose():
# (icon level, terminal text, GUI headline, GUI explanation).
OUTCOMES = {
    "fix_integrated_ok": (
        "ok",
        "Integrated mode: amdgpu drives the backlight. Brightness should work.",
        "Brightness should work",
        "The AMD graphics driver controls the screen brightness."),
    "fix_integrated_wrong_device": (
        "error",
        "Integrated mode, but {device} looks like the device in use instead of amdgpu_bl*. "
        "Brightness probably doesn't work.",
        "Brightness probably doesn't work",
        "The wrong device seems to control the brightness. Restart, then check again."),
    "fix_ec_ok": (
        "ok",
        "{mode} mode: the EC backlight is in use. Brightness should work.",
        "Brightness should work",
        "The laptop's embedded controller controls the screen brightness."),
    "fix_rule_missing": (
        "error",
        "{mode} mode without the modprobe rule: nothing reaches the panel here.",
        "Brightness doesn't work in this mode",
        "Part of the fix is missing. Choose enable, then restart."),
    "fix_rule_not_loaded": (
        "warning",
        "{mode} mode: the modprobe rule is installed, but nvidia_wmi_ec_backlight didn't register. "
        "Reboot so the rule runs when the module loads.",
        "Restart to finish the fix",
        "The fix is installed, but not active in this GPU mode yet."),
    "default_integrated_broken": (
        "error",
        "Integrated mode without the fix: brightness doesn't work here.",
        "Brightness doesn't work in this mode",
        "Choose enable, then restart your laptop."),
    "default_ok": (
        "ok",
        "{mode} mode with the default handling: brightness works here, but not in Integrated mode.",
        "Brightness works in this mode",
        "Without the fix it doesn't work in Integrated mode. Choose enable to fix that."),
    "fix_nvidia_ok": (
        "ok",
        "Ultimate mode: the NVIDIA driver's nvidia_0 drives the backlight. Brightness should work.",
        "Brightness should work",
        "The NVIDIA graphics driver controls the screen brightness."),
    "fix_ultimate_ec_in_use": (
        "error",
        "Ultimate mode, but nvidia_wmi_ec_backlight is loaded and preferred over nvidia_0, while the EC "
        "ignores brightness in this mode. The modprobe rule should skip it here.",
        "Brightness doesn't work in this mode",
        "The wrong device controls the brightness. Choose enable, then restart."),
    "fix_ultimate_wrong_device": (
        "error",
        "Ultimate mode, but {device} looks like the device in use instead of nvidia_0. "
        "Brightness probably doesn't work.",
        "Brightness probably doesn't work",
        "The wrong device seems to control the brightness. Restart, then check again."),
    "unknown_mode": (
        "warning",
        "Couldn't tell which GPU mode this is, so no conclusion on brightness.",
        "Couldn't check brightness",
        "The GPU mode couldn't be detected."),
}

# Side notes about the configuration, keyed by diagnose(): (terminal text, GUI text).
NOTES = {
    "unsupported": (
        f"This isn't a {SUPPORTED_BOARD}, so 'enable' won't apply the fix here.",
        f"This laptop isn't a {SUPPORTED_BOARD}, so the fix can't be enabled here."),
    "platform": (
        "{problem}",
        "This system isn't supported for enabling the fix. See the technical details."),
    "partly": (
        "The fix is only partly configured. Run 'enable' to complete it, or 'disable' to remove what's there.",
        "The fix is only partly set up. Choose enable to complete it."),
    "reboot_to_apply": (
        "The fix is configured but this boot started without it. Reboot to apply it.",
        "Restart your laptop to activate the fix."),
    "reboot_to_remove": (
        "This boot has the fix, but it's no longer configured. The next boot goes back to the default.",
        "The fix is removed and goes away after a restart."),
}

ICONS = {
    "ok": "object-select-symbolic",
    "warning": "dialog-warning-symbolic",
    "error": "dialog-error-symbolic",
}

# pkexec's own exit codes for a dismissed or refused authentication dialog.
PKEXEC_CANCELLED = (126, 127)

_GRUB_LINE_RE = re.compile(r"""^GRUB_CMDLINE_LINUX_DEFAULT=(["'])(.*)\1\s*$""")
_LIMINE_ENTRY_RE = re.compile(r"^\s*/+")
_LIMINE_OPTION_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)(\r?\n)?$")
_LIMINE_CMDLINE_RE = re.compile(
    r"^(\s*(?:cmdline|kernel_cmdline)\s*:\s*)(.*?)(\r?\n)?$", re.IGNORECASE)


class Device(TypedDict):
    name: str
    type: str
    brightness: str
    max: str
    path: str


class State(TypedDict):
    supported: bool
    problem: str | None
    backend: str | None
    mode: str
    panel: tuple[str, str] | None
    configured: list[str] | None
    configured_has_fix: bool
    configured_has_any: bool
    rule: str
    running: list[str]
    running_has_fix: bool
    wmi_ec_loaded: bool
    force: str | None
    devices: list[Device]
    in_use: Device | None


class BacklightFix:
    """Reports on, applies, reverts, and tests the backlight fix above."""

    def __init__(self, silent: bool = False):
        self.silent = silent
        # --silent means no dialogs and no questions. Decided once so every
        # helper below agrees.
        self.gui_tool = None if silent else self._detect_gui()
        # 'ostree', 'grub', 'limine' or None. Decided once for the same reason.
        self.limine_config = self.find_limine_config()
        self.backend = self.kargs_backend()

    # --- dialogs -----------------------------------------------------------

    def _detect_gui(self) -> str | None:
        """
        Pick a dialog tool that matches the desktop.

        Order matters: zenity is GTK and kdialog is Qt, and plenty of KDE
        installs have zenity pulled in as somebody's dependency. Picking it
        first there gives a GTK dialog on a Qt desktop.
        """
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            return None

        desktop = (os.environ.get("XDG_CURRENT_DESKTOP", "")
                   + os.environ.get("XDG_SESSION_DESKTOP", "")).upper()
        if "KDE" in desktop or "PLASMA" in desktop or os.environ.get("KDE_FULL_SESSION"):
            order = ["kdialog", "zenity", "yad"]
        else:
            order = ["zenity", "kdialog", "yad"]

        for tool in order:
            if shutil.which(tool):
                return tool
        return None

    def show_message(self, text: str, is_error: bool = False):
        if not self.gui_tool:
            print(f"\n{'Error: ' if is_error else ''}{text}\n",
                  file=sys.stderr if is_error else sys.stdout)
            return

        if self.gui_tool == "zenity":
            type_flag = "--error" if is_error else "--info"
            cmd = ["zenity", type_flag, "--no-markup", "--width=520",
                   f"--title={TITLE}", f"--text={text}"]
        elif self.gui_tool == "kdialog":
            type_flag = "--error" if is_error else "--msgbox"
            cmd = ["kdialog", type_flag, text, f"--title={TITLE}"]
        else:
            image = "dialog-error" if is_error else "dialog-information"
            cmd = ["yad", f"--image={image}", "--button=OK:0", "--width=520",
                   f"--title={TITLE}", f"--text={text}"]
        subprocess.run(cmd, stderr=subprocess.DEVNULL)

    def show_summary(self, level: str, headline: str, body: list[str]) -> bool:
        """A short status dialog in plain words. True when the technical details are asked for."""
        details = "Technical details"
        markup = (f"<big><b>{html.escape(headline, quote=False)}</b></big>\n\n"
                  + html.escape("\n".join(body), quote=False))

        if self.gui_tool == "zenity":
            res = subprocess.run(
                ["zenity", "--info", f"--title={TITLE}", f"--icon={ICONS[level]}", "--width=520",
                 f"--text={markup}", "--ok-label=Close", f"--extra-button={details}"],
                capture_output=True, text=True)
            return res.stdout.strip() == details
        if self.gui_tool == "kdialog":
            res = subprocess.run(
                ["kdialog", "--yesno", headline + "\n\n" + "\n".join(body), f"--title={TITLE}",
                 "--yes-label", "Close", "--no-label", details],
                stderr=subprocess.DEVNULL)
            return res.returncode == 1
        if self.gui_tool == "yad":
            res = subprocess.run(
                ["yad", f"--image={ICONS[level]}", f"--title={TITLE}", "--width=520",
                 f"--text={markup}", f"--button={details}:2", "--button=Close:0"],
                stderr=subprocess.DEVNULL)
            return res.returncode == 2
        return False

    def show_text(self, text: str) -> bool:
        """Technical output in a scrollable monospace window. False when the user goes back."""
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                         encoding="utf-8") as handle:
            handle.write(text)
            path = handle.name
        try:
            if self.gui_tool == "zenity":
                cmd = ["zenity", "--text-info", f"--title={TITLE}", f"--filename={path}",
                       "--font=monospace", "--width=900", "--height=680",
                       "--ok-label=Close", "--cancel-label=Back"]
            elif self.gui_tool == "kdialog":
                cmd = ["kdialog", f"--title={TITLE}", "--textbox", path, "900", "680"]
            else:
                cmd = ["yad", "--text-info", f"--title={TITLE}", f"--filename={path}",
                       "--fontname=monospace", "--width=900", "--height=680",
                       "--button=Back:1", "--button=Close:0"]
            return subprocess.run(cmd, stderr=subprocess.DEVNULL).returncode == 0
        finally:
            os.unlink(path)

    def ask_yes_no(self, question: str) -> bool | None:
        """True or False from the user, or None when --silent rules out asking."""
        if self.silent:
            return None

        if self.gui_tool == "zenity":
            cmd = ["zenity", "--question", "--no-markup", "--width=520",
                   f"--title={TITLE}", f"--text={question}"]
        elif self.gui_tool == "kdialog":
            cmd = ["kdialog", "--yesno", question, f"--title={TITLE}"]
        elif self.gui_tool == "yad":
            cmd = ["yad", "--image=dialog-question", "--button=No:1", "--button=Yes:0",
                   "--width=520", f"--title={TITLE}", f"--text={question}"]
        else:
            try:
                return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")
            except EOFError:
                return False

        return subprocess.run(cmd, stderr=subprocess.DEVNULL).returncode == 0

    def choose_action(self, summary: str) -> str | None:
        """The action picked from the menu, or None to quit."""
        names = [name for name, _ in ACTIONS]

        if self.gui_tool == "zenity":
            rows = [cell for action in ACTIONS for cell in action]
            cmd = ["zenity", "--list", f"--title={TITLE}", f"--text={summary}",
                   "--width=680", "--height=360", "--column=Action",
                   "--column=What it does", "--print-column=1",
                   "--ok-label=Run", "--cancel-label=Close", *rows]
        elif self.gui_tool == "kdialog":
            rows = [cell for name, label in ACTIONS for cell in (name, f"{name}: {label}")]
            cmd = ["kdialog", "--menu", summary, *rows, f"--title={TITLE}",
                   "--ok-label", "Run", "--cancel-label", "Close"]
        elif self.gui_tool == "yad":
            rows = [cell for action in ACTIONS for cell in action]
            cmd = ["yad", "--list", f"--title={TITLE}", f"--text={summary}",
                   "--width=680", "--height=360", "--column=Action",
                   "--column=What it does", "--print-column=1", "--separator=",
                   "--button=Close:1", "--button=Run:0", *rows]
        else:
            print(f"\n{summary}\n")
            for number, (name, label) in enumerate(ACTIONS, start=1):
                print(f"  {number}. {name:<8} {label}")
            try:
                answer = input("\nPick a number, or press Enter to quit: ").strip()
            except EOFError:
                return None
            if answer.isdigit() and 1 <= int(answer) <= len(ACTIONS):
                return names[int(answer) - 1]
            return None

        res = subprocess.run(cmd, capture_output=True, text=True)
        choice = res.stdout.strip().rstrip("|")
        return choice if res.returncode == 0 and choice in names else None

    def fail(self, text: str) -> NoReturn:
        self.show_message(text, is_error=True)
        sys.exit(1)

    # --- reading the system --------------------------------------------------
    #
    # Everything here is readable without root, so 'status' never asks for a
    # password.

    @staticmethod
    def _read(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            return ""

    def model(self) -> str:
        return self._read(DMI_DIR / "product_name") or "unknown"

    def is_supported_model(self) -> bool:
        return self._read(DMI_DIR / "board_name") == SUPPORTED_BOARD

    def nvidia_pci_devices(self) -> list[str]:
        return sorted(vendor.parent.name
                      for vendor in Path("/sys/bus/pci/devices").glob("*/vendor")
                      if self._read(vendor) == NVIDIA_VENDOR)

    def dgpu_on_pci_bus(self) -> bool:
        """In Integrated mode the NVIDIA dGPU disappears from the PCI bus entirely."""
        return bool(self.nvidia_pci_devices())

    def display_wiring(self) -> list[str]:
        """One line per DRM card: PCI address, driver, and its eDP connectors."""
        drm = Path("/sys/class/drm")
        lines: list[str] = []
        for card in sorted(p for p in drm.glob("card*") if "-" not in p.name):
            driver_link = card / "device" / "driver"
            driver = driver_link.resolve().name if driver_link.exists() else "no driver"
            edp = [f"{connector.name.split('-', 1)[1]} {self._read(connector / 'status')}"
                   for connector in sorted(drm.glob(f"{card.name}-eDP-*"))]
            lines.append(f"{card.name} ({(card / 'device').resolve().name}): {driver}, "
                         + (", ".join(edp) if edp else "no eDP connector"))
        return lines

    def panel_gpu(self) -> tuple[str, str] | None:
        """(driver, PCI address) of the GPU whose internal eDP connector is connected."""
        for status in sorted(Path("/sys/class/drm").glob("card*-eDP-*/status")):
            if self._read(status) != "connected":
                continue
            card = Path("/sys/class/drm", status.parent.name.split("-", 1)[0])
            driver = (card / "device" / "driver").resolve().name
            return driver, (card / "device").resolve().name
        return None

    def gpu_mode(self) -> str:
        """
        Integrated, Hybrid or Ultimate, read from the hardware instead of asusd.

        The dGPU being on the PCI bus separates Integrated from the rest. The
        panel's connector separates Hybrid (panel on amdgpu) from Ultimate,
        where the MUX hands the panel to the NVIDIA GPU.
        """
        if not self.dgpu_on_pci_bus():
            return "Integrated"
        panel = self.panel_gpu()
        if panel and panel[0] == "nvidia":
            return "Ultimate"
        if panel and panel[0] == "amdgpu":
            return "Hybrid"
        return "unknown"

    def backlights(self) -> list[Device]:
        root = Path("/sys/class/backlight")
        if not root.is_dir():
            return []
        return [
            {
                "name": device.name,
                "type": self._read(device / "type"),
                "brightness": self._read(device / "brightness"),
                "max": self._read(device / "max_brightness"),
                "path": str(device.resolve()),
            }
            for device in sorted(root.iterdir())
        ]

    def likely_in_use(self, devices: list[Device]) -> Device | None:
        """
        The device GNOME most likely drives: most specific type first, then the
        one on the GPU that has the panel.

        This matches what testing showed. In Hybrid mode with the fix, GNOME
        uses the firmware-type nvidia_wmi_ec_backlight over the raw amdgpu one,
        even though amdgpu has the panel.
        """
        if not devices:
            return None
        panel = self.panel_gpu()
        panel_address = panel[1] if panel else "\0"

        def rank(device: Device) -> tuple[int, bool]:
            kind = device["type"]
            position = TYPE_ORDER.index(kind) if kind in TYPE_ORDER else len(TYPE_ORDER)
            return position, panel_address not in device["path"]

        return min(devices, key=rank)

    @staticmethod
    def rewrite_grub(text: str, enable: bool,
                     restore: list[str] | None = None) -> tuple[str, list[str]]:
        """
        The GRUB defaults file with the fix's kernel parameter added or removed,
        plus any conflicting values that enabling replaced.

        On disable, restore holds the acpi_backlight= value enabling took out, read
        back from the backup file. Without it, enabling on a machine that already
        had acpi_backlight=vendor and then disabling would leave the machine with
        neither, which is not where it started. It is only ever applied when the
        fix is actually present in params: a stale backup from an enable that was
        later undone by hand must not reintroduce a value nothing here removed.

        Only a single, quoted GRUB_CMDLINE_LINUX_DEFAULT line is edited. Anything
        else raises ValueError instead of guessing at a file that boots the
        machine.
        """
        lines = text.splitlines(keepends=True)
        hits = [(i, m) for i, line in enumerate(lines)
                if (m := _GRUB_LINE_RE.match(line.rstrip("\r\n")))]
        if len(hits) != 1:
            raise ValueError(
                f"expected exactly one quoted GRUB_CMDLINE_LINUX_DEFAULT line in "
                f"{GRUB_DEFAULT}, found {len(hits)}"
            )

        index, match = hits[0]
        ending = lines[index][len(lines[index].rstrip("\r\n")):]
        quote, params = match.group(1), match.group(2).split()

        replaced: list[str] = []
        if enable:
            for wanted in KERNEL_PARAMS:
                if wanted in params:
                    continue
                key = wanted.split("=", 1)[0] + "="
                replaced += [p for p in params if p.startswith(key)]
                params = [p for p in params if not p.startswith(key)]
                params.append(wanted)
        else:
            had_fix = any(p in params for p in KERNEL_PARAMS)
            params = [p for p in params if p not in KERNEL_PARAMS]
            if had_fix:
                # Keys already present now, fixed before the loop starts, so a
                # value the user set by hand after enabling wins over the one
                # from the backup, and a backup with more than one original
                # value for the same key restores all of them instead of only
                # the first (a later one would otherwise find the first one's
                # own restore already claiming that key).
                claimed = {p.split("=", 1)[0] + "=" for p in params}
                for old in restore or []:
                    key = old.split("=", 1)[0] + "="
                    if key not in claimed:
                        params.append(old)
                        replaced.append(old)

        lines[index] = f"GRUB_CMDLINE_LINUX_DEFAULT={quote}{' '.join(params)}{quote}{ending}"
        return "".join(lines), replaced

    def grub_params(self) -> list[str] | None:
        """Parameters in GRUB_CMDLINE_LINUX_DEFAULT, or None if that can't be read safely."""
        try:
            text = GRUB_DEFAULT.read_text(encoding="utf-8")
        except OSError:
            return None
        matches = [m for line in text.splitlines() if (m := _GRUB_LINE_RE.match(line))]
        return matches[0].group(2).split() if len(matches) == 1 else None

    def replaced_by_enable(self) -> list[str]:
        """
        The acpi_backlight= values that were in GRUB_DEFAULT before the last
        enable, taken from the backup it wrote.

        Empty when there is no backup, when it can't be parsed, or when it already
        held the fix's own value, which is the case after a second enable.
        """
        try:
            text = GRUB_BACKUP.read_text(encoding="utf-8")
        except OSError:
            return []
        matches = [m for line in text.splitlines() if (m := _GRUB_LINE_RE.match(line))]
        if len(matches) != 1:
            return []
        keys = tuple(p.split("=", 1)[0] + "=" for p in KERNEL_PARAMS)
        return [p for p in matches[0].group(2).split()
                if p.startswith(keys) and p not in KERNEL_PARAMS]

    @staticmethod
    def limine_config_paths() -> list[Path]:
        paths = {}
        for path in LIMINE_CONFIG_CANDIDATES:
            if path.is_file():
                try:
                    metadata = path.stat()
                except OSError:
                    continue
                paths.setdefault((metadata.st_dev, metadata.st_ino), path)
        return list(paths.values())

    @staticmethod
    def find_limine_config() -> Path | None:
        paths = BacklightFix.limine_config_paths()
        return paths[0] if len(paths) == 1 else None

    @staticmethod
    def efi_loader_info() -> str | None:
        """Read the active bootloader name from the systemd Boot Loader Interface."""
        path = EFI_VARIABLES / "LoaderInfo-4a67b082-0a4c-41cf-b6c7-440b29bb8c4f"
        try:
            data = path.read_bytes()
            if len(data) < 6:
                return None
            return data[4:].decode("utf-16-le").rstrip("\0")
        except (OSError, UnicodeDecodeError):
            return None

    @staticmethod
    def limine_params(text: str) -> list[str]:
        """Kernel parameters in every explicitly Linux Limine entry."""
        lines = text.splitlines(keepends=True)
        starts = [i for i, line in enumerate(lines) if _LIMINE_ENTRY_RE.match(line)]
        if not starts:
            raise ValueError("no Limine menu entries were found")

        common_params: list[str] | None = None
        linux_entries = 0
        for number, start in enumerate(starts):
            end = starts[number + 1] if number + 1 < len(starts) else len(lines)
            block = lines[start:end]
            protocols = [
                match.group(2).strip().lower()
                for line in block
                if (match := _LIMINE_OPTION_RE.match(line))
                and match.group(1).lower() == "protocol"
            ]
            if "linux" not in protocols:
                continue
            if len(protocols) != 1:
                raise ValueError("a Linux entry has more than one protocol option")
            cmdlines = [
                match.group(2)
                for line in block
                if (match := _LIMINE_OPTION_RE.match(line))
                and match.group(1).lower() in ("cmdline", "kernel_cmdline")
            ]
            if len(cmdlines) > 1:
                raise ValueError("a Linux entry has more than one command-line option")
            linux_entries += 1
            entry_params = cmdlines[0].split() if cmdlines else []
            if common_params is None:
                common_params = entry_params
            else:
                entry_param_set = set(entry_params)
                common_params = [param for param in common_params if param in entry_param_set]

        if not linux_entries:
            raise ValueError("no Linux Limine entries were found")
        return common_params or []

    @staticmethod
    def rewrite_limine(text: str, enable: bool) -> tuple[str, list[str]]:
        """Add or remove the fix parameter from each Linux Limine entry."""
        lines = text.splitlines(keepends=True)
        starts = [i for i, line in enumerate(lines) if _LIMINE_ENTRY_RE.match(line)]
        if not starts:
            raise ValueError("no Limine menu entries were found")

        out = lines[:starts[0]]
        linux_entries = 0
        for number, start in enumerate(starts):
            end = starts[number + 1] if number + 1 < len(starts) else len(lines)
            block = lines[start:end]
            protocols = [
                match.group(2).strip().lower()
                for line in block
                if (match := _LIMINE_OPTION_RE.match(line))
                and match.group(1).lower() == "protocol"
            ]
            if "linux" not in protocols:
                out.extend(block)
                continue
            if len(protocols) != 1:
                raise ValueError("a Linux entry has more than one protocol option")
            linux_entries += 1
            cmdline_indexes = [
                i for i, line in enumerate(block)
                if _LIMINE_CMDLINE_RE.match(line)
            ]
            if len(cmdline_indexes) > 1:
                raise ValueError("a Linux entry has more than one command-line option")
            if not cmdline_indexes:
                if enable:
                    if block and not block[-1].endswith(("\n", "\r")):
                        block[-1] += "\n"
                    block.append("    cmdline: acpi_backlight=native\n")
                out.extend(block)
                continue

            index = cmdline_indexes[0]
            match = _LIMINE_CMDLINE_RE.match(block[index])
            assert match is not None
            raw_cmdline = match.group(2)
            parameter = re.compile(r"(?<!\S)acpi_backlight=native(?!\S)")
            if enable:
                if not parameter.search(raw_cmdline):
                    separator = "" if not raw_cmdline or raw_cmdline[-1].isspace() else " "
                    raw_cmdline += f"{separator}acpi_backlight=native"
            else:
                raw_cmdline = parameter.sub("", raw_cmdline)
            ending = match.group(3) or ""
            if not enable and not raw_cmdline.strip():
                del block[index]
            else:
                block[index] = f"{match.group(1)}{raw_cmdline}{ending}"
            out.extend(block)

        if not linux_entries:
            raise ValueError("no Linux Limine entries were found")
        return "".join(out), []

    def rule_state(self) -> str:
        if not MODPROBE_CONF.exists():
            return "absent"
        return "installed" if self._read(MODPROBE_CONF) == MODPROBE_RULE.strip() else "different"

    def kargs_backend(self) -> str | None:
        """
        How this system stores kernel parameters: 'ostree', 'grub', 'limine', or None.

        ostree is checked first on purpose. An image-based system can still
        carry a /etc/default/grub that looks editable but isn't what boots the
        machine, and editing it there would silently do nothing.
        """
        if OSTREE_MARKER.exists():
            return "ostree" if shutil.which("rpm-ostree") else None
        loader_info = self.efi_loader_info()
        if loader_info and loader_info.startswith("Limine "):
            return "limine" if self.limine_config else None
        if loader_info is None and len(self.limine_config_paths()) == 1:
            grub_available = (
                GRUB_DEFAULT.exists() and GRUB_CFG.exists()
                and shutil.which("grub-mkconfig")
            )
            if not grub_available:
                return "limine"
        if GRUB_DEFAULT.exists() and GRUB_CFG.exists() and shutil.which("grub-mkconfig"):
            return "grub"
        return None

    def platform_problem(self) -> str | None:
        """Why enable/disable can't safely run here, or None if they can."""
        if self.backend:
            return None
        if OSTREE_MARKER.exists():
            return (
                "This is an image-based system (ostree, for example Bazzite), but "
                "rpm-ostree isn't on PATH, so the kernel parameter can't be set. "
                f"Follow the manual steps instead:\n{DOC_URL}"
            )
        loader_info = self.efi_loader_info()
        limine_paths = self.limine_config_paths()
        if loader_info and loader_info.startswith("Limine "):
            if len(limine_paths) > 1:
                return (
                    "Limine is running, but more than one Limine configuration file was found. "
                    "The script won't guess which one is active. Keep only the active "
                    f"configuration in a supported location, or follow the manual steps:\n{DOC_URL}"
                )
            return (
                "Limine is running, but its configuration file wasn't found in a supported "
                f"location. Follow the manual steps:\n{DOC_URL}"
            )
        if loader_info is None and len(limine_paths) > 1:
            return (
                "More than one Limine configuration file was found, and the active one "
                f"couldn't be identified. Follow the manual steps:\n{DOC_URL}"
            )
        return (
            f"No supported way to set kernel parameters was found. This script handles "
            f"GRUB ({GRUB_DEFAULT}, {GRUB_CFG} and grub-mkconfig), rpm-ostree, and Limine. "
            "With systemd-boot, add acpi_backlight=native by hand; the modprobe rule is "
            f"the same everywhere. Manual steps:\n{DOC_URL}"
        )

    def configured_params(self) -> list[str] | None:
        """
        The kernel parameters the next boot will use, or None if they can't be read.

        On ostree that's 'rpm-ostree kargs', which reports the staged deployment
        when there is one, so it answers the same question the GRUB defaults file
        does: what is configured, as opposed to what this boot is running.
        """
        if self.backend == "ostree":
            res = subprocess.run(["rpm-ostree", "kargs"], capture_output=True, text=True)
            return res.stdout.split() if res.returncode == 0 else None
        if self.backend == "limine":
            if not self.limine_config:
                return None
            try:
                return self.limine_params(self.limine_config.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, ValueError):
                return None
        return self.grub_params()

    def state(self) -> State:
        configured = self.configured_params()
        running = self._read(Path("/proc/cmdline")).split()
        devices = self.backlights()
        return {
            "supported": self.is_supported_model(),
            "problem": self.platform_problem(),
            "backend": self.backend,
            "mode": self.gpu_mode(),
            "panel": self.panel_gpu(),
            "configured": configured,
            "configured_has_fix": configured is not None
            and all(p in configured for p in KERNEL_PARAMS),
            "configured_has_any": configured is not None
            and any(p in configured for p in KERNEL_PARAMS),
            "rule": self.rule_state(),
            "running": running,
            "running_has_fix": all(p in running for p in KERNEL_PARAMS),
            "wmi_ec_loaded": WMI_EC_MODULE.exists(),
            "force": self._read(WMI_EC_MODULE / "parameters" / "force") or None,
            "devices": devices,
            "in_use": self.likely_in_use(devices),
        }

    # --- privileged helpers --------------------------------------------------
    #
    # This script never needs to run as root itself. Everything that touches
    # /etc, /boot or sysfs for one action is bundled into a single bash script
    # and run through one pkexec call.

    def require_pkexec(self):
        if not shutil.which("pkexec"):
            self.fail("pkexec not found. This script needs it for the privileged steps.")

    @staticmethod
    def run_privileged(script: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["pkexec", "bash", "-c", script],
                              capture_output=True, text=True)

    def _apply(self, karg: str | None, rule: str | None,
               config: tuple[Path, str, str] | None = None) -> bool:
        """
        Change the kernel parameter and/or the modprobe rule, in one prompt.

        karg is 'enable', 'disable' or None, and config carries (path, original,
        new) contents for the GRUB or Limine configuration file.

        Order is deliberate: the kernel parameter goes first, and on GRUB the old
        file is put back if grub-mkconfig fails or the run is interrupted. Only
        after that is the modprobe rule touched. That ordering can't make the two
        atomic together across independent privileged mechanisms, so a modprobe
        failure after the kernel parameter already changed leaves the kernel
        parameter applied; the whole flow re-derives what still needs doing from
        current state, so re-running the same command picks up from there rather
        than duplicating or undoing it. An existing rule that isn't this one is
        copied aside first and restored on disable, and only ever touched again
        when the live file is still exactly the one this script installed,
        because the filename is generic enough that somebody may already be
        using it for something else.

        GRUB_BACKUP is the persistent record replaced_by_enable() reads on a
        later disable, so only enable refreshes it and only a successful disable
        clears it; the rollback copy put_back() uses to undo *this* run lives
        under $work instead, so a failed or interrupted disable can never
        overwrite that record with the fix's own value.

        Every file the root script reads, it writes itself. Handing root a path
        under /tmp that this unprivileged process can still write would leave a
        window to swap the contents between the polkit prompt and the copy, and
        the modprobe rule is a file of commands root runs on every module load.
        """
        q = shlex.quote
        script = ["set -euo pipefail",
                  "work=$(mktemp -d)",
                  'trap \'rm -rf "$work"\' EXIT']

        if karg and self.backend == "ostree":
            # rpm-ostree writes a new deployment, so there's nothing to back
            # up: the running one stays on disk to boot back into.
            flag = "--append-if-missing" if karg == "enable" else "--delete-if-present"
            for param in KERNEL_PARAMS:
                script.append(
                    f"rpm-ostree kargs {flag}={q(param)} "
                    '|| { echo RPM_OSTREE_FAILED >&2; exit 5; }')
        elif karg and config is not None and self.backend == "grub":
            config_path, original, new_config = config
            # Only enable snapshots the persistent backup, and only a successful
            # disable clears it; see the docstring above.
            snapshot = f"cp -p {q(str(GRUB_DEFAULT))} {q(str(GRUB_BACKUP))}" if karg == "enable" else ":"
            cleanup_backup = f"rm -f {q(str(GRUB_BACKUP))}" if karg == "disable" else ":"
            script.append(f"""
printf '%s' {q(original)} > "$work/expected"
printf '%s' {q(new_config)} > "$work/proposed"
cmp -s "$work/expected" {q(str(config_path))} || {{ echo CHANGED_ON_DISK >&2; exit 3; }}
cp -p {q(str(config_path))} "$work/rollback"
put_back() {{ cp -p "$work/rollback" {q(str(config_path))} || {{ echo PUT_BACK_FAILED >&2; exit 6; }}; }}
{snapshot}
# Ctrl+C lands here too: grub-mkconfig is slow enough that people reach for it.
trap 'put_back; exit 130' INT TERM
install -m 644 "$work/proposed" {q(str(config_path))}
if ! out=$(grub-mkconfig -o {q(str(GRUB_CFG))} 2>&1); then
    put_back
    printf '%s\\n' "$out" >&2
    exit 4
fi
trap - INT TERM
{cleanup_backup}""")
        elif karg and config is not None and self.backend == "limine":
            config_path, original, new_config = config
            script.append(f"""
printf '%s' {q(original)} > "$work/expected"
printf '%s' {q(new_config)} > "$work/proposed"
cmp -s "$work/expected" {q(str(config_path))} || {{ echo CHANGED_ON_DISK >&2; exit 3; }}
cp -p {q(str(config_path))} "$work/rollback"
put_back() {{ cp -p "$work/rollback" {q(str(config_path))} || {{ echo PUT_BACK_FAILED >&2; exit 6; }}; }}
trap 'put_back; exit 130' INT TERM
if ! install -m 644 "$work/proposed" {q(str(config_path))}; then
    put_back || exit 6
    exit 7
fi
trap - INT TERM""")

        if rule == "write":
            script.append(f"""
printf '%s' {q(MODPROBE_RULE)} > "$work/rule.conf"
if [ -e {q(str(MODPROBE_CONF))} ] && ! cmp -s "$work/rule.conf" {q(str(MODPROBE_CONF))}; then
    install -D -m 644 {q(str(MODPROBE_CONF))} {q(str(MODPROBE_BACKUP))}
fi
install -D -m 644 "$work/rule.conf" {q(str(MODPROBE_CONF))}""")
        elif rule == "remove":
            # Only ever touch MODPROBE_CONF here when it still holds exactly the
            # rule this script installed. If it was replaced by something else
            # since, or was never ours (no backup, and the live file isn't
            # ours either), leave it alone rather than deleting someone else's
            # config.
            script.append(f"""
printf '%s' {q(MODPROBE_RULE)} > "$work/rule.conf"
if [ -e {q(str(MODPROBE_CONF))} ] && cmp -s "$work/rule.conf" {q(str(MODPROBE_CONF))}; then
    if [ -e {q(str(MODPROBE_BACKUP))} ]; then
        install -D -m 644 {q(str(MODPROBE_BACKUP))} {q(str(MODPROBE_CONF))}
        rm -f {q(str(MODPROBE_BACKUP))}
    else
        rm -f {q(str(MODPROBE_CONF))}
    fi
fi""")

        res = self.run_privileged("\n".join(script))

        if res.returncode == 130:
            self.show_message("Interrupted. Nothing was changed.", is_error=True)
            return False
        if res.returncode == 0:
            return True
        if res.returncode in PKEXEC_CANCELLED:
            self.show_message("Authorization was cancelled or refused. Nothing was changed.",
                              is_error=True)
        elif res.returncode == 3:
            self.show_message(
                f"{config[0] if config else GRUB_DEFAULT} changed while this script was running. Nothing was "
                "changed. Run it again.", is_error=True)
        elif res.returncode == 4:
            print(res.stderr.strip(), file=sys.stderr)
            self.show_message(
                f"grub-mkconfig failed, so {GRUB_DEFAULT} was put back and nothing else "
                "was changed. Its output is in the terminal.", is_error=True)
        elif res.returncode == 5:
            print(res.stderr.strip() or res.stdout.strip(), file=sys.stderr)
            self.show_message(
                "'rpm-ostree kargs' failed, so nothing was changed. Its output is in the "
                "terminal. A staged deployment from another tool can block it; "
                "'rpm-ostree cleanup -p' clears that.", is_error=True)
        elif res.returncode == 6:
            print(res.stderr.strip() or res.stdout.strip(), file=sys.stderr)
            backup = (f" The last known-good copy is at {GRUB_BACKUP}."
                      if self.backend == "grub" else "")
            self.show_message(
                f"The kernel-parameter update failed or was interrupted, and restoring the "
                f"previous configuration at {config[0] if config else GRUB_DEFAULT} failed too. "
                "It may now hold the attempted change "
                f"rather than what it had before; check it by hand.{backup}", is_error=True)
        elif res.returncode == 7:
            print(res.stderr.strip() or res.stdout.strip(), file=sys.stderr)
            self.show_message(
                f"Writing the Limine configuration at {config[0] if config else 'the config file'} "
                "failed. The previous file was restored.", is_error=True)
        else:
            print(res.stderr.strip() or res.stdout.strip(), file=sys.stderr)
            self.show_message(
                f"A privileged step failed (exit code {res.returncode}). Details are in "
                "the terminal. If the kernel parameter step ran first, it may already be "
                "applied; running this command again is safe and picks up from there.",
                is_error=True)
        return False

    def _announce_slow_step(self, karg: str | None):
        """
        Say how long the privileged step takes before it starts.

        Its output is captured, so the terminal shows nothing at all while it
        runs. On an image-based system that silence lasts long enough to read as
        a hang, and reaching for Ctrl+C is the expected reaction rather than an
        unlikely one.
        """
        print("One polkit prompt covers every privileged step below.")
        if not karg:
            print()
            return
        if self.backend == "ostree":
            print("\nTHIS TAKES A WHILE. 'rpm-ostree kargs' writes a whole new deployment:\n"
                  "30 to 60 seconds is normal, and on a slow disk it can be several minutes.\n"
                  "Nothing is printed until it finishes, so a terminal that just sits there\n"
                  "is what this looks like when it is working. Let it run.\n"
                  "Ctrl+C isn't fatal if you do lose patience: rpm-ostree writes the\n"
                  "deployment in one transaction through its daemon, which rolls itself back.\n")
        elif self.backend == "grub":
            print("\nTHIS TAKES A WHILE. grub-mkconfig scans the disks for kernels and other\n"
                  "operating systems. That is a few seconds, sometimes longer, and it prints\n"
                  "nothing until it is done.\n"
                  "Ctrl+C isn't fatal if you do lose patience: this script puts the old\n"
                  f"{GRUB_DEFAULT} back before it quits.\n")
        else:
            print(f"\nThe Limine configuration at {self.limine_config} will be edited.\n")

    def _offer_reboot(self):
        if self.ask_yes_no("Reboot now to apply the change?"):
            subprocess.run(["systemctl", "reboot"])

    def _require_supported_platform(self):
        problem = self.platform_problem()
        if problem:
            self.fail(problem)

    def _karg_location(self) -> str:
        return {
            "ostree": "the ostree deployment",
            "grub": str(GRUB_DEFAULT),
            "limine": str(self.limine_config),
        }.get(self.backend or "", "kernel parameters")

    def _karg_plan(self, enable: bool) -> tuple[bool, list[str], tuple[Path, str, str] | None]:
        """
        What the kernel parameter step has to do: (needs changing, values it
        replaces, and the config file path and contents).

        The config tuple is None on ostree, where rpm-ostree edits the parameters
        itself and there's no file for this script to rewrite. Limine keeps any
        existing acpi_backlight= value and appends native; disable removes only
        native, leaving the previous value intact.
        """
        if self.backend == "ostree":
            configured = self.configured_params()
            if configured is None:
                self.fail("Couldn't read the configured kernel parameters from 'rpm-ostree "
                          f"kargs', so nothing was changed. Manual steps:\n{DOC_URL}")
            present = [p for p in KERNEL_PARAMS if p in configured]
            changes = len(present) != len(KERNEL_PARAMS) if enable else bool(present)
            return changes, [], None

        config_path = self.limine_config if self.backend == "limine" else GRUB_DEFAULT
        if config_path is None:
            self.fail("Couldn't identify the active Limine configuration, so nothing was changed. "
                      f"Follow the manual steps:\n{DOC_URL}")
        try:
            original = config_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            self.fail(f"Couldn't read {config_path}: {error}. Nothing was changed.")
        try:
            if self.backend == "limine":
                new_config, replaced = self.rewrite_limine(original, enable=enable)
            else:
                new_config, replaced = self.rewrite_grub(
                    original, enable=enable,
                    restore=None if enable else self.replaced_by_enable())
        except ValueError as error:
            self.fail(f"Can't edit {config_path} safely: {error}. "
                      f"{'Add' if enable else 'Remove'} acpi_backlight=native by hand "
                      f"instead:\n{DOC_URL}")
        return new_config != original, replaced, (config_path, original, new_config)

    def _print_steps(self, karg_changes: bool, replaced: list[str], rule_before: str,
                     enabling: bool, had_backup: bool = False):
        """The three-step report both enable and disable print after a successful run."""
        print(f"[1/3] Kernel parameter in {self._karg_location()}: {' '.join(KERNEL_PARAMS)}")
        if enabling and karg_changes:
            print("      -> added" + (f", replacing {' '.join(replaced)}" if replaced else ""))
        elif enabling:
            print("      -> already present")
        elif karg_changes:
            print("      -> removed"
                  + (f", putting back {' '.join(replaced)} from the backup" if replaced else ""))
        else:
            print("      -> wasn't there")
        if karg_changes and enabling and self.backend == "grub":
            print(f"      -> previous file kept at {GRUB_BACKUP}")

        print(f"[2/3] modprobe rule for nvidia_wmi_ec_backlight ({MODPROBE_CONF})")
        if enabling:
            print({"installed": "      -> already in place",
                   "different": f"      -> replaced a different rule, kept at {MODPROBE_BACKUP}",
                   "absent": "      -> written"}[rule_before])
        elif rule_before == "absent":
            print("      -> wasn't there")
        elif rule_before == "different":
            print("      -> left alone, it isn't this script's rule")
        elif had_backup:
            print(f"      -> removed, putting back the rule kept at {MODPROBE_BACKUP}")
        else:
            print("      -> removed")

        if self.backend == "ostree":
            print("[3/3] ostree deployment")
            print("      -> staged for the next boot" if karg_changes
                  else "      -> unchanged, nothing staged")
        elif self.backend == "grub":
            print(f"[3/3] GRUB configuration ({GRUB_CFG})")
            print("      -> regenerated" if karg_changes else "      -> unchanged, not regenerated")
        else:
            print(f"[3/3] Limine configuration ({self.limine_config})")
            print("      -> written" if karg_changes else "      -> unchanged")

    # --- enable --------------------------------------------------------------

    def enable(self):
        if not self.is_supported_model():
            self.fail(
                f"This laptop reports '{self.model()}', not a {SUPPORTED_BOARD}. The fix is "
                "specific to how that model's firmware handles brightness, so it isn't "
                f"applied anywhere else. Background:\n{DOC_URL}")
        self._require_supported_platform()
        self.require_pkexec()

        karg_changes, replaced, config = self._karg_plan(enable=True)
        rule_before = self.rule_state()
        running = all(p in self._read(Path("/proc/cmdline")).split() for p in KERNEL_PARAMS)

        print("=== Enabling the backlight fix ===")
        if not karg_changes and rule_before == "installed":
            print("Both parts are already configured.")
            if running:
                self.show_message("The backlight fix is already enabled and active.")
            else:
                self.show_message("The backlight fix is already configured, but this boot "
                                  "started without it. Reboot to apply it.")
                self._offer_reboot()
            return

        self._announce_slow_step("enable" if karg_changes else None)
        if not self._apply("enable" if karg_changes else None,
                           None if rule_before == "installed" else "write", config):
            return

        self._print_steps(karg_changes, replaced, rule_before, enabling=True)

        print("\nDone. REBOOT REQUIRED: both parts are read at boot.")
        print(f"After the reboot, run 'python3 {Path(sys.argv[0]).name} test' to check it.")

        self.show_message(
            "The backlight fix is enabled.\n\n"
            "Both parts are read at boot, so reboot to apply it. Afterwards, use "
            "'test' to check that brightness reaches the panel.")
        self._offer_reboot()

    # --- disable -------------------------------------------------------------

    def disable(self):
        if not self.is_supported_model():
            warning = (
                f"This laptop reports '{self.model()}', not a {SUPPORTED_BOARD}, so this "
                f"script never applied the fix here. Disabling still takes "
                f"{' '.join(KERNEL_PARAMS)} out of the kernel parameters, and on another "
                "machine that parameter is likely to be there for a reason of its own.")
            if self.silent:
                self.fail(f"{warning} Run it without --silent to confirm.")
            if not self.ask_yes_no(f"{warning}\n\nRemove it anyway?"):
                print("Nothing was changed.")
                return
        self._require_supported_platform()
        self.require_pkexec()

        karg_changes, replaced, config = self._karg_plan(enable=False)
        rule_before = self.rule_state()

        print("=== Disabling the backlight fix ===")
        if not karg_changes and rule_before == "absent":
            print("Neither part is configured.")
            self.show_message("The backlight fix isn't enabled, so there's nothing to remove.")
            return

        had_backup = MODPROBE_BACKUP.exists()
        self._announce_slow_step("disable" if karg_changes else None)
        if not self._apply("disable" if karg_changes else None,
                           None if rule_before == "absent" else "remove", config):
            return

        self._print_steps(karg_changes, replaced, rule_before, enabling=False,
                          had_backup=had_backup)

        print("\nDone. REBOOT REQUIRED to go back to the default backlight handling.")
        print("Reminder: without the fix, brightness doesn't work in Integrated mode.")

        self.show_message(
            "The backlight fix is removed.\n\n"
            "Reboot to go back to the default backlight handling. Without the fix, "
            "brightness doesn't work in Integrated mode.")
        self._offer_reboot()

    # --- status --------------------------------------------------------------

    def status(self):
        s = self.state()
        report = self.status_report(s)
        print(report)
        if not self.gui_tool:
            return
        level, headline, body = self.summary(s)
        while self.show_summary(level, headline, body):
            if self.show_text(report):
                return

    @staticmethod
    def fix_label(s: State) -> str:
        configured = s["configured_has_fix"] and s["rule"] == "installed"
        running = s["running_has_fix"]
        if configured:
            return "on" if running else "on after a restart"
        if s["configured_has_any"] or s["rule"] != "absent":
            return "partly set up"
        return "off after a restart" if running else "off"

    @staticmethod
    def diagnose(s: State) -> tuple[str, list[str]]:
        """
        The one conclusion about brightness on this boot, plus side notes about
        the configuration, as keys into OUTCOMES and NOTES.

        The terminal and the GUI word these differently, but both read them from
        here, so they can't disagree.
        """
        notes: list[str] = []
        if not s["supported"]:
            notes.append("unsupported")
        if s["problem"]:
            notes.append("platform")
        configured = s["configured_has_fix"] and s["rule"] == "installed"
        partly = not configured and (s["configured_has_any"] or s["rule"] != "absent")
        running = s["running_has_fix"]
        if partly:
            notes.append("partly")
        if configured and not running:
            notes.append("reboot_to_apply")
        if running and not configured and not partly:
            notes.append("reboot_to_remove")

        mode = s["mode"]
        in_use = s["in_use"]["name"] if s["in_use"] else ""
        if mode not in ("Integrated", "Hybrid", "Ultimate"):
            return "unknown_mode", notes
        if not running:
            return ("default_integrated_broken" if mode == "Integrated" else "default_ok"), notes
        if mode == "Integrated":
            return ("fix_integrated_ok" if in_use.startswith("amdgpu_bl")
                    else "fix_integrated_wrong_device"), notes
        if mode == "Ultimate":
            if in_use == "nvidia_0":
                return "fix_nvidia_ok", notes
            return ("fix_ultimate_ec_in_use" if in_use == "nvidia_wmi_ec_backlight"
                    else "fix_ultimate_wrong_device"), notes
        if in_use == "nvidia_wmi_ec_backlight":
            return "fix_ec_ok", notes
        return ("fix_rule_missing" if s["rule"] != "installed" else "fix_rule_not_loaded"), notes

    def diagnosis_lines(self, s: State) -> list[str]:
        outcome, notes = self.diagnose(s)
        fields = {
            "mode": s["mode"],
            "device": s["in_use"]["name"] if s["in_use"] else "nothing",
            "problem": s["problem"] or "",
        }
        lines = [NOTES[note][0].format(**fields) for note in notes]
        lines.append(OUTCOMES[outcome][1].format(**fields))
        if (outcome in ("default_integrated_broken", "fix_rule_missing", "fix_ultimate_ec_in_use")
                and "reboot_to_apply" not in notes):
            lines.append("Run 'enable' and reboot.")
        lines.append("Run 'test' to see whether brightness actually reaches the panel.")
        return lines

    def summary(self, s: State) -> tuple[str, str, list[str]]:
        """(icon level, headline, body lines) for the plain-words status dialog."""
        outcome, notes = self.diagnose(s)
        level, _, headline, explanation = OUTCOMES[outcome]
        # Enabled but not rebooted yet: "choose enable" would be the wrong advice.
        if "reboot_to_apply" in notes and outcome.startswith("default_"):
            explanation = ""
            if outcome == "default_integrated_broken":
                level, headline = "warning", "Restart to fix brightness"
        # The explanation already says to choose enable.
        if outcome == "fix_rule_missing" and "partly" in notes:
            notes = [note for note in notes if note != "partly"]
        if level == "ok" and notes:
            level = "warning"

        body: list[str] = [explanation, ""] if explanation else []
        body += [f"GPU mode: {MODE_LABELS.get(s['mode'], s['mode'])}",
                 f"Backlight fix: {self.fix_label(s)}"]
        if notes:
            body += [""] + [NOTES[note][1] for note in notes]
        if level == "ok":
            body += ["", "Choose test to check that the brightness really changes."]
        return level, headline, body

    def status_report(self, s: State) -> str:
        def yes_no(present: bool) -> str:
            return "yes" if present else "no"

        def params_line(params: list[str] | None) -> str:
            if params is None:
                if s["backend"] == "ostree":
                    return "couldn't be read"
                if s["backend"] == "limine":
                    return "couldn't read Linux entries in the Limine config"
                return "can't read a single quoted GRUB_CMDLINE_LINUX_DEFAULT line"
            return ", ".join(f"{p}: {yes_no(p in params)}" for p in KERNEL_PARAMS)

        try:
            os_name = platform.freedesktop_os_release().get("PRETTY_NAME", "unknown")
        except OSError:
            os_name = "unknown"

        mode, panel = s["mode"], s["panel"]
        nvidia = self.nvidia_pci_devices()
        out = ["=== Backlight fix status ===", ""]

        out.append("-- Laptop --")
        out.append(f"Model: {self.model()} ({'supported' if s['supported'] else 'not a ' + SUPPORTED_BOARD})")
        out.append(f"OS: {os_name}, kernel {platform.release()}")
        out.append(f"GPU mode: {mode}")

        out.append("")
        out.append("-- Display wiring --")
        out += self.display_wiring()
        out.append(f"Panel connected to: {panel[0]} ({panel[1]})" if panel else "Panel connected to: not found")
        out.append(f"NVIDIA PCI devices: {', '.join(nvidia) if nvidia else 'none, the dGPU is off the bus'}")

        out.append("")
        out.append("-- Configured (takes effect at boot) --")
        source = {"ostree": "rpm-ostree kargs", "grub": str(GRUB_DEFAULT),
                  "limine": str(self.limine_config)}.get(
            s["backend"] or "", "kernel parameters")
        out.append(f"{source}: {params_line(s['configured'])}")
        out.append(f"{MODPROBE_CONF}: {s['rule']}")
        out.append({
            "ostree": "Kernel parameters: ostree deployment, set with rpm-ostree kargs",
            "grub": "Kernel parameters: GRUB",
            "limine": "Kernel parameters: Limine configuration (early, untested)",
        }.get(s["backend"] or "",
              "Kernel parameters: no supported method found (see the diagnosis)"))

        out.append("")
        out.append("-- Running now --")
        out.append(f"Kernel parameter: {params_line(s['running'])}")
        if s["wmi_ec_loaded"]:
            out.append(f"nvidia_wmi_ec_backlight module: loaded, force={s['force']}")
        else:
            out.append("nvidia_wmi_ec_backlight module: not loaded")

        out.append("")
        out.append("-- Backlight devices --")
        in_use = s["in_use"]
        if not s["devices"]:
            out.append("(none)")
        for device in s["devices"]:
            marker = "  <- most likely the one GNOME uses" if device is in_use else ""
            out.append(f"{device['name']}: {device['type']}, brightness "
                       f"{device['brightness']} of {device['max']}{marker}")
        out.append("The number in amdgpu_bl* follows the DRM card number and can change between boots.")

        out.append("")
        out.append("-- Diagnosis --")
        out += self.diagnosis_lines(s)

        out.append("")
        out.append(f"Background and manual steps: {DOC_URL}")
        return "\n".join(out)

    # --- test ----------------------------------------------------------------

    def test(self):
        s = self.state()
        device = s["in_use"]
        if not device:
            self.fail("No backlight device found, so there's nothing to test.")
        try:
            maximum, original = int(device["max"]), int(device["brightness"])
        except ValueError:
            self.fail(f"Couldn't read the brightness of {device['name']}.")
        self.require_pkexec()

        low = max(1, int(maximum * TEST_LEVEL))
        name = device["name"]
        self.show_message(
            f"After you authenticate, the screen dims for {TEST_SECONDS} seconds through "
            f"{name}, then goes back to how it was.\n\nWatch the screen.")

        target = shlex.quote(str(Path("/sys/class/backlight", name, "brightness")))
        # The sleep lets the polkit dialog's own dimmed backdrop fade out first,
        # so it can't be mistaken for the test.
        script = f"""
set -e
restore() {{ echo {original} > {target}; }}
trap restore EXIT
sleep 1
echo {low} > {target}
sleep {TEST_SECONDS}
"""
        print(f"=== Testing {name} ({device['type']}) in {s['mode']} mode ===")
        print(f"Dimming from {original} to {low} of {maximum} for {TEST_SECONDS} seconds...")
        res = self.run_privileged(script)
        if res.returncode in PKEXEC_CANCELLED:
            self.show_message("Authorization was cancelled or refused. Nothing was tested.",
                              is_error=True)
            return
        if res.returncode != 0:
            print(res.stderr.strip(), file=sys.stderr)
            self.fail(f"Couldn't write to {name}. Details are in the terminal.")
        print("Restored.")

        seen = self.ask_yes_no(f"Did the screen get noticeably darker for {TEST_SECONDS} seconds?")
        if seen is None:
            print("Running with --silent, so the result can't be confirmed from here.")
            return
        if seen:
            self.show_message(
                f"Brightness reaches the panel through {name}. The brightness keys and slider "
                "should work too. If they don't, log out and back in so GNOME picks up the "
                "right device.")
            return

        print(f"Not confirmed: nothing reached the panel through {name}.")
        print("\n".join(self.diagnosis_lines(s)[:-1]))
        outcome, _ = self.diagnose(s)
        level, _, _, explanation = OUTCOMES[outcome]
        hint = explanation if level != "ok" else (
            "Log out and back in, then test again. If it still doesn't dim, compare the "
            "technical details in status with the write-up.")
        self.show_message(
            f"The screen didn't dim, so brightness isn't reaching the panel through {name}.\n\n"
            f"{hint}\n\n{DOC_URL}", is_error=True)

    # --- menu ----------------------------------------------------------------

    def menu(self):
        while True:
            s = self.state()
            summary = f"GPU mode: {s['mode']}.  Backlight fix: {self.fix_label(s)}."
            action = self.choose_action(summary)
            if action is None:
                return
            getattr(self, action)()


def main():
    if sys.version_info < MIN_PYTHON:
        need = ".".join(str(n) for n in MIN_PYTHON)
        have = ".".join(str(n) for n in sys.version_info[:3])
        print(f"This script needs Python {need} or newer; this is {have}.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Screen brightness in every GPU mode on the ASUS ROG Zephyrus G16 GA605WV")
    parser.add_argument(
        "action",
        nargs="?",
        choices=[name for name, _ in ACTIONS],
        help="status: what's configured and running, and which backlight is in use. "
             "test: dim the screen briefly to check brightness reaches the panel. "
             "enable: apply the fix. disable: remove it. Leave it out for a menu.",
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="No dialogs and no questions, terminal output only. Needs an action.",
    )
    args = parser.parse_args()
    if args.silent and not args.action:
        parser.error("--silent needs an action")

    fix = BacklightFix(silent=args.silent)
    try:
        if args.action:
            getattr(fix, args.action)()
        else:
            fix.menu()
    except KeyboardInterrupt:
        # The privileged script has its own trap and has already put things back.
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
