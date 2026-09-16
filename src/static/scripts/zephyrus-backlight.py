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

  1. Kernel parameters acpi_backlight=native amdgpu.backlight=0, so amdgpu
     gets a backlight device of its own and drives the panel over PWM.
  2. A modprobe rule that still loads nvidia_wmi_ec_backlight, with
     force=1, whenever the NVIDIA dGPU is on the PCI bus. In Hybrid and
     Ultimate mode brightness goes through the EC, and part 1 on its own
     would stop that driver from registering.

Both parts are read at boot, so enable and disable need a reboot. 'status'
shows what's configured, what's running, and which backlight device is in
use. 'test' dims the screen for a few seconds through that device, so you
can see whether brightness actually reaches the panel.

Built on CachyOS with GRUB (kernel 7.2.5). Integrated and Hybrid mode are
verified; Ultimate mode is not tested yet. Other bootloaders and image-based
systems like Bazzite are detected and refused, with a pointer to the manual
steps instead.

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

# Support policy, not a technical floor: the code itself runs on older Pythons.
# Pinned to the current stable release so nobody runs this on an
# already-unsupported interpreter.
MIN_PYTHON = (3, 14)

SUPPORTED_BOARD = "GA605WV"
DMI_DIR = Path("/sys/class/dmi/id")

GRUB_DEFAULT = Path("/etc/default/grub")
GRUB_CFG = Path("/boot/grub/grub.cfg")
GRUB_BACKUP = Path("/etc/default/grub.zephyrus-backlight.bak")
MODPROBE_CONF = Path("/etc/modprobe.d/nvidia-wmi-ec-backlight.conf")

KERNEL_PARAMS = ("acpi_backlight=native", "amdgpu.backlight=0")

# Identical to the rule in the write-up, so a hand-installed copy counts as
# installed.
MODPROBE_RULE = (
    "# acpi_backlight=native stops this driver from binding, "
    "but in Hybrid/Ultimate the backlight goes through the EC.\n"
    "# Force it only while the NVIDIA dGPU is on the PCI bus. "
    "In Integrated mode the dGPU is absent and amdgpu handles brightness.\n"
    "install nvidia_wmi_ec_backlight "
    "if /usr/bin/grep -qsx 0x10de /sys/bus/pci/devices/*/vendor; "
    "then /usr/bin/modprobe --ignore-install nvidia_wmi_ec_backlight force=1; fi\n"
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
    ("enable", "Apply the fix (kernel parameters and modprobe rule), then reboot"),
    ("disable", "Remove the fix and go back to the default, then reboot"),
]

MODE_LABELS = {
    "Integrated": "Integrated (NVIDIA GPU off)",
    "Hybrid": "Hybrid",
    "Ultimate": "Ultimate (the fix isn't tested in this mode yet)",
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


class Device(TypedDict):
    name: str
    type: str
    brightness: str
    max: str
    path: str


class State(TypedDict):
    supported: bool
    problem: str | None
    mode: str
    panel: tuple[str, str] | None
    grub: list[str] | None
    grub_has_fix: bool
    grub_has_any: bool
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
    def rewrite_grub(text: str, enable: bool) -> tuple[str, list[str]]:
        """
        The GRUB defaults file with the fix's kernel parameters added or removed,
        plus any conflicting values that enabling replaced.

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
            params = [p for p in params if p not in KERNEL_PARAMS]

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

    def rule_state(self) -> str:
        if not MODPROBE_CONF.exists():
            return "absent"
        return "installed" if self._read(MODPROBE_CONF) == MODPROBE_RULE.strip() else "different"

    def platform_problem(self) -> str | None:
        """Why enable/disable can't safely run here, or None if they can."""
        if Path("/run/ostree-booted").exists():
            return (
                "This is an image-based system (ostree, for example Bazzite). Kernel "
                "parameters are set with 'rpm-ostree kargs' there, which this script "
                f"doesn't do. Follow the manual steps instead:\n{DOC_URL}"
            )
        if not (GRUB_DEFAULT.exists() and GRUB_CFG.exists() and shutil.which("grub-mkconfig")):
            return (
                f"GRUB wasn't found ({GRUB_DEFAULT}, {GRUB_CFG} and grub-mkconfig are all "
                "needed). This script only supports GRUB. With systemd-boot or Limine, add "
                "the kernel parameters by hand; the modprobe rule is the same everywhere. "
                f"Manual steps:\n{DOC_URL}"
            )
        return None

    def state(self) -> State:
        grub = self.grub_params()
        running = self._read(Path("/proc/cmdline")).split()
        devices = self.backlights()
        return {
            "supported": self.is_supported_model(),
            "problem": self.platform_problem(),
            "mode": self.gpu_mode(),
            "panel": self.panel_gpu(),
            "grub": grub,
            "grub_has_fix": grub is not None and all(p in grub for p in KERNEL_PARAMS),
            "grub_has_any": grub is not None and any(p in grub for p in KERNEL_PARAMS),
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

    def _apply(self, original: str, new_grub: str | None, rule: str | None) -> bool:
        """
        Write the GRUB defaults and/or change the modprobe rule, in one prompt.

        Order is deliberate: the GRUB file is written and grub-mkconfig run
        first, and the old file is restored if that fails. Only after that is
        the modprobe rule touched, so a failed run leaves nothing half done.
        """
        q = shlex.quote
        with tempfile.TemporaryDirectory(prefix="zephyrus-backlight-") as tmp:
            expected = Path(tmp, "grub.expected")
            proposed = Path(tmp, "grub.new")
            rule_file = Path(tmp, "rule.conf")
            expected.write_text(original, encoding="utf-8")
            proposed.write_text(new_grub or "", encoding="utf-8")
            rule_file.write_text(MODPROBE_RULE, encoding="utf-8")

            script = ["set -euo pipefail"]
            if new_grub is not None:
                script.append(f"""
cmp -s {q(str(expected))} {q(str(GRUB_DEFAULT))} || {{ echo CHANGED_ON_DISK >&2; exit 3; }}
cp -p {q(str(GRUB_DEFAULT))} {q(str(GRUB_BACKUP))}
install -m 644 {q(str(proposed))} {q(str(GRUB_DEFAULT))}
if ! out=$(grub-mkconfig -o {q(str(GRUB_CFG))} 2>&1); then
    cp -p {q(str(GRUB_BACKUP))} {q(str(GRUB_DEFAULT))}
    printf '%s\\n' "$out" >&2
    exit 4
fi""")
            if rule == "write":
                script.append(f"install -D -m 644 {q(str(rule_file))} {q(str(MODPROBE_CONF))}")
            elif rule == "remove":
                script.append(f"rm -f {q(str(MODPROBE_CONF))}")

            res = self.run_privileged("\n".join(script))

        if res.returncode == 0:
            return True
        if res.returncode in PKEXEC_CANCELLED:
            self.show_message("Authorization was cancelled or refused. Nothing was changed.",
                              is_error=True)
        elif res.returncode == 3:
            self.show_message(
                f"{GRUB_DEFAULT} changed while this script was running. Nothing was "
                "changed. Run it again.", is_error=True)
        elif res.returncode == 4:
            print(res.stderr.strip(), file=sys.stderr)
            self.show_message(
                f"grub-mkconfig failed, so {GRUB_DEFAULT} was put back and nothing else "
                "was changed. Its output is in the terminal.", is_error=True)
        else:
            print(res.stderr.strip() or res.stdout.strip(), file=sys.stderr)
            self.show_message(
                f"A privileged step failed (exit code {res.returncode}). Details are in "
                "the terminal.", is_error=True)
        return False

    def _offer_reboot(self):
        if self.ask_yes_no("Reboot now to apply the change?"):
            subprocess.run(["systemctl", "reboot"])

    def _require_grub_platform(self):
        problem = self.platform_problem()
        if problem:
            self.fail(problem)

    # --- enable --------------------------------------------------------------

    def enable(self):
        if not self.is_supported_model():
            self.fail(
                f"This laptop reports '{self.model()}', not a {SUPPORTED_BOARD}. The fix is "
                "specific to how that model's firmware handles brightness, so it isn't "
                f"applied anywhere else. Background:\n{DOC_URL}")
        self._require_grub_platform()
        self.require_pkexec()

        original = GRUB_DEFAULT.read_text(encoding="utf-8")
        try:
            new_grub, replaced = self.rewrite_grub(original, enable=True)
        except ValueError as error:
            self.fail(f"Can't edit the GRUB defaults safely: {error}. Add the kernel "
                      f"parameters by hand instead:\n{DOC_URL}")

        grub_changes = new_grub != original
        rule_before = self.rule_state()
        running = all(p in self._read(Path("/proc/cmdline")).split() for p in KERNEL_PARAMS)

        print("=== Enabling the backlight fix ===")
        if not grub_changes and rule_before == "installed":
            print("Both parts are already configured.")
            if running:
                self.show_message("The backlight fix is already enabled and active.")
            else:
                self.show_message("The backlight fix is already configured, but this boot "
                                  "started without it. Reboot to apply it.")
                self._offer_reboot()
            return

        print("One polkit prompt covers every privileged step below.\n")
        if not self._apply(original, new_grub if grub_changes else None,
                           None if rule_before == "installed" else "write"):
            return

        print(f"[1/3] Kernel parameters in {GRUB_DEFAULT}: {' '.join(KERNEL_PARAMS)}")
        if grub_changes:
            print("      -> added" + (f", replacing {' '.join(replaced)}" if replaced else ""))
            print(f"      -> previous file kept at {GRUB_BACKUP}")
        else:
            print("      -> already present")

        print(f"[2/3] modprobe rule for nvidia_wmi_ec_backlight ({MODPROBE_CONF})")
        print({"installed": "      -> already in place",
               "different": "      -> replaced a different rule with this one",
               "absent": "      -> written"}[rule_before])

        print(f"[3/3] GRUB configuration ({GRUB_CFG})")
        print("      -> regenerated" if grub_changes else "      -> unchanged, not regenerated")

        print("\nDone. REBOOT REQUIRED: both parts are read at boot.")
        print(f"After the reboot, run 'python3 {Path(sys.argv[0]).name} test' to check it.")

        self.show_message(
            "The backlight fix is enabled.\n\n"
            "Both parts are read at boot, so reboot to apply it. Afterwards, use "
            "'test' to check that brightness reaches the panel.")
        self._offer_reboot()

    # --- disable -------------------------------------------------------------

    def disable(self):
        self._require_grub_platform()
        self.require_pkexec()

        original = GRUB_DEFAULT.read_text(encoding="utf-8")
        try:
            new_grub, _ = self.rewrite_grub(original, enable=False)
        except ValueError as error:
            self.fail(f"Can't edit the GRUB defaults safely: {error}. Remove the kernel "
                      f"parameters by hand instead:\n{DOC_URL}")

        grub_changes = new_grub != original
        rule_before = self.rule_state()

        print("=== Disabling the backlight fix ===")
        if not grub_changes and rule_before == "absent":
            print("Neither part is configured.")
            self.show_message("The backlight fix isn't enabled, so there's nothing to remove.")
            return

        print("One polkit prompt covers every privileged step below.\n")
        if not self._apply(original, new_grub if grub_changes else None,
                           None if rule_before == "absent" else "remove"):
            return

        print(f"[1/3] Kernel parameters in {GRUB_DEFAULT}")
        print("      -> removed" if grub_changes else "      -> weren't there")
        if grub_changes:
            print(f"      -> previous file kept at {GRUB_BACKUP}")
        print(f"[2/3] modprobe rule ({MODPROBE_CONF})")
        print("      -> weren't there" if rule_before == "absent" else "      -> removed")
        print(f"[3/3] GRUB configuration ({GRUB_CFG})")
        print("      -> regenerated" if grub_changes else "      -> unchanged, not regenerated")

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
        configured = s["grub_has_fix"] and s["rule"] == "installed"
        running = s["running_has_fix"]
        if configured:
            return "on" if running else "on after a restart"
        if s["grub_has_any"] or s["rule"] != "absent":
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
        configured = s["grub_has_fix"] and s["rule"] == "installed"
        partly = not configured and (s["grub_has_any"] or s["rule"] != "absent")
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
        if outcome in ("default_integrated_broken", "fix_rule_missing") and "reboot_to_apply" not in notes:
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
        if mode == "Ultimate":
            out.append("  (the fix hasn't been tested in Ultimate mode yet)")

        out.append("")
        out.append("-- Display wiring --")
        out += self.display_wiring()
        out.append(f"Panel connected to: {panel[0]} ({panel[1]})" if panel else "Panel connected to: not found")
        out.append(f"NVIDIA PCI devices: {', '.join(nvidia) if nvidia else 'none, the dGPU is off the bus'}")

        out.append("")
        out.append("-- Configured (takes effect at boot) --")
        out.append(f"{GRUB_DEFAULT}: {params_line(s['grub'])}")
        out.append(f"{MODPROBE_CONF}: {s['rule']}")
        out.append("Bootloader: not supported by this script (see the diagnosis)" if s["problem"]
                   else "Bootloader: GRUB")

        out.append("")
        out.append("-- Running now --")
        out.append(f"Kernel parameters: {params_line(s['running'])}")
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
    if args.action:
        getattr(fix, args.action)()
    else:
        fix.menu()


if __name__ == "__main__":
    main()
