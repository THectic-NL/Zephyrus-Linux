#!/usr/bin/env python3
"""
Zephyrus G16 Setup (Linux)
--------------------------
A menu for setting up an ASUS ROG Zephyrus G16 (GA605WV) the way the guides at
https://zephyrus-linux.thectic.nl describe it. Every item has a status (done,
partly done, still to do), a one-line explanation, the exact steps it would
take, and a "learn more" link to the page of the guide that explains it.

  python3 zephyrus-setup.py                  a menu (dialogs, or the terminal)
  python3 zephyrus-setup.py list             every item and where it stands
  python3 zephyrus-setup.py show asus-tools  one item in detail, with its link
  python3 zephyrus-setup.py apply --recommended --dry-run
  python3 zephyrus-setup.py apply asus-tools nvidia-prime
  python3 zephyrus-setup.py learn wsf        open the guide page for an item

Nothing changes until you have seen the plan and confirmed it. The plan lists
packages (pacman, AUR, Flathub), the steps that need root, the steps that run
as you, and what is left for you to do by hand. All root steps of one run go
into a single script under one pkexec call, so there is one polkit password
prompt per run, not one per step.

What this script does not do on its own: change the bootloader or kernel
parameters, edit PAM files, enroll Secure Boot keys, or register a YubiKey. A
mistake in any of those can lock you out of the machine, so they stay manual
items. The script shows the steps and links the guide instead.

Applying is built for CachyOS and other Arch-based systems. On anything else
(Bazzite included) 'list', 'show' and 'learn' still work, and 'apply' says why
it won't run. AUR packages need a terminal, because paru shows each PKGBUILD
for review before it builds anything. Dialogs use zenity when it is installed;
without it, or with --terminal, everything happens in the terminal.

Author: Stensel8
Structured like mt7925-tune.py and zephyrus-backlight.py: standard library
only.
"""

from __future__ import annotations
import argparse
import enum
import getpass
import hashlib
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# Support policy, not a technical floor: pinned to the current stable release
# so nobody runs this on an already-unsupported interpreter.
MIN_PYTHON = (3, 14)

TITLE = "Zephyrus G16 Setup"
SITE = "https://zephyrus-linux.thectic.nl"
SCRIPT_DIR = Path(__file__).resolve().parent
SUPPORTED_BOARD = "GA605WV"
DMI_DIR = Path("/sys/class/dmi/id")
FLATHUB_REPO = "https://dl.flathub.org/repo/flathub.flatpakrepo"

# Where the other scripts and the color profiles come from when they are not
# sitting next to this one. The ref can be changed with --ref, for example to
# try a branch before it is merged.
REPO = "THectic-NL/Zephyrus-Linux"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}"
DEFAULT_REF = "main"
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "zephyrus-setup"

# The dedicated scripts the guides publish, and the guide page that shows the
# SHA-256 of each one. That published hash is what a downloaded copy is checked
# against, so a tampered or half-downloaded script is never run.
TOOLS = {
    "zephyrus-backlight.py": "known-issues",
    "mt7925-tune.py": "networking/mt7925-wifi-performance",
    "saxion-eduroam.py": "networking/eduroam-network-installation",
}

SECTIONS = [
    ("hardware", "Hardware & ASUS", "asusctl, battery limit, power profiles, brightness"),
    ("gpu", "NVIDIA & GPU", "driver power services, PRIME offload, display freezes"),
    ("display", "Display", "factory color profiles"),
    ("network", "Networking", "Wi-Fi tuning, eduroam"),
    ("desktop", "GNOME desktop", "window buttons, focus, shortcuts, extensions, touchpad"),
    ("security", "Security & login", "autologin, YubiKey, Secure Boot"),
    ("dev", "Development", "git, GPG signing, editors, cloud tools"),
    ("apps", "Applications", "browser, messaging, office, utilities"),
    ("gaming", "Gaming", "Steam, Proton tools, overlays"),
    ("virt", "Virtualization & containers", "KVM, Podman, Distrobox, Windows apps"),
]


# --- small helpers -----------------------------------------------------------

def read_text(path: Path) -> str:
    """The file's text, or an empty string when it is missing or unreadable."""
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def doc_url(spec: str) -> str:
    """'hardware/asusctl-rog-control#anchor' -> the full URL on the guide site."""
    page, _, anchor = spec.partition("#")
    page = page.strip("/")
    url = f"{SITE}/docs/{page}/" if page else f"{SITE}/docs/"
    return f"{url}#{anchor}" if anchor else url


def color(code: str, text: str) -> str:
    if sys.stdout.isatty() and not os.environ.get("NO_COLOR"):
        return f"\033[{code}m{text}\033[0m"
    return text


def read_os_release() -> dict[str, str]:
    data: dict[str, str] = {}
    for line in read_text(Path("/etc/os-release")).splitlines():
        key, sep, value = line.partition("=")
        if sep and not key.startswith("#"):
            data[key] = value.strip().strip('"')
    return data


# --- status of one item ------------------------------------------------------

class State(enum.Enum):
    DONE = "done"
    PARTIAL = "partly done"
    TODO = "to do"
    NA = "not applicable"
    UNKNOWN = "unknown"


SYMBOLS = {State.DONE: "[x]", State.PARTIAL: "[~]", State.TODO: "[ ]", State.NA: "[-]", State.UNKNOWN: "[?]"}
SYMBOL_COLORS = {State.DONE: "32", State.PARTIAL: "33", State.TODO: "31", State.NA: "90", State.UNKNOWN: "90"}


@dataclass(frozen=True)
class Check:
    state: State
    detail: str = ""

    @property
    def symbol(self) -> str:
        return color(SYMBOL_COLORS[self.state], SYMBOLS[self.state])


# --- reading the system --------------------------------------------------------
#
# Everything in here is readable without root, so 'list' and 'show' never ask
# for a password.

class System:
    """What this machine is, plus cached answers to the questions the checks ask."""

    def __init__(self, ref: str = DEFAULT_REF, trust_local: bool = False):
        self.ref = ref
        self.trust_local = trust_local
        release = read_os_release()
        self.os_name = release.get("PRETTY_NAME") or release.get("NAME") or "Linux"
        family = f"{release.get('ID', '')} {release.get('ID_LIKE', '')}".lower()
        self.is_arch = "arch" in family or "cachyos" in family
        self.is_ostree = Path("/run/ostree-booted").exists()
        self.user = getpass.getuser()
        self.home = Path.home()
        self.vendor = read_text(DMI_DIR / "sys_vendor")
        self.board = read_text(DMI_DIR / "board_name")
        self.product = read_text(DMI_DIR / "product_name")
        self.desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
        self.is_gnome = "GNOME" in self.desktop.upper()
        self.is_asus = "ASUS" in self.vendor.upper()
        self.is_g16 = SUPPORTED_BOARD in self.board.upper()
        self.has_tty = sys.stdin.isatty() and sys.stdout.isatty()
        self._pacman: set[str] | None = None
        self._flatpaks: set[str] | None = None
        self._lspci: str | None = None
        self._in_repos: dict[str, bool] = {}

    def refresh(self):
        """Forget cached answers, after something was installed or changed."""
        self._pacman = None
        self._flatpaks = None

    # --- running commands ---------------------------------------------------

    @staticmethod
    def run(cmd: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return subprocess.CompletedProcess(cmd, 127, "", str(exc))

    def out(self, cmd: list[str]) -> str:
        return self.run(cmd).stdout.strip()

    @staticmethod
    def has_cmd(name: str) -> bool:
        return shutil.which(name) is not None

    # --- packages -----------------------------------------------------------

    def pacman_installed(self) -> set[str]:
        if self._pacman is None:
            res = self.run(["pacman", "-Qq"])
            self._pacman = set(res.stdout.split()) if res.returncode == 0 else set()
        return self._pacman

    def in_repos(self, name: str) -> bool:
        """Whether a package is in a repository pacman knows. The AUR is only for what is not."""
        if name not in self._in_repos:
            self._in_repos[name] = self.is_arch and self.run(["pacman", "-Si", name]).returncode == 0
        return self._in_repos[name]

    def flatpaks(self) -> set[str]:
        if self._flatpaks is None:
            res = self.run(["flatpak", "list", "--app", "--columns=application"])
            self._flatpaks = set(res.stdout.split()) if res.returncode == 0 else set()
        return self._flatpaks

    def has_flathub(self) -> bool:
        return "flathub" in self.out(["flatpak", "remotes", "--columns=name"]).split()

    # --- services, settings, hardware ---------------------------------------

    def unit_state(self, unit: str) -> str:
        """enabled, disabled, masked, static ... or not-found."""
        res = self.run(["systemctl", "is-enabled", unit])
        text = res.stdout.strip().splitlines()
        if text:
            return text[0]
        return "not-found" if "no such file" in res.stderr.lower() or "not-found" in res.stderr.lower() else "unknown"

    def unit_active(self, unit: str) -> bool:
        return self.run(["systemctl", "is-active", unit]).stdout.strip() == "active"

    def nvidia_handles_suspend(self) -> str | None:
        """
        Why the NVIDIA suspend units are not needed here, or None when they may be.

        NVIDIA's README: with the open kernel modules, saving video memory over
        suspend "is handled automatically if NVreg_UseKernelSuspendNotifiers=1".
        Arch's nvidia-utils sets that in /usr/lib/modprobe.d. The closed module
        still goes through the units. The open module reports a "Dual MIT/GPL" license.
        """
        if "GPL" not in self.out(["modinfo", "-F", "license", "nvidia"]).upper():
            return None
        value = None
        lines = [line for folder in ("/usr/lib/modprobe.d", "/etc/modprobe.d")
                 for conf in sorted(Path(folder).glob("*.conf")) for line in read_text(conf).splitlines()
                 if re.match(r"\s*options\s+nvidia\s", line)]
        for text in (*lines, self.cmdline):
            if found := re.findall(r"NVreg_UseKernelSuspendNotifiers=(\d)", text):
                value = found[-1]
        if value != "1":
            return None
        return "nvidia-open saves video memory itself (NVreg_UseKernelSuspendNotifiers=1), nothing to enable"

    def gsettings(self, schema: str, key: str) -> str | None:
        if not self.has_cmd("gsettings"):
            return None
        res = self.run(["gsettings", "get", schema, key])
        if res.returncode != 0:
            return None
        value = res.stdout.strip()
        return value[4:] if value.startswith("@as ") else value

    def lspci(self) -> str:
        if self._lspci is None:
            self._lspci = self.out(["lspci"]) if self.has_cmd("lspci") else ""
        return self._lspci

    @property
    def has_nvidia(self) -> bool:
        """
        Whether there is an NVIDIA GPU to set up. In Integrated mode the dGPU is off the PCI bus and
        lspci does not list it, so the G16 (it always has one) and an installed driver count as well.
        """
        return ("nvidia" in self.lspci().lower() or self.is_g16
                or "nvidia-utils" in self.pacman_installed())

    @property
    def has_mt7925(self) -> bool:
        return "mt7925" in self.lspci().lower()

    @property
    def cmdline(self) -> str:
        return read_text(Path("/proc/cmdline"))

    def bootloader(self) -> str:
        """limine, grub, systemd-boot or unknown. /boot is root-only, so this goes by /etc and packages."""
        packages = self.pacman_installed()
        if Path("/etc/default/limine").exists() or "limine" in packages:
            return "limine"
        if Path("/etc/default/grub").exists() or "grub" in packages:
            return "grub"
        if Path("/etc/sdboot-manage.conf").exists() or "systemd-boot-manager" in packages:
            return "systemd-boot"
        return "unknown"

    def in_group(self, group: str) -> bool:
        """Whether the account is in the group in /etc/group (a running session may not know yet)."""
        for line in read_text(Path("/etc/group")).splitlines():
            name, _, rest = line.partition(":")
            if name == group:
                return self.user in rest.rsplit(":", 1)[-1].split(",")
        return False


# --- the plan: what applying a set of items would do ------------------------------

@dataclass
class Step:
    """One thing done as the user. Either a command, or a Python callable."""
    desc: str
    argv: list[str] | None = None
    call: Callable[[], None] | None = None
    # Decided when the step runs, not when the plan is made: an earlier part of
    # the same run may have installed the tool this step needs.
    when: Callable[[], bool] | None = None
    # Needs the terminal for questions of its own (a login, a password prompt).
    interactive: bool = False
    # Runs before anything is installed or removed, for steps that need a tool an undo is about to remove.
    early: bool = False


@dataclass
class Plan:
    pacman: list[str] = field(default_factory=list)
    aur: list[str] = field(default_factory=list)
    flatpak: list[str] = field(default_factory=list)
    # What undoing removes. Packages some other package still needs are kept, not forced out.
    remove_pacman: list[str] = field(default_factory=list)
    remove_flatpak: list[str] = field(default_factory=list)
    root: list[tuple[str, str]] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    reboot_for: list[str] = field(default_factory=list)
    relogin_for: list[str] = field(default_factory=list)

    @staticmethod
    def _add(target: list[str], names: list[str]):
        for name in names:
            if name not in target:
                target.append(name)

    def add_pacman(self, names: list[str]):
        self._add(self.pacman, names)

    def add_aur(self, names: list[str]):
        self._add(self.aur, names)

    def add_flatpak(self, names: list[str]):
        self._add(self.flatpak, names)

    def add_root(self, desc: str, script: str):
        self.root.append((desc, script))

    def add_remove(self, pacman: list[str], flatpak: list[str]):
        self._add(self.remove_pacman, pacman)
        self._add(self.remove_flatpak, flatpak)

    @property
    def empty(self) -> bool:
        return not (self.pacman or self.aur or self.flatpak or self.root or self.steps
                    or self.remove_pacman or self.remove_flatpak)


# --- items ------------------------------------------------------------------------

@dataclass
class Item:
    id: str
    section: str
    title: str
    summary: str
    doc: str
    check: Callable[[System], Check]
    # None means the script cannot do this one for you; 'manual' says how.
    plan: Callable[[System, Plan], None] | None = None
    # Steps left for you, as a list or as a function of the machine (the bootloader decides some of them).
    manual: list[str] | Callable[[System], list[str]] = field(default_factory=list)
    undo: str = ""
    # What undoing it does, as a plan. None means the script cannot undo this one.
    undo_plan: Callable[[System, Plan], None] | None = None
    # A reason undoing it would do harm right now (a login that still depends on it), or None.
    undo_blocker: Callable[[System], str | None] | None = None
    recommended: bool = False
    advanced: bool = False
    # asus, g16, nvidia, mt7925 or empty
    hardware: str = ""
    needs_gnome: bool = False
    # A dedicated script from the guides that can be opened from here, and the
    # arguments that make it show something useful when it has no menu of its own.
    tool: str = ""
    tool_args: tuple[str, ...] = ()
    # A chooser built into this script, opened with "Open tool", for things you switch between after setting them up.
    picker: Callable[[App, TerminalUi | ZenityUi], None] | None = None
    # Packages that come from the AUR (community build scripts) unless a repository has them.
    aur: tuple[str, ...] = ()

    @property
    def url(self) -> str:
        return doc_url(self.doc)

    @property
    def has_tool(self) -> bool:
        return bool(self.tool) or self.picker is not None

    def needs_aur(self, s: System) -> bool:
        """True when something here can only come from the AUR. A package that is in a repo never counts."""
        return any(not s.in_repos(name) for name in self.aur)

    def manual_steps(self, s: System) -> list[str]:
        return self.manual(s) if callable(self.manual) else list(self.manual)

    def not_applicable(self, s: System) -> str | None:
        if self.hardware == "asus" and not s.is_asus:
            return "this is not an ASUS laptop"
        if self.hardware == "g16" and not s.is_g16:
            return f"this is a {s.product or 'different machine'}, not a Zephyrus G16 ({SUPPORTED_BOARD})"
        if self.hardware == "nvidia" and not s.has_nvidia:
            return "no NVIDIA GPU found"
        if self.hardware == "mt7925" and not s.has_mt7925:
            return "no MediaTek MT7925 Wi-Fi card found"
        if self.needs_gnome and not s.is_gnome:
            return "this needs the GNOME desktop"
        return None

    def status(self, s: System) -> Check:
        reason = self.not_applicable(s)
        if reason:
            return Check(State.NA, reason)
        return self.check(s)


def packages_check(s: System, pacman: tuple[str, ...], aur: tuple[str, ...], flatpak: tuple[str, ...]) -> Check:
    """Done when everything is installed, partly done when some of it is."""
    if (pacman or aur) and not s.is_arch:
        return Check(State.UNKNOWN, "package check needs an Arch-based system")
    installed = s.pacman_installed()
    flat = s.flatpaks() if flatpak else set()
    missing = [p for p in (*pacman, *aur) if p not in installed] + [f for f in flatpak if f not in flat]
    total = len(pacman) + len(aur) + len(flatpak)
    if not missing:
        return Check(State.DONE, "installed")
    if len(missing) == total:
        return Check(State.TODO, "not installed")
    return Check(State.PARTIAL, "missing: " + ", ".join(missing))


def package_item(item_id: str, section: str, title: str, summary: str, doc: str, *,
                 pacman: tuple[str, ...] = (), aur: tuple[str, ...] = (), flatpak: tuple[str, ...] = (),
                 recommended: bool = False, advanced: bool = False, hardware: str = "",
                 needs_gnome: bool = False, manual: tuple[str, ...] = (),
                 extra_check: Callable[[System, Check], Check] | None = None,
                 extra_plan: Callable[[System, Plan], None] | None = None,
                 extra_undo: Callable[[System, Plan], None] | None = None,
                 undo_keep: tuple[str, ...] = (), undoable: bool = True,
                 undo_blocker: Callable[[System], str | None] | None = None,
                 undo: str = "") -> Item:
    """An item that is, at heart, a set of packages, with an optional extra step or check on top."""

    def check(s: System) -> Check:
        result = packages_check(s, pacman, aur, flatpak)
        return extra_check(s, result) if extra_check else result

    def plan(s: System, p: Plan):
        installed = s.pacman_installed()
        p.add_pacman([x for x in pacman if x not in installed])
        wanted = [x for x in aur if x not in installed]
        p.add_pacman([x for x in wanted if s.in_repos(x)])
        p.add_aur([x for x in wanted if not s.in_repos(x)])
        p.add_flatpak([x for x in flatpak if x not in s.flatpaks()])
        if extra_plan:
            extra_plan(s, p)

    def undo_plan(s: System, p: Plan):
        if extra_undo:
            extra_undo(s, p)
        installed = s.pacman_installed()
        p.add_remove([x for x in (*pacman, *aur) if x in installed and x not in undo_keep],
                     [x for x in flatpak if x in s.flatpaks()])

    if not undo:
        parts = []
        if pacman or aur:
            parts.append("sudo pacman -Rs " + " ".join(x for x in (*pacman, *aur) if x not in undo_keep))
        if flatpak:
            parts.append("flatpak uninstall " + " ".join(flatpak))
        undo = "; ".join(parts)

    return Item(item_id, section, title, summary, doc, check, plan, list(manual), undo,
                undo_plan if undoable else None, undo_blocker, recommended, advanced, hardware, needs_gnome,
                aur=aur)


# --- individual checks and plan steps --------------------------------------------------

def check_battery_limit(s: System) -> Check:
    if not s.has_cmd("asusctl"):
        return Check(State.UNKNOWN, "asusctl is not installed yet")
    match = re.search(r"(\d+)\s*%", s.out(["asusctl", "battery", "info"]))
    if not match:
        return Check(State.UNKNOWN, "could not read the charge limit (is asusd running?)")
    limit = int(match.group(1))
    return Check(State.DONE if limit < 100 else State.TODO, f"charge limit is {limit}%")


def plan_battery_limit(s: System, p: Plan):
    p.add_pacman([x for x in ("asusctl", "rog-control-center") if x not in s.pacman_installed()])
    p.steps.append(Step("Limit charging to 80%", ["asusctl", "battery", "limit", "80"],
                        when=lambda: shutil.which("asusctl") is not None))


def ron_flag(text: str, key: str) -> bool | None:
    match = re.search(rf"\b{key}:\s*(true|false)", text)
    return None if match is None else match.group(1) == "true"


def check_slash(s: System) -> Check:
    if not s.has_cmd("asusctl"):
        return Check(State.UNKNOWN, "asusctl is not installed yet")
    text = read_text(Path("/etc/asusd/slash.ron"))
    enabled, battery, sleep = (ron_flag(text, k) for k in ("enabled", "show_on_battery", "show_on_sleep"))
    if enabled is None:
        return Check(State.UNKNOWN, "could not read /etc/asusd/slash.ron")
    if not enabled:
        return Check(State.DONE, "the Slash LED is switched off")
    if battery or sleep:
        return Check(State.TODO,
                     f"lit on battery: {'yes' if battery else 'no'}, during sleep: {'yes' if sleep else 'no'}")
    return Check(State.DONE, "lit on AC only, off on battery and during sleep")


def check_ppd(s: System) -> Check:
    state = s.unit_state("power-profiles-daemon.service")
    if state in ("masked", "not-found"):
        return Check(State.DONE, "power-profiles-daemon is " + ("masked" if state == "masked" else "not installed"))
    running = "running" if s.unit_active("power-profiles-daemon.service") else "not running"
    return Check(State.TODO, f"power-profiles-daemon is {state} and {running}, and fights asusd over profiles")


def plan_ppd(s: System, p: Plan):
    p.add_root("Mask power-profiles-daemon so asusd owns the power profiles",
               "systemctl mask --now power-profiles-daemon.service")
    p.notes.append("GNOME's own power-mode switch stops working once power-profiles-daemon is masked. "
                   "Switch profiles with 'asusctl profile next' or ROG Control Center instead.")


# The three units the asus-linux.org and Open Gaming Collective Arch guides enable. The fourth one,
# suspend-then-hibernate, is left alone on purpose: both guides say not to touch it unless you use that sleep mode.
NVIDIA_UNITS = ("nvidia-hibernate.service", "nvidia-suspend.service", "nvidia-resume.service")
NVIDIA_SLEEP_UNIT = "nvidia-suspend-then-hibernate.service"


def check_nvidia_services(s: System) -> Check:
    states = {unit: s.unit_state(unit) for unit in NVIDIA_UNITS}
    if all(state == "not-found" for state in states.values()):
        return Check(State.UNKNOWN, "the NVIDIA power services are not installed (is the driver there?)")
    enabled = [u for u, state in states.items() if state == "enabled"]
    reason = s.nvidia_handles_suspend()
    if reason and not enabled:
        return Check(State.NA, reason)
    if len(enabled) == len(NVIDIA_UNITS):
        return Check(State.DONE, "all three services are enabled")
    if enabled:
        return Check(State.PARTIAL, f"{len(enabled)} of {len(NVIDIA_UNITS)} services are enabled")
    return Check(State.TODO, "none of the three services is enabled")


def plan_nvidia_services(s: System, p: Plan):
    p.add_root("Enable the NVIDIA suspend, resume and hibernate services",
               "systemctl enable " + " ".join(NVIDIA_UNITS))
    p.notes.append("nvidia-suspend-then-hibernate.service stays off: enable it only if you use that sleep mode.")


def check_backlight(s: System) -> Check:
    param = "acpi_backlight=native" in s.cmdline
    rule = Path("/etc/modprobe.d/nvidia-wmi-ec-backlight.conf").exists()
    detail = f"kernel parameter: {'yes' if param else 'no'}, modprobe rule: {'yes' if rule else 'no'}"
    if param and rule:
        return Check(State.DONE, detail)
    return Check(State.PARTIAL if param or rule else State.TODO, detail)


BACKLIGHT_MANUAL = {
    "limine": ["zephyrus-backlight.py handles Limine itself (it edits /etc/default/limine and runs "
               "limine-update); the guide has the manual steps if you prefer them"],
    "grub": ["zephyrus-backlight.py handles GRUB itself; the guide has the manual steps if you prefer them"],
    "systemd-boot": ["Only if zephyrus-backlight.py refuses systemd-boot:",
                     "Add acpi_backlight=native to LINUX_OPTIONS in /etc/sdboot-manage.conf, "
                     "then: sudo sdboot-manage gen",
                     "Add the modprobe rule from the guide to /etc/modprobe.d/nvidia-wmi-ec-backlight.conf",
                     "Reboot"],
}


@dataclass(frozen=True)
class VerifiedTool:
    path: Path
    digest: str
    origin: str


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def curl_bytes(url: str) -> bytes:
    """A file over HTTPS, via curl, or a RuntimeError saying what went wrong."""
    res = subprocess.run(["curl", "-fsSL", "--proto", "=https", "--proto-redir", "=https", "--max-time", "30", url],
                         capture_output=True)
    if res.returncode != 0:
        why = res.stderr.decode("utf-8", errors="replace").strip() or f"curl exited with {res.returncode}"
        raise RuntimeError(f"could not download {url}: {why}")
    return res.stdout


def published_hash(name: str, page_text: str) -> str | None:
    """The SHA-256 a guide page publishes for a script, from its 'sha256sum -c' line."""
    match = re.search(rf"([0-9a-f]{{64}})\s+{re.escape(name)}", page_text)
    return match.group(1) if match else None


def expected_hash(name: str, ref: str) -> tuple[str, str]:
    """(hash, where it was read) as published on the guide page for the script."""
    page = TOOLS[name]
    local_doc = REPO_ROOT / "src" / "content" / "docs" / f"{page}.md"
    text = read_text(local_doc) if (SCRIPT_DIR / name).exists() else ""
    source = f"the guide page in this checkout ({page}.md)"
    if not text:
        source = f"{RAW_BASE}/{ref}/src/content/docs/{page}.md"
        text = curl_bytes(source).decode("utf-8", errors="replace")
    digest = published_hash(name, text)
    if digest is None:
        raise RuntimeError(f"no SHA-256 for {name} found on {source}")
    return digest, source


def verified_tool(s: System, name: str) -> VerifiedTool:
    """
    The path of a dedicated script whose SHA-256 matches the one published in the guide.

    A copy next to this script is used when it matches. Otherwise the script is
    downloaded from the repository at the chosen ref and checked before it is
    kept, so nothing that fails the check is ever written to the cache or run.
    """
    digest, source = expected_hash(name, s.ref)
    local = SCRIPT_DIR / name
    if local.exists():
        actual = sha256_of(local.read_bytes())
        if actual == digest:
            return VerifiedTool(local, digest, "next to this script")
        if s.trust_local:
            print(f"[WARN] {name} next to this script does not match the guide ({actual} instead of {digest}); "
                  "running it anyway because of --trust-local.")
            return VerifiedTool(local, actual, "next to this script, NOT matching the guide")
        raise RuntimeError(
            f"{name} next to this script does not match the SHA-256 in the guide.\n"
            f"  expected {digest} (from {source})\n  found    {actual}\n"
            "If you changed it yourself, run .github/scripts/check-doc-checksums.sh --apply, or use --trust-local.")
    cached = CACHE_DIR / digest / name
    if cached.exists() and sha256_of(cached.read_bytes()) == digest:
        return VerifiedTool(cached, digest, "cached download")
    url = f"{RAW_BASE}/{s.ref}/src/static/scripts/{name}"
    data = curl_bytes(url)
    actual = sha256_of(data)
    if actual != digest:
        raise RuntimeError(f"{name} downloaded from {url} does not match the SHA-256 in the guide "
                           f"(expected {digest}, got {actual}). Not running it.")
    cached.parent.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.chmod(0o700)
    cached.write_bytes(data)
    return VerifiedTool(cached, digest, f"downloaded from {url}")


def run_tool(s: System, name: str, args: list[str]):
    """Fetch and verify one of the dedicated scripts, then run it with the terminal and dialogs it expects."""
    tool = verified_tool(s, name)
    print(f"{name}: SHA-256 {tool.digest} ({tool.origin})")
    res = subprocess.run([sys.executable, str(tool.path), *args])
    if res.returncode != 0:
        raise RuntimeError(f"{name} exited with code {res.returncode}")


def plan_delegated(s: System, p: Plan, desc: str, script: str, *args: str, reboot: str = "", relogin: str = ""):
    """Run one of the dedicated scripts: next to this one, or downloaded and checked against the guide."""
    p.steps.append(Step(f"{desc} (dedicated script, checked against the SHA-256 in the guide)",
                        call=lambda: run_tool(s, script, list(args)), interactive=True))
    note = "The dedicated scripts ask for their own password prompt when they need root."
    if note not in p.notes:
        p.notes.append(note)
    if reboot:
        p.reboot_for.append(reboot)
    if relogin:
        p.relogin_for.append(relogin)


def plan_backlight(s: System, p: Plan):
    plan_delegated(s, p, "Apply the brightness fix with zephyrus-backlight.py", "zephyrus-backlight.py",
                   "enable", "--silent", reboot="the brightness fix")
    if s.bootloader() == "limine":
        p.notes.append("This machine boots with Limine: limine-update rebuilds the boot images, "
                       "which takes a minute or more and prints nothing until it is done.")


def check_psr(s: System) -> Check:
    if "amdgpu.dcdebugmask=0x600" in s.cmdline:
        return Check(State.DONE, "PSR is disabled on the AMD GPU")
    return Check(State.TODO, "PSR is on, which is fine: the freezes were mostly on kernels 6.15 to 6.18")


PSR_MANUAL = {
    "limine": ["Add amdgpu.dcdebugmask=0x600 to KERNEL_CMDLINE in /etc/default/limine",
               "Run: sudo limine-update", "Reboot"],
    "grub": ["Add amdgpu.dcdebugmask=0x600 to GRUB_CMDLINE_LINUX_DEFAULT in /etc/default/grub",
             "Run: sudo grub-mkconfig -o /boot/grub/grub.cfg", "Reboot"],
    "systemd-boot": ["Add amdgpu.dcdebugmask=0x600 to LINUX_OPTIONS in /etc/sdboot-manage.conf",
                     "Run: sudo sdboot-manage gen", "Reboot"],
}


def check_mt7925(s: System) -> Check:
    modprobe = Path("/etc/modprobe.d/mt7925e.conf").exists()
    nm = Path("/etc/NetworkManager/conf.d/wifi-powersave.conf").exists()
    detail = (f"PCIe ASPM override: {'yes' if modprobe else 'no'}, "
              f"NetworkManager power saving off: {'yes' if nm else 'no'}")
    if modprobe and nm:
        return Check(State.DONE, detail)
    return Check(State.PARTIAL if modprobe or nm else State.TODO, detail)


def check_eduroam(s: System) -> Check:
    if not s.has_cmd("nmcli"):
        return Check(State.UNKNOWN, "NetworkManager is not available")
    names = s.out(["nmcli", "-t", "-f", "NAME", "connection", "show"]).splitlines()
    if "eduroam" in names:
        return Check(State.DONE, "an eduroam connection exists")
    return Check(State.TODO, "no eduroam connection (only needed at Saxion)")


# --- GNOME settings ---------------------------------------------------------------------

WM_PREFS = "org.gnome.desktop.wm.preferences"
MEDIA_KEYS = "org.gnome.settings-daemon.plugins.media-keys"
SHORTCUTS = [
    ("org.gnome.desktop.wm.keybindings", "show-desktop", "['<Super>d']", "Super+D shows the desktop"),
    ("org.gnome.shell.keybindings", "show-screenshot-ui", "['<Shift><Super>s']", "Shift+Super+S takes a screenshot"),
    ("org.gnome.shell.keybindings", "show-screen-recording-ui", "['<Shift><Super>r']",
     "Shift+Super+R records the screen"),
    (MEDIA_KEYS, "control-center", "['<Super>i']", "Super+I opens Settings"),
    (MEDIA_KEYS, "home", "['<Super>e']", "Super+E opens the file manager"),
]


def normalise(value: str | None) -> str:
    return (value or "").replace(" ", "").replace('"', "'")


def gsettings_check(s: System, schema: str, key: str, wanted: str, what: str) -> Check:
    current = s.gsettings(schema, key)
    if current is None:
        return Check(State.UNKNOWN, "could not read the GNOME setting")
    if normalise(current) == normalise(wanted):
        return Check(State.DONE, what)
    return Check(State.TODO, f"now {current}")


def gsettings_step(schema: str, key: str, value: str, desc: str) -> Step:
    return Step(desc, ["gsettings", "set", schema, key, value])


def check_shortcuts(s: System) -> Check:
    done = [normalise(s.gsettings(schema, key)) == normalise(value) for schema, key, value, _ in SHORTCUTS]
    if all(done):
        return Check(State.DONE, "all five shortcuts are set")
    if any(done):
        return Check(State.PARTIAL, f"{sum(done)} of {len(done)} shortcuts are set")
    return Check(State.TODO, "none of the five shortcuts is set")


def plan_shortcuts(s: System, p: Plan):
    for schema, key, value, what in SHORTCUTS:
        if normalise(s.gsettings(schema, key)) != normalise(value):
            p.steps.append(gsettings_step(schema, key, value, what))


CUSTOM_KEYS = MEDIA_KEYS + ".custom-keybinding"
CUSTOM_BASE = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"


def custom_keybindings(s: System) -> list[str]:
    return re.findall(r"'([^']+)'", s.gsettings(MEDIA_KEYS, "custom-keybindings") or "")


def check_smile_shortcut(s: System) -> Check:
    for path in custom_keybindings(s):
        if "it.mijorus.smile" in (s.gsettings(f"{CUSTOM_KEYS}:{path}", "command") or ""):
            return Check(State.DONE, "a shortcut for Smile exists")
    return Check(State.TODO, "no shortcut for Smile yet")


def add_smile_shortcut():
    """Add a custom GNOME shortcut that opens Smile on the Copilot key."""
    s = System()
    existing = custom_keybindings(s)
    number = 0
    while f"{CUSTOM_BASE}/custom{number}/" in existing:
        number += 1
    path = f"{CUSTOM_BASE}/custom{number}/"
    for key, value in (("name", "Emoji picker"), ("command", "flatpak run it.mijorus.smile"),
                       ("binding", "<Shift><Super>XF86TouchpadOff")):
        res = s.run(["gsettings", "set", f"{CUSTOM_KEYS}:{path}", key, value])
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip() or f"gsettings set {key} failed")
    listing = "[" + ", ".join(f"'{p}'" for p in [*existing, path]) + "]"
    res = s.run(["gsettings", "set", MEDIA_KEYS, "custom-keybindings", listing])
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or "gsettings set custom-keybindings failed")


def plan_smile_shortcut(s: System, p: Plan):
    if "it.mijorus.smile" not in s.flatpaks():
        p.add_flatpak(["it.mijorus.smile"])
    p.steps.append(Step("Add a GNOME shortcut: Copilot key opens Smile", call=add_smile_shortcut))


EXTENSIONS = [
    ("PiP on Top", "pip-on-top"),
    ("Astra Monitor", "monitor@astraext"),
    ("Just Perfection", "just-perfection-desktop"),
    ("Smile complementary extension", "smile-extension"),
]


def check_extensions(s: System) -> Check:
    if not s.has_cmd("gnome-extensions"):
        return Check(State.UNKNOWN, "gnome-extensions is not available")
    installed = s.out(["gnome-extensions", "list"]).splitlines()
    have = [name for name, key in EXTENSIONS if any(key in uuid for uuid in installed)]
    if len(have) == len(EXTENSIONS):
        return Check(State.DONE, "all four extensions are installed")
    missing = [name for name, _ in EXTENSIONS if name not in have]
    return Check(State.PARTIAL if have else State.TODO, "missing: " + ", ".join(missing))


def check_wsf(s: System) -> Check:
    if not s.has_cmd("wsf"):
        return Check(State.TODO, "wayland-scroll-factor is not installed")
    status = s.out(["wsf", "status"])
    if "enabled: yes" in status and "gnome-shell library mapped: yes" in status:
        return Check(State.DONE, "active in gnome-shell")
    if "enabled: yes" in status:
        return Check(State.PARTIAL, "enabled, but gnome-shell has not loaded it: log out and back in")
    return Check(State.PARTIAL, "installed, not enabled yet")


def wsf_config_exists() -> bool:
    return (Path.home() / ".config" / "wayland-scroll-factor" / "config").exists()


def wsf_enabled() -> bool:
    res = System.run(["wsf", "status"])
    return "enabled: yes" in res.stdout


def plan_wsf(s: System, p: Plan):
    if "wayland-scroll-factor" not in s.pacman_installed():
        if s.in_repos("wayland-scroll-factor"):
            p.add_pacman(["wayland-scroll-factor"])
        else:
            p.add_aur(["wayland-scroll-factor"])
    p.steps.append(Step("Set the scroll factor to 0.2 (1.0 is the default speed)", ["wsf", "set", "0.2"],
                        when=lambda: shutil.which("wsf") is not None and not wsf_config_exists()))
    p.steps.append(Step("Enable wayland-scroll-factor", ["wsf", "enable"],
                        when=lambda: shutil.which("wsf") is not None and not wsf_enabled()))
    p.relogin_for.append("wayland-scroll-factor")


# --- security ------------------------------------------------------------------------------

GDM_CONF = Path("/etc/gdm/custom.conf")


def set_ini_keys(text: str, section: str, values: dict[str, str]) -> str:
    """Set keys in one section of an INI file, reusing commented-out lines and keeping everything else."""
    lines = text.splitlines()
    done: set[str] = set()
    current = ""
    section_end = None
    for index, line in enumerate(lines):
        header = re.match(r"\s*\[([^\]]+)\]\s*$", line)
        if header:
            if current == section and section_end is None:
                section_end = index
            current = header.group(1)
            continue
        if current != section:
            continue
        for key, value in values.items():
            if key not in done and re.match(rf"\s*#?\s*{re.escape(key)}\s*=", line):
                lines[index] = f"{key}={value}"
                done.add(key)
    pending = [f"{key}={value}" for key, value in values.items() if key not in done]
    if pending:
        if current == section and section_end is None:
            section_end = len(lines)
        if section_end is None:
            lines += ["", f"[{section}]", *pending]
        else:
            lines[section_end:section_end] = pending
    return "\n".join(lines) + "\n"


def check_autologin(s: System) -> Check:
    if not GDM_CONF.exists():
        return Check(State.NA, "GDM is not installed")
    conf = read_text(GDM_CONF)
    enabled = re.search(r"^\s*AutomaticLoginEnable\s*=\s*true", conf, re.MULTILINE | re.IGNORECASE)
    user = re.search(r"^\s*AutomaticLogin\s*=\s*(\S+)", conf, re.MULTILINE)
    if enabled and user and user.group(1) == s.user:
        return Check(State.DONE, f"autologin is on for {s.user}")
    return Check(State.TODO, "you still get the GDM login screen after the disk unlock")


def plan_autologin(s: System, p: Plan):
    new = set_ini_keys(read_text(GDM_CONF) + "\n", "daemon",
                       {"AutomaticLoginEnable": "True", "AutomaticLogin": s.user})
    backup = shlex.quote(str(GDM_CONF) + ".zephyrus-setup.bak")
    p.add_root(f"Turn on GDM autologin for {s.user}",
               f"[ -e {backup} ] || cp -a {shlex.quote(str(GDM_CONF))} {backup}\n"
               f"cat > {shlex.quote(str(GDM_CONF))} <<'ZEPHYRUS_EOF'\n{new}ZEPHYRUS_EOF")
    p.reboot_for.append("GDM autologin")


def check_yubikey(s: System) -> Check:
    packages = ("pam-u2f", "ccid", "pcsclite")
    missing = [x for x in packages if x not in s.pacman_installed()]
    if missing:
        return Check(State.TODO, "missing: " + ", ".join(missing))
    socket_on = s.unit_state("pcscd.socket") == "enabled"
    keys = (s.home / ".config" / "Yubico" / "u2f_keys").exists()
    wired = [name for name in ("sudo", "polkit-1", "gdm-password")
             if "pam_u2f" in read_text(Path("/etc/pam.d") / name)]
    detail = (f"pcscd socket: {'on' if socket_on else 'off'}, key registered: {'yes' if keys else 'no'}, "
              f"PAM wired: {', '.join(wired) or 'none'}")
    if socket_on and keys and len(wired) == 3:
        return Check(State.DONE, detail)
    return Check(State.PARTIAL, detail)


def plan_yubikey(s: System, p: Plan):
    p.add_pacman([x for x in ("pam-u2f", "ccid", "pcsclite") if x not in s.pacman_installed()])
    p.add_flatpak([x for x in ("com.yubico.yubioath",) if x not in s.flatpaks()])
    p.add_root("Start the smart card daemon now and at boot", "systemctl enable --now pcscd.socket")


def check_secure_boot(s: System) -> Check:
    state = s.out(["bootctl", "status"]) if s.has_cmd("bootctl") else ""
    enabled = re.search(r"Secure Boot:\s*enabled", state, re.IGNORECASE) is not None
    has_sbctl = "sbctl" in s.pacman_installed()
    if enabled and has_sbctl:
        return Check(State.DONE, "Secure Boot is on and sbctl is installed")
    if has_sbctl:
        return Check(State.PARTIAL, "sbctl is installed, Secure Boot is still off")
    return Check(State.TODO, f"Secure Boot is {'on' if enabled else 'off'}, sbctl is not installed")


def plan_secure_boot(s: System, p: Plan):
    p.add_pacman([x for x in ("sbctl",) if x not in s.pacman_installed()])


# --- development and applications -------------------------------------------------------

def check_gh(s: System, result: Check) -> Check:
    if result.state is not State.DONE:
        return result
    if s.run(["gh", "auth", "status"]).returncode != 0:
        return Check(State.PARTIAL, "installed, but not signed in to GitHub yet")
    return Check(State.DONE, "installed and signed in to GitHub")


def git_config(key: str) -> str:
    return System.run(["git", "config", "--global", "--get", key]).stdout.strip()


def check_git_signing(s: System, result: Check) -> Check:
    key = git_config("user.signingkey")
    commits = git_config("commit.gpgsign") == "true"
    tags = git_config("tag.gpgsign") == "true"
    if result.state is State.TODO:
        return result
    if key and commits and tags:
        return Check(State.DONE, f"commits and tags are signed with {key}")
    if not key:
        return Check(State.PARTIAL, "Kleopatra is installed, but git has no signing key yet")
    return Check(State.PARTIAL, f"commit signing: {'on' if commits else 'off'}, tag signing: {'on' if tags else 'off'}")


def plan_git_signing(s: System, p: Plan):
    if not git_config("user.signingkey"):
        p.notes.append("Create or import a key in Kleopatra, then run: git config --global user.signingkey <key id>. "
                       "Run this item again afterwards to switch on signing.")
        return
    for key, value in (("commit.gpgsign", "true"), ("tag.gpgsign", "true"), ("gpg.program", "gpg")):
        if git_config(key) != value:
            p.steps.append(Step(f"Set git {key} to {value}", ["git", "config", "--global", key, value]))


TOPGRADE_CONF = Path.home() / ".config" / "topgrade.toml"
TOPGRADE_TEXT = """[misc]
# fwupdmgr wants a reboot into the firmware updater on the G16, rarely what you want mid-update
disable = ["firmware"]
ignore_failures = ["containers"]
assume_yes = true

[linux]
arch_package_manager = "paru"
"""


def check_topgrade(s: System, result: Check) -> Check:
    if result.state is not State.DONE:
        return result
    if not TOPGRADE_CONF.exists():
        return Check(State.PARTIAL, "installed, no ~/.config/topgrade.toml yet")
    return Check(State.DONE, "installed and configured")


def write_topgrade_conf():
    if TOPGRADE_CONF.exists():
        return
    TOPGRADE_CONF.parent.mkdir(parents=True, exist_ok=True)
    TOPGRADE_CONF.write_text(TOPGRADE_TEXT, encoding="utf-8")


def plan_topgrade(s: System, p: Plan):
    if not TOPGRADE_CONF.exists():
        p.steps.append(Step("Write ~/.config/topgrade.toml (skip firmware, use paru)", call=write_topgrade_conf))


def check_vscode(s: System, result: Check) -> Check:
    if result.state is State.DONE and "code" in s.pacman_installed():
        return Check(State.PARTIAL, "the Microsoft build is installed, and so is Code - OSS: remove it with "
                     "'sudo pacman -R code' (see the guide)")
    return result


def plan_localsend(s: System, p: Plan):
    if s.unit_active("ufw.service"):
        p.add_root("Open the LocalSend port (53317) in ufw",
                   "ufw allow 53317/tcp comment 'LocalSend-App'\nufw allow 53317/udp comment 'LocalSend-App'")


def plan_podman(s: System, p: Plan):
    p.add_root("Silence the 'Emulate Docker CLI' notice", "touch /etc/containers/nodocker")
    p.add_root("Let short image names resolve through docker.io and ghcr.io",
               "mkdir -p /etc/containers/registries.conf.d\n"
               "cat > /etc/containers/registries.conf.d/99-zephyrus-search.conf <<'ZEPHYRUS_EOF'\n"
               "unqualified-search-registries = [\"docker.io\", \"ghcr.io\"]\nZEPHYRUS_EOF")


def check_podman(s: System, result: Check) -> Check:
    if result.state is State.DONE and not Path("/etc/containers/nodocker").exists():
        return Check(State.PARTIAL, "installed; short image names and the docker notice are not configured yet")
    return result


def check_kvm(s: System, result: Check) -> Check:
    if result.state is not State.DONE:
        return result
    parts = {"libvirtd enabled": s.unit_state("libvirtd.service") == "enabled",
             "in the libvirt group": s.in_group("libvirt")}
    off = [name for name, ok in parts.items() if not ok]
    if off:
        return Check(State.PARTIAL, "installed, but: " + ", ".join(off).replace("enabled", "is not enabled"))
    return Check(State.DONE, "installed, libvirtd enabled, you are in the libvirt group")


def plan_kvm(s: System, p: Plan):
    script = [f"usermod --append --groups libvirt {shlex.quote(s.user)}",
              "systemctl enable --now libvirtd",
              "virsh net-start default || true",
              "virsh net-autostart default"]
    p.add_root("Set up libvirt: your account, the service, the default network", "\n".join(script))
    if s.unit_active("ufw.service"):
        p.add_root("Let VMs reach DNS and DHCP through ufw",
                   "ufw allow in on virbr0 to any port 53 proto udp comment 'VM DNS'\n"
                   "ufw allow in on virbr0 to any port 67 proto udp comment 'VM DHCP'\n"
                   "ufw route allow in on virbr0\nufw route allow out on virbr0")
    p.relogin_for.append("the libvirt group")


def check_virtio_iso(s: System) -> Check:
    iso = Path("/var/lib/libvirt/images/virtio-win.iso")
    try:
        size = iso.stat().st_size
    except OSError:
        return Check(State.TODO, "no VirtIO drivers ISO yet")
    return Check(State.DONE if size > 700_000_000 else State.PARTIAL,
                 f"{size // 1_000_000} MB (a complete download is about 753 MB)")


def plan_virtio_iso(s: System, p: Plan):
    p.add_root("Download the VirtIO drivers ISO (about 753 MB)",
               "mkdir -p /var/lib/libvirt/images\n"
               "curl -fL --proto '=https' -o /var/lib/libvirt/images/virtio-win.iso "
               "https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso")


# --- color profiles ------------------------------------------------------------------------

ICC_DIR = Path.home() / ".local" / "share" / "icc"
# colord's own store, owned by root. A profile that lands there shadows a file with the same contents in ICC_DIR.
COLORD_STORE = Path("/var/lib/colord/icc")
GPU_VENDORS = {"0x1002": "1002", "0x10de": "10DE"}


def internal_panel() -> tuple[str, str] | None:
    """(GPU vendor id, panel id) of the built-in display, e.g. ('1002', '104D158E'), from its EDID."""
    for status in sorted(Path("/sys/class/drm").glob("card*-eDP-*/status")):
        if read_text(status) != "connected":
            continue
        try:
            edid = (status.parent / "edid").read_bytes()
        except OSError:
            continue
        # The connector (card2-eDP-2) has no vendor file of its own; the card it belongs to does.
        card = status.parent.name.split("-", 1)[0]
        gpu = GPU_VENDORS.get(read_text(Path("/sys/class/drm") / card / "device" / "vendor").lower())
        if len(edid) >= 12 and gpu:
            # ASUS names the panel by the EDID's manufacturer and product bytes, both read little-endian
            # ('SHP' and 0x158E become 104D158E).
            maker = int.from_bytes(edid[8:10], "little")
            product = int.from_bytes(edid[10:12], "little")
            return gpu, f"{maker:04X}{product:04X}"
    return None


def asus_profile_name() -> str | None:
    panel = internal_panel()
    return f"GA605WV_{panel[0]}_{panel[1]}_CMDEF.icm" if panel else None


# The modes G-Helper offers on Windows (Gamut: Native, sRGB, DCIP3, DisplayP3): the factory-calibrated profile of
# the panel itself, and three generic ASUS ones. (key, name shown in GNOME, file; None is the panel's own profile.)
COLOR_MODES = [
    ("native", "ASUS Native (factory calibrated)", None),
    ("srgb", "ASUS sRGB", "ASUS_sRGB.icm"),
    ("dcip3", "ASUS DCI-P3", "ASUS_DCIP3.icm"),
    ("displayp3", "ASUS Display P3", "ASUS_DisplayP3.icm"),
]
KNOWN_PANELS = {f"GA605WV_{gpu}_{panel}_CMDEF.icm" for gpu in ("1002", "10DE")
                for panel in ("104D158E", "834C41AE", "E5090C19")}


def color_mode_files() -> list[tuple[str, str, str]]:
    """(key, title, file name) of each mode for this machine's panel, or nothing when the panel is unknown."""
    native = asus_profile_name()
    if native is None or native not in KNOWN_PANELS:
        return []
    return [(key, title, name or native) for key, title, name in COLOR_MODES]


def icc_tags(data: bytes) -> list[tuple[bytes, bytes]]:
    """The (signature, content) of every tag in an ICC profile, in table order."""
    count = struct.unpack(">I", data[128:132])[0]
    tags = []
    for index in range(count):
        sig, offset, size = struct.unpack(">4sII", data[132 + 12 * index:144 + 12 * index])
        tags.append((sig, data[offset:offset + size]))
    return tags


def icc_description(data: bytes) -> str:
    """The profile description, which is the name GNOME and colord show for it."""
    for sig, blob in icc_tags(data):
        if sig != b"desc":
            continue
        if blob[:4] == b"desc":
            length = struct.unpack(">I", blob[8:12])[0]
            return blob[12:12 + max(length - 1, 0)].decode("latin-1")
        if blob[:4] == b"mluc":
            size, offset = struct.unpack(">II", blob[20:28])
            return blob[offset:offset + size].decode("utf-16-be")
    return ""


def icc_with_description(data: bytes, title: str) -> bytes:
    """A copy of an ICC profile with another description. Everything else, the color data included, is untouched."""
    text = title.encode("ascii")
    if data[8] >= 4:
        utf16 = title.encode("utf-16-be")
        new = (b"mluc" + bytes(4) + struct.pack(">II", 1, 12) + b"enUS" + struct.pack(">II", len(utf16), 28) + utf16)
    else:
        new = (b"desc" + bytes(4) + struct.pack(">I", len(text) + 1) + text + b"\0" + bytes(4) + bytes(4)
               + bytes(2) + bytes(1) + bytes(67))
    tags = [(sig, new if sig == b"desc" else blob) for sig, blob in icc_tags(data)]
    offset = 128 + 4 + 12 * len(tags)
    placed: dict[bytes, int] = {}
    body = b""
    entries = []
    for sig, blob in tags:
        if blob not in placed:
            placed[blob] = offset + len(body)
            body += blob + bytes((-len(blob)) % 4)
        entries.append(struct.pack(">4sII", sig, placed[blob], len(blob)))
    header = bytearray(data[:128])
    struct.pack_into(">I", header, 0, offset + len(body))
    header[84:100] = bytes(16)  # the profile ID no longer matches the content; zero means "not computed"
    return bytes(header) + struct.pack(">I", len(tags)) + b"".join(entries) + body


def icc_source(ref: str, name: str) -> bytes:
    """A profile from this checkout when it is here, otherwise from the repository at the chosen ref."""
    local = SCRIPT_DIR.parent / "icc-profiles" / name
    data = local.read_bytes() if local.exists() else curl_bytes(f"{RAW_BASE}/{ref}/src/static/icc-profiles/{name}")
    # ICC profiles carry the signature 'acsp' at byte 36. Anything else is not one, whatever the server said.
    if data[36:40] != b"acsp":
        raise RuntimeError(f"{name} is not an ICC profile (bad signature), not installing it")
    return data


STAGE_DIR = Path.home() / ".cache" / "zephyrus-setup" / "icc"


def stage_color_modes(ref: str):
    """
    Prepare the four modes under readable names in a private folder. The root step copies them from there into
    colord's own folder, and the step after it adds them to the display.

    Copies this script put in ~/.local/share/icc in an earlier version are removed first. A file there has the
    same contents, so the same colord ID, as the one in colord's folder, and colord drops the ID for both when
    either file goes away.
    """
    modes = color_mode_files()
    if not modes:
        raise RuntimeError("no factory profiles are published for this panel")
    for _, _, name in modes:
        (ICC_DIR / name).unlink(missing_ok=True)
    STAGE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    for _, title, name in modes:
        (STAGE_DIR / name).write_bytes(icc_with_description(icc_source(ref, name), title))


def unstage_color_modes():
    for path in STAGE_DIR.glob("*"):
        path.unlink(missing_ok=True)


# --- colord: the profiles of the built-in display ---------------------------------------------

def colord_object(text: str) -> str | None:
    match = re.search(r"Object Path:\s*(\S+)", text)
    return match.group(1) if match else None


def display_device(s: System) -> str | None:
    """colord's object path of the built-in display, the one GNOME's Color Management lists as Built-in Screen."""
    text = s.out(["colormgr", "get-devices-by-kind", "display"])
    for block in re.split(r"\n(?=Object Path:)", text):
        if re.search(r"Embedded:\s*Yes", block) or "XRANDR_name=eDP" in block:
            return colord_object(block)
    return None


def profile_id(path: Path) -> str | None:
    """
    colord's ID for a profile file: 'icc-' and the MD5 of its contents.

    colord keeps one profile per ID. A second file with the same contents, such as ours next to a copy colord made
    itself, is not a profile of its own, so profiles are matched by this ID and never by path alone.
    """
    try:
        return "icc-" + hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()
    except OSError:
        return None


def device_profile_list(s: System, device: str) -> list[tuple[str, str]]:
    """(profile ID, file name) of the profiles on a device, in priority order. The first one is the active profile."""
    text = s.out(["colormgr", "get-devices-by-kind", "display"])
    for block in re.split(r"\n(?=Object Path:)", text):
        if colord_object(block) == device:
            return re.findall(r"Profile \d+:\s+(\S+)\s*\n\s+(\S+)", block)
    return []


def colord_profile(s: System, path: Path, title: str = "") -> str | None:
    """
    colord's object path for a profile file, by file name first and then by its contents. With a title, only once
    colord has read the file with that title.
    """
    lookups = [["colormgr", "find-profile-by-filename", str(path)]]
    if pid := profile_id(path):
        lookups.append(["colormgr", "find-profile", pid])
    for cmd in lookups:
        res = s.run(cmd)
        if res.returncode != 0:
            continue
        if title and not re.search(rf"Title:\s*{re.escape(title)}\s*$", res.stdout, re.MULTILINE):
            continue
        if found := colord_object(res.stdout):
            return found
    return None


def system_color_copies() -> list[Path]:
    """Our modes in colord's own folder, found by title so a copy under another name counts. Root removes them."""
    titles = {title for _, title, _ in color_mode_files()}
    found = []
    for path in sorted(COLORD_STORE.glob("*.ic*")):
        try:
            if icc_description(path.read_bytes()) in titles:
                found.append(path)
        except OSError:
            continue
    return found


def color_mode_state(s: System) -> list[tuple[str, str, Path, bool, bool]]:
    """(key, title, file, on the display, active) for each mode."""
    device = display_device(s) if s.has_cmd("colormgr") else None
    ids = [pid for pid, _ in device_profile_list(s, device)] if device else []
    out = []
    for key, title, name in color_mode_files():
        path = COLORD_STORE / name
        pid = profile_id(path)
        out.append((key, title, path, pid in ids, bool(ids) and ids[0] == pid))
    return out


def wait_for_profile(s: System, path: Path, title: str, tries: int) -> str | None:
    """colord's object path once it has read this file with this title. It reads new files a moment after they land."""
    for _ in range(tries):
        found = colord_profile(s, path, title)
        if found:
            return found
        time.sleep(0.5)
    return None


def register_color_modes(s: System):
    """Give the display all four modes, so Settings > Color Management lists them, the way G-Helper lists its modes."""
    device = display_device(s)
    if device is None:
        raise RuntimeError("colord does not know the built-in display. Run this inside the GNOME session.")
    on_device = device_profile_list(s, device)
    registered = []
    for _, title, name in color_mode_files():
        path = COLORD_STORE / name
        found = wait_for_profile(s, path, title, 20)
        if found is None:
            raise RuntimeError(f"colord did not pick up {path} within 10 seconds")
        registered.append((found, str(path)))
        # Asked again for every mode: colord changes the display's list as it reads the files.
        if profile_id(path) not in [pid for pid, _ in device_profile_list(s, device)]:
            res = s.run(["colormgr", "device-add-profile", device, found])
            reason = (res.stderr or res.stdout).strip()
            if res.returncode != 0 and "already been added" not in reason:
                # colormgr prints its complaints on stdout
                raise RuntimeError(f"could not add {path.name} to the display: {reason or 'colord gave no reason'}")
    # Native becomes the active profile, but only when nothing but the automatic EDID profile was in charge.
    active = on_device[0][1] if on_device else ""
    if not active or Path(active).name.startswith("edid-"):
        native = registered[0]
        res = s.run(["colormgr", "device-make-profile-default", device, native[0]])
        if res.returncode != 0:
            raise RuntimeError(f"could not make {Path(native[1]).name} the active profile: "
                               f"{(res.stderr or res.stdout).strip() or 'colord gave no reason'}")
    unstage_color_modes()


def set_color_mode(s: System, key: str):
    state = color_mode_state(s)
    device = display_device(s) if s.has_cmd("colormgr") else None
    chosen = next((row for row in state if row[0] == key), None)
    if chosen is None or device is None:
        raise RuntimeError("no color modes for this display. Apply 'display-color-modes' first.")
    if not chosen[3]:
        raise RuntimeError(f"{chosen[1]} is not on the display yet. Apply 'display-color-modes' first.")
    profile = colord_profile(s, chosen[2])
    if profile:
        # A display can list a profile colord has since dropped and read again. Adding it first puts it back.
        s.run(["colormgr", "device-add-profile", device, profile])
    res = s.run(["colormgr", "device-make-profile-default", device, profile or ""])
    if profile is None or res.returncode != 0:
        raise RuntimeError(f"could not switch to {chosen[1]}: "
                           f"{(res.stderr or res.stdout).strip() or 'colord does not know the file'}")


def check_color_modes(s: System) -> Check:
    modes = color_mode_files()
    if not modes:
        if asus_profile_name() is None:
            return Check(State.UNKNOWN, "could not read the built-in display's panel ID")
        return Check(State.UNKNOWN, f"no factory profile is published for this panel ({asus_profile_name()})")
    if not s.has_cmd("colormgr"):
        return Check(State.UNKNOWN, "colormgr (colord) is not installed")
    titles = {name: title for _, title, name in modes}
    installed = [n for n, title in titles.items() if (COLORD_STORE / n).exists()
                 and icc_description((COLORD_STORE / n).read_bytes()) == title]
    on_display = [row for row in color_mode_state(s) if row[3]]
    old_copies = [n for n in titles if (ICC_DIR / n).exists()]  # from an earlier version of this script
    if len(installed) == len(modes) and len(on_display) == len(modes):
        active = next((row[1] for row in on_display if row[4]), "none of them")
        return Check(State.DONE, f"all four modes are on the display, active: {active}")
    if installed or on_display or old_copies:
        extra = ", an older copy is in your home folder" if old_copies else ""
        return Check(State.PARTIAL,
                     f"{len(installed)} of {len(modes)} installed, {len(on_display)} on the display{extra}")
    return Check(State.TODO, "the ASUS color modes are not installed")


def plan_color_modes(s: System, p: Plan):
    names = [name for _, _, name in color_mode_files()]
    p.steps.append(Step("Prepare the four ASUS color profiles under readable names",
                        call=lambda: stage_color_modes(s.ref), early=True))
    # A file that is already there with the same contents is left alone: colord drops a profile when its file is
    # overwritten and does not always read it again, and a restart of colord does not bring the display back
    # until the next login. So nothing here ever touches a profile that is already in place.
    copies = "\n".join(f"cmp -s {shlex.quote(str(STAGE_DIR / name))} {shlex.quote(str(COLORD_STORE / name))} || "
                       f"install -m 644 -o colord -g colord {shlex.quote(str(STAGE_DIR / name))} "
                       f"{shlex.quote(str(COLORD_STORE / name))}" for name in names)
    p.add_root("Put the profiles in colord's own profile folder, where it reads them reliably",
               f"install -d -m 755 -o colord -g colord {shlex.quote(str(COLORD_STORE))}\n{copies}")
    p.steps.append(Step("Add them to the Built-in Screen in colord", call=lambda: register_color_modes(System())))
    p.notes.append("Pick a mode in Settings > Color Management > Built-in Screen, or with: "
                   "python3 zephyrus-setup.py color set srgb")
    p.notes.append("These profiles tell color-managed apps (browsers, image editors) what the panel does. They do not "
                   "change how the desktop looks: GNOME applies no color transform of its own to it, and the "
                   "ASUS sRGB, DCI-P3 and Display P3 gamut switch on Windows is a firmware command that Linux lacks.")
    p.notes.append("After switching GPU mode (Hybrid, Integrated, Ultimate), run this item again: each mode has "
                   "its own display.")


def pick_color_mode(app: App, ui: TerminalUi | ZenityUi):
    """Choose the active mode, like the Gamut list in G-Helper."""
    state = color_mode_state(app.s)
    if not state or not any(row[3] for row in state):
        ui.message("The color modes are not on the display yet. Apply 'display-color-modes' first.")
        return
    options = [(key, title + ("   (active)" if active else "")) for key, title, _, on, active in state if on]
    chosen = ui.choose("Color mode", "Which mode should the built-in screen use?", options)
    if chosen:
        try:
            set_color_mode(app.s, chosen)
        except RuntimeError as exc:
            ui.message(str(exc))
            return
        ui.message(f"Switched to {dict(options)[chosen].split('   (')[0]}.")
        app.reset()


# --- undoing -----------------------------------------------------------------------------------------
#
# Each function says what putting one item back would do. They restore the stock state, which is not always
# what was there before: a setting you had changed yourself goes back to the default, not to your value.

def undo_battery_limit(s: System, p: Plan):
    p.steps.append(Step("Charge to 100% again", ["asusctl", "battery", "limit", "100"], early=True))


def undo_slash(s: System, p: Plan):
    p.steps.append(Step("Slash LED: lit on battery and during sleep again",
                        ["asusctl", "slash", "set", "--enable", "-b", "true", "-s", "true"], early=True))


def undo_ppd(s: System, p: Plan):
    p.add_root("Unmask power-profiles-daemon", "systemctl unmask power-profiles-daemon.service")


def undo_nvidia_services(s: System, p: Plan):
    p.add_root("Disable the NVIDIA suspend/resume/hibernate services",
               "systemctl disable " + " ".join((*NVIDIA_UNITS, NVIDIA_SLEEP_UNIT)))


def undo_backlight(s: System, p: Plan):
    plan_delegated(s, p, "Remove the brightness fix with zephyrus-backlight.py", "zephyrus-backlight.py",
                   "disable", "--silent", reboot="removing the brightness fix")


def undo_mt7925(s: System, p: Plan):
    plan_delegated(s, p, "Revert the Wi-Fi tuning with mt7925-tune.py", "mt7925-tune.py", "disable",
                   reboot="reverting the PCIe ASPM override")


def undo_eduroam(s: System, p: Plan):
    p.steps.append(Step("Remove the eduroam connection", ["nmcli", "connection", "delete", "eduroam"]))


def release_color_modes(s: System):
    """
    First half of an undo, as the user: hand the display back to its automatic profile and remove the copies an
    earlier version put in ~/.local/share/icc. A copy there has the same colord ID as the one in colord's folder,
    so it goes before the root step removes that one.
    """
    device = display_device(s) if s.has_cmd("colormgr") else None
    if device is None:
        raise RuntimeError("colord does not know the built-in display. Run this inside the GNOME session.")
    names = [name for _, _, name in color_mode_files()]
    ours = {pid for pid in (profile_id(COLORD_STORE / name) for name in names) if pid}
    on_device = device_profile_list(s, device)
    if on_device and on_device[0][0] in ours:
        auto = next((f for _, f in on_device if Path(f).name.startswith("edid-")), None)
        automatic = colord_profile(s, Path(auto)) if auto else None
        if automatic:
            s.run(["colormgr", "device-make-profile-default", device, automatic])
    for name in names:
        (ICC_DIR / name).unlink(missing_ok=True)
    unstage_color_modes()


def restore_automatic_profile(s: System):
    """Last half of an undo: never leave the screen without a profile. Put the automatic one (from EDID) back."""
    device = display_device(s) if s.has_cmd("colormgr") else None
    if device is None or device_profile_list(s, device):
        return
    edid = next(iter(sorted(ICC_DIR.glob("edid-*.icc"))), None)
    automatic = colord_profile(s, edid) if edid else None
    if automatic:
        s.run(["colormgr", "device-add-profile", device, automatic])
        s.run(["colormgr", "device-make-profile-default", device, automatic])


def undo_color_modes(s: System, p: Plan):
    p.steps.append(Step("Switch the display back to its automatic profile and remove older copies",
                        call=lambda: release_color_modes(s), early=True))
    if copies := system_color_copies():
        p.add_root("Remove the profiles from colord's own profile folder",
                   "rm -f -- " + " ".join(shlex.quote(str(path)) for path in copies))
    p.steps.append(Step("Check that the display kept its automatic profile",
                        call=lambda: restore_automatic_profile(s)))


def undo_window_buttons(s: System, p: Plan):
    p.steps.append(Step("Reset the window button layout", ["gsettings", "reset", WM_PREFS, "button-layout"]))


def undo_focus(s: System, p: Plan):
    p.steps.append(Step("Reset how new windows get focus", ["gsettings", "reset", WM_PREFS, "focus-new-windows"]))


def undo_shortcuts(s: System, p: Plan):
    for schema, key, value, what in SHORTCUTS:
        if normalise(s.gsettings(schema, key)) == normalise(value):  # leave one you changed yourself alone
            p.steps.append(Step(f"Reset: {what}", ["gsettings", "reset", schema, key]))


def remove_smile_shortcut(s: System):
    keep = []
    for path in custom_keybindings(s):
        if "it.mijorus.smile" in (s.gsettings(f"{CUSTOM_KEYS}:{path}", "command") or ""):
            s.run(["gsettings", "reset-recursively", f"{CUSTOM_KEYS}:{path}"])
        else:
            keep.append(path)
    if keep:
        s.run(["gsettings", "set", MEDIA_KEYS, "custom-keybindings", "[" + ", ".join(f"'{x}'" for x in keep) + "]"])
    else:
        s.run(["gsettings", "reset", MEDIA_KEYS, "custom-keybindings"])


def undo_smile_shortcut(s: System, p: Plan):
    p.steps.append(Step("Remove the Copilot key shortcut for Smile", call=lambda: remove_smile_shortcut(s)))


def undo_wsf(s: System, p: Plan):
    p.steps.append(Step("Switch wayland-scroll-factor off", ["wsf", "disable"], early=True,
                        when=lambda: shutil.which("wsf") is not None))
    p.add_remove([x for x in ("wayland-scroll-factor",) if x in s.pacman_installed()], [])
    p.relogin_for.append("switching wayland-scroll-factor off")


def undo_autologin(s: System, p: Plan):
    conf = shlex.quote(str(GDM_CONF))
    backup_path = Path(str(GDM_CONF) + ".zephyrus-setup.bak")
    if backup_path.exists():
        backup = shlex.quote(str(backup_path))
        p.add_root("Put the GDM config back as it was before", f"cp -a {backup} {conf}\nrm -f {backup}")
    else:
        new = set_ini_keys(read_text(GDM_CONF) + "\n", "daemon", {"AutomaticLoginEnable": "False"})
        p.add_root("Turn GDM autologin off", f"cat > {conf} <<'ZEPHYRUS_EOF'\n{new}ZEPHYRUS_EOF")
    p.reboot_for.append("turning autologin off")


def undo_virtio_iso(s: System, p: Plan):
    p.add_root("Delete the VirtIO drivers ISO", "rm -f /var/lib/libvirt/images/virtio-win.iso")


def ufw_forget(*rules: str) -> str:
    """Delete ufw rules again. A rule that is not there is not an error."""
    return "\n".join(f"ufw --force {rule} || true" for rule in rules)


def undo_kvm(s: System, p: Plan):
    p.add_root("Stop libvirt and take your account out of the libvirt group",
               f"systemctl disable --now libvirtd || true\ngpasswd -d {shlex.quote(s.user)} libvirt || true")
    if s.unit_active("ufw.service"):
        p.add_root("Take the VM rules out of ufw again", ufw_forget(
            "delete allow in on virbr0 to any port 53 proto udp", "delete allow in on virbr0 to any port 67 proto udp",
            "route delete allow in on virbr0", "route delete allow out on virbr0"))
    p.relogin_for.append("leaving the libvirt group")


def undo_podman(s: System, p: Plan):
    p.add_root("Remove the Podman settings this script added",
               "rm -f /etc/containers/nodocker /etc/containers/registries.conf.d/99-zephyrus-search.conf")


def undo_localsend(s: System, p: Plan):
    if s.unit_active("ufw.service"):
        p.add_root("Close the LocalSend port in ufw again",
                   ufw_forget("delete allow 53317/tcp", "delete allow 53317/udp"))


def remove_topgrade_conf():
    if TOPGRADE_CONF.exists() and read_text(TOPGRADE_CONF) == TOPGRADE_TEXT.strip():  # one you edited stays
        TOPGRADE_CONF.unlink()


def undo_topgrade(s: System, p: Plan):
    p.steps.append(Step("Remove ~/.config/topgrade.toml if it is still the one this script wrote",
                        call=remove_topgrade_conf))


def undo_yubikey(s: System, p: Plan):
    p.add_root("Stop the smart card daemon", "systemctl disable --now pcscd.socket || true")
    p.add_remove([x for x in ("pam-u2f", "ccid") if x in s.pacman_installed()],
                 [x for x in ("com.yubico.yubioath",) if x in s.flatpaks()])


def yubikey_blocker(s: System) -> str | None:
    wired = [name for name in ("sudo", "polkit-1", "gdm-password")
             if "pam_u2f" in read_text(Path("/etc/pam.d") / name)]
    if wired:
        return ("still referenced in /etc/pam.d/" + ", ".join(wired) + ". Remove those pam_u2f lines first: "
                "taking the module away while they are there can lock you out")
    return None


def undo_git_signing(s: System, p: Plan):
    for key in ("commit.gpgsign", "tag.gpgsign"):
        if git_config(key) == "true":
            p.steps.append(Step(f"Stop signing: unset git {key}", ["git", "config", "--global", "--unset", key]))


UNDO_PLANS: dict[str, Callable[[System, Plan], None]] = {
    "asus-battery-limit": undo_battery_limit, "asus-slash": undo_slash, "asus-ppd-mask": undo_ppd,
    "backlight-fix": undo_backlight, "nvidia-power-services": undo_nvidia_services,
    "display-color-modes": undo_color_modes, "wifi-mt7925": undo_mt7925, "eduroam-saxion": undo_eduroam,
    "gnome-window-buttons": undo_window_buttons, "gnome-focus": undo_focus, "gnome-shortcuts": undo_shortcuts,
    "gnome-smile-shortcut": undo_smile_shortcut, "wsf": undo_wsf, "gdm-autologin": undo_autologin,
    "virtio-iso": undo_virtio_iso, "yubikey": undo_yubikey,
}
UNDO_BLOCKERS: dict[str, Callable[[System], str | None]] = {"yubikey": yubikey_blocker}


# --- the catalogue ----------------------------------------------------------------------------

def build_items() -> list[Item]:
    items: list[Item] = []
    add = items.append
    asus_doc = "hardware/asusctl-rog-control"

    # Hardware & ASUS
    add(package_item("asus-tools", "hardware", "asusctl and ROG Control Center",
                     "The daemon, CLI and GUI behind fan curves, profiles and the Slash LED", asus_doc,
                     pacman=("asusctl", "rog-control-center"), recommended=True, hardware="asus"))
    add(Item("asus-battery-limit", "hardware", "Battery charge limit 80%",
             "Stops charging at 80% to make the battery last longer", asus_doc,
             check_battery_limit, plan_battery_limit, undo="asusctl battery limit 100",
             recommended=True, hardware="asus"))
    add(Item("asus-slash", "hardware", "Slash LED on AC only",
             "Light bar on the lid: off on battery and during sleep", asus_doc, check_slash,
             lambda s, p: p.steps.append(Step("Slash LED: on AC only",
                                              ["asusctl", "slash", "set", "--enable", "-b", "false", "-s", "false"])),
             undo="asusctl slash set --enable -b true -s true", hardware="asus"))
    add(Item("asus-ppd-mask", "hardware", "Let asusd own the power profiles",
             "Masks power-profiles-daemon, which fights asusd over the same interface", asus_doc,
             check_ppd, plan_ppd, undo="sudo systemctl unmask power-profiles-daemon.service",
             recommended=True, hardware="asus"))
    add(package_item("asus-monitoring", "hardware", "Hardware monitoring tools",
                     "nvtop, powertop, s-tui, lm_sensors and i2c-tools", asus_doc,
                     pacman=("nvtop", "powertop", "s-tui", "lm_sensors", "i2c-tools")))
    add(Item("backlight-fix", "hardware", "Brightness in every GPU mode",
             "Without it brightness is dead in Integrated mode (kernel parameter plus modprobe rule)",
             "known-issues", check_backlight, plan_backlight,
             manual=lambda s: BACKLIGHT_MANUAL.get(s.bootloader(), []),
             undo="zephyrus-backlight.py disable", recommended=True, hardware="g16",
             tool="zephyrus-backlight.py"))

    # NVIDIA & GPU
    add(Item("nvidia-power-services", "gpu", "NVIDIA suspend and resume services",
             "Only for a driver that does not save video memory itself: nvidia-open already does, so not there",
             "cachyos/nvidia", check_nvidia_services,
             plan_nvidia_services, undo="sudo systemctl disable " + " ".join((*NVIDIA_UNITS, NVIDIA_SLEEP_UNIT)),
             recommended=True, hardware="nvidia"))
    add(package_item("nvidia-prime", "gpu", "prime-run",
                     "Runs a program on the RTX 4060 instead of the iGPU",
                     "gaming/proton-slr#making-sure-the-rtx-4060-is-doing-the-work",
                     pacman=("nvidia-prime",), recommended=True, hardware="nvidia"))
    add(Item("amdgpu-psr", "gpu", "Disable AMD Panel Self Refresh",
             "Not needed on modern kernels. Only if the system still freezes with an external monitor over "
             "USB-C or Thunderbolt (the bug was mostly on kernels 6.15 to 6.18)",
             "known-issues", check_psr, None, manual=lambda s: PSR_MANUAL.get(s.bootloader(), []),
             advanced=True, hardware="g16"))

    # Display
    add(Item("display-color-modes", "display", "ASUS display color modes",
             "The panel's factory profile plus the three ASUS gamut profiles, for color-managed apps. "
             "They do not change how the desktop looks, unlike G-Helper's switch on Windows",
             "hardware/color-profiles", check_color_modes, plan_color_modes,
             manual=["Pick a mode in Settings > Color Management > Built-in Screen, or run: "
                     "python3 zephyrus-setup.py color set srgb"],
             undo="remove the ASUS profiles in Settings > Color Management and delete ~/.local/share/icc/ASUS_*.icm",
             recommended=True, hardware="g16", picker=pick_color_mode))

    # Networking
    add(Item("wifi-mt7925", "network", "Wi-Fi throughput tuning (MT7925)",
             "No PCIe ASPM, no Wi-Fi power saving, a bigger AQL queue: about double the speed",
             "networking/mt7925-wifi-performance",
             check_mt7925,
             lambda s, p: plan_delegated(s, p, "Apply the Wi-Fi tuning with mt7925-tune.py", "mt7925-tune.py",
                                         "enable", reboot="PCIe ASPM"),
             undo="mt7925-tune.py disable", recommended=True, hardware="mt7925",
             tool="mt7925-tune.py", tool_args=("status",)))
    add(Item("eduroam-saxion", "network", "eduroam at Saxion",
             "Connects to eduroam with the right pinned certificates (Saxion only)",
             "networking/eduroam-network-installation", check_eduroam,
             lambda s, p: plan_delegated(s, p, "Set up eduroam with saxion-eduroam.py", "saxion-eduroam.py"),
             undo="nmcli connection delete eduroam", tool="saxion-eduroam.py"))

    # GNOME desktop
    apps = "applications/"
    add(Item("gnome-window-buttons", "desktop", "Minimize and maximize buttons",
             "GNOME 50 only shows the close button by default",
             apps + "#gnome-window-buttons-adding-minimize--maximize-back",
             lambda s: gsettings_check(s, WM_PREFS, "button-layout", "'appmenu:minimize,maximize,close'",
                                       "minimize, maximize and close are shown"),
             lambda s, p: p.steps.append(gsettings_step(WM_PREFS, "button-layout", "appmenu:minimize,maximize,close",
                                                        "Show minimize and maximize buttons")),
             undo="gsettings reset org.gnome.desktop.wm.preferences button-layout", recommended=True,
             needs_gnome=True))
    add(Item("gnome-focus", "desktop", "New windows come to the front",
             "focus-new-windows 'smart' (also install Just Perfection, see the guide)",
             apps + "#gnome-window-focus-apps-opening-in-the-background",
             lambda s: gsettings_check(s, WM_PREFS, "focus-new-windows", "'smart'", "new windows get focus"),
             lambda s, p: p.steps.append(gsettings_step(WM_PREFS, "focus-new-windows", "smart",
                                                        "Let GNOME bring new windows to the front")),
             manual=["Also turn on 'Window Demands Attention Focus' in the Just Perfection extension "
                     "(Behavior tab): the setting alone is not enough for apps without XDG Activation."],
             undo="gsettings reset org.gnome.desktop.wm.preferences focus-new-windows", recommended=True,
             needs_gnome=True))
    add(Item("gnome-shortcuts", "desktop", "Windows-like shortcuts",
             "Super+D, Shift+Super+S, Shift+Super+R, Super+I and Super+E",
             apps + "#gnome-keyboard-shortcuts-making-it-feel-more-like-windows", check_shortcuts, plan_shortcuts,
             undo="gsettings reset <schema> <key> for each of the five", needs_gnome=True))
    add(Item("gnome-smile-shortcut", "desktop", "Copilot key opens the emoji picker",
             "Uses the Copilot key as a shortcut for Smile", "applications/utilities#smile-emoji-picker",
             check_smile_shortcut, plan_smile_shortcut,
             manual=["If the key does not trigger Smile, set the shortcut yourself: Settings > Keyboard > "
                     "Custom Shortcuts, command 'flatpak run it.mijorus.smile', then press the Copilot key."],
             undo="remove the 'Emoji picker' shortcut in Settings > Keyboard", needs_gnome=True))
    add(package_item("gnome-extension-manager", "desktop", "Extension Manager",
                     "Install GNOME Shell extensions without a browser add-on", "desktop/gnome-extensions",
                     pacman=("extension-manager",), recommended=True, needs_gnome=True))
    add(Item("gnome-extensions", "desktop", "PiP on Top, Astra Monitor, Just Perfection, Smile",
             "The extensions the guide uses (installed by hand from Extension Manager)", "desktop/gnome-extensions",
             check_extensions, None,
             manual=["Open Extension Manager and go to the Browse tab",
                     "Install PiP on Top, Astra Monitor, Just Perfection and Smile complementary extension",
                     "Log out and back in so GNOME Shell loads them"], needs_gnome=True))
    add(package_item("astra-monitor-deps", "desktop", "Astra Monitor extras",
                     "libgtop, amdgpu_top and nethogs for more accurate panel readouts", "desktop/astra-monitor",
                     pacman=("libgtop", "amdgpu_top", "nethogs"), needs_gnome=True, undo_keep=("libgtop",)))
    add(Item("wsf", "desktop", "Touchpad scroll speed",
             "wayland-scroll-factor: GNOME has no setting for it", "desktop/touchpad-scroll-speed", check_wsf,
             plan_wsf, undo="wsf disable", recommended=True, needs_gnome=True,
             aur=("wayland-scroll-factor",)))

    # Security & login
    add(Item("gdm-autologin", "security", "Skip the login screen after the disk unlock",
             "One password at boot (LUKS), then straight to the desktop. The lock screen still asks.",
             "security/autologin", check_autologin, plan_autologin,
             undo="restore /etc/gdm/custom.conf.zephyrus-setup.bak over /etc/gdm/custom.conf", needs_gnome=True))
    add(Item("yubikey", "security", "YubiKey for sudo and the lock screen",
             "pam-u2f, the smart card daemon and Yubico Authenticator", "security/yubikey", check_yubikey,
             plan_yubikey,
             manual=["Register the key: mkdir -p ~/.config/Yubico && pamu2fcfg > ~/.config/Yubico/u2f_keys",
                     "Add 'auth sufficient pam_u2f.so cue' as the first auth line of /etc/pam.d/sudo, "
                     "/etc/pam.d/polkit-1 and /etc/pam.d/gdm-password (the guide has the full files)",
                     "Test sudo in a second terminal before you close the first one"],
             advanced=True))
    add(Item("secure-boot", "security", "Secure Boot with your own keys",
             "sbctl enrolls your keys; the rest happens in the firmware, so it stays manual",
             "cachyos/secure-boot", check_secure_boot, plan_secure_boot,
             manual=["Reboot into the ASUS UEFI (systemctl reboot --firmware-setup) and put Secure Boot in Setup Mode",
                     "sudo sbctl create-keys", "sudo sbctl enroll-keys --microsoft",
                     "Sign the boot files: sbctl-batch-sign for systemd-boot, limine-enroll-config and limine-update "
                     "for Limine",
                     "Enable Secure Boot in the UEFI again, then check with: sudo sbctl status"],
             undo="clear the Secure Boot keys in the UEFI", advanced=True))

    # Development
    dev = apps + "development"
    add(package_item("git-github-cli", "dev", "Git and GitHub CLI", "git plus gh for pull requests and issues",
                     dev + "#git--github-cli", pacman=("git", "github-cli"), recommended=True, extra_check=check_gh,
                     undo_keep=("git",), manual=("Sign in once: gh auth login",)))
    add(package_item("git-gpg-signing", "dev", "Kleopatra and GPG commit signing",
                     "Sign commits and tags with your GPG key", dev + "#kleopatra--gpg-commit-signing",
                     pacman=("kleopatra",), recommended=True, extra_check=check_git_signing,
                     extra_plan=plan_git_signing, extra_undo=undo_git_signing))
    add(package_item("vscode", "dev", "Visual Studio Code (Microsoft build)",
                     "The official binary with the Microsoft marketplace, from the AUR", dev + "#visual-studio-code",
                     aur=("visual-studio-code-bin",), extra_check=check_vscode))
    add(package_item("desktop-plus", "dev", "Desktop Plus", "A GitHub Desktop fork with more features, from the AUR",
                     dev + "#github-desktop", aur=("desktop-plus-bin",)))
    add(package_item("aws-cli", "dev", "AWS CLI v2", "The aws command", dev + "#aws-cli", pacman=("aws-cli-v2",),
                     manual=("Sign in: aws configure sso (or aws configure)",)))
    add(package_item("topgrade", "dev", "Topgrade", "Updates pacman, the AUR, Flatpaks and more in one command",
                     "cachyos/updates", pacman=("topgrade",), extra_check=check_topgrade, extra_plan=plan_topgrade,
                     extra_undo=undo_topgrade))
    add(Item("archi", "dev", "Archi (ArchiMate)", "A portable archive: unpack it to /opt and add a desktop entry",
             dev + "#archi-archimate-modeling-tool",
             lambda s: Check(State.DONE, "found in /opt/Archi") if Path("/opt/Archi").exists()
             else Check(State.TODO, "not in /opt/Archi"), None,
             manual=["Follow the guide: download, move to /opt, symlink, desktop entry"]))

    # Applications
    prod = apps + "productivity"
    util = apps + "utilities"
    add(package_item("brave-origin", "apps", "Brave Origin", "The lighter Brave, from the CachyOS repository",
                     apps + "browser", pacman=("brave-origin-bin",)))
    add(package_item("signal", "apps", "Signal", "Signal Messenger, the native package", prod + "#signal-messenger",
                     pacman=("signal-desktop",)))
    add(package_item("proton-mail", "apps", "Proton Mail", "The desktop app, a native package", prod + "#proton-mail",
                     pacman=("proton-mail-bin",)))
    add(package_item("standard-notes", "apps", "Standard Notes", "End-to-end encrypted notes, from Flathub",
                     prod + "#standard-notes", flatpak=("org.standardnotes.standardnotes",)))
    add(package_item("bitwarden", "apps", "Bitwarden", "Password manager, from Flathub", prod + "#bitwarden",
                     flatpak=("com.bitwarden.desktop",)))
    add(package_item("onlyoffice", "apps", "OnlyOffice", "The closest thing to Microsoft 365", prod + "#onlyoffice",
                     pacman=("onlyoffice-bin",)))
    add(package_item("libreoffice", "apps", "LibreOffice Fresh", "Built-in APA references", prod + "#libreoffice",
                     pacman=("libreoffice-fresh",)))
    add(package_item("smile", "apps", "Smile", "Emoji picker", util + "#smile-emoji-picker",
                     flatpak=("it.mijorus.smile",), needs_gnome=True))
    add(package_item("solaar", "apps", "Solaar", "Manages Logitech keyboards and mice",
                     util + "#solaar-for-logitech-devices", pacman=("solaar",)))
    add(package_item("localsend", "apps", "LocalSend", "Send files between your phone and the laptop",
                     util + "#localsend", pacman=("localsend",), extra_plan=plan_localsend,
                     extra_undo=undo_localsend))
    add(package_item("mission-center", "apps", "Mission Center", "A GNOME-native task manager",
                     util + "#mission-center-gnome-native-task-manager", flatpak=("io.missioncenter.MissionCenter",)))
    add(package_item("high-tide", "apps", "High Tide", "A native GTK4 Tidal client, from Flathub",
                     apps + "gaming-media#tidal", flatpak=("io.github.nokse22.high-tide",)))
    add(package_item("tmog", "apps", "TMOG task manager prerequisites",
                     "fuse2 for the AppImage; the download is manual",
                     util + "#tmog-dave-plummers-task-manager", pacman=("fuse2",),
                     manual=("Download the AppImage from tmog.org, then chmod +x and run it",),
                     undoable=False))
    add(package_item("bottles", "apps", "Bottles", "Windows software through Wine, Flathub only",
                     apps + "gaming-media#bottles-running-windows-software", flatpak=("com.usebottles.bottles",)))

    # Gaming
    add(package_item("steam", "gaming", "Steam", "Steam with Proton included", apps + "gaming-media#steam",
                     pacman=("steam",)))
    add(package_item("gaming-tools", "gaming", "gamescope, MangoHud and GameMode",
                     "The launch options the Proton guide uses", "gaming/proton-slr#launch-options-worth-knowing",
                     pacman=("gamescope", "mangohud", "gamemode", "lib32-gamemode")))
    add(package_item("protonup-qt", "gaming", "ProtonUp-Qt",
                     "Installs Proton-GE for games Valve's builds struggle with",
                     "gaming/proton-slr#proton-ge", flatpak=("net.davidotek.pupgui2",)))

    # Virtualization & containers
    virt = "virtualization/"
    add(package_item("kvm", "virt", "virt-manager and KVM", "A Windows 11 VM with VirtIO and SPICE",
                     virt + "vm-setup", pacman=("virt-manager", "qemu-full", "swtpm", "edk2-ovmf", "dnsmasq"),
                     extra_check=check_kvm, extra_plan=plan_kvm, extra_undo=undo_kvm, undo_keep=("dnsmasq",)))
    add(Item("virtio-iso", "virt", "VirtIO drivers ISO", "The Windows guest drivers, about 753 MB",
             virt + "vm-setup", check_virtio_iso, plan_virtio_iso,
             undo="sudo rm /var/lib/libvirt/images/virtio-win.iso"))
    add(package_item("podman", "virt", "Podman and Podman Desktop", "Rootless containers with a docker-compatible CLI",
                     apps + "development#podman--podman-desktop", pacman=("podman", "podman-docker", "podman-desktop"),
                     extra_check=check_podman, extra_plan=plan_podman, extra_undo=undo_podman))
    add(package_item("distrobox", "virt", "Distrobox", "Another distribution's userspace, integrated with your session",
                     virt + "distrobox", pacman=("distrobox",)))
    add(package_item("quickemu", "virt", "Quickemu", "Throwaway VMs in two commands", virt + "quickemu",
                     pacman=("quickemu",)))
    add(package_item("winboat", "virt", "WinBoat", "Windows apps as windows on your desktop (beta)", virt + "winboat",
                     pacman=("winboat",)))
    add(package_item("vmware", "virt", "VMware Workstation", "Best VM performance; needs DKMS modules and a few fixes",
                     virt + "vmware-workstation", aur=("vmware-workstation",), advanced=True,
                     manual=("Follow the guide for the DKMS modules, networking and the Wayland keyboard fix",)))
    for item in items:
        if item.id in UNDO_PLANS:
            item.undo_plan = UNDO_PLANS[item.id]
        if item.id in UNDO_BLOCKERS:
            item.undo_blocker = UNDO_BLOCKERS[item.id]
    return items


# --- planning and running ----------------------------------------------------------------------

@dataclass
class Row:
    item: Item
    check: Check

    @property
    def open(self) -> bool:
        """Something is left to do, and this script can do it."""
        return self.check.state in (State.TODO, State.PARTIAL) and self.item.plan is not None

    @property
    def undoable(self) -> bool:
        """Something is set up, and this script can put it back."""
        return self.check.state in (State.DONE, State.PARTIAL) and self.item.undo_plan is not None


@dataclass
class Selection:
    """What the user asked for in a list of items."""
    action: str
    ids: list[str] = field(default_factory=list)
    message: str = ""


class Quit(Exception):
    """Raised from a menu to leave the whole program."""


def tags(item: Item, s: System) -> str:
    """Short labels shown after an item's title: where the software comes from and how risky it is."""
    marks = [label for label, wanted in (("AUR", item.needs_aur(s)), ("advanced", item.advanced)) if wanted]
    return f"  ({', '.join(marks)})" if marks else ""


def show_command(argv: list[str]) -> str:
    """A command as it reads best on screen. For display only: it is never run from this text."""
    return " ".join(a if re.fullmatch(r"[\w@%+=:,./-]+", a) else f'"{a}"' for a in argv)


def stream(cmd: list[str]) -> tuple[int, list[str]]:
    """Run a command, print its output as it arrives, and return the exit code and the lines."""
    lines: list[str] = []
    try:
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1) as proc:
            for line in proc.stdout or []:
                print(line, end="", flush=True)
                lines.append(line)
            return proc.wait(), lines
    except OSError as exc:
        print(f"Could not run {cmd[0]}: {exc}", file=sys.stderr)
        return 127, lines


def root_script(plan: Plan) -> str:
    """Everything that needs root for one run, as one script for one pkexec call."""
    lines = ["set -euo pipefail"]
    if plan.pacman:
        lines.append(f"echo {shlex.quote('==> pacman: installing ' + ', '.join(plan.pacman))}")
        lines.append("pacman -S --needed --noconfirm " + " ".join(shlex.quote(p) for p in plan.pacman))
    for desc, snippet in plan.root:
        lines.append(f"echo {shlex.quote('==> ' + desc)}")
        lines.append(snippet)
    if plan.remove_pacman:
        lines.append(f"echo {shlex.quote('==> pacman: removing ' + ', '.join(plan.remove_pacman))}")
        names = " ".join(shlex.quote(name) for name in plan.remove_pacman)
        lines.append(f'for pkg in {names}; do pacman -Rs --noconfirm "$pkg" || echo "kept $pkg: still needed"; done')
    return "\n".join(lines) + "\n"


def parse_selection(text: str, rows: list[Row]) -> Selection:
    """Turn what was typed at the item prompt into a Selection."""
    answer = text.strip().lower()
    if answer in ("", "b"):
        return Selection("back")
    if answer == "q":
        return Selection("quit")
    if answer == "r":
        return Selection("apply", [r.item.id for r in rows if r.open and r.item.recommended and not r.item.advanced])
    if answer == "a":
        return Selection("apply", [r.item.id for r in rows if r.open and not r.item.advanced])
    one = re.fullmatch(r"([?lit])\s*(\d+)", answer)
    if one:
        number = int(one.group(2))
        if not 1 <= number <= len(rows):
            return Selection("error", message=f"There is no item {number}.")
        action = {"?": "learn", "l": "learn", "i": "info", "t": "tool"}[one.group(1)]
        return Selection(action, [rows[number - 1].item.id])
    action = "apply"
    if answer.startswith("u"):
        action, answer = "undo", answer[1:].strip()
    ids: list[str] = []
    for token in re.split(r"[\s,]+", answer):
        span = re.fullmatch(r"(\d+)(?:-(\d+))?", token)
        if not span:
            return Selection("error", message=f"Did not understand '{token or answer}'.")
        first, last = int(span.group(1)), int(span.group(2) or span.group(1))
        if not 1 <= first <= last <= len(rows):
            return Selection("error", message=f"'{token}' is outside 1-{len(rows)}.")
        ids += [rows[n - 1].item.id for n in range(first, last + 1) if rows[n - 1].item.id not in ids]
    return Selection(action, ids)


class App:
    """The catalogue plus everything that reads, plans and applies it."""

    def __init__(self, system: System, silent: bool = False):
        self.s = system
        self.silent = silent
        self.items = build_items()
        self.by_id = {item.id: item for item in self.items}
        self._checks: dict[str, Check] = {}

    # --- reading -------------------------------------------------------------

    def check(self, item: Item) -> Check:
        if item.id not in self._checks:
            self._checks[item.id] = item.status(self.s)
        return self._checks[item.id]

    def reset(self):
        self._checks.clear()
        self.s.refresh()

    def rows(self, section: str | None = None) -> list[Row]:
        return [Row(i, self.check(i)) for i in self.items if section in (None, i.section)]

    def find(self, ident: str) -> Item | None:
        if ident in self.by_id:
            return self.by_id[ident]
        matches = [i for i in self.items if i.id.startswith(ident)]
        return matches[0] if len(matches) == 1 else None

    def section_title(self, section: str) -> str:
        return next((title for key, title, _ in SECTIONS if key == section), section)

    def section_rows(self) -> list[tuple[str, str, str, str]]:
        out = []
        for key, title, about in SECTIONS:
            rows = [r for r in self.rows(key) if r.check.state is not State.NA]
            done = sum(1 for r in rows if r.check.state is State.DONE)
            out.append((key, title, f"{done}/{len(rows)} done", about))
        return out

    def recommended_ids(self) -> list[str]:
        return [r.item.id for r in self.rows() if r.open and r.item.recommended and not r.item.advanced]

    def section_ids(self, section: str) -> list[str]:
        return [r.item.id for r in self.rows(section) if r.open and not r.item.advanced]

    def list_text(self, section: str | None = None, only_open: bool = False, urls: bool = False) -> str:
        s = self.s
        lines = [f"{TITLE}  |  {s.os_name}  |  {s.product or 'unknown machine'}"
                 f"{'  |  ' + s.desktop if s.desktop else ''}",
                 "[x] done  [~] partly done  [ ] to do  [-] not applicable  [?] unknown or manual", ""]
        for key, title, _ in SECTIONS:
            if section not in (None, key):
                continue
            rows = [r for r in self.rows(key) if not only_open or r.check.state in (State.TODO, State.PARTIAL)]
            if not rows:
                continue
            counted = [r for r in self.rows(key) if r.check.state is not State.NA]
            done = sum(1 for r in counted if r.check.state is State.DONE)
            lines.append(f"{title} ({done}/{len(counted)})")
            width = max(len(r.item.id) for r in rows)
            for r in rows:
                lines.append(f"  {r.check.symbol} {r.item.id:<{width}}  {r.item.title}{tags(r.item, s)}")
                if r.check.detail:
                    lines.append(f"      {r.check.detail}")
                if urls:
                    lines.append(f"      {r.item.url}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def describe(self, item: Item) -> str:
        check = self.check(item)
        lines = [f"{item.title}  ({item.id})", "",
                 f"  Status      {SYMBOLS[check.state]} {check.state.value}"
                 + (f": {check.detail}" if check.detail else ""),
                 f"  About       {item.summary}",
                 f"  Learn more  {item.url}"]
        if item.tool:
            lines.append(f"  Own tool    {item.tool}  (zephyrus-setup.py tool {item.id})")
        elif item.picker is not None:
            lines.append("  Own tool    a chooser: open it from the menu with 'Open tool'")
        if item.needs_aur(self.s):
            lines.append("  AUR         only in the AUR, so built from a community script that paru shows for review")
        if item.advanced:
            lines.append("  Advanced    left out of 'recommended' and of whole-section selections")
        reason = item.not_applicable(self.s)
        if check.state is State.DONE:
            lines += ["", "Nothing to do: this is done already."]
        elif item.plan is not None and not reason:
            plan, _ = self.build_plan([item.id])
            lines += ["", "What applying it would do:", *self.render_plan(plan, show_manual=False).splitlines()]
        manual = item.manual_steps(self.s)
        if manual:
            lines += ["", "By hand:", *[f"  {n}. {step}" for n, step in enumerate(manual, 1)]]
        if item.undo_plan is not None and check.state in (State.DONE, State.PARTIAL):
            undo_plan, skipped = self.build_undo_plan([item.id])
            lines += ["", f"What undoing it would do (zephyrus-setup.py undo {item.id}):",
                      *self.render_plan(undo_plan, skipped, show_manual=False).splitlines()]
        elif item.undo and item.undo_plan is None:
            lines += ["", f"To undo it by hand: {item.undo}"]
        return "\n".join(lines) + "\n"

    # --- planning ------------------------------------------------------------

    def build_plan(self, ids: list[str]) -> tuple[Plan, list[str]]:
        plan = Plan()
        skipped: list[str] = []
        for item_id in ids:
            item = self.by_id[item_id]
            reason = item.not_applicable(self.s)
            if reason:
                skipped.append(f"{item.id}: {reason}")
            elif self.check(item).state is State.DONE:
                skipped.append(f"{item.id}: already done")
            elif item.plan is None:
                skipped.append(f"{item.id}: the script cannot do this one for you, "
                               f"see the steps under 'show {item.id}'")
            else:
                item.plan(self.s, plan)
        if plan.flatpak:
            if not self.s.has_cmd("flatpak"):
                plan.add_pacman(["flatpak"])
            if not self.s.has_flathub():
                plan.root.insert(0, ("Add the Flathub remote",
                                     f"flatpak remote-add --if-not-exists flathub {shlex.quote(FLATHUB_REPO)}"))
        if plan.aur and not self.s.has_cmd("paru"):
            plan.add_pacman(["paru"])
        return plan, skipped

    def build_undo_plan(self, ids: list[str]) -> tuple[Plan, list[str]]:
        """What putting the chosen items back would do, and why some cannot be put back."""
        plan = Plan()
        skipped: list[str] = []
        for item_id in ids:
            item = self.by_id[item_id]
            reason = item.not_applicable(self.s)
            if reason:
                skipped.append(f"{item.id}: {reason}")
            elif item.undo_plan is None:
                skipped.append(f"{item.id}: the script cannot undo this one, see 'show {item.id}'")
            elif self.check(item).state not in (State.DONE, State.PARTIAL):
                skipped.append(f"{item.id}: nothing to undo, it is not set up")
            else:
                blocked = item.undo_blocker(self.s) if item.undo_blocker else None
                if blocked:
                    skipped.append(f"{item.id}: {blocked}")
                else:
                    item.undo_plan(self.s, plan)
        return plan, skipped

    def render_plan(self, plan: Plan, skipped: list[str] | None = None, show_manual: bool = True,
                    ids: list[str] | None = None) -> str:
        lines: list[str] = []
        if plan.pacman:
            lines.append("Packages from the repositories (pacman):  " + " ".join(plan.pacman))
        if plan.aur:
            lines.append("Packages from the AUR (paru, you review each PKGBUILD):  " + " ".join(plan.aur))
        if plan.flatpak:
            lines.append("Flatpaks from Flathub:  " + " ".join(plan.flatpak))
        if plan.remove_pacman:
            lines.append("Packages removed (pacman; one that something else still needs is kept):  "
                         + " ".join(plan.remove_pacman))
        if plan.remove_flatpak:
            lines.append("Flatpaks removed:  " + " ".join(plan.remove_flatpak))
        if plan.root:
            lines.append("As root, in the same single pkexec prompt:")
            for desc, snippet in plan.root:
                lines.append(f"  - {desc}")
                lines += [f"      {line}" for line in snippet.splitlines() if line.strip()][:8]
        if plan.steps:
            lines.append("As you:")
            for step in plan.steps:
                shown = show_command(step.argv) if step.argv else ""
                command = f"   $ {shown}" if shown and step.desc != shown else ""
                lines.append(f"  - {step.desc}{command}")
        if not lines:
            lines.append("Nothing to run.")
        if plan.reboot_for:
            lines.append("Needs a reboot to take effect: " + ", ".join(plan.reboot_for))
        if plan.relogin_for:
            lines.append("Needs logging out and back in: " + ", ".join(plan.relogin_for))
        for note in plan.notes:
            lines.append(f"Note: {note}")
        if skipped:
            lines += ["Skipped:", *[f"  - {text}" for text in skipped]]
        if show_manual and ids:
            for item_id in ids:
                item = self.by_id[item_id]
                manual = item.manual_steps(self.s)
                if manual:
                    lines += [f"By hand ({item.title}):", *[f"  {n}. {step}" for n, step in enumerate(manual, 1)]]
        return "\n".join(lines) + "\n"

    def preflight(self, plan: Plan) -> list[str]:
        """Reasons the plan cannot run on this machine, found before anything is changed."""
        problems = []
        if (plan.pacman or plan.root or plan.remove_pacman) and not self.s.has_cmd("pkexec"):
            problems.append("pkexec is not installed, and the root steps need it")
        if plan.aur and not self.s.has_tty:
            problems.append("AUR packages need a terminal: paru shows each PKGBUILD for review. "
                            "Run this from a terminal, or install them with paru yourself")
        if any(step.interactive for step in plan.steps) and not self.s.has_tty:
            problems.append("a dedicated tool in this plan asks questions of its own, so it needs a terminal")
        return problems

    # --- running -------------------------------------------------------------

    def execute(self, plan: Plan) -> list[str]:
        """Run the plan. Returns the failures, empty when everything worked."""
        failures: list[str] = []
        failures += [f for f in (self.run_step(step) for step in plan.steps if step.early) if f]

        if plan.pacman or plan.root or plan.remove_pacman:
            print("==> Steps that need root: one polkit prompt covers all of them")
            code, _ = stream(["pkexec", "bash", "-c", root_script(plan)])
            if code != 0:
                return [f"the root steps failed (exit code {code}); nothing after them was run. If pacman could not "
                        "find a package, refresh the databases first with: sudo pacman -Syu"]

        if plan.aur:
            print("==> AUR packages with paru")
            res = subprocess.run(["paru", "-S", "--needed", "--sudo", "pkexec", "--nosudoloop", *plan.aur])
            if res.returncode != 0:
                failures.append(f"paru exited with code {res.returncode} for: {' '.join(plan.aur)}")

        if plan.flatpak:
            print("==> Flatpaks from Flathub")
            res = subprocess.run(["flatpak", "install", "-y", "flathub", *plan.flatpak])
            if res.returncode != 0:
                failures.append(f"flatpak exited with code {res.returncode} for: {' '.join(plan.flatpak)}")

        if plan.remove_flatpak:
            print("==> Removing Flatpaks")
            res = subprocess.run(["flatpak", "uninstall", "-y", *plan.remove_flatpak])
            if res.returncode != 0:
                failures.append(f"flatpak exited with code {res.returncode} for: {' '.join(plan.remove_flatpak)}")

        failures += [f for f in (self.run_step(step) for step in plan.steps if not step.early) if f]
        return failures

    @staticmethod
    def run_step(step: Step) -> str | None:
        """Run one step as the user. Returns what went wrong, or None."""
        if step.when is not None and not step.when():
            print(f"-- already in place, skipped: {step.desc}")
            return None
        print(f"==> {step.desc}")
        try:
            if step.call is not None:
                step.call()
            elif step.argv:
                res = subprocess.run(step.argv)
                if res.returncode != 0:
                    raise RuntimeError(f"{step.argv[0]} exited with code {res.returncode}")
        except (RuntimeError, OSError) as exc:
            print(f"[FAIL] {exc}", file=sys.stderr)
            return f"{step.desc}: {exc}"
        return None

    def apply_flow(self, ids: list[str], ui: TerminalUi | ZenityUi, assume_yes: bool = False,
                   dry_run: bool = False, undo: bool = False) -> bool:
        """Plan, show, confirm and run, or with undo put things back. True when nothing failed or was cancelled."""
        if not ids:
            print("Nothing to undo: nothing chosen is set up." if undo else
                  "Nothing to apply: everything chosen is done already, or cannot be done by this script.")
            return True
        if not self.s.is_arch:
            ui.message(f"Applying is built for CachyOS and other Arch-based systems. This is {self.s.os_name}, "
                       "so 'list', 'show' and 'learn' work and 'apply' does not. The guides describe the steps.")
            return False
        plan, skipped = self.build_undo_plan(ids) if undo else self.build_plan(ids)
        text = self.render_plan(plan, skipped, show_manual=not undo, ids=ids)
        if undo:
            text = "UNDO: this puts things back to the stock state. Settings you changed yourself go to the " \
                   "default, not to your value.\n\n" + text
        if dry_run:
            print(text)
            return True
        problems = self.preflight(plan)
        if problems:
            ui.message("Cannot run this plan:\n- " + "\n- ".join(problems))
            return False
        if plan.empty:
            ui.message(text)
            return True
        if not assume_yes and not ui.confirm_plan(text):
            print("Cancelled, nothing was changed.")
            return False
        failures = self.execute(plan)
        self.reset()
        report = ["Results:"]
        for item_id in ids:
            result = self.check(self.by_id[item_id])
            report.append(f"  {SYMBOLS[result.state]} {item_id}: {result.detail}")
        if plan.reboot_for:
            report.append("Reboot to finish: " + ", ".join(plan.reboot_for))
        if plan.relogin_for:
            report.append("Log out and back in to finish: " + ", ".join(plan.relogin_for))
        if failures:
            report += ["", "Something went wrong:", *[f"  - {f}" for f in failures]]
        ui.report("\n".join(report))
        return not failures

    def learn(self, item: Item, open_browser: bool = True):
        print(f"{item.title}: {item.url}")
        if open_browser and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            webbrowser.open(item.url)

    def open_tool(self, item: Item, ui: TerminalUi | ZenityUi):
        if item.picker is not None:
            item.picker(self, ui)
            return
        if not item.tool:
            ui.message(f"{item.title} has no dedicated tool. Use 'show {item.id}' for what it does.")
            return
        try:
            run_tool(self.s, item.tool, list(item.tool_args))
        except RuntimeError as exc:
            ui.message(f"{item.tool}: {exc}")
        self.reset()

    # --- the menu --------------------------------------------------------------

    def interactive(self, ui: TerminalUi | ZenityUi):
        try:
            while True:
                action, value = ui.pick_section(self.section_rows())
                if action == "quit":
                    return
                if action == "recommended":
                    self.apply_flow(self.recommended_ids(), ui)
                    ui.pause()
                elif action == "section":
                    self.section_loop(value, ui)
        except Quit:
            return

    def section_loop(self, section: str, ui: TerminalUi | ZenityUi):
        while True:
            rows = self.rows(section)
            choice = ui.pick_items(self.section_title(section), rows)
            if choice.action == "back":
                return
            if choice.action == "quit":
                raise Quit
            if choice.action == "error":
                ui.message(choice.message)
            elif choice.action == "apply":
                self.apply_flow(choice.ids, ui)
                ui.pause()
            elif choice.action == "undo":
                self.apply_flow(choice.ids, ui, undo=True)
                ui.pause()
            elif choice.action == "learn":
                self.learn(self.by_id[choice.ids[0]])
            elif choice.action == "info":
                ui.show_text(self.describe(self.by_id[choice.ids[0]]))
            elif choice.action == "tool":
                self.open_tool(self.by_id[choice.ids[0]], ui)


# --- terminal menu ---------------------------------------------------------------------------------

class TerminalUi:
    def __init__(self, app: App):
        self.app = app

    @staticmethod
    def ask(prompt: str) -> str:
        try:
            return input(prompt)
        except EOFError:
            raise Quit from None

    def message(self, text: str):
        print(f"\n{text}\n")

    def choose(self, title: str, text: str, options: list[tuple[str, str]]) -> str | None:
        """One of the options by its key, or None when cancelled."""
        print(f"\n{color('1', title)}\n{text}\n")
        for number, (_, label) in enumerate(options, 1):
            print(f"  {number}. {label}")
        answer = self.ask("\nPick one, or press Enter to cancel: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1][0]
        return None

    def show_text(self, text: str):
        print(f"\n{text}")

    def report(self, text: str):
        print(f"\n{text}")

    def pause(self):
        if sys.stdin.isatty():
            self.ask("\nPress Enter to go on. ")

    def confirm_plan(self, text: str) -> bool:
        print(f"\nThis is what will happen:\n\n{text}")
        return self.ask("Run this? [y/N] ").strip().lower() in ("y", "yes")

    def pick_section(self, rows: list[tuple[str, str, str, str]]) -> tuple[str, str]:
        s = self.app.s
        print(f"\n{color('1', TITLE)}  |  {s.os_name}  |  {s.product or 'unknown machine'}\n")
        for number, (_, title, done, about) in enumerate(rows, 1):
            print(f"  {number:>2}. {title:<28} {done:>9}   {about}")
        print("\n   r. apply everything recommended      q. quit")
        answer = self.ask("\nPick a section: ").strip().lower()
        if answer in ("q", ""):
            return "quit", ""
        if answer == "r":
            return "recommended", ""
        if answer.isdigit() and 1 <= int(answer) <= len(rows):
            return "section", rows[int(answer) - 1][0]
        print(f"Pick a number between 1 and {len(rows)}.")
        return "none", ""

    def pick_items(self, title: str, rows: list[Row]) -> Selection:
        print(f"\n{color('1', title)}\n")
        width = max(len(r.item.id) for r in rows)
        for number, row in enumerate(rows, 1):
            label = row.item.title + tags(row.item, self.app.s)
            print(f"  {number:>2}. {row.check.symbol} {row.item.id:<{width}}  {label}")
            detail = f"{row.item.summary}  [{row.check.detail}]" if row.check.detail else row.item.summary
            print(f"        {detail}")
        print("\n  numbers apply (2 4-6)   r recommended   a all open   u2 undo (u 2 4-6)   ?N learn more   "
              "iN details   tN open its tool   b back")
        return parse_selection(self.ask("\nYour choice: "), rows)


# --- dialogs ---------------------------------------------------------------------------------------

def gui_available() -> bool:
    """Dialogs are used when there is a desktop session and zenity is installed."""
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")) and shutil.which("zenity") is not None


class ZenityUi:
    def __init__(self, app: App):
        self.app = app

    @staticmethod
    def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, capture_output=True, text=True)

    def message(self, text: str):
        self.run(["zenity", "--info", "--no-markup", "--width=560", f"--title={TITLE}", f"--text={text}"])

    def choose(self, title: str, text: str, options: list[tuple[str, str]]) -> str | None:
        cells = [cell for option in options for cell in option]
        res = self.run(["zenity", "--list", f"--title={TITLE}: {title}", f"--text={text}", "--width=520",
                        "--height=380", "--column=ID", "--column=Mode", "--hide-column=1", "--print-column=1",
                        "--ok-label=Use this", "--cancel-label=Cancel", *cells])
        out = res.stdout.strip().rstrip("|")
        return out if res.returncode == 0 and out else None

    def pause(self):
        """Dialogs wait for you already."""

    def show_text(self, text: str):
        self._text_dialog(text, ok="Close", cancel=None)

    def report(self, text: str):
        print(f"\n{text}")
        self._text_dialog(text, ok="Close", cancel=None)

    def confirm_plan(self, text: str) -> bool:
        return self._text_dialog("This is what will happen:\n\n" + text, ok="Run", cancel="Cancel")

    def _text_dialog(self, text: str, ok: str, cancel: str | None) -> bool:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
            handle.write(text)
            path = handle.name
        try:
            cmd = ["zenity", "--text-info", f"--title={TITLE}", f"--filename={path}", "--font=monospace",
                   "--width=900", "--height=640", f"--ok-label={ok}"]
            if cancel:
                cmd.append(f"--cancel-label={cancel}")
            return self.run(cmd).returncode == 0
        finally:
            os.unlink(path)

    def pick_section(self, rows: list[tuple[str, str, str, str]]) -> tuple[str, str]:
        s = self.app.s
        cells = [cell for row in rows for cell in row]
        heading = f"{s.os_name}  |  {s.product or 'unknown machine'}"
        res = self.run(["zenity", "--list", f"--title={TITLE}", f"--text={heading}",
                        "--width=820", "--height=520", "--column=ID", "--column=Section", "--column=Done",
                        "--column=About", "--hide-column=1", "--print-column=1", "--ok-label=Open",
                        "--cancel-label=Quit", "--extra-button=Apply everything recommended", *cells])
        out = res.stdout.strip().rstrip("|")
        if out == "Apply everything recommended":
            return "recommended", ""
        if res.returncode == 0 and out:
            return "section", out
        return "quit", ""

    def _pick_one(self, rows: list[Row], question: str) -> str | None:
        cells = [cell for r in rows for cell in (r.item.id, r.item.title, r.check.state.value)]
        res = self.run(["zenity", "--list", f"--title={TITLE}", f"--text={question}", "--width=700",
                        "--height=520", "--column=ID", "--column=Item", "--column=Status", "--hide-column=1",
                        "--print-column=1", *cells])
        out = res.stdout.strip().rstrip("|")
        return out if res.returncode == 0 and out else None

    def _pick_many(self, rows: list[Row], question: str, ok: str) -> list[str]:
        cells = [cell for r in rows for cell in ("FALSE", r.item.id, r.item.title, r.check.state.value)]
        res = self.run(["zenity", "--list", "--checklist", f"--title={TITLE}", f"--text={question}", "--width=760",
                        "--height=520", "--column=Pick", "--column=ID", "--column=Item", "--column=Status",
                        "--hide-column=2", "--print-column=2", "--separator=,", f"--ok-label={ok}",
                        "--cancel-label=Cancel", *cells])
        out = res.stdout.strip()
        return [i for i in out.split(",") if i] if res.returncode == 0 else []

    def pick_items(self, title: str, rows: list[Row]) -> Selection:
        cells = []
        for r in rows:
            checked = "TRUE" if r.open and r.item.recommended and not r.item.advanced else "FALSE"
            cells += [checked, r.item.id, r.item.title + tags(r.item, self.app.s), r.check.state.value, r.item.summary]
        res = self.run(["zenity", "--list", "--checklist", f"--title={TITLE}: {title}",
                        "--text=Tick what to set up. Apply shows the plan first and changes nothing until you confirm.",
                        "--width=1100", "--height=680", "--column=Apply", "--column=ID", "--column=Item",
                        "--column=Status", "--column=What it does", "--hide-column=2", "--print-column=2",
                        "--separator=,", "--ok-label=Apply selected", "--cancel-label=Back",
                        "--extra-button=Learn more", "--extra-button=Open tool", "--extra-button=Details",
                        "--extra-button=Undo", *cells])
        out = res.stdout.strip()
        if out == "Undo":
            pool = [r for r in rows if r.undoable]
            if not pool:
                return Selection("error", message="Nothing in this section is set up in a way the script can undo.")
            chosen = self._pick_many(pool, "Tick what to put back. The plan is shown before anything changes.",
                                     "Undo selected")
            return Selection("undo", chosen) if chosen else Selection("none")
        extras = {"Learn more": ("learn", "Learn more about which item?"),
                  "Open tool": ("tool", "Open the dedicated tool of which item?"),
                  "Details": ("info", "Show the details of which item?")}
        if out in extras:
            action, question = extras[out]
            pool = [r for r in rows if r.item.has_tool] if action == "tool" else rows
            if not pool:
                return Selection("error", message="None of the items here has a dedicated tool.")
            chosen = self._pick_one(pool, question)
            return Selection(action, [chosen]) if chosen else Selection("none")
        if res.returncode == 0:
            ids = [i for i in out.split(",") if i]
            return Selection("apply", ids) if ids else Selection("error", message="Nothing is ticked.")
        return Selection("back")


# --- command line ------------------------------------------------------------------------------------

def ask_yes_no(question: str) -> bool:
    try:
        return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def resolve(app: App, ident: str) -> Item:
    """The item an id on the command line means: exact, or a unique start of one. Exits with a message otherwise."""
    if ident in app.by_id:
        return app.by_id[ident]
    matches = [i for i in app.items if i.id.startswith(ident)]
    if len(matches) == 1:
        return matches[0]
    if matches:
        print(f"'{ident}' could mean: " + ", ".join(m.id for m in matches), file=sys.stderr)
    else:
        print(f"Unknown item '{ident}'. 'list' shows them all.", file=sys.stderr)
    sys.exit(2)


def selected_ids(app: App, args: argparse.Namespace) -> list[str]:
    ids: list[str] = []
    for ident in args.ids:
        ids.append(resolve(app, ident).id)
    if args.recommended:
        ids += app.recommended_ids()
    for section in args.section or []:
        if section not in {key for key, _, _ in SECTIONS}:
            print(f"Unknown section '{section}'. Sections: " + ", ".join(key for key, _, _ in SECTIONS),
                  file=sys.stderr)
            sys.exit(2)
        ids += app.section_ids(section)
    return list(dict.fromkeys(ids))


def main():
    if sys.version_info < MIN_PYTHON:
        need = ".".join(str(n) for n in MIN_PYTHON)
        have = ".".join(str(n) for n in sys.version_info[:3])
        print(f"This script needs Python {need} or newer; this is {have}.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        prog="zephyrus-setup.py",
        description="Set up an ASUS ROG Zephyrus G16 the way the Zephyrus-Linux guides describe it. "
                    "Without a command it opens a menu.")
    parser.add_argument("--terminal", action="store_true", help="Use the terminal menu even when zenity is installed.")
    parser.add_argument("--silent", action="store_true",
                        help="No dialogs and no questions, terminal output only. 'apply' then needs --yes.")
    parser.add_argument("--ref", default=DEFAULT_REF,
                        help=f"Branch, tag or commit to fetch the dedicated scripts and color profiles from "
                             f"(default: {DEFAULT_REF}).")
    parser.add_argument("--trust-local", action="store_true",
                        help="Run a dedicated script next to this one even when its SHA-256 differs from the "
                             "guide. For working on the scripts themselves.")
    commands = parser.add_subparsers(dest="command")

    commands.add_parser("menu", help="Open the menu (the default).")
    listing = commands.add_parser("list", help="Show every item and where it stands.")
    listing.add_argument("--section", help="Only this section (see the section names in the menu).")
    listing.add_argument("--todo", action="store_true", help="Only items that are not done yet.")
    listing.add_argument("--urls", action="store_true", help="Also print each item's guide link.")
    show = commands.add_parser("show", help="One item in detail: status, plan, manual steps, undo, link.")
    show.add_argument("id")
    learn = commands.add_parser("learn", help="Print the guide link of an item and open it in the browser.")
    learn.add_argument("id")
    learn.add_argument("--no-open", action="store_true", help="Only print the link.")
    tool = commands.add_parser("tool", help="Run a dedicated script (an item id or a script name), downloaded and "
                                            "checked against the SHA-256 in the guide when it is not here.")
    tool.add_argument("name")
    tool.add_argument("args", nargs=argparse.REMAINDER, help="Passed on to the script.")
    color_cmd = commands.add_parser("color", help="Show or switch the ASUS color mode of the built-in screen.")
    color_cmd.add_argument("action", nargs="?", choices=["list", "set"], default="list")
    color_cmd.add_argument("mode", nargs="?", help="native, srgb, dcip3 or displayp3 (with 'set').")
    undo_cmd = commands.add_parser("undo", help="Plan, confirm and put items back as they were.")
    undo_cmd.add_argument("ids", nargs="+", help="Item ids (a unique start of an id is enough).")
    undo_cmd.add_argument("--dry-run", action="store_true", help="Show the plan and stop.")
    undo_cmd.add_argument("--yes", action="store_true", help="Do not ask for confirmation.")
    apply = commands.add_parser("apply", help="Plan, confirm and apply items.")
    apply.add_argument("ids", nargs="*", help="Item ids (a unique start of an id is enough).")
    apply.add_argument("--recommended", action="store_true", help="Everything recommended that is not done yet.")
    apply.add_argument("--section", action="append", help="Every open, non-advanced item of a section.")
    apply.add_argument("--dry-run", action="store_true", help="Show the plan and stop.")
    apply.add_argument("--yes", action="store_true", help="Do not ask for confirmation.")
    args = parser.parse_args()

    if os.geteuid() == 0:
        print("Run this as your normal user. It asks for root through pkexec when it needs it.", file=sys.stderr)
        sys.exit(1)

    app = App(System(ref=args.ref, trust_local=args.trust_local), silent=args.silent)
    command = args.command or "menu"

    try:
        if command == "list":
            if args.section and args.section not in {key for key, _, _ in SECTIONS}:
                print("Unknown section. Sections: " + ", ".join(key for key, _, _ in SECTIONS), file=sys.stderr)
                sys.exit(2)
            print(app.list_text(args.section, args.todo, args.urls), end="")
        elif command == "show":
            print(app.describe(resolve(app, args.id)), end="")
        elif command == "learn":
            app.learn(resolve(app, args.id), open_browser=not (args.no_open or args.silent))
        elif command == "tool":
            item = app.by_id.get(args.name) or next((i for i in app.items if i.tool == args.name), None)
            if item is None and args.name not in TOOLS:
                item = resolve(app, args.name)
            name = item.tool if item and item.tool else args.name
            if name not in TOOLS:
                print(f"'{args.name}' has no dedicated script. The scripts are: " + ", ".join(TOOLS),
                      file=sys.stderr)
                sys.exit(2)
            extra = args.args[1:] if args.args[:1] == ["--"] else args.args
            try:
                run_tool(app.s, name, extra or (list(item.tool_args) if item else []))
            except RuntimeError as exc:
                print(f"[ERROR] {exc}", file=sys.stderr)
                sys.exit(1)
        elif command == "color":
            state = color_mode_state(app.s)
            if args.action == "set":
                if args.mode not in [row[0] for row in state]:
                    parser.error("color set needs one of: " + ", ".join(row[0] for row in state))
                try:
                    set_color_mode(app.s, args.mode)
                except RuntimeError as exc:
                    print(f"[ERROR] {exc}", file=sys.stderr)
                    sys.exit(1)
                print(f"Switched to {args.mode}.")
            elif not any(row[3] for row in state):
                print("The ASUS color modes are not on the display yet. Run: zephyrus-setup.py apply "
                      "display-color-modes")
            else:
                for key, title, _, on_display, active in state:
                    print(f"  {'*' if active else ' '} {key:<10} {title}{'' if on_display else '  (not added yet)'}")
        elif command == "undo":
            if args.silent and not (args.yes or args.dry_run):
                parser.error("--silent does not ask questions, so 'undo' needs --yes (or --dry-run)")
            ids = list(dict.fromkeys(resolve(app, ident).id for ident in args.ids))
            ok = app.apply_flow(ids, TerminalUi(app), assume_yes=args.yes, dry_run=args.dry_run, undo=True)
            sys.exit(0 if ok else 1)
        elif command == "apply":
            ids = selected_ids(app, args)
            if not ids:
                parser.error("nothing selected: give item ids, --recommended or --section")
            if args.silent and not (args.yes or args.dry_run):
                parser.error("--silent does not ask questions, so 'apply' needs --yes (or --dry-run)")
            ui = TerminalUi(app)
            ok = app.apply_flow(ids, ui, assume_yes=args.yes, dry_run=args.dry_run)
            sys.exit(0 if ok else 1)
        else:
            if args.silent:
                parser.error("--silent needs a command; the menu asks questions")
            ui = ZenityUi(app) if gui_available() and not args.terminal else TerminalUi(app)
            app.interactive(ui)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
