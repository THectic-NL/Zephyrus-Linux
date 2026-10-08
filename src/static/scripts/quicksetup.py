#!/usr/bin/env python3
"""
Zephyrus Setup
--------------
A checklist for setting up Linux the way the guides at
https://zephyrus-linux.thectic.nl describe it. Tick what you want, untick what
you don't, read the plan, apply it.

    python3 quicksetup.py

That is all of it: no commands, no options.

It needs Python 3.14 and, for the window, PyGObject with GTK 4 and libadwaita:

    sudo pacman -S python-gobject gtk4 libadwaita

Changes are made on Arch-based systems (it is built on CachyOS). Anywhere else
the window opens read-only: you see what is set up and can open the guides.

Everything that needs root runs as one script behind one polkit prompt. This
script never edits the bootloader or the Secure Boot keys, because a mistake in
either can stop the machine from booting: the AMD PSR fix and Secure Boot are
guides, not toggles. The PAM files are the exception, only for the YubiKey: it
adds one 'sufficient' line, keeps a backup, checks the result and puts the old
file back when the check fails. The brightness fix runs its own script, which
keeps a backup of what it changes.

Author: Stensel8
One file, standard library plus PyGObject, like the dedicated scripts next to it.
"""

from __future__ import annotations
import difflib
import enum
import getpass
import hashlib
import io
import json
import logging
import logging.handlers
import os
import re
import shlex
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

# The window needs these. Everything else in this file works without them, so a missing toolkit becomes a
# message with the command that fixes it instead of a traceback.
try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango
    TOOLKIT_ERROR = ""
except (ImportError, ValueError) as _toolkit_error:
    Adw = Gdk = Gio = GLib = Gtk = Pango = None
    TOOLKIT_ERROR = str(_toolkit_error)

# Support policy, not a technical floor: pinned to the current stable release
# so nobody runs this on an already-unsupported interpreter.
MIN_PYTHON = (3, 14)
# AdwDialog and AdwAlertDialog arrived in libadwaita 1.5.
MIN_ADW = (1, 5)

TITLE = "Zephyrus Setup"
APP_ID = "nl.thectic.ZephyrusSetup"
SITE = "https://zephyrus-linux.thectic.nl"
SCRIPT_DIR = Path(__file__).resolve().parent
SUPPORTED_BOARD = "GA605WV"
DMI_DIR = Path("/sys/class/dmi/id")
FLATHUB_REPO = "https://dl.flathub.org/repo/flathub.flatpakrepo"

# Where the dedicated scripts and the color profiles come from when they are not
# sitting next to this one (a checkout of the repository has them).
REPO = "THectic-NL/Zephyrus-Linux"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main"
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "zephyrus-setup"
LOG_DIR = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state") / "zephyrus-setup"
LOG_FILE = LOG_DIR / "setup.log"

# The SHA-256 of every file this script fetches or copies. A file that does not
# match is never used, whether it came from next to this script or from GitHub.
# .github/scripts/check-doc-checksums.sh --apply rewrites these lines when the
# files change, so edit the files, not the numbers.
TOOL_SHA256 = {
    "zephyrus-backlight.py": "47999987b8dba31fed6f8931a3ef50d23ed0e8dad32dbb890a40c2f5f92c087f",
    "mt7925-tune.py": "cf5aa114d872c6480525b55f637fab346337f9cbbdce9657e0688fd48cac1247",
    "saxion-eduroam.py": "c037f0fc7e282b8e9126e7646d87b5b50069d69e60053d22d4792c88b5bb89a8",
}
PROFILE_SHA256 = {
    "ASUS_sRGB.icm": "5ce1af74f5345876385cc56f98b363c3cd91f73ea2c5176fffab3f61ed7cc428",
    "GA605WV_1002_104D158E_CMDEF.icm": "c0efca6aab2734b940dc660ff9e09aaf5478808789488e352891b801d4868474",
    "GA605WV_1002_834C41AE_CMDEF.icm": "89626535ed7a1a9b8739e34c9ab0d8ae1aa9354daa9626e58a895266f5da2519",
    "GA605WV_1002_E5090C19_CMDEF.icm": "5c1c60a4020c1fab8b7cb8eeb1d9d33987e2ea6b67b67736fd6080dbcfd69427",
    "GA605WV_10DE_104D158E_CMDEF.icm": "9db806ad90c95813095085aec184592c6017c17bfedf894851f5857a970e6bd7",
    "GA605WV_10DE_834C41AE_CMDEF.icm": "04ea034c858a982560602a9c2c2ef2d30e222700cc978143e5c0b9e93b1a47ef",
    "GA605WV_10DE_E5090C19_CMDEF.icm": "acb0c403677c275247d4700835ca3437d5e64d189a956695367b8f6d4a4480c9",
}

# Packages that are never removed by an untick, whatever an item says. They are
# either shared with the rest of the system or what this window runs on.
PROTECTED_PACKAGES = frozenset({
    "base", "linux", "linux-firmware", "pacman", "systemd", "glibc", "bash", "sudo", "polkit", "pkexec",
    "python", "python-gobject", "gtk4", "libadwaita", "gnome-shell", "gdm", "mutter", "networkmanager",
    "flatpak", "paru", "git", "libgtop", "dnsmasq", "colord",
})

log = logging.getLogger("zephyrus-setup")


# --- logging and errors --------------------------------------------------------------

def setup_logging() -> Path | None:
    """Log to a file in the state folder. Returns its path, or None when it cannot be written."""
    log.setLevel(logging.DEBUG)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=512_000, backupCount=2, encoding="utf-8")
        os.chmod(LOG_FILE, 0o600)
    except OSError:
        log.addHandler(logging.NullHandler())
        return None
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s"))
    log.addHandler(handler)
    return LOG_FILE


class SetupError(Exception):
    """Something went wrong that the person using this can be told about in one sentence."""


# --- small helpers ---------------------------------------------------------------------

def read_text(path: Path, raw: bool = False) -> str:
    """The file's text (as it is on disk with raw), or an empty string when it is missing or unreadable."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text if raw else text.strip()


def doc_url(spec: str) -> str:
    """'hardware/asusctl-rog-control#anchor' -> the full URL on the guide site."""
    page, _, anchor = spec.partition("#")
    page = page.strip("/")
    url = f"{SITE}/docs/{page}/" if page else f"{SITE}/docs/"
    return f"{url}#{anchor}" if anchor else url


def shell_word(word: str) -> str:
    """One word the way it is written in a shell. Double quotes when single quotes are in it, which reads far better."""
    if "'" in word and not re.search(r'["$`\\!]', word):
        return f'"{word}"'
    return shlex.quote(word)


def shell_line(argv: Iterable[str]) -> str:
    """A command as a line of shell: pasted into a shell it passes exactly these arguments."""
    return " ".join(shell_word(word) for word in argv)


def file_diff(path: Path, old: str, new: str, to: Path | None = None) -> str:
    """The change to a text file as a unified diff, the way 'diff -u' would print it. 'to' is a different new path."""
    return "\n".join(difflib.unified_diff(old.splitlines(), new.splitlines(), str(path), str(to or path), lineterm=""))


def reference_url(section: str, item_id: str) -> str:
    """Where the reference on the site lists one item: a page per section of the window, an anchor per item."""
    return f"{SITE}/docs/setup-script/reference/{section}/#{item_id}"


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def valid_username(name: str) -> bool:
    """A login name that is safe to put in a root script. POSIX portable names, nothing fancier."""
    return re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", name) is not None


# Parsing English output needs English output. LANGUAGE would still win over LC_ALL=C.UTF-8, so go all the way.
C_ENV = {**{k: v for k, v in os.environ.items() if k not in ("LANGUAGE", "LC_ALL", "LANG")}, "LC_ALL": "C"}


@dataclass(frozen=True)
class Result:
    code: int
    out: str = ""
    err: str = ""

    @property
    def ok(self) -> bool:
        return self.code == 0

    @property
    def text(self) -> str:
        """Whatever the command said, for a message. colormgr and a few others print their complaints on stdout."""
        return self.err.strip() or self.out.strip()


def run(cmd: list[str], timeout: float = 20, stdin_text: str | None = None) -> Result:
    """Run a command and never raise. A missing command is exit code 127, a timeout 124."""
    log.debug("run: %s", shlex.join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout, env=C_ENV,
                              input=stdin_text, stdin=None if stdin_text is not None else subprocess.DEVNULL)
    except FileNotFoundError:
        return Result(127, "", f"{cmd[0]} is not installed")
    except subprocess.TimeoutExpired:
        return Result(124, "", f"{cmd[0]} did not answer within {timeout:g} seconds")
    except OSError as exc:
        return Result(126, "", f"could not run {cmd[0]}: {exc}")
    return Result(proc.returncode, proc.stdout, proc.stderr)


def stream(cmd: list[str], on_line: Callable[[str], None]) -> int:
    """Run a command, hand its output to on_line as it arrives, and return the exit code."""
    log.info("stream: %s", shlex.join(cmd))
    try:
        # The script needs Python 3.14, so the warning that errors= only exists on Python 3.6+ cannot apply.
        # nosemgrep: python.lang.compatibility.python36.python36-compatibility-Popen1
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                              text=True, errors="replace", bufsize=1) as proc:
            for line in proc.stdout or []:
                on_line(line.rstrip("\n"))
            return proc.wait()
    except OSError as exc:
        on_line(f"Could not run {cmd[0]}: {exc}")
        return 127


# curl exit codes of a connection that broke, which another try usually fixes: DNS, connect, timeout, TLS, send, read
TRANSIENT_CURL_CODES = frozenset({6, 7, 18, 28, 35, 52, 55, 56})


def curl_bytes(url: str, limit: int = 300_000_000) -> bytes:
    """A file over HTTPS, via curl, with two more tries when the connection breaks. Raises SetupError."""
    if not url.startswith("https://"):
        raise SetupError(f"refusing to download {url}: only https is allowed")
    log.info("download: %s", url)
    why = ""
    for attempt in (1, 2, 3):
        try:
            res = subprocess.run(["curl", "-fsSL", "--proto", "=https", "--proto-redir", "=https", "--max-time", "600",
                                  "--max-filesize", str(limit), url],
                                 capture_output=True, stdin=subprocess.DEVNULL, env=C_ENV)
        except FileNotFoundError:
            raise SetupError("curl is not installed, and downloads need it") from None
        except OSError as exc:
            raise SetupError(f"could not run curl: {exc}") from None
        if res.returncode == 0:
            return res.stdout
        why = res.stderr.decode("utf-8", errors="replace").strip() or f"curl exited with {res.returncode}"
        if res.returncode not in TRANSIENT_CURL_CODES or attempt == 3:
            break
        log.warning("download of %s broke (%s), trying again", url, why)
        time.sleep(2 * attempt)
    raise SetupError(f"could not download {url}: {why}")


# --- EDID, ICC profiles and gamut -----------------------------------------------------

@dataclass(frozen=True)
class Edid:
    pnp: str                   # the three-letter maker code, e.g. SHP
    maker: str                 # the same two bytes the way ASUS writes them in file names, e.g. 104D
    product: str               # the product code, e.g. 158E
    name: str                  # the monitor name from its descriptors, empty when it has none
    # red x/y, green x/y, blue x/y, white x/y in CIE 1931, or None when the panel does not report them
    primaries: tuple[float, float, float, float, float, float, float, float] | None
    gamma: float | None

    @property
    def panel_id(self) -> str:
        return self.maker + self.product


def parse_edid(data: bytes) -> Edid | None:
    """The identity and the primaries of a display from its EDID, or None when this is not an EDID."""
    if len(data) < 128 or data[:8] != bytes.fromhex("00ffffffffffff00"):
        return None
    code = (data[8] << 8) | data[9]
    pnp = "".join(chr(((code >> shift) & 31) + 64) for shift in (10, 5, 0))
    # ASUS names a panel by these bytes read little-endian: 'SHP' and 0x158E become 104D158E.
    maker = f"{int.from_bytes(data[8:10], 'little'):04X}"
    product = f"{int.from_bytes(data[10:12], 'little'):04X}"
    name = ""
    for start in (54, 72, 90, 108):
        block = data[start:start + 18]
        if block[:3] == b"\0\0\0" and block[3] == 0xFC:
            name = block[5:].split(b"\n")[0].decode("ascii", errors="replace").strip()
            break
    low1, low2 = data[25], data[26]

    def ten(high: int, low: int) -> float:
        return ((high << 2) | low) / 1024

    values = (ten(data[27], (low1 >> 6) & 3), ten(data[28], (low1 >> 4) & 3),
              ten(data[29], (low1 >> 2) & 3), ten(data[30], low1 & 3),
              ten(data[31], (low2 >> 6) & 3), ten(data[32], (low2 >> 4) & 3),
              ten(data[33], (low2 >> 2) & 3), ten(data[34], low2 & 3))
    primaries = values if all(0 < v < 1 for v in values) else None
    gamma = (data[23] + 100) / 100 if data[23] != 0xFF else None
    return Edid(pnp, maker, product, name, primaries, gamma)


Point = tuple[float, float]
SRGB_PRIMARIES: tuple[Point, Point, Point] = ((0.640, 0.330), (0.300, 0.600), (0.150, 0.060))
P3_PRIMARIES: tuple[Point, Point, Point] = ((0.680, 0.320), (0.265, 0.690), (0.150, 0.060))


def polygon_area(points: list[Point]) -> float:
    """Signed area: positive when the points run counter-clockwise."""
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1])) / 2


def clip_polygon(subject: list[Point], window: list[Point]) -> list[Point]:
    """The part of a polygon inside a convex one (Sutherland-Hodgman)."""
    if polygon_area(window) < 0:
        window = window[::-1]
    result = subject
    for (x1, y1), (x2, y2) in zip(window, window[1:] + window[:1]):
        def inside(p: Point) -> bool:
            return (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1) >= 0

        def cross(p: Point, q: Point) -> Point:
            d1 = (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1)
            d2 = (x2 - x1) * (q[1] - y1) - (y2 - y1) * (q[0] - x1)
            t = d1 / (d1 - d2)
            return p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])

        source, result = result, []
        for index, current in enumerate(source):
            previous = source[index - 1]
            if inside(current):
                if not inside(previous):
                    result.append(cross(previous, current))
                result.append(current)
            elif inside(previous):
                result.append(cross(previous, current))
        if not result:
            break
    return result


def gamut_coverage(panel: Iterable[Point], reference: Iterable[Point]) -> float:
    """How much of the reference triangle (in CIE xy) the panel's triangle covers, from 0 to 1."""
    panel_tri, ref_tri = list(panel), list(reference)
    overlap = clip_polygon(ref_tri, panel_tri)
    return abs(polygon_area(overlap)) / abs(polygon_area(ref_tri)) if len(overlap) >= 3 else 0.0


def icc_check(data: bytes) -> None:
    """Raise SetupError unless this looks like a whole ICC profile (size field, 'acsp' signature, tag table)."""
    if len(data) < 132 or data[36:40] != b"acsp":
        raise SetupError("not an ICC profile (no 'acsp' signature)")
    if struct.unpack(">I", data[:4])[0] != len(data):
        raise SetupError("the ICC profile is cut short or has extra bytes (its size field does not match)")
    count = struct.unpack(">I", data[128:132])[0]
    if count > 200 or 132 + 12 * count > len(data):
        raise SetupError("the ICC profile has a broken tag table")


def icc_tags(data: bytes) -> list[tuple[bytes, bytes]]:
    """The (signature, content) of every tag in an ICC profile, in table order."""
    count = struct.unpack(">I", data[128:132])[0]
    tags = []
    for index in range(count):
        sig, offset, size = struct.unpack(">4sII", data[132 + 12 * index:144 + 12 * index])
        if offset + size > len(data):
            raise SetupError("the ICC profile has a tag that points outside the file")
        tags.append((sig, data[offset:offset + size]))
    return tags


def icc_description(data: bytes) -> str:
    """The profile description, which is the name GNOME and colord show for it."""
    try:
        for sig, blob in icc_tags(data):
            if sig != b"desc":
                continue
            if blob[:4] == b"desc":
                length = struct.unpack(">I", blob[8:12])[0]
                return blob[12:12 + max(length - 1, 0)].decode("latin-1")
            if blob[:4] == b"mluc":
                size, offset = struct.unpack(">II", blob[20:28])
                return blob[offset:offset + size].decode("utf-16-be")
    except (SetupError, struct.error, UnicodeDecodeError):
        return ""
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


# --- the machine ---------------------------------------------------------------------------

class State(enum.Enum):
    DONE = "done"
    PARTIAL = "partly done"
    TODO = "to do"
    NA = "not available"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Check:
    state: State
    detail: str = ""


def read_os_release() -> dict[str, str]:
    data: dict[str, str] = {}
    for line in read_text(Path("/etc/os-release")).splitlines():
        key, sep, value = line.partition("=")
        if sep and not key.startswith("#"):
            data[key] = value.strip().strip('"')
    return data


class System:
    """What this machine is, plus cached answers to the questions the checks ask. Everything here works without root."""

    def __init__(self) -> None:
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
        self.bios = read_text(DMI_DIR / "bios_version")
        self.desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
        self.session_type = os.environ.get("XDG_SESSION_TYPE", "")
        self.is_gnome = "GNOME" in self.desktop.upper()
        self.is_asus = "ASUS" in self.vendor.upper()
        self.model = self._model_code()
        self.is_g16 = SUPPORTED_BOARD in (self.model, self.board.upper())
        self._lock = threading.RLock()
        self._pacman: set[str] | None = None
        self._flatpaks: set[str] | None = None
        self._lspci: str | None = None
        self._in_repos: dict[str, bool] = {}
        self._shell: tuple[int, str] | None = None

    def _model_code(self) -> str:
        """
        The model code, the way G-Helper finds it on Windows: the part of the BIOS version before the first dot
        ('GA605WV.309' is a GA605WV). The board name is the fallback.
        """
        first = self.bios.partition(".")[0].strip().upper()
        if re.fullmatch(r"[A-Z0-9_]{4,12}", first) and any(c.isdigit() for c in first):
            return first
        return self.board.strip().upper()

    def refresh(self) -> None:
        """Forget cached answers, after something was installed or changed."""
        with self._lock:
            self._pacman = None
            self._flatpaks = None

    # --- running commands ---------------------------------------------------

    @staticmethod
    def run(cmd: list[str], timeout: float = 20) -> Result:
        return run(cmd, timeout)

    def out(self, cmd: list[str]) -> str:
        return run(cmd).out.strip()

    @staticmethod
    def has_cmd(name: str) -> bool:
        return shutil.which(name) is not None

    # --- packages -----------------------------------------------------------

    def pacman_installed(self) -> set[str]:
        with self._lock:
            if self._pacman is None:
                res = run(["pacman", "-Qq"], timeout=30)
                self._pacman = set(res.out.split()) if res.ok else set()
            return self._pacman

    def in_repos(self, name: str) -> bool:
        """Whether a package is in a repository pacman knows. The AUR is only for what is not."""
        with self._lock:
            if name not in self._in_repos:
                self._in_repos[name] = self.is_arch and run(["pacman", "-Si", name]).ok
            return self._in_repos[name]

    def flatpaks(self) -> set[str]:
        with self._lock:
            if self._flatpaks is None:
                res = run(["flatpak", "list", "--app", "--columns=application"], timeout=30)
                self._flatpaks = set(res.out.split()) if res.ok else set()
            return self._flatpaks

    def has_flathub(self) -> bool:
        return "flathub" in self.out(["flatpak", "remotes", "--columns=name"]).split()

    def pacman_locked(self) -> bool:
        return Path("/var/lib/pacman/db.lck").exists()

    def database_age_days(self) -> float | None:
        """How old the newest pacman sync database is, in days, or None when there is none."""
        times = []
        for path in Path("/var/lib/pacman/sync").glob("*.db"):
            try:
                times.append(path.stat().st_mtime)
            except OSError:
                continue
        return (time.time() - max(times)) / 86400 if times else None

    def kernel_package(self) -> str | None:
        """The package the running kernel came from (linux-cachyos, linux, ...), from its pkgbase file."""
        release = os.uname().release
        base = read_text(Path("/usr/lib/modules") / release / "pkgbase")
        return base if re.fullmatch(r"[a-z0-9][a-z0-9+._-]*", base) else None

    # --- services, settings, hardware ---------------------------------------

    def unit_state(self, unit: str) -> str:
        """enabled, disabled, masked, static ... or not-found."""
        res = run(["systemctl", "is-enabled", unit])
        text = res.out.strip().splitlines()
        if text:
            return text[0]
        return "not-found" if "no such file" in res.err.lower() or "not-found" in res.err.lower() else "unknown"

    def unit_active(self, unit: str) -> bool:
        return run(["systemctl", "is-active", unit]).out.strip() == "active"

    def gsettings(self, schema: str, key: str) -> str | None:
        if not self.has_cmd("gsettings"):
            return None
        res = run(["gsettings", "get", schema, key])
        if not res.ok:
            return None
        value = res.out.strip()
        return value[4:] if value.startswith("@as ") else value

    def lspci(self) -> str:
        with self._lock:
            if self._lspci is None:
                self._lspci = self.out(["lspci"]) if self.has_cmd("lspci") else ""
            return self._lspci

    @property
    def has_nvidia(self) -> bool:
        """
        Whether there is an NVIDIA GPU to set up. In Integrated mode the dGPU is off the PCI bus and lspci does not
        list it, so the G16 (it always has one) and an installed driver count as well.
        """
        return "nvidia" in self.lspci().lower() or self.is_g16 or "nvidia-utils" in self.pacman_installed()

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

    def shell_version(self) -> tuple[int, str] | None:
        """(major, full text) of GNOME Shell, e.g. (51, '51.0'), or None when it is not there."""
        with self._lock:
            if self._shell is None:
                match = re.search(r"(\d+)(?:\.[\w.]+)?", self.out(["gnome-shell", "--version"]))
                self._shell = (int(match.group(1)), match.group(0)) if match else (0, "")
            return self._shell if self._shell[0] else None

    def nvidia_handles_suspend(self) -> str | None:
        """
        Why the NVIDIA suspend units are not needed here, or None when they may be.

        NVIDIA's README: with the open kernel modules, saving video memory over suspend "is handled automatically
        if NVreg_UseKernelSuspendNotifiers=1". Arch's nvidia-utils sets that in /usr/lib/modprobe.d. The closed
        module still goes through the units. The open module reports a "Dual MIT/GPL" license.
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

    def online(self) -> bool:
        """A quick look at whether the internet is reachable: the first pacman mirror, then two well-known hosts."""
        hosts = []
        for line in read_text(Path("/etc/pacman.d/mirrorlist")).splitlines():
            found = re.match(r"\s*Server\s*=\s*https?://([^/:]+)", line)
            if found:
                hosts.append(found.group(1))
                break
        for host in (*hosts, "archlinux.org", "github.com"):
            try:
                with socket.create_connection((host, 443), timeout=4):
                    return True
            except OSError:
                continue
        return False


# --- the plan: what applying a set of changes would do -------------------------------------

@dataclass
class Step:
    """One thing done as you. Either a command or a Python callable."""
    desc: str
    argv: list[str] | None = None
    call: Callable[[], None] | None = None
    # For a step that needs a terminal: the command, worked out when it runs (it may need a download and a check).
    argv_factory: Callable[[], list[str]] | None = None
    # Decided when the step runs, not when the plan is made: an earlier part of the same run may have installed
    # the tool this step needs.
    when: Callable[[], bool] | None = None
    # Needs a terminal window of its own, because it asks you something (a password, a username).
    interactive: bool = False
    # Runs before anything is installed or removed, for steps that need a tool a removal is about to take away.
    early: bool = False
    # Fetches something from the internet, so the plan warns when there is no connection.
    network: bool = False
    # What an error message calls the program of an interactive step, when its last argument says nothing.
    name: str = ""
    # What the step runs, as the lines a shell would show. A command shows itself, so this is for a step that is a
    # Python function, or whose command is only known when it runs: it has to say what it amounts to, because the
    # review and the reference on the site list nothing else. A step that says nothing about itself cannot be made.
    shown: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not (self.argv or self.shown):
            raise ValueError(f"the step {self.desc!r} does not say what it runs")

    def commands(self) -> list[str]:
        """The lines to show for this step: what it says it runs, otherwise its own command."""
        return self.shown or [shell_line(self.argv or [])]


def shell_step(desc: str, script: str, **options) -> Step:
    """A step that is a few lines of shell, run as you. The script is what the review shows, word for word."""
    return Step(desc, ["bash", "-euo", "pipefail", "-c", script], shown=[script], **options)


@dataclass(frozen=True)
class Snippet:
    """A piece of the root script: what it is for, the shell it runs and, for a file it edits, the change as a diff."""
    desc: str
    script: str
    diff: str = ""


# The package manager commands live here and nowhere else: the root script and the Executor build their command lines
# from these and the review prints them, so what is listed is what runs.
PACMAN_INSTALL = ("pacman", "-S", "--needed", "--noconfirm", "--noprogressbar")
PACMAN_REMOVE = ("pacman", "-Rs", "--noconfirm", "--noprogressbar")
PARU_INSTALL = ("paru", "-S", "--needed")
FLATPAK_INSTALL = ("flatpak", "install", "-y", "flathub")
FLATPAK_REMOVE = ("flatpak", "uninstall", "-y")


@dataclass
class Plan:
    pacman: list[str] = field(default_factory=list)
    aur: list[str] = field(default_factory=list)
    flatpak: list[str] = field(default_factory=list)
    # What turning things off removes. Packages some other package still needs are kept, not forced out.
    remove_pacman: list[str] = field(default_factory=list)
    remove_flatpak: list[str] = field(default_factory=list)
    # Root snippets: 'root_early' runs first (stop a service before its package goes), 'root' after the installs.
    root_early: list[Snippet] = field(default_factory=list)
    root: list[Snippet] = field(default_factory=list)
    # A root snippet fetches something from the internet. A Step says so itself, and the packages are counted apart.
    network: bool = False
    steps: list[Step] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    reboot_for: list[str] = field(default_factory=list)
    relogin_for: list[str] = field(default_factory=list)

    @staticmethod
    def _add(target: list[str], names: Iterable[str]) -> None:
        for name in names:
            if name not in target:
                target.append(name)

    def add_pacman(self, names: Iterable[str]) -> None:
        self._add(self.pacman, names)

    def add_aur(self, names: Iterable[str]) -> None:
        self._add(self.aur, names)

    def add_flatpak(self, names: Iterable[str]) -> None:
        self._add(self.flatpak, names)

    def add_root(self, desc: str, script: str, early: bool = False, network: bool = False, diff: str = "") -> None:
        (self.root_early if early else self.root).append(Snippet(desc, script, diff))
        self.network = self.network or network

    def add_remove(self, pacman: Iterable[str], flatpak: Iterable[str]) -> None:
        self._add(self.remove_pacman, pacman)
        self._add(self.remove_flatpak, flatpak)

    def note(self, text: str) -> None:
        if text not in self.notes:
            self.notes.append(text)

    @property
    def empty(self) -> bool:
        return not (self.pacman or self.aur or self.flatpak or self.root or self.root_early or self.steps
                    or self.remove_pacman or self.remove_flatpak)

    @property
    def needs_network(self) -> bool:
        return bool(self.pacman or self.aur or self.flatpak or self.network
                    or any(step.network for step in self.steps))


# --- items ------------------------------------------------------------------------------------

@dataclass
class Item:
    id: str
    section: str
    title: str
    summary: str
    doc: str
    check: Callable[[System], Check]
    # What turning it on and off does, as a plan. None on either side means this script cannot do it.
    on: Callable[[System, Plan], None] | None = None
    off: Callable[[System, Plan], None] | None = None
    group: str = ""
    # Steps left for you, as a list or as a function of the machine (the bootloader decides some of them).
    manual: list[str] | Callable[[System], list[str]] = field(default_factory=list)
    # The same for undoing it by hand: for a row with no switch of its own, and for what an untick leaves behind.
    manual_off: list[str] | Callable[[System], list[str]] = field(default_factory=list)
    # Reasons to refuse right now (a login that still depends on it, a package that clashes), or None.
    on_blocker: Callable[[System], str | None] | None = None
    off_blocker: Callable[[System], str | None] | None = None
    # A reason it cannot be turned on today even though the machine is fine, e.g. an extension that does not
    # support this GNOME yet.
    unavailable: Callable[[System], str | None] | None = None
    recommended: bool = False
    advanced: bool = False
    # asus, g16, nvidia, mt7925 or empty
    hardware: str = ""
    needs_gnome: bool = False
    # Packages that come from the AUR (community build scripts) unless a repository has them.
    aur: tuple[str, ...] = ()
    # Other items this one cannot work without, and items it cannot be on together with.
    requires: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    # No toggle: the steps touch the bootloader or Secure Boot, so they stay yours.
    # The row is a status and a guide.
    guide_only: bool = False

    @property
    def url(self) -> str:
        return doc_url(self.doc)

    @property
    def toggleable(self) -> bool:
        return not self.guide_only and self.on is not None and self.off is not None

    def needs_aur(self, s: System) -> bool:
        """True when something here can only come from the AUR. A package that is in a repo never counts."""
        return any(not s.in_repos(name) for name in self.aur)

    def manual_steps(self, s: System) -> list[str]:
        return self.manual(s) if callable(self.manual) else list(self.manual)

    def manual_off_steps(self, s: System) -> list[str]:
        return self.manual_off(s) if callable(self.manual_off) else list(self.manual_off)

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


def package_item(item_id: str, section: str, title: str, summary: str, doc: str, *, group: str = "",
                 pacman: tuple[str, ...] = (), aur: tuple[str, ...] = (), flatpak: tuple[str, ...] = (),
                 recommended: bool = False, advanced: bool = False, hardware: str = "", needs_gnome: bool = False,
                 manual: tuple[str, ...] = (), requires: tuple[str, ...] = (), conflicts: tuple[str, ...] = (),
                 extra_check: Callable[[System, Check], Check] | None = None,
                 extra_on: Callable[[System, Plan], None] | None = None,
                 extra_off: Callable[[System, Plan], None] | None = None,
                 keep: tuple[str, ...] = (),
                 on_blocker: Callable[[System], str | None] | None = None,
                 off_blocker: Callable[[System], str | None] | None = None) -> Item:
    """An item that is, at heart, a set of packages, with an optional extra step or check on top."""

    def check(s: System) -> Check:
        result = packages_check(s, pacman, aur, flatpak)
        return extra_check(s, result) if extra_check else result

    def on(s: System, p: Plan) -> None:
        installed = s.pacman_installed()
        p.add_pacman([x for x in pacman if x not in installed])
        wanted = [x for x in aur if x not in installed]
        p.add_pacman([x for x in wanted if s.in_repos(x)])
        p.add_aur([x for x in wanted if not s.in_repos(x)])
        p.add_flatpak([x for x in flatpak if x not in s.flatpaks()])
        if extra_on:
            extra_on(s, p)

    def off(s: System, p: Plan) -> None:
        if extra_off:
            extra_off(s, p)
        installed = s.pacman_installed()
        names = [x for x in (*pacman, *aur) if x in installed]
        held = [x for x in names if x in keep or x in PROTECTED_PACKAGES]
        p.add_remove([x for x in names if x not in held], [x for x in flatpak if x in s.flatpaks()])
        if held:
            p.note("Kept, because other things use them: " + ", ".join(held))

    return Item(item_id, section, title, summary, doc, check, on, off, group=group, manual=list(manual),
                on_blocker=on_blocker, off_blocker=off_blocker, recommended=recommended, advanced=advanced,
                hardware=hardware, needs_gnome=needs_gnome, aur=aur, requires=requires, conflicts=conflicts)


# --- the dedicated scripts ------------------------------------------------------------------

def verified_tool(name: str) -> Path:
    """
    The path of a dedicated script whose SHA-256 matches the one built into this script.

    A copy next to this script is used when it matches. Otherwise the script is downloaded and checked before it
    is kept, so nothing that fails the check is ever written to the cache or run.
    """
    digest = TOOL_SHA256.get(name)
    if digest is None:
        raise SetupError(f"{name} is not one of the scripts this setup knows")
    local = SCRIPT_DIR / name
    if local.exists():
        actual = sha256_of(local.read_bytes())
        if actual == digest:
            return local
        raise SetupError(
            f"{name} next to this script does not match the SHA-256 this setup expects ({actual[:16]}... instead of "
            f"{digest[:16]}...). Download a fresh copy of both, or run .github/scripts/check-doc-checksums.sh --apply "
            "in the repository if you changed it yourself.")
    cached = CACHE_DIR / digest / name
    if cached.exists() and sha256_of(cached.read_bytes()) == digest:
        return cached
    data = curl_bytes(f"{RAW_BASE}/src/static/scripts/{name}", limit=5_000_000)
    actual = sha256_of(data)
    if actual != digest:
        raise SetupError(f"{name} downloaded from GitHub does not match the SHA-256 this setup expects "
                         f"({actual[:16]}... instead of {digest[:16]}...). Not running it.")
    cached.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    cached.write_bytes(data)
    return cached


def tool_argv(name: str, *args: str) -> list[str]:
    return [sys.executable, str(verified_tool(name)), *args]


def run_tool(name: str, *args: str) -> None:
    """Run one of the dedicated scripts after checking it, and fail with its own last words when it does."""
    lines: list[str] = []
    code = stream(tool_argv(name, *args), lines.append)
    log.info("%s %s -> %s", name, " ".join(args), code)
    if code != 0:
        tail = " | ".join(line for line in lines[-4:] if line.strip())
        raise SetupError(f"{name} exited with code {code}" + (f": {tail}" if tail else ""))


def tool_lines(script: str, *args: str, guide: str) -> list[str]:
    """
    How a dedicated script shows up in a plan: the command, where the script comes from, the hash it has to match and
    the guide that says what it changes. What the script does is its own business: it is published, and pinned by hash.
    """
    return [shell_line(["python3", script, *args]),
            f"# {script} is the copy next to quicksetup.py, or else",
            f"#   {RAW_BASE}/src/static/scripts/{script}",
            f"# It only runs when its SHA-256 is {TOOL_SHA256[script]}",
            f"#   which is the one published at {SITE}/scripts/{script}",
            f"# What it changes, and why: {doc_url(guide)}"]


def plan_tool(p: Plan, desc: str, script: str, *args: str, guide: str, reboot: str = "", relogin: str = "") -> None:
    p.steps.append(Step(f"{desc} (checked against the SHA-256 built into this setup)",
                        call=lambda: run_tool(script, *args), shown=tool_lines(script, *args, guide=guide)))
    if reboot:
        p.reboot_for.append(reboot)
    if relogin:
        p.relogin_for.append(relogin)


# --- hardware and ASUS -----------------------------------------------------------------------

def check_battery_limit(s: System) -> Check:
    if not s.has_cmd("asusctl"):
        return Check(State.TODO, "asusctl is not installed yet")
    match = re.search(r"(\d+)\s*%", s.out(["asusctl", "battery", "info"]))
    if not match:
        return Check(State.UNKNOWN, "could not read the charge limit (is asusd running?)")
    limit = int(match.group(1))
    return Check(State.DONE if limit < 100 else State.TODO, f"charge limit is {limit}%")


def on_battery_limit(s: System, p: Plan) -> None:
    p.add_pacman([x for x in ("asusctl", "rog-control-center") if x not in s.pacman_installed()])
    p.steps.append(Step("Limit charging to 80%", ["asusctl", "battery", "limit", "80"],
                        when=lambda: shutil.which("asusctl") is not None))


def off_battery_limit(s: System, p: Plan) -> None:
    p.steps.append(Step("Charge to 100% again", ["asusctl", "battery", "limit", "100"], early=True))


def ron_flag(text: str, key: str) -> bool | None:
    match = re.search(rf"\b{key}:\s*(true|false)", text)
    return None if match is None else match.group(1) == "true"


def check_slash(s: System) -> Check:
    if not s.has_cmd("asusctl"):
        return Check(State.TODO, "asusctl is not installed yet")
    text = read_text(Path("/etc/asusd/slash.ron"))
    enabled, battery, sleep = (ron_flag(text, k) for k in ("enabled", "show_on_battery", "show_on_sleep"))
    if enabled is None:
        return Check(State.UNKNOWN, "could not read /etc/asusd/slash.ron")
    if not enabled:
        return Check(State.DONE, "the Slash LED is switched off")
    if battery or sleep:
        return Check(State.TODO, f"lit on battery: {'yes' if battery else 'no'}, "
                                 f"during sleep: {'yes' if sleep else 'no'}")
    return Check(State.DONE, "lit on AC only, off on battery and during sleep")


def on_slash(s: System, p: Plan) -> None:
    p.add_pacman([x for x in ("asusctl",) if x not in s.pacman_installed()])
    p.steps.append(Step("Slash LED: on AC only", ["asusctl", "slash", "set", "--enable", "-b", "false", "-s", "false"],
                        when=lambda: shutil.which("asusctl") is not None))


def off_slash(s: System, p: Plan) -> None:
    p.steps.append(Step("Slash LED: lit on battery and during sleep again",
                        ["asusctl", "slash", "set", "--enable", "-b", "true", "-s", "true"], early=True))


def check_ppd(s: System) -> Check:
    state = s.unit_state("power-profiles-daemon.service")
    if state in ("masked", "not-found"):
        return Check(State.DONE, "power-profiles-daemon is " + ("masked" if state == "masked" else "not installed"))
    running = "running" if s.unit_active("power-profiles-daemon.service") else "not running"
    return Check(State.TODO, f"power-profiles-daemon is {state} and {running}, and fights asusd over profiles")


def on_ppd(s: System, p: Plan) -> None:
    p.add_root("Mask power-profiles-daemon so asusd owns the power profiles",
               "systemctl mask --now power-profiles-daemon.service")
    p.note("GNOME's own power-mode switch stops working once power-profiles-daemon is masked. "
           "Switch profiles with 'asusctl profile next' or ROG Control Center instead.")


def off_ppd(s: System, p: Plan) -> None:
    p.add_root("Unmask power-profiles-daemon", "systemctl unmask power-profiles-daemon.service", early=True)


def ppd_off_blocker(s: System) -> str | None:
    if s.unit_state("power-profiles-daemon.service") == "not-found":
        return "power-profiles-daemon is not installed, so there is nothing to unmask"
    return None


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


def on_backlight(s: System, p: Plan) -> None:
    plan_tool(p, "Apply the brightness fix with zephyrus-backlight.py", "zephyrus-backlight.py", "enable", "--silent",
              guide="known-issues", reboot="the brightness fix")
    if s.bootloader() == "limine":
        p.note("This machine boots with Limine: limine-update rebuilds the boot images, which takes a minute or "
               "more and prints nothing until it is done.")


def off_backlight(s: System, p: Plan) -> None:
    plan_tool(p, "Remove the brightness fix with zephyrus-backlight.py", "zephyrus-backlight.py", "disable",
              "--silent", guide="known-issues", reboot="removing the brightness fix")
    p.note("Without the fix, brightness does not work in Integrated mode.")


# --- graphics -----------------------------------------------------------------------------------

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


def on_nvidia_services(s: System, p: Plan) -> None:
    p.add_root("Enable the NVIDIA suspend, resume and hibernate services", "systemctl enable " + " ".join(NVIDIA_UNITS))
    p.note(f"{NVIDIA_SLEEP_UNIT} stays as it is: enable it only if you use that sleep mode.")


def off_nvidia_services(s: System, p: Plan) -> None:
    p.add_root("Disable the NVIDIA suspend, resume and hibernate services",
               "systemctl disable " + " ".join(NVIDIA_UNITS), early=True)
    p.note(f"{NVIDIA_SLEEP_UNIT} is left alone: this never enabled it.")


def check_nvidia_powerd(s: System) -> Check:
    state = s.unit_state("nvidia-powerd.service")
    if state == "not-found":
        return Check(State.NA, "nvidia-powerd is not installed (it comes with the NVIDIA driver)")
    if state == "enabled":
        return Check(State.DONE, "Dynamic Boost daemon is enabled")
    return Check(State.TODO, f"nvidia-powerd is {state}")


def on_nvidia_powerd(s: System, p: Plan) -> None:
    p.add_root("Enable NVIDIA Dynamic Boost (nvidia-powerd)",
               "systemctl unmask nvidia-powerd.service\nsystemctl enable nvidia-powerd.service\n"
               "systemctl start nvidia-powerd.service || echo 'nvidia-powerd did not start now (normal in "
               "Integrated mode, the dGPU is off)'")
    p.note("The firmware decides whether Dynamic Boost does anything. asusd stops the service on battery by itself.")


def off_nvidia_powerd(s: System, p: Plan) -> None:
    p.add_root("Disable NVIDIA Dynamic Boost (nvidia-powerd)", "systemctl disable --now nvidia-powerd.service",
               early=True)


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


# --- networking ---------------------------------------------------------------------------------

def check_mt7925(s: System) -> Check:
    modprobe = Path("/etc/modprobe.d/mt7925e.conf").exists()
    nm = Path("/etc/NetworkManager/conf.d/wifi-powersave.conf").exists()
    detail = (f"PCIe ASPM override: {'yes' if modprobe else 'no'}, "
              f"NetworkManager power saving off: {'yes' if nm else 'no'}")
    if modprobe and nm:
        return Check(State.DONE, detail)
    return Check(State.PARTIAL if modprobe or nm else State.TODO, detail)


MT7925_GUIDE = "networking/mt7925-wifi-performance"


def on_mt7925(s: System, p: Plan) -> None:
    plan_tool(p, "Apply the Wi-Fi tuning with mt7925-tune.py", "mt7925-tune.py", "enable", guide=MT7925_GUIDE,
              reboot="PCIe ASPM")


def off_mt7925(s: System, p: Plan) -> None:
    plan_tool(p, "Revert the Wi-Fi tuning with mt7925-tune.py", "mt7925-tune.py", "disable", guide=MT7925_GUIDE,
              reboot="reverting the PCIe ASPM override")


def check_eduroam(s: System) -> Check:
    if not s.has_cmd("nmcli"):
        return Check(State.UNKNOWN, "NetworkManager is not available")
    names = s.out(["nmcli", "-t", "-f", "NAME", "connection", "show"]).splitlines()
    if "eduroam" in names:
        return Check(State.DONE, "an eduroam connection exists")
    return Check(State.TODO, "no eduroam connection (only needed at Saxion)")


EDUROAM_GUIDE = "networking/eduroam-network-installation"
EDUROAM_CA_DIR = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "saxion-eduroam"


def on_eduroam(s: System, p: Plan) -> None:
    p.steps.append(Step("Set up eduroam with saxion-eduroam.py in a terminal window (it asks for your login)",
                        argv_factory=lambda: tool_argv("saxion-eduroam.py"), interactive=True,
                        shown=tool_lines("saxion-eduroam.py", guide=EDUROAM_GUIDE)))


def off_eduroam(s: System, p: Plan) -> None:
    p.steps.append(Step("Remove the eduroam connection", ["nmcli", "connection", "delete", "eduroam"]))
    ca_file = shlex.quote(str(EDUROAM_CA_DIR / "saxion-eduroam-ca.pem"))
    p.steps.append(shell_step("Remove the pinned certificate authority the setup wrote",
                              f"rm -f {ca_file}\nrmdir {shlex.quote(str(EDUROAM_CA_DIR))} 2>/dev/null || true"))


# --- GNOME settings ---------------------------------------------------------------------------

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


def gsettings_reset(schema: str, key: str, desc: str) -> Step:
    return Step(desc, ["gsettings", "reset", schema, key])


def check_shortcuts(s: System) -> Check:
    done = [normalise(s.gsettings(schema, key)) == normalise(value) for schema, key, value, _ in SHORTCUTS]
    if all(done):
        return Check(State.DONE, "all five shortcuts are set")
    if any(done):
        return Check(State.PARTIAL, f"{sum(done)} of {len(done)} shortcuts are set")
    return Check(State.TODO, "none of the five shortcuts is set")


def on_shortcuts(s: System, p: Plan) -> None:
    for schema, key, value, what in SHORTCUTS:
        if normalise(s.gsettings(schema, key)) != normalise(value):
            p.steps.append(gsettings_step(schema, key, value, what))


def off_shortcuts(s: System, p: Plan) -> None:
    for schema, key, value, what in SHORTCUTS:
        if normalise(s.gsettings(schema, key)) == normalise(value):  # leave one you changed yourself alone
            p.steps.append(gsettings_reset(schema, key, f"Reset: {what}"))


CUSTOM_KEYS = MEDIA_KEYS + ".custom-keybinding"
CUSTOM_BASE = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"
SMILE_ID = "it.mijorus.smile"
# What GNOME 51 on the G16 reports for the Copilot key (it used to show up as XF86TouchpadOff).
COPILOT_KEY_BINDING = "<Shift><Super>F23"


def custom_keybindings(s: System) -> list[str]:
    return re.findall(r"'([^']+)'", s.gsettings(MEDIA_KEYS, "custom-keybindings") or "")


def check_smile_shortcut(s: System) -> Check:
    for path in custom_keybindings(s):
        if SMILE_ID in (s.gsettings(f"{CUSTOM_KEYS}:{path}", "command") or ""):
            return Check(State.DONE, "a shortcut for Smile exists")
    return Check(State.TODO, "no shortcut for Smile yet")


def on_smile_shortcut(s: System, p: Plan) -> None:
    """A custom GNOME shortcut that opens Smile on the Copilot key, as plain gsettings commands."""
    existing = custom_keybindings(s)
    number = 0
    while f"{CUSTOM_BASE}/custom{number}/" in existing:
        number += 1
    path = f"{CUSTOM_BASE}/custom{number}/"
    for key, value in (("name", "Emoji picker"), ("command", f"flatpak run {SMILE_ID}"),
                       ("binding", COPILOT_KEY_BINDING)):
        p.steps.append(gsettings_step(f"{CUSTOM_KEYS}:{path}", key, value, f"Shortcut for Smile: set its {key}"))
    listing = "[" + ", ".join(f"'{x}'" for x in [*existing, path]) + "]"
    p.steps.append(gsettings_step(MEDIA_KEYS, "custom-keybindings", listing,
                                  "Shortcut for Smile: add it to the custom shortcuts"))


def off_smile_shortcut(s: System, p: Plan) -> None:
    keep, removed = [], False
    for path in custom_keybindings(s):
        if SMILE_ID in (s.gsettings(f"{CUSTOM_KEYS}:{path}", "command") or ""):
            p.steps.append(Step("Remove the Copilot key shortcut for Smile",
                                ["gsettings", "reset-recursively", f"{CUSTOM_KEYS}:{path}"]))
            removed = True
        else:
            keep.append(path)
    if not removed:
        return
    if keep:
        p.steps.append(gsettings_step(MEDIA_KEYS, "custom-keybindings", "[" + ", ".join(f"'{x}'" for x in keep) + "]",
                                      "Keep your other custom shortcuts"))
    else:
        p.steps.append(gsettings_reset(MEDIA_KEYS, "custom-keybindings", "Reset the list of custom shortcuts"))


# --- GNOME Shell extensions -----------------------------------------------------------------------
#
# Installed from extensions.gnome.org without a browser add-on: the site publishes, per extension, which GNOME
# Shell versions each build supports, so the window can say "not on GNOME 51 yet" before anything is downloaded.

EGO = "https://extensions.gnome.org"
EXT_USER_DIR = Path.home() / ".local" / "share" / "gnome-shell" / "extensions"
EXT_SYSTEM_DIR = Path("/usr/share/gnome-shell/extensions")
SHELL_SCHEMA = "org.gnome.shell"


@dataclass(frozen=True)
class ExtensionSpec:
    key: str
    name: str
    uuid: str
    pk: int            # the number in the extensions.gnome.org URL
    summary: str
    doc: str
    recommended: bool = False
    requires: tuple[str, ...] = ()


EXTENSIONS = (
    ExtensionSpec("just-perfection", "Just Perfection", "just-perfection-desktop@just-perfection", 3843,
                  "Tweaks the shell. Its 'Window Demands Attention Focus' fixes apps that open in the background",
                  "applications/#gnome-window-focus-apps-opening-in-the-background", recommended=True),
    ExtensionSpec("astra-monitor", "Astra Monitor", "monitor@astraext.github.io", 6682,
                  "CPU, memory, disk, network and both GPUs in the top bar", "desktop/astra-monitor"),
    ExtensionSpec("in-picture", "In Picture", "in-picture@filiprund.cz", 8692,
                  "Moves and resizes Picture-in-Picture windows and can keep them on top, also on Wayland",
                  "desktop/gnome-extensions#in-picture"),
    ExtensionSpec("smile", "Smile complementary extension", "smile-extension@mijorus.it", 6096,
                  "Lets Smile paste the emoji for you on Wayland", "applications/utilities#smile-emoji-picker",
                  requires=("smile",)),
)


def extension_location(uuid: str) -> str | None:
    """'user' or 'system' when the extension is on disk, else None."""
    if (EXT_USER_DIR / uuid / "metadata.json").exists():
        return "user"
    if (EXT_SYSTEM_DIR / uuid / "metadata.json").exists():
        return "system"
    return None


def enabled_extensions(s: System) -> list[str]:
    return re.findall(r"'([^']+)'", s.gsettings(SHELL_SCHEMA, "enabled-extensions") or "")


def set_extension_enabled(uuid: str, on: bool) -> None:
    """
    Turn an extension on or off in the setting GNOME Shell reads. That works whether or not the running shell has
    noticed a freshly installed extension yet, which is why it is not 'gnome-extensions enable'.
    """
    s = System()
    current = enabled_extensions(s)
    if on:
        wanted = current if uuid in current else [*current, uuid]
    else:
        wanted = [x for x in current if x != uuid]
    if wanted != current:
        listing = "[" + ", ".join(f"'{x}'" for x in wanted) + "]"
        res = run(["gsettings", "set", SHELL_SCHEMA, "enabled-extensions", listing])
        if not res.ok:
            raise SetupError(res.text or "gsettings could not change enabled-extensions")
    if on:
        run(["gnome-extensions", "enable", uuid])  # makes it live right away when the shell already knows it


@dataclass(frozen=True)
class EgoBuild:
    """What extensions.gnome.org says about one extension for one GNOME Shell version."""
    compatible: bool
    tag: int | None
    newest_supported: str


def parse_ego_info(info: dict, shell_major: int) -> EgoBuild:
    """
    Read an extension-info answer. The site answers 200 even for a Shell version nobody supports, with the newest
    build, so compatibility comes from shell_version_map and never from the status code.
    """
    versions = info.get("shell_version_map") or {}
    newest = max((v for v in versions if v.isdigit()), key=int, default="")
    build = versions.get(str(shell_major))
    tag = build.get("pk") if isinstance(build, dict) else None
    return EgoBuild(isinstance(tag, int), tag if isinstance(tag, int) else None, newest)


def fetch_ego_build(spec: ExtensionSpec, shell_major: int) -> EgoBuild:
    raw = curl_bytes(f"{EGO}/extension-info/?pk={spec.pk}&shell_version={shell_major}", limit=2_000_000)
    try:
        info = json.loads(raw)
    except ValueError:
        raise SetupError("extensions.gnome.org sent something that is not JSON") from None
    if info.get("uuid") != spec.uuid:
        raise SetupError(f"extensions.gnome.org returned {info.get('uuid')!r} where {spec.uuid!r} was expected")
    return parse_ego_info(info, shell_major)


def check_extension_zip(data: bytes, uuid: str) -> None:
    """Raise SetupError unless this is a sane zip for this UUID: no escaping paths, a matching metadata.json."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise SetupError("the download is not a zip file") from None
    total = 0
    for info in archive.infolist():
        name = info.filename
        total += info.file_size
        if name.startswith("/") or ".." in Path(name).parts:
            raise SetupError(f"the zip contains a path that leaves its folder: {name}")
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise SetupError(f"the zip contains a symbolic link: {name}")
    if total > 60_000_000:
        raise SetupError("the zip unpacks to more than 60 MB, which no extension needs")
    try:
        meta = json.loads(archive.read("metadata.json"))
    except (KeyError, ValueError):
        raise SetupError("the zip has no readable metadata.json") from None
    if meta.get("uuid") != uuid:
        raise SetupError(f"the zip is for {meta.get('uuid')!r}, not {uuid!r}")


def install_extension(spec: ExtensionSpec) -> None:
    """Download the build that fits this GNOME Shell, check it, install it, switch it on."""
    s = System()
    shell = s.shell_version()
    if shell is None:
        raise SetupError("GNOME Shell is not running here, so the extension cannot be installed")
    build = fetch_ego_build(spec, shell[0])
    if not build.compatible or build.tag is None:
        raise SetupError(f"{spec.name} does not support GNOME {shell[0]} yet "
                         f"(newest supported: {build.newest_supported})")
    data = curl_bytes(f"{EGO}/download-extension/{spec.uuid}.shell-extension.zip?version_tag={build.tag}",
                      limit=20_000_000)
    check_extension_zip(data, spec.uuid)
    folder = CACHE_DIR / "extensions"
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = folder / f"{spec.key}-{build.tag}.zip"
    target.write_bytes(data)
    res = run(["gnome-extensions", "install", "--force", str(target)], timeout=60)
    if not res.ok:
        raise SetupError(f"gnome-extensions could not install {spec.name}: {res.text}")
    set_extension_enabled(spec.uuid, True)


def remove_extension(spec: ExtensionSpec) -> None:
    set_extension_enabled(spec.uuid, False)
    if extension_location(spec.uuid) == "user":
        res = run(["gnome-extensions", "uninstall", spec.uuid], timeout=60)
        folder = EXT_USER_DIR / spec.uuid
        if not res.ok and folder.is_dir() and folder.resolve().parent == EXT_USER_DIR.resolve():
            # The shell may not be answering; the folder is ours (inside the user extensions folder), so remove it.
            shutil.rmtree(folder, ignore_errors=True)
        if extension_location(spec.uuid) == "user":
            raise SetupError(f"could not remove {spec.name}: {res.text or 'the folder is still there'}")


def install_lines(spec: ExtensionSpec) -> list[str]:
    """What install_extension() amounts to. The build number and what is switched on now are known at run time."""
    archive = f"{CACHE_DIR / 'extensions' / spec.key}-<build>.zip"
    return [
        "# quicksetup.py does this itself (install_extension), and it amounts to:",
        f"curl -fsSL '{EGO}/extension-info/?pk={spec.pk}&shell_version=<your GNOME Shell version>'   # which build",
        f"curl -fsSL -o {archive} '{EGO}/download-extension/{spec.uuid}.shell-extension.zip?version_tag=<build>'",
        "# ^ refused unless it is a sane zip: no path out of its folder, no symlink, under 60 MB, this UUID's metadata",
        f"gnome-extensions install --force {archive}",
        f"gsettings set {SHELL_SCHEMA} enabled-extensions \"[<what is switched on now>, '{spec.uuid}']\"",
        f"gnome-extensions enable {spec.uuid}",
    ]


def remove_lines(spec: ExtensionSpec) -> list[str]:
    """What remove_extension() amounts to."""
    return [
        "# quicksetup.py does this itself (remove_extension), and it amounts to:",
        f"gsettings set {SHELL_SCHEMA} enabled-extensions \"[<what is switched on now, without '{spec.uuid}'>]\"",
        f"gnome-extensions uninstall {spec.uuid}",
        f"# ^ a copy in your home folder only. If the shell does not answer, {EXT_USER_DIR / spec.uuid} is deleted",
    ]


class ExtensionCatalog:
    """What extensions.gnome.org says per extension for the running GNOME Shell. Fetched in the background once."""

    def __init__(self) -> None:
        self._builds: dict[str, EgoBuild | str] = {}
        self._lock = threading.Lock()

    def refresh(self, s: System) -> None:
        shell = s.shell_version()
        if shell is None:
            return
        for spec in EXTENSIONS:
            try:
                result: EgoBuild | str = fetch_ego_build(spec, shell[0])
            except SetupError as exc:
                result = str(exc)
            with self._lock:
                self._builds[spec.key] = result

    def reason_unavailable(self, s: System, spec: ExtensionSpec) -> str | None:
        shell = s.shell_version()
        with self._lock:
            build = self._builds.get(spec.key)
        if shell is None or not isinstance(build, EgoBuild) or build.compatible:
            return None
        newest = f" (the newest build supports up to {build.newest_supported})" if build.newest_supported else ""
        return f"No build for GNOME {shell[0]} yet{newest}"

    def known(self, spec: ExtensionSpec) -> bool:
        with self._lock:
            return spec.key in self._builds


def extension_item(spec: ExtensionSpec, catalog: ExtensionCatalog) -> Item:
    def check(s: System) -> Check:
        if not s.has_cmd("gnome-extensions"):
            return Check(State.UNKNOWN, "gnome-extensions is not available")
        where = extension_location(spec.uuid)
        enabled = spec.uuid in enabled_extensions(s)
        if where and enabled:
            return Check(State.DONE, "installed and switched on" + (" (from a package)" if where == "system" else ""))
        if where:
            return Check(State.PARTIAL, "installed, but switched off")
        if enabled:
            return Check(State.PARTIAL, "switched on, but not installed")
        return Check(State.TODO, "not installed")

    def on(s: System, p: Plan) -> None:
        p.steps.append(Step(f"Install {spec.name} from extensions.gnome.org and switch it on",
                            call=lambda: install_extension(spec), network=True, shown=install_lines(spec)))
        p.relogin_for.append(f"{spec.name} (only if it does not show up by itself)")

    def off(s: System, p: Plan) -> None:
        p.steps.append(Step(f"Switch {spec.name} off and remove it", call=lambda: remove_extension(spec),
                            shown=remove_lines(spec)))
        p.note("Settings of a removed extension stay in your home folder, so installing it again brings them back.")

    return Item(f"ext-{spec.key}", "desktop", spec.name, spec.summary, spec.doc, check, on, off, group="Extensions",
                recommended=spec.recommended, needs_gnome=True, requires=spec.requires,
                unavailable=lambda s: catalog.reason_unavailable(s, spec))


# --- touchpad scroll speed --------------------------------------------------------------------------

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
    return "enabled: yes" in run(["wsf", "status"]).out


def on_wsf(s: System, p: Plan) -> None:
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


def off_wsf(s: System, p: Plan) -> None:
    p.steps.append(Step("Switch wayland-scroll-factor off", ["wsf", "disable"], early=True,
                        when=lambda: shutil.which("wsf") is not None))
    p.add_remove([x for x in ("wayland-scroll-factor",) if x in s.pacman_installed()], [])
    p.relogin_for.append("switching wayland-scroll-factor off")


# --- security -------------------------------------------------------------------------------------

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
            while not lines[section_end - 1].strip():  # straight after the last line that says something
                section_end -= 1
            lines[section_end:section_end] = pending
    return "\n".join(lines) + "\n"


def ini_value(text: str, section: str, key: str) -> str | None:
    """The value of an uncommented key in one section of an INI file."""
    current = ""
    for line in text.splitlines():
        header = re.match(r"\s*\[([^\]]+)\]\s*$", line)
        if header:
            current = header.group(1)
        elif current == section:
            found = re.match(rf"\s*{re.escape(key)}\s*=\s*(.*?)\s*$", line)
            if found:
                return found.group(1)
    return None


def check_autologin(s: System) -> Check:
    if not GDM_CONF.exists():
        return Check(State.NA, "GDM is not installed")
    conf = read_text(GDM_CONF)
    enabled = (ini_value(conf, "daemon", "AutomaticLoginEnable") or "").lower() == "true"
    user = ini_value(conf, "daemon", "AutomaticLogin")
    if enabled and user == s.user:
        return Check(State.DONE, f"autologin is on for {s.user}")
    if enabled:
        return Check(State.TODO, f"autologin is on for {user}, not for you")
    return Check(State.TODO, "you still get the GDM login screen after the disk unlock")


def staged_install(staged: Path, digest: str, target: str, mode: str = "644") -> str:
    """
    Root snippet that installs a file this window prepared in your cache, after checking its SHA-256.

    The prepared file sits in a folder you own, so any program running as you could swap it while the password
    dialog is open. Root therefore only installs it when it still has the content this window computed.
    """
    return ("# prepared in your cache folder by this setup: root installs it only while its SHA-256 still matches\n"
            f"echo {shlex.quote(digest + '  ' + str(staged))} | sha256sum -c --quiet -\n"
            f"install -m {mode} -o root -g root {shlex.quote(str(staged))} {shlex.quote(target)}")


def stage_file(name: str, data: bytes) -> tuple[Path, str]:
    """Write a file into the staging folder (only you can read it) and return it with its SHA-256."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    staged = CACHE_DIR / name
    staged.write_bytes(data)
    return staged, sha256_of(data)


def on_autologin(s: System, p: Plan) -> None:
    if not valid_username(s.user):
        raise SetupError(f"'{s.user}' is not a login name this setup is willing to put in a root script")
    new = set_ini_keys(read_text(GDM_CONF) + "\n", "daemon", {"AutomaticLoginEnable": "True", "AutomaticLogin": s.user})
    if ini_value(new, "daemon", "AutomaticLogin") != s.user:
        raise SetupError("could not write the autologin lines into the GDM config")
    staged, digest = stage_file("gdm-custom.conf", new.encode("utf-8"))
    conf, backup = shlex.quote(str(GDM_CONF)), shlex.quote(str(GDM_CONF) + ".zephyrus-setup.bak")
    p.add_root(f"Turn on GDM autologin for {s.user} (the old file is kept as custom.conf.zephyrus-setup.bak)",
               f"[ -e {backup} ] || cp -a {conf} {backup}\n" + staged_install(staged, digest, str(GDM_CONF)) + "\n"
               f"grep -q '^AutomaticLogin={s.user}$' {conf} || {{ cp -a {backup} {conf}; "
               f"echo 'The GDM config check failed, the old file is back'; exit 1; }}",
               diff=file_diff(GDM_CONF, read_text(GDM_CONF, raw=True), new))
    p.reboot_for.append("GDM autologin")
    p.note("Anyone who can unlock the disk lands in your session. The lock screen still asks for your password.")


def off_autologin(s: System, p: Plan) -> None:
    backup_path = Path(str(GDM_CONF) + ".zephyrus-setup.bak")
    conf = shlex.quote(str(GDM_CONF))
    if backup_path.exists():
        backup = shlex.quote(str(backup_path))
        p.add_root("Put the GDM config back as it was before", f"cp -a {backup} {conf}\nrm -f {backup}", early=True,
                   diff=file_diff(GDM_CONF, read_text(GDM_CONF, raw=True), read_text(backup_path, raw=True)))
    else:
        new = set_ini_keys(read_text(GDM_CONF) + "\n", "daemon", {"AutomaticLoginEnable": "False"})
        staged, digest = stage_file("gdm-custom.conf", new.encode("utf-8"))
        p.add_root("Turn GDM autologin off", staged_install(staged, digest, str(GDM_CONF)), early=True,
                   diff=file_diff(GDM_CONF, read_text(GDM_CONF, raw=True), new))
    p.reboot_for.append("turning autologin off")


YUBIKEY_PACKAGES = ("pam-u2f", "ccid", "pcsclite")
# The services where a touch of the key can answer a password prompt: sudo, the graphical prompt of polkit and the
# GNOME lock screen (GDM uses the same service for its login screen).
YUBIKEY_PAM_FILES = ("sudo", "polkit-1", "gdm-password")
PAM_DIR = Path("/etc/pam.d")
# PAM reads a service from /etc/pam.d first and falls back to the file the package ships here. polkit-1 and
# gdm-password live only here on a fresh install, so wiring them means putting a copy in /etc/pam.d.
PAM_VENDOR_DIR = Path("/usr/lib/pam.d")
PAM_U2F_MODULE = Path("/usr/lib/security/pam_u2f.so")
PAM_U2F_MARKER = "# Added by Zephyrus Setup: touch the YubiKey instead of typing the password"
PAM_U2F_LINE = "auth       sufficient   pam_u2f.so cue"
PAM_U2F_AUTH = re.compile(r"\s*auth\s+sufficient\s+pam_u2f\.so(?:\s.*)?")
# One registration as pamu2fcfg prints it: key handle, public key, key type and options.
U2F_CREDENTIAL = re.compile(r"[A-Za-z0-9+/=_-]+,[A-Za-z0-9+/=_-]+,(?:es256|eddsa|rs256)(?:,[+A-Za-z]*)?")


def pam_source(name: str) -> Path | None:
    """The file PAM reads for a service: yours in /etc/pam.d, else the one the package ships."""
    for folder in (PAM_DIR, PAM_VENDOR_DIR):
        if (folder / name).is_file():
            return folder / name
    return None


def pam_targets() -> list[str]:
    """The services from YUBIKEY_PAM_FILES that exist here. polkit-1 and gdm-password need polkit and GDM."""
    return [name for name in YUBIKEY_PAM_FILES if pam_source(name)]


def pam_text(name: str) -> str:
    source = pam_source(name)
    try:
        return source.read_text(encoding="utf-8") if source else ""
    except OSError:
        return ""


def pam_calls_u2f(text: str) -> bool:
    return any("pam_u2f.so" in line for line in text.splitlines() if not line.lstrip().startswith("#"))


def yubikey_wired() -> list[str]:
    return [name for name in pam_targets() if pam_calls_u2f(pam_text(name))]


def yubikey_wired_elsewhere() -> list[str]:
    """Services outside YUBIKEY_PAM_FILES that call pam_u2f. Someone added those by hand."""
    try:
        files = sorted(PAM_DIR.iterdir())
    except OSError:
        return []
    found = []
    for path in files:
        if path.name in YUBIKEY_PAM_FILES or path.name.endswith(".bak") or not path.is_file():
            continue
        try:
            if pam_calls_u2f(path.read_text(encoding="utf-8", errors="replace")):
                found.append(path.name)
        except OSError:
            continue
    return found


def pam_with_u2f(text: str) -> str:
    """The PAM file with the YubiKey line as its first auth line, so a touch is tried before the password."""
    lines = text.splitlines()
    for number, line in enumerate(lines):
        if re.match(r"\s*auth\s", line):
            return "\n".join([*lines[:number], PAM_U2F_MARKER, PAM_U2F_LINE, *lines[number:]]) + "\n"
    raise SetupError("it has no auth line, so there is no sensible place for the YubiKey line")


def pam_without_u2f(text: str) -> str:
    """The PAM file without the YubiKey line (and the note above it), whoever added it."""
    kept = [line for line in text.splitlines()
            if line.strip() != PAM_U2F_MARKER and not PAM_U2F_AUTH.fullmatch(line)]
    if pam_calls_u2f("\n".join(kept)):
        raise SetupError("it calls pam_u2f in a form this window did not write. Take that line out yourself")
    return "\n".join(kept) + "\n"


def pam_install_snippet(name: str, staged: Path, digest: str, existed: bool) -> str:
    """
    Root snippet that puts a prepared PAM file in place and checks it afterwards. The old file is kept next to it.
    When the check fails the old file comes back (or the new copy goes away again), so a bad edit never stays.
    """
    target = shlex.quote(str(PAM_DIR / name))
    backup = shlex.quote(str(PAM_DIR / name) + ".zephyrus-setup.bak")
    undo = f"cp -a {backup} {target}" if existed else f"rm -f {target}"
    return (f"[ -e {shlex.quote(str(PAM_U2F_MODULE))} ] || "
            "{ echo 'pam_u2f.so is not installed, so PAM would have nothing to call'; exit 1; }\n"
            + (f"[ -e {backup} ] || cp -a {target} {backup}\n" if existed else "")
            + staged_install(staged, digest, str(PAM_DIR / name)) + "\n"
            f"grep -Eq '^auth[[:space:]]+sufficient[[:space:]]+pam_u2f\\.so' {target} || "
            f"{{ {undo}; echo 'The PAM check failed, the old file is back'; exit 1; }}")


def check_yubikey(s: System) -> Check:
    missing = [x for x in YUBIKEY_PACKAGES if x not in s.pacman_installed()]
    if missing:
        return Check(State.TODO if len(missing) == len(YUBIKEY_PACKAGES) else State.PARTIAL,
                     "missing: " + ", ".join(missing))
    if s.unit_state("pcscd.socket") != "enabled":
        return Check(State.PARTIAL, "installed, but the smart card socket (pcscd) is not enabled")
    return Check(State.DONE, "tools installed, smart card daemon on")


def on_yubikey(s: System, p: Plan) -> None:
    p.add_pacman([x for x in YUBIKEY_PACKAGES if x not in s.pacman_installed()])
    p.add_flatpak([x for x in ("com.yubico.yubioath",) if x not in s.flatpaks()])
    p.add_root("Start the smart card daemon now and at boot", "systemctl enable --now pcscd.socket")


def off_yubikey(s: System, p: Plan) -> None:
    p.add_root("Stop the smart card daemon", "systemctl disable --now pcscd.socket || true", early=True)
    p.add_remove([x for x in ("pam-u2f", "ccid") if x in s.pacman_installed()],
                 [x for x in ("com.yubico.yubioath",) if x in s.flatpaks()])
    p.note("pcsclite stays: other smart card tools use it.")


def yubikey_off_blocker(s: System) -> str | None:
    """The three services this window wires are covered by 'requires'. Anything else would be someone's own edit."""
    elsewhere = yubikey_wired_elsewhere()
    if elsewhere:
        return ("pam_u2f is also used in /etc/pam.d/" + ", /etc/pam.d/".join(elsewhere) + ", which this window did "
                "not set up. Take those lines out first: removing the module while they are there can lock you out")
    return None


# --- the registration: which keys may answer for you --------------------------------------

def u2f_keys_file(home: Path) -> Path:
    """Where pam_u2f looks by default. The line is 'user:key1:key2', one credential per registered key."""
    return home / ".config" / "Yubico" / "u2f_keys"


def u2f_credentials(text: str, user: str) -> list[str]:
    for line in text.splitlines():
        name, _, rest = line.partition(":")
        if name == user:
            return [part for part in rest.split(":") if part]
    return []


def u2f_with_credential(text: str, user: str, credential: str) -> str:
    """The key file with one more credential on the user's line. Other users' lines stay as they are."""
    if not U2F_CREDENTIAL.fullmatch(credential):
        raise SetupError("what the key returned does not look like a registration, so it was not saved")
    lines = text.splitlines()
    for number, line in enumerate(lines):
        name, _, rest = line.partition(":")
        if name == user:
            lines[number] = f"{line}:{credential}" if rest else f"{user}:{credential}"
            break
    else:
        lines.append(f"{user}:{credential}")
    return "\n".join(lines) + "\n"


def u2f_first_credential_only(text: str, user: str) -> str:
    lines = text.splitlines()
    for number, line in enumerate(lines):
        name, _, _rest = line.partition(":")
        if name == user:
            lines[number] = ":".join([user, *u2f_credentials(text, user)[:1]])
    return "\n".join(lines) + "\n"


def write_private(path: Path, text: str) -> None:
    """Replace a file in one step, readable by you only (this is a key file)."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name(path.name + ".tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(temp, path)


def registered_keys(s: System) -> int:
    try:
        return len(u2f_credentials(u2f_keys_file(s.home).read_text(encoding="utf-8"), s.user))
    except OSError:
        return 0


def staged_registration() -> Path:
    return CACHE_DIR / "yubikey-registration"


def register_command(spare: bool) -> list[str]:
    """
    What the terminal window runs: ask for the key, let pamu2fcfg talk to it (it asks for the key's PIN itself when
    the key has one) and keep what it prints. Only the part that needs you sits in the terminal.
    """
    staged = shlex.quote(str(staged_registration()))
    ask = ("Take the first key out and plug in the spare one, then press Enter. " if spare
           else "Plug in your YubiKey, then press Enter. ")
    script = (f'umask 077; mkdir -p "$(dirname {staged})"; rm -f {staged}\n'
              f'read -r -p {shlex.quote(ask)} _\n'
              'echo "Touch the key when it blinks. If it asks for a PIN, that is the PIN of the key itself."\n'
              f'pamu2fcfg -n > {staged} || {{ code=$?; rm -f {staged}; exit "$code"; }}')
    return ["bash", "-c", script]


def save_registration(s: System) -> None:
    """Add what the terminal step got from the key to your key file, and never leave the raw output lying around."""
    staged = staged_registration()
    try:
        credential = staged.read_text(encoding="utf-8").strip().lstrip(":")
    except OSError:
        credential = ""
    finally:
        staged.unlink(missing_ok=True)
    if not credential:
        raise SetupError("the key did not return a registration. Run the step again with the key plugged in")
    path = u2f_keys_file(s.home)
    try:
        existing = path.read_text(encoding="utf-8")
    except OSError:
        existing = ""
    write_private(path, u2f_with_credential(existing, s.user, credential))
    log.info("saved a U2F registration for %s (%d now)", s.user, registered_keys(s))


def plan_registration(s: System, p: Plan, spare: bool) -> None:
    what = "spare YubiKey" if spare else "YubiKey"
    keys = shlex.quote(str(u2f_keys_file(s.home)))
    p.steps.append(Step(f"Register your {what}: plug it in, and touch it when it blinks",
                        argv_factory=lambda: register_command(spare), interactive=True, name="pamu2fcfg",
                        shown=[register_command(spare)[-1]]))
    p.steps.append(Step(f"Save the registration of your {what} in ~/.config/Yubico/u2f_keys",
                        call=lambda: save_registration(s),
                        shown=["# quicksetup.py does this itself (save_registration), with umask 077:",
                               f"# a first key adds the line '{s.user}:<registration>' to {keys},",
                               "# a spare adds ':<registration>' to the end of your line there",
                               f"rm -f {shlex.quote(str(staged_registration()))}   # either way the staged file goes"]))


def check_yubikey_key(s: System) -> Check:
    count = registered_keys(s)
    if count:
        return Check(State.DONE, f"{plural(count, 'key', 'keys')} registered for {s.user}")
    return Check(State.TODO, "no key registered yet")


def on_yubikey_key(s: System, p: Plan) -> None:
    plan_registration(s, p, spare=False)


def off_yubikey_key(s: System, p: Plan) -> None:
    path = u2f_keys_file(s.home)
    backup = path.with_name(path.name + ".zephyrus-setup.bak")
    p.steps.append(Step("Forget the registered keys (the file is kept as u2f_keys.zephyrus-setup.bak)",
                        ["mv", "-f", str(path), str(backup)]))
    p.note("The keys themselves are not touched. Registering again takes a few seconds.")


def check_yubikey_spare(s: System) -> Check:
    count = registered_keys(s)
    if count >= 2:
        return Check(State.DONE, f"{count} keys registered for {s.user}")
    return Check(State.TODO, "one key registered, no spare yet" if count else "register your first key first")


def on_yubikey_spare(s: System, p: Plan) -> None:
    plan_registration(s, p, spare=True)


def off_yubikey_spare(s: System, p: Plan) -> None:
    path = u2f_keys_file(s.home)

    def keep_first() -> None:
        write_private(path, u2f_first_credential_only(path.read_text(encoding="utf-8"), s.user))

    p.steps.append(Step("Forget the spare key (the first registered key stays)", call=keep_first,
                        shown=["# quicksetup.py does this itself (keep_first): your line keeps its first key, mode 600",
                               f"sed -E -i 's/^({s.user}:[^:]*).*$/\\1/' {shlex.quote(str(path))}"]))


# --- the PAM wiring: a touch instead of the password --------------------------------------

def check_yubikey_pam(s: System) -> Check:
    wired, targets = yubikey_wired(), pam_targets()
    if wired and "pam-u2f" not in s.pacman_installed():
        return Check(State.PARTIAL, "PAM calls pam_u2f but the pam-u2f package is not installed. Fix this first")
    if "pam-u2f" not in s.pacman_installed():
        return Check(State.TODO, "install the YubiKey tools first")
    if not targets:
        return Check(State.NA, "none of sudo, polkit or GDM has a PAM file here")
    if len(wired) == len(targets):
        return Check(State.DONE, "a touch works for " + ", ".join(wired))
    if wired:
        return Check(State.PARTIAL, "a touch works for " + ", ".join(wired) + ", not yet for "
                     + ", ".join(name for name in targets if name not in wired))
    return Check(State.TODO, "sudo, the graphical prompt and the lock screen still ask for the password")


def on_yubikey_pam(s: System, p: Plan) -> None:
    targets = pam_targets()
    if "sudo" not in targets:
        raise SetupError("there is no PAM file for sudo, so there is nothing to wire")
    for name in targets:
        text = pam_text(name)
        if pam_calls_u2f(text):
            continue
        try:
            new = pam_with_u2f(text)
        except SetupError as exc:
            raise SetupError(f"{PAM_DIR / name}: {exc}") from exc
        existed = (PAM_DIR / name).is_file()
        staged, digest = stage_file(f"pam-{name}", new.encode("utf-8"))
        how = ("the old file is kept as " + name + ".zephyrus-setup.bak" if existed
               else "a copy of the file the package ships, in /etc/pam.d")
        p.add_root(f"Put the YubiKey line first in /etc/pam.d/{name} ({how})",
                   pam_install_snippet(name, staged, digest, existed),
                   diff=file_diff(pam_source(name), text, new, PAM_DIR / name))
    p.note("A touch of the key now replaces the password for sudo, the graphical prompt and the lock screen, so "
           "whoever holds the key can use them. Without the key plugged in, the password works as before.")
    p.note("Test sudo in a second terminal before you close this one.")


def off_yubikey_pam(s: System, p: Plan) -> None:
    for name in pam_targets():
        target = PAM_DIR / name
        try:
            text = target.read_text(encoding="utf-8")
        except OSError:
            continue
        if not pam_calls_u2f(text):
            continue
        try:
            stripped = pam_without_u2f(text)
        except SetupError as exc:
            raise SetupError(f"{target}: {exc}") from exc
        backup = shlex.quote(str(target) + ".zephyrus-setup.bak")
        vendor = PAM_VENDOR_DIR / name
        if vendor.is_file() and stripped.split() == vendor.read_text(encoding="utf-8").split():
            p.add_root(f"Take the YubiKey line out of /etc/pam.d/{name} by removing the copy, so the file the "
                       "package ships is used again", f"rm -f {shlex.quote(str(target))} {backup}", early=True,
                       diff=file_diff(target, text, read_text(vendor, raw=True), vendor))
        else:
            staged, digest = stage_file(f"pam-{name}", stripped.encode("utf-8"))
            p.add_root(f"Take the YubiKey line out of /etc/pam.d/{name}",
                       staged_install(staged, digest, str(target)) + f"\nrm -f {backup}", early=True,
                       diff=file_diff(target, text, stripped))


def secure_boot_enabled(s: System) -> bool:
    state = s.out(["bootctl", "status"]) if s.has_cmd("bootctl") else ""
    return re.search(r"Secure Boot:\s*enabled", state, re.IGNORECASE) is not None


def sbctl_off_blocker(s: System) -> str | None:
    """sbctl signs every new kernel through a pacman hook. Without it, Secure Boot refuses the next kernel."""
    if secure_boot_enabled(s):
        return ("Secure Boot is on, and sbctl is what signs every new kernel. Turn Secure Boot off in the UEFI "
                "first, or the next kernel update will not boot")
    return None


def check_secure_boot(s: System) -> Check:
    enabled = secure_boot_enabled(s)
    has_sbctl = "sbctl" in s.pacman_installed()
    if enabled and has_sbctl:
        return Check(State.DONE, "Secure Boot is on and sbctl is installed")
    if has_sbctl:
        return Check(State.PARTIAL, "sbctl is installed, Secure Boot is still off")
    return Check(State.TODO, f"Secure Boot is {'on' if enabled else 'off'}, sbctl is not installed")


# --- color: what the built-in screen is --------------------------------------------------------
#
# How this fits together, and what is and is not possible on Linux:
#
# * G-Helper on Windows asks ASUS's AsusSplendid.exe to switch the gamut. The .icm files only decide which modes
#   G-Helper lists, and they describe the panel after that switch. Linux has no such switch.
# * A color profile assigned in colord (what Settings > Color does) tells color-managed apps what the screen does.
#   GNOME's compositor reads only the gamma table (vcgt) out of it, and none of the ASUS profiles has one, so
#   switching profiles alone changes nothing you can see. mutter 51 builds the output color state from the color
#   mode only; applying the ICC profile itself is upstream work for GNOME 52 (mutter !5177, issue #4597).
# * What does change the picture is GNOME's own color mode (mutter 50 and newer, 'sdr-native'): the compositor
#   converts sRGB content to the panel's real primaries, read from its EDID. That is a real sRGB mode, and the
#   only compositor switch there is: 'default' treats the panel as sRGB, which on a wide gamut screen is vivid.
# * The panel natively covers about Display P3, so the DCI-P3 and Display P3 modes of G-Helper would show exactly
#   the picture of Native, while telling color-managed apps something that is not true. They are not offered.
#
# So a mode here is two layers kept in step: the compositor color mode, and the colord profile that describes the
# resulting screen: the factory profile for Native, an sRGB profile for sRGB.

GPU_VENDORS = {"0x1002": "1002", "0x10de": "10DE"}
COLORD_STORE = Path("/var/lib/colord/icc")
# An earlier version of this script put copies here. They share a colord ID with the ones in colord's own folder.
OLD_ICC_DIR = Path.home() / ".local" / "share" / "icc"
STAGE_DIR = CACHE_DIR / "icc"

MUTTER_DEFAULT, MUTTER_BT2100, MUTTER_SDR_NATIVE = 0, 1, 2


@dataclass(frozen=True)
class Panel:
    connector: str
    gpu: str            # '1002' (AMD) or '10DE' (NVIDIA): the GPU the built-in screen hangs off right now
    edid: Edid


def internal_panel() -> Panel | None:
    """The built-in display, from its EDID, e.g. ('eDP-2', '1002', Sharp 104D158E)."""
    for status in sorted(Path("/sys/class/drm").glob("card*-eDP-*/status")):
        if read_text(status) != "connected":
            continue
        try:
            raw = (status.parent / "edid").read_bytes()
        except OSError:
            continue
        edid = parse_edid(raw)
        # The connector (card2-eDP-2) has no vendor file of its own; the card it belongs to does.
        card, _, connector = status.parent.name.partition("-")
        gpu = GPU_VENDORS.get(read_text(Path("/sys/class/drm") / card / "device" / "vendor").lower())
        if edid and gpu:
            return Panel(connector, gpu, edid)
    return None


@dataclass(frozen=True)
class ColorMode:
    key: str
    title: str
    summary: str
    profile_title: str     # what GNOME's Color settings call the profile
    file: str | None       # None: the panel's own factory profile
    compositor: int        # the GNOME color mode this one uses


# The two G-Helper gamut modes that mean something on Linux. They also make sense on a laptop with no ASUS profiles.
COLOR_MODES = (
    ColorMode("native", "Native", "Vivid. The panel as it comes, with its whole wide gamut, so sRGB content is "
              "stretched to it.", "ASUS Native (factory calibrated)", None, MUTTER_DEFAULT),
    ColorMode("srgb", "sRGB", "GNOME maps colors onto the panel's real primaries, so sRGB content looks the way it "
              "was made. Fullscreen apps can no longer skip the compositor.", "ASUS sRGB", "ASUS_sRGB.icm",
              MUTTER_SDR_NATIVE),
)
# Profiles an earlier version installed for modes that only looked the same as Native. Cleaned up, never installed.
RETIRED_PROFILES = {"ASUS_DCIP3.icm": "ASUS DCI-P3", "ASUS_DisplayP3.icm": "ASUS Display P3"}
MUTTER_MODE_NAMES = {MUTTER_DEFAULT: "default", MUTTER_BT2100: "bt2100", MUTTER_SDR_NATIVE: "sdr-native"}


def native_file(s: System, panel: Panel | None) -> str | None:
    """The factory profile of this panel, named the way ASUS names it, when this repository ships it."""
    if panel is None or not s.model:
        return None
    name = f"{s.model}_{panel.gpu}_{panel.edid.panel_id}_CMDEF.icm"
    return name if name in PROFILE_SHA256 else None


def profile_set(s: System, panel: Panel | None) -> list[tuple[ColorMode, str]]:
    """(mode, file name) for every mode that has a color profile on this machine. Empty without the ASUS set."""
    native = native_file(s, panel)
    if native is None:
        return []
    return [(mode, mode.file or native) for mode in COLOR_MODES]


def profile_source(name: str) -> bytes:
    """A profile from this checkout when it is here, otherwise from GitHub. Always checked against its SHA-256."""
    digest = PROFILE_SHA256.get(name)
    if digest is None:
        raise SetupError(f"{name} is not a color profile this setup knows")
    local = SCRIPT_DIR.parent / "icc-profiles" / name
    data = local.read_bytes() if local.exists() else curl_bytes(f"{RAW_BASE}/src/static/icc-profiles/{name}", 1_000_000)
    if sha256_of(data) != digest:
        raise SetupError(f"{name} does not match the SHA-256 this setup expects, so it is not used")
    icc_check(data)
    return data


def profile_id(path: Path) -> str | None:
    """
    colord's ID for a profile file: 'icc-' and the MD5 of its contents.

    colord keeps one profile per ID. A second file with the same contents is not a profile of its own, so profiles
    are matched by this ID and never by path alone. MD5 is colord's own scheme here, not a security measure.
    """
    try:
        return "icc-" + hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()
    except OSError:
        return None


# --- color: colord ---------------------------------------------------------------------------------

def colord_object(text: str) -> str | None:
    match = re.search(r"Object Path:\s*(\S+)", text)
    return match.group(1) if match else None


def device_blocks(text: str) -> list[str]:
    return [b for b in re.split(r"\n(?=Object Path:)", text) if "Object Path:" in b]


def parse_display_device(text: str) -> str | None:
    """colord's object path of the built-in display, the one GNOME's Color Management lists as Built-in Screen."""
    for block in device_blocks(text):
        if re.search(r"Embedded:\s*Yes", block) or "XRANDR_name=eDP" in block:
            return colord_object(block)
    return None


def parse_device_profiles(text: str, device: str) -> list[tuple[str, str]]:
    """(profile ID, file name) of the profiles on a device, in priority order. The first one is the active profile."""
    for block in device_blocks(text):
        if colord_object(block) == device:
            return re.findall(r"Profile \d+:\s+(\S+)\s*\n\s+(\S+)", block)
    return []


class Colord:
    """The few things this window asks colord, through colormgr."""

    def display_device(self) -> str | None:
        res = run(["colormgr", "get-devices-by-kind", "display"])
        return parse_display_device(res.out) if res.ok else None

    def profiles(self, device: str) -> list[tuple[str, str]]:
        return parse_device_profiles(run(["colormgr", "get-devices-by-kind", "display"]).out, device)

    def find_profile(self, path: Path, title: str = "") -> str | None:
        """
        colord's object path for a profile file, by file name first and then by its contents. With a title, only
        once colord has read the file with that title.
        """
        lookups = [["colormgr", "find-profile-by-filename", str(path)]]
        if pid := profile_id(path):
            lookups.append(["colormgr", "find-profile", pid])
        for cmd in lookups:
            res = run(cmd)
            if not res.ok:
                continue
            if title and not re.search(rf"Title:\s*{re.escape(title)}\s*$", res.out, re.MULTILINE):
                continue
            if found := colord_object(res.out):
                return found
        return None

    def wait_for_profile(self, path: Path, title: str, tries: int = 20) -> str | None:
        """colord reads new files a moment after they land."""
        for _ in range(tries):
            if found := self.find_profile(path, title):
                return found
            time.sleep(0.5)
        return None

    def add(self, device: str, profile: str) -> None:
        res = run(["colormgr", "device-add-profile", device, profile])
        if not res.ok and "already been added" not in res.text:
            raise SetupError(f"colord would not add the profile to the screen: {res.text or 'no reason given'}")

    def make_default(self, device: str, profile: str) -> None:
        res = run(["colormgr", "device-make-profile-default", device, profile])
        if not res.ok:
            raise SetupError(f"colord would not make the profile active: {res.text or 'no reason given'}")


# --- color: GNOME's display service ------------------------------------------------------------------

MUTTER_NAME = "org.gnome.Mutter.DisplayConfig"
MUTTER_PATH = "/org/gnome/Mutter/DisplayConfig"
APPLY_SIGNATURE = "(uua(iiduba(ssa{sv}))a{sv})"


@dataclass
class MutterMonitor:
    connector: str
    builtin: bool
    current_mode: str | None
    color_mode: int | None
    supported_modes: list[int]
    rgb_range: int | None
    underscanning: bool
    properties: dict[str, object] = field(default_factory=dict)      # everything GNOME reports, for the details


@dataclass
class MutterLogical:
    x: int
    y: int
    scale: float
    transform: int
    primary: bool
    connectors: list[str]


@dataclass
class MutterState:
    serial: int
    monitors: dict[str, MutterMonitor]
    logicals: list[MutterLogical]
    layout_mode: int | None
    can_change_layout_mode: bool


def parse_mutter_state(reply: tuple) -> MutterState:
    """Read the answer of GetCurrentState (already unpacked into plain Python values)."""
    serial, monitors, logicals, props = reply
    parsed: dict[str, MutterMonitor] = {}
    for spec, modes, mprops in monitors:
        current = next((m[0] for m in modes if m[6].get("is-current")), None)
        parsed[spec[0]] = MutterMonitor(
            connector=spec[0], builtin=bool(mprops.get("is-builtin")) or spec[0].startswith(("eDP", "LVDS", "DSI")),
            current_mode=current, color_mode=mprops.get("color-mode"),
            supported_modes=list(mprops.get("supported-color-modes") or []), rgb_range=mprops.get("rgb-range"),
            underscanning=bool(mprops.get("is-underscanning")), properties=dict(mprops))
    layouts = [MutterLogical(lx, ly, scale, transform, bool(primary), [m[0] for m in members])
               for lx, ly, scale, transform, primary, members, _ in logicals]
    return MutterState(serial, parsed, layouts, props.get("layout-mode"),
                       bool(props.get("supports-changing-layout-mode")))


class DisplayConfig:
    """GNOME's display service (mutter), the same one Settings and gdctl talk to."""

    def __init__(self) -> None:
        self._proxy = None

    def _call(self, method: str, params):
        import gi
        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib
        try:
            if self._proxy is None:
                self._proxy = Gio.DBusProxy.new_for_bus_sync(
                    Gio.BusType.SESSION,
                    Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES | Gio.DBusProxyFlags.DO_NOT_AUTO_START, None,
                    MUTTER_NAME, MUTTER_PATH, MUTTER_NAME, None)
            return self._proxy.call_sync(method, params, Gio.DBusCallFlags.NO_AUTO_START, 8000, None)
        except GLib.Error as exc:
            self._proxy = None
            if any(text in exc.message for text in ("without an owner", "ServiceUnknown", "not provided by any")):
                raise SetupError("GNOME's display service is not running here. "
                                 "This needs a GNOME session on Wayland.") from None
            raise SetupError(f"GNOME's display service did not answer ({exc.message})") from None

    def state(self) -> MutterState:
        return parse_mutter_state(self._call("GetCurrentState", None).unpack())

    def builtin(self, state: MutterState | None = None) -> MutterMonitor | None:
        state = state or self.state()
        return next((m for m in state.monitors.values() if m.builtin and m.current_mode), None)

    def set_color_mode(self, connector: str, mode: int) -> None:
        """
        Change the color mode of one screen and keep everything else exactly as it is: the same layout, scale,
        resolution and refresh rate. The change is saved, so it survives a restart, like a change in Settings.
        """
        from gi.repository import GLib
        for attempt in (1, 2):
            state = self.state()
            target = state.monitors.get(connector)
            if target is None or target.current_mode is None:
                raise SetupError(f"the screen {connector} is not active")
            if mode not in target.supported_modes:
                raise SetupError("this screen does not offer that color mode")
            logicals = []
            for logical in state.logicals:
                members = []
                for name in logical.connectors:
                    monitor = state.monitors[name]
                    options: dict[str, object] = {}
                    wanted = mode if name == connector else monitor.color_mode
                    if wanted is not None:
                        options["color-mode"] = GLib.Variant("u", wanted)
                    if monitor.rgb_range is not None:
                        options["rgb-range"] = GLib.Variant("u", monitor.rgb_range)
                    if monitor.underscanning:
                        options["underscanning"] = GLib.Variant("b", True)
                    members.append((name, monitor.current_mode, options))
                logicals.append((logical.x, logical.y, logical.scale, logical.transform, logical.primary, members))
            properties = {}
            if state.can_change_layout_mode and state.layout_mode is not None:
                properties["layout-mode"] = GLib.Variant("u", state.layout_mode)
            try:
                self._call("ApplyMonitorsConfig",
                           GLib.Variant(APPLY_SIGNATURE, (state.serial, 2, logicals, properties)))
                return
            except SetupError as exc:
                if attempt == 2 or "stale" not in str(exc).lower():
                    raise


# --- color: both layers together ------------------------------------------------------------------

@dataclass
class ColorInfo:
    model: str
    bios: str
    panel: Panel | None
    native: str | None                    # the factory profile this panel would use
    coverage_srgb: float | None
    coverage_p3: float | None
    modes: list[ColorMode]
    profiles_installed: bool
    compositor_ok: bool
    compositor_note: str
    colord_ok: bool
    current: str | None
    current_detail: str
    compositor_mode: str = ""                                    # what GNOME uses now: default, sdr-native, bt2100
    compositor_offers: list[str] = field(default_factory=list)   # the color modes GNOME offers for this screen
    active_profile: str = ""                                     # the profile colord has active on the screen
    extra: dict[str, str] = field(default_factory=dict)          # more for the details: GNOME version, session, ...


class ColorController:
    """Reads and switches the two layers behind a color mode. Blocking: call it from a worker thread."""

    def __init__(self, system: System, display: DisplayConfig | None = None, colord: Colord | None = None) -> None:
        self.s = system
        self.display = display or DisplayConfig()
        self.colord = colord or Colord()

    def info(self) -> ColorInfo:
        panel = internal_panel()
        files = profile_set(self.s, panel)
        coverage = (None, None)
        if panel and panel.edid.primaries:
            p = panel.edid.primaries
            tri = [(p[0], p[1]), (p[2], p[3]), (p[4], p[5])]
            coverage = (gamut_coverage(tri, SRGB_PRIMARIES), gamut_coverage(tri, P3_PRIMARIES))
        compositor_ok, note, monitor = False, "", None
        try:
            monitor = self.display.builtin()
            if monitor is None:
                note = "GNOME does not report a built-in screen"
            elif MUTTER_SDR_NATIVE not in monitor.supported_modes:
                note = self._why_no_srgb()
            else:
                compositor_ok = True
        except SetupError as exc:
            note = str(exc)
        colord_ok = self.s.has_cmd("colormgr")
        device = self.colord.display_device() if colord_ok else None
        listed = self.colord.profiles(device) if device else []
        active = Path(listed[0][1]).name if listed else ""
        installed = bool(files) and device is not None and all(
            profile_id(COLORD_STORE / name) in [pid for pid, _ in listed] for _, name in files)
        current, detail = self._current(files, monitor, active, compositor_ok)
        mode_name = offers = None
        if monitor is not None:
            mode_name = MUTTER_MODE_NAMES.get(monitor.color_mode, str(monitor.color_mode)) \
                if monitor.color_mode is not None else "default"
            offers = [MUTTER_MODE_NAMES.get(m, str(m)) for m in monitor.supported_modes]
        extra = self._extra(panel, monitor, device, listed)
        return ColorInfo(self.s.model, self.s.bios, panel, native_file(self.s, panel), coverage[0], coverage[1],
                         list(COLOR_MODES), installed, compositor_ok, note, colord_ok, current, detail,
                         mode_name or "", offers or [], active, extra)

    def _why_no_srgb(self) -> str:
        shell = self.s.shell_version()
        if shell is not None and shell[0] < 50:
            return f"GNOME {shell[0]} does not have the sRGB color mode. It needs GNOME 50 or newer on Wayland."
        return ("GNOME offers the sRGB color mode only for a screen whose EDID lists its primaries, white point and "
                "gamma. Either this screen's does not, or this is not GNOME 50 or newer on Wayland.")

    def _extra(self, panel: Panel | None, monitor: MutterMonitor | None, device: str | None,
               listed: list[tuple[str, str]]) -> dict[str, str]:
        """What a bug report about colors needs, beyond what the window already shows."""
        shell = self.s.shell_version()
        extra = {"GNOME Shell": shell[1] if shell else "not running", "Session": self.s.session_type or "unknown"}
        if panel is not None and panel.edid.primaries:
            p = panel.edid.primaries
            extra["EDID primaries"] = (f"R {p[0]:.3f} {p[1]:.3f}, G {p[2]:.3f} {p[3]:.3f}, B {p[4]:.3f} {p[5]:.3f}, "
                                       f"white {p[6]:.3f} {p[7]:.3f}")
            extra["EDID gamma"] = f"{panel.edid.gamma:.2f}" if panel.edid.gamma else "not given"
        if monitor is not None:
            extra["GNOME monitor properties"] = ", ".join(sorted(monitor.properties)) or "none"
        extra["colord device"] = device or "not found"
        extra["colord profiles"] = ", ".join(Path(f).name for _, f in listed) or "none"
        return extra

    def report(self, info: ColorInfo) -> str:
        """Everything worth pasting into a bug report about colors, as plain text."""
        panel = info.panel
        lines = ["Zephyrus Setup, color details", ""]
        lines.append(f"Model: {info.model or 'unknown'} (BIOS {info.bios or 'unknown'})")
        if panel is not None:
            edid = panel.edid
            lines.append(f"Panel: {edid.name or edid.pnp}, {panel.connector}, EDID {edid.panel_id}, GPU {panel.gpu}")
        if info.coverage_srgb is not None and info.coverage_p3 is not None:
            lines.append(f"Gamut from the EDID: {info.coverage_srgb * 100:.0f}% of sRGB, "
                         f"{info.coverage_p3 * 100:.0f}% of DCI-P3")
        lines.append(f"Factory profile for this panel: {info.native or 'none published'}")
        lines.append(f"Profiles installed on the screen: {'yes' if info.profiles_installed else 'no'}")
        lines.append(f"GNOME color mode: {info.compositor_mode or 'unknown'}"
                     f" (offered: {', '.join(info.compositor_offers) or 'unknown'})")
        if info.compositor_note:
            lines.append(f"Note: {info.compositor_note}")
        lines.append(f"Active color profile in colord: {info.active_profile or 'none'}")
        if info.current:
            lines.append(f"This window thinks the mode is: {info.current}")
        else:
            lines.append("This window thinks the mode is: neither"
                         + (f" ({info.current_detail})" if info.current_detail else ""))
        lines += [f"{key}: {value}" for key, value in info.extra.items()]
        return "\n".join(lines) + "\n"

    def _current(self, files: list[tuple[ColorMode, str]], monitor: MutterMonitor | None, active: str,
                 compositor_ok: bool) -> tuple[str | None, str]:
        if monitor is not None and monitor.color_mode == MUTTER_BT2100:
            return None, "HDR is on, and HDR has its own color mode"
        if compositor_ok and monitor is not None:
            sdr = monitor.color_mode == MUTTER_SDR_NATIVE
            if sdr and (not files or active in ("", "ASUS_sRGB.icm") or active.startswith("edid-")):
                return "srgb", ""
            if sdr:
                return None, f"GNOME uses sRGB mode, but the active profile is {active}"
            for mode, name in files:
                if mode.compositor == MUTTER_DEFAULT and name == active:
                    return mode.key, ""
            if not active or active.startswith("edid-") or not files:
                return "native", ""
            if active in RETIRED_PROFILES:
                return None, f"the active profile is {active}, from a mode that only looked like Native. Pick Native"
            return None, f"the active profile is {active}, which is not one of these"
        for mode, name in files:
            if name == active:
                return mode.key, ""
        return ("native", "") if not active or active.startswith("edid-") else (None, f"the active profile is {active}")

    def switch(self, key: str, info: ColorInfo | None = None) -> list[str]:
        """
        Switch to a mode and check that it took. Returns notes for the person (what was and was not changed).
        If the second layer fails after the first changed, the first is put back.
        """
        info = info or self.info()
        mode = next((m for m in info.modes if m.key == key), None)
        if mode is None:
            raise SetupError("that color mode is not available on this machine")
        log.info("color: switching to %s; GNOME is on %s and offers %s; colord has %s active", key,
                 info.compositor_mode or "?", ",".join(info.compositor_offers) or "?", info.active_profile or "nothing")
        notes: list[str] = []
        files = dict((m.key, name) for m, name in profile_set(self.s, info.panel))
        previous_compositor = None
        monitor = None
        if info.compositor_ok:
            monitor = self.display.builtin()
            if monitor is not None and monitor.color_mode != mode.compositor:
                previous_compositor = monitor.color_mode if monitor.color_mode is not None else MUTTER_DEFAULT
                if monitor.color_mode == MUTTER_BT2100:
                    notes.append("HDR was on and is off now. You can turn it on again in Settings, under Displays.")
                self.display.set_color_mode(monitor.connector, mode.compositor)
                if not self._wait_for_compositor(mode.compositor):
                    raise SetupError("GNOME accepted the change but is not using the new color mode")
        elif mode.compositor != MUTTER_DEFAULT:
            notes.append(info.compositor_note or "The screen's color mode could not be changed.")
        try:
            notes += self._set_profile(mode, files.get(key), info)
        except SetupError:
            if previous_compositor is not None and monitor is not None:
                try:
                    self.display.set_color_mode(monitor.connector, previous_compositor)
                except SetupError as exc:
                    log.warning("could not put the compositor color mode back: %s", exc)
            raise
        log.info("color: %s is set. %s", key, " ".join(notes) or "Both layers took it.")
        return notes

    def _wait_for_compositor(self, wanted: int) -> bool:
        for _ in range(12):
            monitor = self.display.builtin()
            if monitor is not None and monitor.color_mode == wanted:
                return True
            time.sleep(0.25)
        return False

    def _set_profile(self, mode: ColorMode, name: str | None, info: ColorInfo) -> list[str]:
        if name is None:
            return []
        if not info.colord_ok:
            return ["colord (colormgr) is not installed, so color-managed apps were not told."]
        device = self.colord.display_device()
        if device is None:
            return ["colord does not know the built-in screen yet: run this inside the GNOME session."]
        path = COLORD_STORE / name
        if profile_id(path) not in [pid for pid, _ in self.colord.profiles(device)]:
            return ["The ASUS color profiles are not on the screen yet: tick 'ASUS color profiles' below and apply, "
                    "then color-managed apps will be told too."]
        profile = self.colord.find_profile(path)
        if profile is None:
            raise SetupError(f"colord does not know {name}")
        # A display can list a profile colord has since dropped and read again. Adding it first puts it back.
        self.colord.add(device, profile)
        self.colord.make_default(device, profile)
        listed = self.colord.profiles(device)
        if not listed or listed[0][0] != profile_id(path):
            raise SetupError("colord accepted the profile but did not make it the active one")
        return []


def color_runs(connector: str) -> str:
    """What switching a color mode does, in plain text: the two calls the window makes, and the way back."""
    return (
        "A switch needs no root and downloads nothing. It makes two calls, as you:\n\n"
        f"1. GNOME's display service, the call Settings > Displays makes: D-Bus {MUTTER_NAME},\n"
        f"   {MUTTER_PATH}, ApplyMonitorsConfig (persistent) for {connector} only,\n"
        "   with color-mode 0 (default) for Native or 2 (sdr-native) for sRGB. The layout, scale, resolution,\n"
        "   refresh rate and every other screen are sent back as they are.\n"
        "2. colord, for color-managed apps, once 'ASUS color profiles' is ticked: colormgr device-add-profile and\n"
        "   device-make-profile-default <Built-in Screen> <profile>. Native uses the panel's factory profile,\n"
        "   sRGB uses ASUS_sRGB.icm.\n\n"
        "When the second call fails, the first is put back. The way back: pick the other mode, or press Undo in\n"
        "the message that shows for a few seconds after a switch. The code: ColorController.switch.\n")


# --- color: installing the profiles (an item in the list) --------------------------------------------

def check_color_profiles(s: System) -> Check:
    panel = internal_panel()
    files = profile_set(s, panel)
    if not files:
        if panel is None:
            return Check(State.UNKNOWN, "could not read the built-in screen's panel ID")
        return Check(State.UNKNOWN, f"no factory profile is published for this panel ({s.model}_{panel.gpu}_"
                                    f"{panel.edid.panel_id})")
    if not s.has_cmd("colormgr"):
        return Check(State.UNKNOWN, "colormgr (colord) is not installed")
    colord = Colord()
    device = colord.display_device()
    in_store = [name for mode, name in files if (COLORD_STORE / name).exists()
                and icc_description((COLORD_STORE / name).read_bytes()) == mode.profile_title]
    on_display = []
    if device:
        ids = [pid for pid, _ in colord.profiles(device)]
        on_display = [name for _, name in files if profile_id(COLORD_STORE / name) in ids]
    old_copies = [name for name in (*(n for _, n in files), *RETIRED_PROFILES) if (OLD_ICC_DIR / name).exists()]
    retired = system_color_copies(s, retired_only=True)
    if len(in_store) == len(files) and len(on_display) == len(files) and not retired:
        return Check(State.DONE, "both profiles are on the built-in screen")
    if in_store or on_display or old_copies or retired:
        extra = ", an older copy is in your home folder" if old_copies else ""
        if retired:
            extra += ", profiles of two modes that no longer exist are still installed"
        return Check(State.PARTIAL,
                     f"{len(in_store)} of {len(files)} installed, {len(on_display)} on the screen{extra}")
    return Check(State.TODO, "the ASUS color profiles are not installed")


def stage_profiles(s: System) -> list[tuple[Path, str, str]]:
    """
    Prepare the profiles under readable names in a folder only you can read: checked against their SHA-256, with the
    description rewritten to the name GNOME shows. Returns (staged file, its SHA-256, name in colord's folder).
    """
    files = profile_set(s, internal_panel())
    if not files:
        raise SetupError("no factory profiles are published for this panel")
    STAGE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    staged = []
    for mode, name in files:
        data = icc_with_description(profile_source(name), mode.profile_title)
        icc_check(data)
        path = STAGE_DIR / name
        path.write_bytes(data)
        staged.append((path, sha256_of(data), name))
    return staged


def on_color_profiles(s: System, p: Plan) -> None:
    staged = stage_profiles(s)
    copies = "\n".join(
        f"echo {shlex.quote(digest + '  ' + str(path))} | sha256sum -c --quiet -\n"
        f"cmp -s {shlex.quote(str(path))} {shlex.quote(str(COLORD_STORE / name))} || "
        f"install -m 644 -o colord -g colord {shlex.quote(str(path))} {shlex.quote(str(COLORD_STORE / name))}"
        for path, digest, name in staged)
    # A file that is already there with the same contents is left alone: colord drops a profile when its file is
    # overwritten and does not always read it again. So nothing here ever touches a profile that is already in place.
    p.add_root("Put the profiles in colord's own profile folder, where it reads them reliably",
               "# prepared in your cache folder by this setup: the files published in the repository (the copy in this "
               "checkout,\n"
               f"# or else {RAW_BASE}/src/static/icc-profiles/), checked against the SHA-256 built into the setup, "
               "with the\n"
               "# description rewritten to the name GNOME shows. Root installs them only while their SHA-256 still "
               "matches.\n"
               f"install -d -m 755 -o colord -g colord {shlex.quote(str(COLORD_STORE))}\n{copies}")
    if retired := system_color_copies(s, retired_only=True):
        p.add_root("Remove the DCI-P3 and Display P3 profiles that an earlier version put there",
                   "rm -f -- " + " ".join(shlex.quote(str(path)) for path in retired), early=True)
    p.steps.append(Step("Add the profiles to the Built-in Screen in colord", call=lambda: register_color_profiles(s),
                        shown=register_lines([name for _, _, name in staged])))
    p.note("After switching GPU mode (Hybrid, Integrated, Ultimate), tick this again: each mode has its own display "
           "and its own profile.")


def register_lines(names: list[str]) -> list[str]:
    """What register_color_profiles() amounts to. The object paths are colord's own, known at run time."""
    return ["# quicksetup.py does this itself (register_color_profiles), and it amounts to, with colord's colormgr:",
            "colormgr get-devices-by-kind display   # the Built-in Screen is the display colord marks as embedded",
            *[f"colormgr find-profile-by-filename {COLORD_STORE / name}   # retried for up to 10 seconds"
              for name in names],
            "colormgr device-add-profile <Built-in Screen> <profile>   # each of them, unless the screen lists it",
            "# the factory profile then becomes the default, but only if just the automatic profile was in charge",
            "colormgr device-make-profile-default <Built-in Screen> <factory profile>",
            f"rm -rf {shlex.quote(str(STAGE_DIR))}"]


def release_lines(names: list[str]) -> list[str]:
    """What release_color_profiles() amounts to."""
    return ["# quicksetup.py does this itself (release_color_profiles), and it amounts to:",
            "colormgr device-make-profile-default <Built-in Screen> <automatic profile>   # only if one was active",
            "rm -f " + " ".join(shlex.quote(str(OLD_ICC_DIR / name)) for name in names) + "   # older copies",
            f"rm -rf {shlex.quote(str(STAGE_DIR))}"]


def register_color_profiles(s: System) -> None:
    """Give the built-in screen every profile, so Settings > Color lists them, the way G-Helper lists its modes."""
    colord = Colord()
    device = colord.display_device()
    if device is None:
        raise SetupError("colord does not know the built-in screen. Run this inside the GNOME session.")
    before = colord.profiles(device)
    registered = []
    for mode, name in profile_set(s, internal_panel()):
        path = COLORD_STORE / name
        found = colord.wait_for_profile(path, mode.profile_title)
        if found is None:
            raise SetupError(f"colord did not pick up {path} within 10 seconds")
        registered.append((mode, found))
        # Asked again for every mode: colord changes the display's list as it reads the files.
        if profile_id(path) not in [pid for pid, _ in colord.profiles(device)]:
            colord.add(device, found)
    # Native becomes the active profile, but only when nothing but the automatic EDID profile was in charge.
    active = before[0][1] if before else ""
    if not active or Path(active).name.startswith("edid-"):
        native = next(found for mode, found in registered if mode.key == "native")
        colord.make_default(device, native)
    shutil.rmtree(STAGE_DIR, ignore_errors=True)


def release_color_profiles(s: System) -> None:
    """First half of an undo, as you: hand the screen back to its automatic profile, and drop old copies."""
    colord = Colord()
    device = colord.display_device()
    if device is None:
        raise SetupError("colord does not know the built-in screen. Run this inside the GNOME session.")
    names = [name for _, name in profile_set(s, internal_panel())] + list(RETIRED_PROFILES)
    ours = {pid for pid in (profile_id(COLORD_STORE / name) for name in names) if pid}
    listed = colord.profiles(device)
    if listed and listed[0][0] in ours:
        auto = next((f for _, f in listed if Path(f).name.startswith("edid-")), None)
        automatic = colord.find_profile(Path(auto)) if auto else None
        if automatic:
            colord.make_default(device, automatic)
    for name in names:
        (OLD_ICC_DIR / name).unlink(missing_ok=True)
    shutil.rmtree(STAGE_DIR, ignore_errors=True)


def restore_automatic_profile(s: System) -> None:
    """Last half of an undo: never leave the screen without a profile. Put the automatic one (from EDID) back."""
    colord = Colord()
    device = colord.display_device()
    if device is None or colord.profiles(device):
        return
    edid = next(iter(sorted(OLD_ICC_DIR.glob("edid-*.icc"))), None)
    automatic = colord.find_profile(edid) if edid else None
    if automatic:
        colord.add(device, automatic)
        colord.make_default(device, automatic)


def system_color_copies(s: System, retired_only: bool = False) -> list[Path]:
    """
    Our profiles in colord's own folder, found by title so a copy under another name counts. Root removes them.
    With retired_only, just the ones an earlier version installed for modes that no longer exist.
    """
    titles = set(RETIRED_PROFILES.values())
    if not retired_only:
        titles |= {mode.profile_title for mode, _ in profile_set(s, internal_panel())}
    found = []
    for path in sorted(COLORD_STORE.glob("*.ic*")):
        try:
            if icc_description(path.read_bytes()) in titles:
                found.append(path)
        except OSError:
            continue
    return found


def off_color_profiles(s: System, p: Plan) -> None:
    names = [name for _, name in profile_set(s, internal_panel())] + list(RETIRED_PROFILES)
    p.steps.append(Step("Switch the screen back to its automatic profile and remove older copies",
                        call=lambda: release_color_profiles(s), early=True, shown=release_lines(names)))
    if copies := system_color_copies(s):
        p.add_root("Remove the profiles from colord's own profile folder",
                   "rm -f -- " + " ".join(shlex.quote(str(path)) for path in copies), early=True)
    p.steps.append(Step("Check that the screen kept its automatic profile", call=lambda: restore_automatic_profile(s),
                        shown=["# quicksetup.py does this itself (restore_automatic_profile): a screen left without "
                               "any profile gets its automatic one back"]))


# --- development, applications and virtualization ----------------------------------------------

def check_gh(s: System, result: Check) -> Check:
    if result.state is not State.DONE:
        return result
    if not run(["gh", "auth", "status"]).ok:
        return Check(State.DONE, "installed. Sign in once with: gh auth login")
    return Check(State.DONE, "installed and signed in to GitHub")


def git_config(key: str) -> str:
    return run(["git", "config", "--global", "--get", key]).out.strip()


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


def on_git_signing(s: System, p: Plan) -> None:
    if not git_config("user.signingkey"):
        p.note("Create or import a key in Kleopatra, then run: git config --global user.signingkey <key id>. "
               "Tick this item again afterwards to switch on signing.")
        return
    for key, value in (("commit.gpgsign", "true"), ("tag.gpgsign", "true"), ("gpg.program", "gpg")):
        if git_config(key) != value:
            p.steps.append(Step(f"Set git {key} to {value}", ["git", "config", "--global", key, value]))


def off_git_signing(s: System, p: Plan) -> None:
    for key in ("commit.gpgsign", "tag.gpgsign"):
        if git_config(key) == "true":
            p.steps.append(Step(f"Stop signing: unset git {key}", ["git", "config", "--global", "--unset", key]))
    p.note("Your GPG keys stay where they are. Only git stops signing.")


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


def on_topgrade(s: System, p: Plan) -> None:
    if not TOPGRADE_CONF.exists():
        conf = shlex.quote(str(TOPGRADE_CONF))
        p.steps.append(shell_step("Write ~/.config/topgrade.toml (skip firmware, use paru)",
                                  f"mkdir -p {shlex.quote(str(TOPGRADE_CONF.parent))}\n"
                                  f"[ -e {conf} ] || cat > {conf} <<'ZEPHYRUS_EOF'\n{TOPGRADE_TEXT}ZEPHYRUS_EOF"))


def off_topgrade(s: System, p: Plan) -> None:
    conf = shlex.quote(str(TOPGRADE_CONF))  # one you edited stays
    p.steps.append(shell_step("Remove ~/.config/topgrade.toml if it is still the one this script wrote",
                              f"if cmp -s - {conf} <<'ZEPHYRUS_EOF'\n{TOPGRADE_TEXT}ZEPHYRUS_EOF\n"
                              f"then rm -f {conf}; fi"))


def check_vscode(s: System, result: Check) -> Check:
    if result.state is State.DONE and "code" in s.pacman_installed():
        return Check(State.PARTIAL, "the Microsoft build is installed, and so is Code - OSS: remove it with "
                     "'sudo pacman -R code' (see the guide)")
    return result


def aws_on_blocker(s: System) -> str | None:
    if "aws-cli" in s.pacman_installed():
        return "AWS CLI v1 (aws-cli) is installed and v2 replaces it. Remove v1 first, then tick this again"
    return None


def podman_on_blocker(s: System) -> str | None:
    if "docker" in s.pacman_installed():
        return ("Docker is installed and podman-docker replaces it. Remove Docker yourself first (your images and "
                "volumes stay in /var/lib/docker), then tick this again")
    return None


def plan_localsend(s: System, p: Plan) -> None:
    if s.unit_active("ufw.service"):
        p.add_root("Open the LocalSend port (53317) in ufw",
                   "ufw allow 53317/tcp comment 'LocalSend-App'\nufw allow 53317/udp comment 'LocalSend-App'")


def ufw_forget(*rules: str) -> str:
    """Delete ufw rules again. A rule that is not there is not an error."""
    return "\n".join(f"ufw --force {rule} || true" for rule in rules)


def off_localsend(s: System, p: Plan) -> None:
    if s.unit_active("ufw.service"):
        p.add_root("Close the LocalSend port in ufw again",
                   ufw_forget("delete allow 53317/tcp", "delete allow 53317/udp"), early=True)


def on_podman(s: System, p: Plan) -> None:
    p.add_root("Silence the 'Emulate Docker CLI' notice", "touch /etc/containers/nodocker")
    p.add_root("Let short image names resolve through docker.io and ghcr.io",
               "mkdir -p /etc/containers/registries.conf.d\n"
               "cat > /etc/containers/registries.conf.d/99-zephyrus-search.conf <<'ZEPHYRUS_EOF'\n"
               "unqualified-search-registries = [\"docker.io\", \"ghcr.io\"]\nZEPHYRUS_EOF")


def off_podman(s: System, p: Plan) -> None:
    p.add_root("Remove the Podman settings this script added",
               "rm -f /etc/containers/nodocker /etc/containers/registries.conf.d/99-zephyrus-search.conf", early=True)
    p.note("Your containers, images and volumes stay in your home folder.")


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


def on_kvm(s: System, p: Plan) -> None:
    if not valid_username(s.user):
        raise SetupError(f"'{s.user}' is not a login name this setup is willing to put in a root script")
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


def off_kvm(s: System, p: Plan) -> None:
    p.add_root("Stop libvirt, its default network and take your account out of the libvirt group",
               "virsh net-autostart --disable default || true\n"
               "virsh net-destroy default || true\n"
               "systemctl disable --now libvirtd || true\n"
               f"gpasswd -d {shlex.quote(s.user)} libvirt || true", early=True)
    if s.unit_active("ufw.service"):
        p.add_root("Take the VM rules out of ufw again", ufw_forget(
            "delete allow in on virbr0 to any port 53 proto udp", "delete allow in on virbr0 to any port 67 proto udp",
            "route delete allow in on virbr0", "route delete allow out on virbr0"), early=True)
    p.relogin_for.append("leaving the libvirt group")
    p.note("Your virtual machines and their disks in /var/lib/libvirt stay where they are.")


VIRTIO_ISO = Path("/var/lib/libvirt/images/virtio-win.iso")
VIRTIO_URL = "https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso"


def check_virtio_iso(s: System) -> Check:
    try:
        size = VIRTIO_ISO.stat().st_size
    except OSError:
        return Check(State.TODO, "no VirtIO drivers ISO yet")
    return Check(State.DONE if size > 700_000_000 else State.PARTIAL,
                 f"{size // 1_000_000} MB (a complete download is about 880 MB)")


def on_virtio_iso(s: System, p: Plan) -> None:
    target = VIRTIO_ISO.parent if VIRTIO_ISO.parent.exists() else Path("/var/lib")
    free = shutil.disk_usage(target).free
    if free < 1_300_000_000:
        raise SetupError(f"only {free // 1_000_000} MB is free in {target}, and the ISO needs about 900 MB")
    part = shlex.quote(str(VIRTIO_ISO) + ".part")
    p.add_root("Download the VirtIO drivers ISO (about 880 MB)",
               f"mkdir -p {shlex.quote(str(VIRTIO_ISO.parent))}\n"
               f"curl -fL --proto '=https' -o {part} {shlex.quote(VIRTIO_URL)}\n"
               f"[ \"$(stat -c %s {part})\" -gt 700000000 ] || "
               f"{{ rm -f {part}; echo 'The download is incomplete'; exit 1; }}\n"
               f"mv -f {part} {shlex.quote(str(VIRTIO_ISO))}", network=True)


def off_virtio_iso(s: System, p: Plan) -> None:
    iso, part = shlex.quote(str(VIRTIO_ISO)), shlex.quote(str(VIRTIO_ISO) + ".part")
    p.add_root("Delete the VirtIO drivers ISO", f"rm -f {iso} {part}", early=True)


# Archi has no package. The project publishes a tarball and a SHA-256 for it next to every release, so this is
# pinned to one release and checked, the way the guide does it by hand.
ARCHI_VERSION = "5.10.0"
ARCHI_SHA256 = "f9422455a00a22f5340dc28692ceafe0ad720c8cde839eaafb0fab1cea57287f"
# The project has renamed its release tags before (5.9.0, then 5.10_0, now 5.10) and the file under them stays the
# same. The SHA-256 above is what makes any of them safe, so each spelling is tried, newest first.
ARCHI_TAGS = ("5.10", "5.10_0", "5.10.0")
ARCHI_BASE = "https://github.com/archimatetool/archi.io/releases/download"
ARCHI_URLS = tuple(f"{ARCHI_BASE}/{tag}/Archi-Linux64-{ARCHI_VERSION}.tgz" for tag in ARCHI_TAGS)
ARCHI_DIR = Path("/opt/Archi")


def archi_version() -> str | None:
    for path in sorted((ARCHI_DIR / "plugins").glob("com.archimatetool.editor_*")):
        match = re.match(r"com\.archimatetool\.editor_(\d+\.\d+\.\d+)", path.name)
        if match:
            return match.group(1)
    return None


def check_archi(s: System) -> Check:
    if not (ARCHI_DIR / "Archi").exists():
        return Check(State.TODO, "not in /opt/Archi")
    version = archi_version()
    if version and version != ARCHI_VERSION:
        return Check(State.DONE, f"version {version} is installed (this setup installs {ARCHI_VERSION})")
    return Check(State.DONE, f"version {version or ARCHI_VERSION} in /opt/Archi")


def download_archi() -> Path:
    data = None
    for url in ARCHI_URLS:
        try:
            data = curl_bytes(url, limit=300_000_000)
            break
        except SetupError as exc:
            if "404" not in str(exc):
                raise
            log.warning("archi: %s is gone, trying the next release tag", url)
    if data is None:
        raise SetupError("Archi's download link has moved again. Get the archive from archimatetool.com, "
                         "the guide has the commands to check and install it")
    if sha256_of(data) != ARCHI_SHA256:
        raise SetupError("the Archi download does not match the SHA-256 the project publishes. Not installing it")
    staged, _ = stage_file(f"Archi-Linux64-{ARCHI_VERSION}.tgz", data)
    return staged


def on_archi(s: System, p: Plan) -> None:
    staged = CACHE_DIR / f"Archi-Linux64-{ARCHI_VERSION}.tgz"
    p.steps.append(Step(f"Download Archi {ARCHI_VERSION} (about 180 MB) and check it against the published SHA-256",
                        call=download_archi, early=True, network=True,
                        shown=["# quicksetup.py does this itself (download_archi), and it amounts to:",
                               f"curl -fsSL {ARCHI_URLS[0]} -o {shlex.quote(str(staged))}   # the tags "
                               f"{', '.join(ARCHI_TAGS[1:])} follow when this one is gone",
                               f"echo {shlex.quote(ARCHI_SHA256 + '  ' + str(staged))} | sha256sum -c -"]))
    desktop = ("[Desktop Entry]\nVersion=1.0\nType=Application\nName=Archi\nComment=ArchiMate Modelling Tool\n"
               "Exec=/opt/Archi/Archi\nIcon=__ICON__\nTerminal=false\nCategories=Development;IDE;\n"
               "StartupWMClass=Archi\n")
    p.add_root(f"Install Archi {ARCHI_VERSION} in /opt/Archi, with a launcher and an 'archi' command",
               f"echo {shlex.quote(ARCHI_SHA256 + '  ' + str(staged))} | sha256sum -c --quiet -\n"
               f"rm -rf /opt/Archi\ntar -xzf {shlex.quote(str(staged))} -C /opt\n"
               "ln -sfn /opt/Archi/Archi /usr/local/bin/archi\n"
               "icon=$(find /opt/Archi/plugins -name app-128.png | head -1)\n"
               f"printf %s {shlex.quote(desktop)} | sed \"s|__ICON__|$icon|\" > /usr/share/applications/archi.desktop")
    p.steps.append(Step("Remove the downloaded archive", ["rm", "-f", str(staged)]))


def off_archi(s: System, p: Plan) -> None:
    p.add_root("Remove Archi, its launcher and the 'archi' command",
               "rm -rf /opt/Archi\n"
               "[ \"$(readlink /usr/local/bin/archi)\" = /opt/Archi/Archi ] && rm -f /usr/local/bin/archi\n"
               "rm -f /usr/share/applications/archi.desktop", early=True)
    p.note("Archi's models and settings in your home folder stay.")


# VMware builds kernel modules, so it needs the headers of the kernel you run and DKMS next to the AUR package.
def vmware_headers(s: System) -> str | None:
    base = s.kernel_package()
    return f"{base}-headers" if base else None


def check_vmware(s: System) -> Check:
    if not s.is_arch:
        return Check(State.UNKNOWN, "package check needs an Arch-based system")
    if "vmware-workstation" not in s.pacman_installed():
        return Check(State.TODO, "not installed")
    parts = []
    if s.unit_state("vmware-networks.service") != "enabled":
        parts.append("the vmware-networks service is not enabled")
    if "vmmon" not in read_text(Path("/proc/modules")):
        parts.append("the vmmon module is not loaded (reboot, or see the guide)")
    if parts:
        return Check(State.PARTIAL, "installed, but " + " and ".join(parts))
    return Check(State.DONE, "installed and running")


def on_vmware(s: System, p: Plan) -> None:
    if "vmware-workstation" not in s.pacman_installed():
        p.add_aur(["vmware-workstation"])
    headers = vmware_headers(s)
    wanted = ["dkms"] + ([headers] if headers else [])
    p.add_pacman([x for x in wanted if x not in s.pacman_installed()])
    if headers is None:
        p.note("Could not tell which kernel package you run, so no kernel headers are added. Install the headers "
               "that match your kernel yourself, or the vmmon and vmnet modules will not build.")
    p.steps.append(Step("Enable the VMware networking service (one more password prompt)",
                        ["pkexec", "systemctl", "enable", "--now", "vmware-networks.service"],
                        when=lambda: s.unit_state("vmware-networks.service") not in ("not-found", "enabled")))
    p.reboot_for.append("VMware's kernel modules (vmmon, vmnet)")


def off_vmware(s: System, p: Plan) -> None:
    p.add_root("Stop the VMware services", "systemctl disable --now vmware-networks.service || true\n"
               "systemctl disable --now vmware.service || true", early=True)
    p.add_remove(["vmware-workstation"] if "vmware-workstation" in s.pacman_installed() else [], [])
    p.note("DKMS and the kernel headers stay: other kernel modules (NVIDIA) use them. Your virtual machines stay.")


VMWARE_GRABS = (("org.gnome.mutter.wayland", "xwayland-allow-grabs", "true"),
                ("org.gnome.mutter.wayland", "xwayland-grab-access-rules", "['vmware', 'vmware-vmx']"))


def check_vmware_keyboard(s: System) -> Check:
    values = [normalise(s.gsettings(schema, key)) == normalise(value) for schema, key, value in VMWARE_GRABS]
    if all(values):
        return Check(State.DONE, "XWayland keyboard grabs are allowed for VMware")
    return Check(State.PARTIAL if any(values) else State.TODO, "not set")


def on_vmware_keyboard(s: System, p: Plan) -> None:
    for schema, key, value in VMWARE_GRABS:
        p.steps.append(gsettings_step(schema, key, value, f"Set {key}"))
    p.relogin_for.append("the VMware keyboard fix")


def off_vmware_keyboard(s: System, p: Plan) -> None:
    for schema, key, _ in VMWARE_GRABS:
        p.steps.append(gsettings_reset(schema, key, f"Reset {key}"))
    p.relogin_for.append("undoing the VMware keyboard fix")


# --- the catalogue -------------------------------------------------------------------------------

SECTIONS = [
    ("hardware", "ASUS hardware", "computer-symbolic", "asusctl, battery limit, power profiles, brightness"),
    ("gpu", "Graphics", "preferences-system-symbolic", "NVIDIA services, PRIME offload, display freezes"),
    ("display", "Display", "video-display-symbolic", "color modes and the factory color profiles"),
    ("network", "Network", "network-wireless-symbolic", "Wi-Fi tuning, eduroam"),
    ("desktop", "GNOME desktop", "preferences-desktop-appearance-symbolic",
     "window buttons, shortcuts, extensions, touchpad"),
    ("security", "Security and login", "system-lock-screen-symbolic", "autologin, YubiKey, Secure Boot"),
    ("dev", "Development", "utilities-terminal-symbolic", "git, signing, editors, cloud tools"),
    ("apps", "Applications", "view-app-grid-symbolic", "browser, messaging, office, utilities"),
    ("gaming", "Gaming", "applications-games-symbolic", "Steam, Proton tools, overlays"),
    ("virt", "Virtual machines and containers", "drive-multidisk-symbolic", "KVM, Podman, Distrobox, Windows apps"),
]


def build_items(catalog: ExtensionCatalog) -> list[Item]:
    items: list[Item] = []
    add = items.append
    asus_doc = "hardware/asusctl-rog-control"
    apps = "applications/"
    dev = apps + "development"
    prod = apps + "productivity"
    util = apps + "utilities"
    virt = "virtualization/"

    # ASUS hardware
    add(package_item("asus-tools", "hardware", "asusctl and ROG Control Center",
                     "The daemon, command line and window behind fan curves, profiles and the Slash LED", asus_doc,
                     group="Tools", pacman=("asusctl", "rog-control-center"), recommended=True, hardware="asus"))
    add(package_item("asus-monitoring", "hardware", "Hardware monitoring tools",
                     "nvtop, powertop, s-tui, lm_sensors and i2c-tools", asus_doc, group="Tools",
                     pacman=("nvtop", "powertop", "s-tui", "lm_sensors", "i2c-tools")))
    add(Item("asus-battery-limit", "hardware", "Battery charge limit of 80%",
             "Stops charging at 80% so the battery lasts longer", asus_doc, check_battery_limit, on_battery_limit,
             off_battery_limit, group="Settings", requires=("asus-tools",), recommended=True, hardware="asus"))
    add(Item("asus-slash", "hardware", "Slash LED on AC only",
             "The light bar on the lid: off on battery and during sleep", asus_doc, check_slash, on_slash, off_slash,
             group="Settings", requires=("asus-tools",), hardware="asus"))
    add(Item("asus-ppd-mask", "hardware", "Let asusd own the power profiles",
             "Masks power-profiles-daemon, which fights asusd over the same interface", asus_doc, check_ppd, on_ppd,
             off_ppd, group="Settings", off_blocker=ppd_off_blocker, recommended=True, hardware="asus"))
    add(Item("backlight-fix", "hardware", "Brightness in every GPU mode",
             "Without it brightness is dead in Integrated mode (kernel parameter and modprobe rule). Needs a reboot",
             "known-issues", check_backlight, on_backlight, off_backlight, group="Fixes",
             manual=lambda s: BACKLIGHT_MANUAL.get(s.bootloader(), []), recommended=True, hardware="g16"))

    # Graphics
    add(Item("nvidia-power-services", "gpu", "NVIDIA suspend and resume services",
             "Only for a driver that does not save video memory itself. nvidia-open already does, so not there",
             "cachyos/nvidia", check_nvidia_services, on_nvidia_services, off_nvidia_services, group="NVIDIA",
             recommended=True, hardware="nvidia"))
    add(Item("nvidia-powerd", "gpu", "NVIDIA Dynamic Boost (nvidia-powerd)",
             "Shifts the power budget between CPU and GPU. The firmware decides if it does anything, so it is optional",
             "cachyos/nvidia#nvidia-powerd-dynamic-boost", check_nvidia_powerd, on_nvidia_powerd, off_nvidia_powerd,
             group="NVIDIA", hardware="nvidia"))
    add(package_item("nvidia-prime", "gpu", "prime-run", "Runs a program on the RTX 4060 instead of the iGPU",
                     "gaming/proton-slr#making-sure-the-rtx-4060-is-doing-the-work", group="NVIDIA",
                     pacman=("nvidia-prime",), recommended=True, hardware="nvidia"))
    add(Item("amdgpu-psr", "gpu", "Disable AMD Panel Self Refresh",
             "Only if the system still freezes with an external monitor over USB-C or Thunderbolt. The bug was mostly "
             "on kernels 6.15 to 6.18", "known-issues", check_psr, group="AMD",
             manual=lambda s: PSR_MANUAL.get(s.bootloader(), []),
             manual_off=lambda s: [step.replace("Add ", "Remove ").replace(" to ", " from ")
                                   for step in PSR_MANUAL.get(s.bootloader(), [])],
             advanced=True, hardware="g16", guide_only=True))

    # Display: the live color modes have a page of their own, the profiles are an item
    add(Item("display-color-profiles", "display", "ASUS color profiles",
             "The panel's factory profile and the ASUS sRGB profile, on the built-in screen "
             "in colord, for color-managed apps", "hardware/color-profiles", check_color_profiles, on_color_profiles,
             off_color_profiles, group="Color profiles", recommended=True, hardware="g16", needs_gnome=True))

    # Network
    add(Item("wifi-mt7925", "network", "Wi-Fi throughput tuning (MT7925)",
             "No PCIe ASPM, no Wi-Fi power saving, a bigger AQL queue: about double the speed",
             MT7925_GUIDE, check_mt7925, on_mt7925, off_mt7925,
             group="Wi-Fi", recommended=True, hardware="mt7925"))
    add(Item("eduroam-saxion", "network", "eduroam at Saxion",
             "Connects to eduroam with the right pinned certificates. Saxion only",
             EDUROAM_GUIDE, check_eduroam, on_eduroam, off_eduroam, group="Campus"))

    # GNOME desktop
    add(Item("gnome-window-buttons", "desktop", "Minimize and maximize buttons",
             "GNOME only shows the close button by default",
             apps + "#gnome-window-buttons-adding-minimize--maximize-back",
             lambda s: gsettings_check(s, WM_PREFS, "button-layout", "'appmenu:minimize,maximize,close'",
                                       "minimize, maximize and close are shown"),
             lambda s, p: p.steps.append(gsettings_step(WM_PREFS, "button-layout", "appmenu:minimize,maximize,close",
                                                        "Show minimize and maximize buttons")),
             lambda s, p: p.steps.append(gsettings_reset(WM_PREFS, "button-layout", "Reset the window button layout")),
             group="Window behavior", recommended=True, needs_gnome=True))
    add(Item("gnome-focus", "desktop", "New windows come to the front",
             "focus-new-windows 'smart'. Works best together with the Just Perfection extension",
             apps + "#gnome-window-focus-apps-opening-in-the-background",
             lambda s: gsettings_check(s, WM_PREFS, "focus-new-windows", "'smart'", "new windows get focus"),
             lambda s, p: p.steps.append(gsettings_step(WM_PREFS, "focus-new-windows", "smart",
                                                        "Let GNOME bring new windows to the front")),
             lambda s, p: p.steps.append(gsettings_reset(WM_PREFS, "focus-new-windows",
                                                         "Reset how new windows get focus")),
             group="Window behavior",
             manual=["Also turn on 'Window Demands Attention Focus' in the Just Perfection extension (Behavior tab): "
                     "the setting alone is not enough for apps without XDG Activation."],
             recommended=True, needs_gnome=True))
    add(Item("gnome-shortcuts", "desktop", "Windows-like shortcuts",
             "Super+D, Shift+Super+S, Shift+Super+R, Super+I and Super+E",
             apps + "#gnome-keyboard-shortcuts-making-it-feel-more-like-windows", check_shortcuts, on_shortcuts,
             off_shortcuts, group="Keyboard", needs_gnome=True))
    add(Item("gnome-smile-shortcut", "desktop", "Copilot key opens the emoji picker",
             "Uses the Copilot key as the shortcut for Smile", util + "#smile-emoji-picker", check_smile_shortcut,
             on_smile_shortcut, off_smile_shortcut, group="Keyboard", requires=("smile",),
             manual=["If the key does not trigger Smile, set the shortcut yourself: Settings > Keyboard > Custom "
                     "Shortcuts, command 'flatpak run it.mijorus.smile', then press the Copilot key."],
             needs_gnome=True))
    add(Item("wsf", "desktop", "Touchpad scroll speed",
             "wayland-scroll-factor: GNOME has no setting for it", "desktop/touchpad-scroll-speed", check_wsf,
             on_wsf, off_wsf, group="Touchpad", recommended=True, needs_gnome=True, aur=("wayland-scroll-factor",)))
    add(package_item("gnome-extension-manager", "desktop", "Extension Manager",
                     "Install and manage GNOME Shell extensions without a browser add-on", "desktop/gnome-extensions",
                     group="Extensions", pacman=("extension-manager",), recommended=True, needs_gnome=True))
    for spec in EXTENSIONS:
        add(extension_item(spec, catalog))
    add(package_item("astra-monitor-deps", "desktop", "Astra Monitor extras",
                     "libgtop, amdgpu_top and nethogs for more accurate readouts", "desktop/astra-monitor",
                     group="Extensions", pacman=("libgtop", "amdgpu_top", "nethogs"), needs_gnome=True,
                     keep=("libgtop",)))

    # Security and login
    add(Item("gdm-autologin", "security", "Skip the login screen after the disk unlock",
             "One password at boot (LUKS), then straight to the desktop. The lock screen still asks",
             "security/autologin", check_autologin, on_autologin, off_autologin, group="Login", needs_gnome=True))
    add(Item("yubikey-tools", "security", "YubiKey tools",
             "pam-u2f, the smart card daemon and Yubico Authenticator", "security/yubikey", check_yubikey,
             on_yubikey, off_yubikey, group="Hardware keys", off_blocker=yubikey_off_blocker, advanced=True))
    add(Item("yubikey-key", "security", "Register your YubiKey",
             "Plug it in and touch it when it blinks. It is saved for your account and nothing else changes",
             "security/yubikey#pam-u2f", check_yubikey_key, on_yubikey_key, off_yubikey_key, group="Hardware keys",
             requires=("yubikey-tools",), advanced=True))
    add(Item("yubikey-spare", "security", "Register a spare YubiKey",
             "A second key for the same account, for the day the first one is lost. Optional",
             "security/yubikey#pam-u2f", check_yubikey_spare, on_yubikey_spare, off_yubikey_spare,
             group="Hardware keys", requires=("yubikey-key",), advanced=True))
    add(Item("yubikey-pam", "security", "YubiKey for sudo and the lock screen",
             "A touch replaces typing the password, also in the graphical sudo prompt. Without the key the password "
             "still works", "security/yubikey#wiring-it-into-pam", check_yubikey_pam, on_yubikey_pam,
             off_yubikey_pam, group="Hardware keys", requires=("yubikey-key",), advanced=True,
             manual=["Open a second terminal and run: sudo true. Touch the key when it blinks. Keep the first terminal "
                     "open until that works",
                     "Lock the screen with Super+L and touch the key to unlock it"]))
    add(package_item("sbctl", "security", "sbctl", "The tool that creates and enrolls your own Secure Boot keys",
                     "cachyos/secure-boot", group="Secure Boot", pacman=("sbctl",), advanced=True,
                     off_blocker=sbctl_off_blocker))
    add(Item("secure-boot", "security", "Secure Boot with your own keys",
             "Keys, firmware setup and signing the boot files: a mistake can stop the machine from booting, so it "
             "stays manual", "cachyos/secure-boot", check_secure_boot, group="Secure Boot", guide_only=True,
             advanced=True,
             manual=["Reboot into the ASUS UEFI (systemctl reboot --firmware-setup) and put Secure Boot in Setup Mode",
                     "sudo sbctl create-keys", "sudo sbctl enroll-keys --microsoft",
                     "Sign the boot files: sbctl-batch-sign for systemd-boot, limine-enroll-config and limine-update "
                     "for Limine",
                     "Enable Secure Boot in the UEFI again, then check with: sudo sbctl status"],
             manual_off=["Reboot into the ASUS UEFI (systemctl reboot --firmware-setup) and set Secure Boot Control "
                         + "to Disabled, under Security > Secure Boot. The machine boots as before",
                         "Optional: your own keys do no harm while Secure Boot is off. Put the firmware's default keys "
                         + "back under Key Management only if you want them gone",
                         "Optional: untick sbctl in this window to remove the tool and its pacman hook, which "
                         + "re-signs new kernels"]))

    # Development
    add(package_item("git-github-cli", "dev", "Git and GitHub CLI", "git plus gh for pull requests and issues",
                     dev + "#git--github-cli", group="Git", pacman=("git", "github-cli"), recommended=True,
                     extra_check=check_gh, keep=("git",)))
    add(package_item("git-gpg-signing", "dev", "Kleopatra and GPG commit signing",
                     "Sign commits and tags with your GPG key", dev + "#kleopatra--gpg-commit-signing", group="Git",
                     pacman=("kleopatra",), recommended=True, extra_check=check_git_signing, extra_on=on_git_signing,
                     extra_off=off_git_signing))
    add(package_item("github-desktop", "dev", "GitHub Desktop", "The standard Linux port of the official app",
                     dev + "#github-desktop", group="Git", pacman=("github-desktop",)))
    add(package_item("desktop-plus", "dev", "Desktop Plus", "A GitHub Desktop fork with more features, from the AUR",
                     dev + "#github-desktop", group="Git", aur=("desktop-plus-bin",)))
    add(package_item("vscode", "dev", "Visual Studio Code (Microsoft build)",
                     "The official binary with the Microsoft marketplace, from the AUR", dev + "#visual-studio-code",
                     group="Editors", aur=("visual-studio-code-bin",), extra_check=check_vscode,
                     conflicts=("vscode-oss",)))
    add(package_item("vscode-oss", "dev", "Code - OSS", "The open source build, with the Open VSX marketplace",
                     dev + "#visual-studio-code", group="Editors", pacman=("code",), conflicts=("vscode",)))
    add(package_item("vscodium", "dev", "VSCodium", "A community build of the same source, from the CachyOS repository",
                     dev + "#visual-studio-code", group="Editors", pacman=("vscodium",)))
    add(package_item("aws-cli", "dev", "AWS CLI v2", "The aws command", dev + "#aws-cli", group="Tools",
                     pacman=("aws-cli-v2",), on_blocker=aws_on_blocker,
                     manual=("Sign in: aws configure sso (or aws configure)",)))
    add(package_item("topgrade", "dev", "Topgrade", "Updates pacman, the AUR, Flatpaks and more in one command",
                     "cachyos/updates", group="Tools", aur=("topgrade",), extra_check=check_topgrade,
                     extra_on=on_topgrade, extra_off=off_topgrade))
    add(Item("archi", "dev", "Archi (ArchiMate)",
             f"Version {ARCHI_VERSION} from the project, checked against its published SHA-256, in /opt/Archi",
             dev + "#archi-archimate-modeling-tool", check_archi, on_archi, off_archi, group="Tools"))

    # Applications
    add(package_item("brave-origin", "apps", "Brave Origin", "The lighter Brave, from the CachyOS repository",
                     apps + "browser", group="Browsers", pacman=("brave-origin-bin",)))
    add(package_item("brave", "apps", "Brave", "The regular Brave with its full feature set", apps + "browser",
                     group="Browsers", pacman=("brave-bin",)))
    add(package_item("signal", "apps", "Signal", "Signal Messenger, the native package", prod + "#signal-messenger",
                     group="Communication", pacman=("signal-desktop",)))
    add(package_item("proton-mail", "apps", "Proton Mail", "The desktop app, a native package", prod + "#proton-mail",
                     group="Communication", pacman=("proton-mail-bin",)))
    add(package_item("standard-notes", "apps", "Standard Notes", "End-to-end encrypted notes, from Flathub",
                     prod + "#standard-notes", group="Notes and passwords",
                     flatpak=("org.standardnotes.standardnotes",)))
    add(package_item("bitwarden", "apps", "Bitwarden", "Password manager, from Flathub", prod + "#password-manager",
                     group="Notes and passwords", flatpak=("com.bitwarden.desktop",)))
    add(package_item("proton-pass", "apps", "Proton Pass", "Password manager, the native package",
                     prod + "#password-manager", group="Notes and passwords", pacman=("proton-pass",)))
    add(package_item("onlyoffice", "apps", "OnlyOffice", "The closest thing to Microsoft 365", prod + "#onlyoffice",
                     group="Office", pacman=("onlyoffice-bin",)))
    add(package_item("libreoffice", "apps", "LibreOffice Fresh", "Built-in APA references", prod + "#libreoffice",
                     group="Office", pacman=("libreoffice-fresh",)))
    add(package_item("calibre", "apps", "Calibre", "E-book library and e-reader manager, for a Kobo for example",
                     util + "#calibre-e-book-library", group="Office", pacman=("calibre",)))
    add(package_item("smile", "apps", "Smile", "Emoji picker", util + "#smile-emoji-picker", group="Utilities",
                     flatpak=(SMILE_ID,), needs_gnome=True))
    add(package_item("solaar", "apps", "Solaar", "Manages Logitech keyboards and mice",
                     util + "#solaar-for-logitech-devices", group="Utilities", pacman=("solaar",)))
    add(package_item("localsend", "apps", "LocalSend", "Send files between your phone and the laptop",
                     util + "#localsend", group="Utilities", pacman=("localsend",), extra_on=plan_localsend,
                     extra_off=off_localsend))
    add(package_item("mission-center", "apps", "Mission Center", "A GNOME-native task manager",
                     util + "#mission-center-gnome-native-task-manager", group="Utilities",
                     flatpak=("io.missioncenter.MissionCenter",)))
    add(package_item("tmog", "apps", "AppImage support for TMOG",
                     "fuse2 for AppImages. Download TMOG itself from tmog.org",
                     util + "#tmog-dave-plummers-task-manager", group="Utilities", pacman=("fuse2",),
                     manual=("Download the AppImage from tmog.org, then chmod +x and run it",)))
    add(package_item("high-tide", "apps", "High Tide", "A native GTK4 Tidal client, from Flathub",
                     apps + "gaming-media#tidal", group="Music", flatpak=("io.github.nokse22.high-tide",)))
    add(package_item("tidal-hifi", "apps", "Tidal Hi-Fi", "The Tidal web player as a desktop app, from Flathub",
                     apps + "gaming-media#tidal-hi-fi", group="Music", flatpak=("com.mastermindzh.tidal-hifi",)))
    add(package_item("bottles", "apps", "Bottles", "Windows software through Wine, Flathub only",
                     apps + "gaming-media#bottles-running-windows-software", group="Windows software",
                     flatpak=("com.usebottles.bottles",)))

    # Gaming
    add(package_item("steam", "gaming", "Steam", "Steam with Proton included", apps + "gaming-media#steam",
                     pacman=("steam",)))
    add(package_item("gaming-tools", "gaming", "gamescope, MangoHud and GameMode",
                     "The launch options the Proton guide uses", "gaming/proton-slr#launch-options-worth-knowing",
                     pacman=("gamescope", "mangohud", "gamemode", "lib32-gamemode")))
    add(package_item("protonup-qt", "gaming", "ProtonUp-Qt",
                     "Installs Proton-GE for games Valve's builds struggle with",
                     "gaming/proton-slr#proton-ge", flatpak=("net.davidotek.pupgui2",)))

    # Virtual machines and containers
    add(package_item("kvm", "virt", "virt-manager and KVM", "A Windows 11 VM with VirtIO and SPICE", virt + "vm-setup",
                     group="Virtual machines", pacman=("virt-manager", "qemu-full", "swtpm", "edk2-ovmf", "dnsmasq"),
                     extra_check=check_kvm, extra_on=on_kvm, extra_off=off_kvm, keep=("dnsmasq",)))
    add(Item("virtio-iso", "virt", "VirtIO drivers ISO", "The Windows guest drivers, about 880 MB", virt + "vm-setup",
             check_virtio_iso, on_virtio_iso, off_virtio_iso, group="Virtual machines", requires=("kvm",)))
    add(package_item("quickemu", "virt", "Quickemu", "Throwaway VMs in two commands", virt + "quickemu",
                     group="Virtual machines", aur=("quickemu",)))
    add(package_item("winboat", "virt", "WinBoat",
                     "Windows apps as windows on your desktop (beta). Needs Podman or Docker",
                     virt + "winboat", group="Virtual machines", pacman=("winboat",)))
    add(Item("vmware", "virt", "VMware Workstation",
             "Best VM performance. Builds kernel modules, so it needs DKMS and your kernel's headers",
             virt + "vmware-workstation", check_vmware, on_vmware, off_vmware, group="Virtual machines",
             advanced=True, aur=("vmware-workstation",)))
    add(Item("vmware-keyboard", "virt", "VMware keyboard fix for GNOME Wayland",
             "Lets VMware grab the keyboard through XWayland. Needed on GNOME 49, untested on newer",
             virt + "vmware-workstation#gnome-49-wayland-keyboard-grab", check_vmware_keyboard, on_vmware_keyboard,
             off_vmware_keyboard, group="Virtual machines", requires=("vmware",), advanced=True, needs_gnome=True))
    add(package_item("podman", "virt", "Podman and Podman Desktop", "Rootless containers with a docker-compatible CLI",
                     apps + "development#podman--podman-desktop", group="Containers",
                     pacman=("podman", "podman-docker", "podman-desktop"), extra_check=check_podman,
                     extra_on=on_podman, extra_off=off_podman, on_blocker=podman_on_blocker))
    add(package_item("distrobox", "virt", "Distrobox", "Another distribution's userspace, integrated with your session",
                     virt + "distrobox", group="Containers", pacman=("distrobox", "podman"), keep=("podman",)))

    ids = [item.id for item in items]
    if len(ids) != len(set(ids)):
        raise RuntimeError("the catalog has duplicate item ids")
    for item in items:
        for other in (*item.requires, *item.conflicts):
            if other not in ids:
                raise RuntimeError(f"{item.id} refers to unknown item {other}")
    return items


# --- terminal windows: for what needs your input ----------------------------------------------
#
# paru shows each PKGBUILD for review and asks for your sudo password, and a few scripts ask for a login. They get
# a terminal window of their own. A small wrapper writes the exit code to a file when it is done, so this does not
# depend on how the terminal behaves (some fork into a server and return at once).

TERMINAL_PREFERENCE = ("ptyxis", "gnome-terminal", "kgx", "konsole", "xfce4-terminal", "alacritty", "kitty", "foot",
                       "wezterm", "xterm")
# How to say "run this program" to terminals whose desktop entry does not say it (X-TerminalArgExec).
TERMINAL_EXEC_ARGS = {
    "ptyxis": ["-x"], "gnome-terminal": ["--wait", "--"], "kgx": ["-e"], "konsole": ["--nofork", "-e"],
    "xfce4-terminal": ["--disable-server", "-x"], "alacritty": ["-e"], "kitty": [], "foot": [],
    "wezterm": ["start", "--"], "xterm": ["-e"],
}


def terminal_candidates() -> list[list[str]]:
    """The terminal emulators on this machine, each as the start of a command line that runs one more program."""
    data_dirs = [Path.home() / ".local" / "share", *(Path(d) for d in
                 os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":") if d)]
    declared: dict[str, list[str]] = {}
    for folder in data_dirs:
        for desktop in sorted((folder / "applications").glob("*.desktop")):
            text = read_text(desktop)
            if "TerminalEmulator" not in text:
                continue
            exec_line = re.search(r"^Exec=(.+)$", text, re.MULTILINE)
            try:
                binary = shlex.split(exec_line.group(1))[0] if exec_line else ""
            except ValueError:
                continue
            binary = Path(binary).name
            arg = re.search(r"^X-TerminalArgExec=(.*)$", text, re.MULTILINE)
            if binary and shutil.which(binary) and binary not in declared:
                declared[binary] = shlex.split(arg.group(1)) if arg and arg.group(1).strip() else []
    candidates = []
    for binary in [*TERMINAL_PREFERENCE, *sorted(set(declared) - set(TERMINAL_PREFERENCE))]:
        if not shutil.which(binary):
            continue
        # the program's own table first: gnome-terminal needs --wait to stay in the foreground, for example
        args = TERMINAL_EXEC_ARGS.get(binary) if binary in TERMINAL_EXEC_ARGS else declared.get(binary) or ["-e"]
        candidates.append([binary, *args])
    return candidates


WRAPPER = """#!/usr/bin/env bash
status={status}
finish() {{ printf '%s' "$1" > "$status.tmp" && mv -f "$status.tmp" "$status"; }}
trap 'finish 129; exit 129' HUP TERM
echo {title}
echo
{command}
code=$?
finish "$code"
echo
if [ "$code" -eq 0 ]; then
    echo "Done. You can close this window."
else
    echo "That did not work (exit code $code). Read the messages above."
fi
read -r -p "Press Enter to close this window. " _
exit "$code"
"""


def run_in_terminal(argv: list[str], title: str, stop: Callable[[], bool]) -> int | None:
    """
    Run a program in a terminal window and return its exit code, or None when no terminal could be opened or the
    caller stopped waiting. Blocks, so call it from a worker thread.
    """
    candidates = terminal_candidates()
    if not candidates:
        return None
    CACHE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    work = Path(tempfile.mkdtemp(prefix="terminal-", dir=CACHE_DIR))
    try:
        status = work / "status"
        script = work / "run.sh"
        script.write_text(WRAPPER.format(status=shlex.quote(str(status)), title=shlex.quote(title),
                                         command=shlex.join(argv)), encoding="utf-8")
        script.chmod(0o700)
        for terminal in candidates:
            log.info("terminal: %s", shlex.join([*terminal, str(script)]))
            try:
                # The terminal comes from the desktop entries of this user's own session, so there is no
                # privilege boundary to cross here (semgrep: dangerous-subprocess-use-tainted-env-args).
                # nosemgrep
                proc = subprocess.Popen([*terminal, str(script)], stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        start_new_session=True)
            except OSError as exc:
                log.warning("could not start %s: %s", terminal[0], exc)
                continue
            started = time.monotonic()
            while True:
                if status.exists():
                    text = read_text(status)
                    return int(text) if text.lstrip("-").isdigit() else 1
                if stop():
                    return None
                exited = proc.poll()
                # A terminal that fails to open at all exits at once with an error. One that forks into a server
                # exits at once with 0, and the window is still there: keep waiting for the status file then.
                if exited not in (None, 0) and time.monotonic() - started < 6:
                    log.warning("%s exited with %s straight away, trying the next terminal", terminal[0], exited)
                    break
                time.sleep(0.4)
        return None
    finally:
        shutil.rmtree(work, ignore_errors=True)


# --- the root script ---------------------------------------------------------------------------

ROOT_HEADER = """set -uo pipefail
failed=()
run_step() {
  echo "==> $1"
  bash -euo pipefail -c "$2"
  local code=$?
  if [ "$code" -ne 0 ]; then echo "[FAILED] $1 (exit code $code)"; failed+=("$1"); fi
  return 0
}
"""


def root_script(plan: Plan) -> str:
    """
    Everything that needs root for one run, as one script for one pkexec call. Order: snippets that stop things
    first, then installs, then the snippets that need the new packages, then removals. A failing snippet is reported
    and the rest goes on; a failing install stops the script, because what comes after may need those packages.
    """
    lines = [ROOT_HEADER]
    for snippet in plan.root_early:
        lines.append(f"run_step {shlex.quote(snippet.desc)} {shlex.quote(snippet.script)}")
    if plan.pacman:
        lines.append(f"echo {shlex.quote('==> pacman: installing ' + ', '.join(plan.pacman))}")
        lines.append(f"if ! {shlex.join([*PACMAN_INSTALL, *plan.pacman])}; then\n"
                     "  echo '[FAILED] pacman could not install the packages. Nothing after this step was run.'\n"
                     "  echo 'If it says a package was not found or a download failed (404), update the system first "
                     "with: sudo pacman -Syu'\n  exit 1\nfi")
    for snippet in plan.root:
        lines.append(f"run_step {shlex.quote(snippet.desc)} {shlex.quote(snippet.script)}")
    if plan.remove_pacman:
        names = " ".join(shlex.quote(p) for p in plan.remove_pacman)
        lines.append(f"echo {shlex.quote('==> pacman: removing ' + ', '.join(plan.remove_pacman))}")
        lines.append(f'for pkg in {names}; do\n'
                     f'  if {shlex.join(PACMAN_REMOVE)} "$pkg"; then echo "removed $pkg";\n'
                     '  else echo "kept $pkg: something else still needs it"; fi\ndone')
    lines.append('if [ "${#failed[@]}" -gt 0 ]; then\n  echo\n  echo "These steps failed:"\n'
                 '  printf " - %s\\n" "${failed[@]}"\n  exit 1\nfi')
    return "\n".join(lines) + "\n"


PKEXEC_CODES = {126: "the password prompt was dismissed, or you are not allowed to run this as root",
                127: "authentication failed"}


# --- planning ---------------------------------------------------------------------------------------

@dataclass
class Built:
    """A plan for a set of changes, plus everything the person should hear before saying yes."""
    plan: Plan = field(default_factory=Plan)
    turn_on: list[Item] = field(default_factory=list)
    turn_off: list[Item] = field(default_factory=list)
    included: list[str] = field(default_factory=list)       # items added because another one needs them
    blockers: list[str] = field(default_factory=list)       # reasons this cannot run
    warnings: list[str] = field(default_factory=list)       # things to know, not reasons to stop
    skipped: list[str] = field(default_factory=list)
    manual: list[tuple[str, list[str]]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.blockers


@dataclass(frozen=True)
class Command:
    """One piece of a run, written the way a shell would show it. The review and the site list a run this way."""
    phase: str      # when in the run it happens, a key of PHASE_TITLES
    who: str        # root, terminal (you, in a terminal window) or you
    desc: str       # what it is for, one line
    text: str       # the command or commands, as many lines as it takes
    diff: str = ""  # for a file that gets edited: the change, as a unified diff


PHASE_TITLES = {
    "early": "As you, first",
    "root": "As root, one password prompt for all of it",
    "aur": "As you, in a terminal window",
    "flatpak": "As you, from Flathub",
    "steps": "As you",
}


def plan_commands(plan: Plan) -> list[Command]:
    """
    Everything a run does, as the commands themselves, in the order they run (Executor.run does it in this order).
    The package manager lines come from the same constants as root_script() and the Executor, so this listing cannot
    say one thing while the run does another.
    """
    def step_command(phase: str, step: Step) -> Command:
        return Command(phase, "terminal" if step.interactive else "you", step.desc, "\n".join(step.commands()))

    def snippet_command(snippet: Snippet) -> Command:
        return Command("root", "root", snippet.desc, snippet.script, snippet.diff)

    commands = [step_command("early", step) for step in plan.steps if step.early]
    commands += [snippet_command(snippet) for snippet in plan.root_early]
    if plan.pacman:
        commands.append(Command("root", "root", "Install packages from the repositories",
                                shell_line([*PACMAN_INSTALL, *plan.pacman])))
    commands += [snippet_command(snippet) for snippet in plan.root]
    if plan.remove_pacman:
        removals = "\n".join(shell_line([*PACMAN_REMOVE, name]) for name in plan.remove_pacman)
        commands.append(Command("root", "root",
                                "Remove packages, one at a time (one that something else still needs is kept)",
                                removals))
    if plan.aur:
        commands.append(Command("aur", "terminal",
                                "Install from the AUR: paru shows each PKGBUILD, and you read it before it builds",
                                shell_line([*PARU_INSTALL, *plan.aur])))
    if plan.flatpak:
        commands.append(Command("flatpak", "you", "Install from Flathub",
                                shell_line([*FLATPAK_INSTALL, *plan.flatpak])))
    if plan.remove_flatpak:
        commands.append(Command("flatpak", "you", "Remove Flatpaks",
                                shell_line([*FLATPAK_REMOVE, *plan.remove_flatpak])))
    commands += [step_command("steps", step) for step in plan.steps if not step.early]
    return commands


def render_plan(plan: Plan) -> str:
    """The plan as plain text, grouped by when it runs: every command a run would start, in full."""
    commands, lines = plan_commands(plan), []
    for phase, title in PHASE_TITLES.items():
        group = [command for command in commands if command.phase == phase]
        if group:
            lines += [f"{title}:", ""]
        for command in group:
            lines.append(f"  # {command.desc}")
            lines += [f"  {line}".rstrip() for line in command.text.splitlines()]
            if command.diff:
                lines.append("  # the change to the file, as a diff:")
                lines += [f"  {line}".rstrip() for line in command.diff.splitlines()]
            lines.append("")
    return "\n".join(lines).rstrip() + "\n" if lines else "Nothing to run.\n"


class Backend:
    """The catalogue and everything that reads, plans and applies it. No toolkit in here: the window sits on top."""

    def __init__(self, system: System | None = None) -> None:
        self.s = system or System()
        self.catalog = ExtensionCatalog()
        self.items = build_items(self.catalog)
        self.by_id = {item.id: item for item in self.items}
        self._checks: dict[str, Check] = {}
        self.lock = threading.RLock()

    # --- reading -------------------------------------------------------------

    @property
    def read_only(self) -> str | None:
        """Why changes cannot be made on this machine, or None when they can."""
        if not self.s.is_arch:
            return (f"Changes are made on CachyOS and other Arch-based systems. This is {self.s.os_name}, so you can "
                    "look around and open the guides, but not apply anything.")
        if os.geteuid() == 0:
            return "Run this as your normal user. It asks for root when it needs it."
        return None

    def check(self, item: Item) -> Check:
        with self.lock:
            cached = self._checks.get(item.id)
        if cached is not None:
            return cached
        try:
            result = item.status(self.s)      # not under the lock: a slow probe must not freeze the window
        except Exception as exc:  # a broken probe must not take the window down
            log.exception("check of %s failed", item.id)
            result = Check(State.UNKNOWN, f"could not check ({exc})")
        with self.lock:
            return self._checks.setdefault(item.id, result)

    def refresh(self) -> None:
        with self.lock:
            self._checks.clear()
        self.s.refresh()

    def check_all(self) -> None:
        for item in self.items:
            self.check(item)

    def refresh_extensions(self) -> None:
        self.catalog.refresh(self.s)

    def items_in(self, section: str) -> list[Item]:
        return [i for i in self.items if i.section == section]

    def section_counts(self, section: str) -> tuple[int, int]:
        """(done, total) over the items that apply on this machine."""
        rows = [self.check(i) for i in self.items_in(section) if not i.guide_only]
        counted = [c for c in rows if c.state is not State.NA]
        return sum(1 for c in counted if c.state is State.DONE), len(counted)

    def blocked_reason(self, item: Item) -> str | None:
        """Why this row cannot be ticked right now (the row says it), or None."""
        if item.guide_only:
            return "guide only"
        if self.read_only:
            return "read-only here"
        check = self.check(item)
        if check.state is State.NA:
            return check.detail
        if check.state is State.UNKNOWN and not item.toggleable:
            return check.detail
        if item.unavailable is not None and check.state is not State.DONE:
            return item.unavailable(self.s)
        return None

    def baseline(self, item: Item) -> bool | None:
        """What an untouched row means: True when it is set up, False when not, None when partly."""
        state = self.check(item).state
        if state is State.DONE:
            return True
        if state is State.PARTIAL:
            return None
        return False

    def recommended_ids(self) -> list[str]:
        return [i.id for i in self.items if i.recommended and not i.advanced and not self.blocked_reason(i)
                and self.check(i).state in (State.TODO, State.PARTIAL)]

    # --- planning ------------------------------------------------------------

    def build_plan(self, wanted: dict[str, bool], dry: bool = False) -> Built:
        """
        Turn a set of wanted changes (item id -> on or off) into a plan, adding what a change needs and refusing what
        cannot be done safely. Nothing is changed on the machine, though a plan may prepare files in your cache.
        With dry=True an item that refuses itself (its own on_blocker or off_blocker) is still worked out, and the
        refusal stays in the blockers: that is for showing what it would run, and the plan can never be applied.
        """
        s, built = self.s, Built()
        changes: dict[str, bool] = {}
        for item_id, want in wanted.items():
            state = self.check(self.by_id[item_id]).state
            if (want and state is State.DONE) or (not want and state in (State.TODO, State.NA, State.UNKNOWN)):
                continue
            changes[item_id] = want

        for item_id in list(changes):                      # what a tick needs gets ticked too
            item = self.by_id[item_id]
            if not changes[item_id]:
                continue
            for needed in item.requires:
                if needed not in changes and self.check(self.by_id[needed]).state is not State.DONE:
                    changes[needed] = True
                    built.included.append(f"{self.by_id[needed].title} (needed by {item.title})")

        def stays_on(other: Item) -> bool:
            return changes.get(other.id, self.check(other).state in (State.DONE, State.PARTIAL))

        for item_id, want in changes.items():
            item = self.by_id[item_id]
            if not want:
                for other in self.items:
                    if item.id in other.requires and stays_on(other):
                        built.blockers.append(f"{other.title} needs {item.title}. Untick {other.title} as well, or "
                                              f"keep {item.title}.")
            else:
                for rival in item.conflicts:
                    other = self.by_id[rival]
                    # Even when the rival is unticked in the same run: installs go first, so the two would clash.
                    if self.check(other).state in (State.DONE, State.PARTIAL) or changes.get(rival):
                        built.blockers.append(f"{item.title} and {other.title} replace each other. Apply the removal "
                                              f"of {other.title} first, then tick {item.title}.")

        ordered = [i for i in self.items if i.id in changes]
        for item in [i for i in ordered if not changes[i.id]] + [i for i in ordered if changes[i.id]]:
            on = changes[item.id]
            reason = self.blocked_reason(item)
            if reason == "read-only here":
                continue
            if reason and on:
                built.blockers.append(f"{item.title}: {reason}")
                continue
            blocker = (item.on_blocker if on else item.off_blocker)
            problem = blocker(s) if blocker else None
            if problem:
                built.blockers.append(f"{item.title}: {problem}")
                if not dry:
                    continue
            action = item.on if on else item.off
            if action is None:
                built.skipped.append(f"{item.title}: this setup cannot do that one for you, see its details")
                continue
            try:
                action(s, built.plan)
            except SetupError as exc:
                built.blockers.append(f"{item.title}: {exc}")
                continue
            except Exception as exc:  # a bug in one item must not hide the others
                log.exception("planning %s failed", item.id)
                built.blockers.append(f"{item.title}: could not prepare this change ({exc})")
                continue
            (built.turn_on if on else built.turn_off).append(item)
            if on and (steps := item.manual_steps(s)):
                built.manual.append((item.title, steps))

        self._finish_plan(built)
        return built

    def _finish_plan(self, built: Built) -> None:
        s, plan = self.s, built.plan
        if reason := self.read_only:
            built.blockers.append(reason)
            return
        protected = [p for p in plan.remove_pacman if p in PROTECTED_PACKAGES]
        if protected:
            plan.remove_pacman = [p for p in plan.remove_pacman if p not in PROTECTED_PACKAGES]
            plan.note("Kept, because the system or this window needs them: " + ", ".join(protected))
        if plan.flatpak:
            if not s.has_cmd("flatpak"):
                plan.add_pacman(["flatpak"])
            if not s.has_flathub():
                plan.root.insert(0, Snippet("Add the Flathub remote",
                                            f"flatpak remote-add --if-not-exists flathub {shlex.quote(FLATHUB_REPO)}"))
        if plan.aur and not s.has_cmd("paru"):
            plan.add_pacman(["paru"])
        needs_root = bool(plan.pacman or plan.root or plan.root_early or plan.remove_pacman)
        if needs_root and not s.has_cmd("pkexec"):
            built.blockers.append("pkexec is not installed, and the steps that need root use it")
        if (plan.pacman or plan.remove_pacman) and s.pacman_locked():
            built.blockers.append("pacman is busy (/var/lib/pacman/db.lck exists). Close any other package manager, "
                                  "or remove the lock if none is running, then try again")
        missing = [p for p in plan.pacman if not s.in_repos(p)]
        if missing:
            built.blockers.append("Not found in your pacman repositories: " + ", ".join(missing)
                                  + ". Some of these come from the CachyOS repositories")
        elif plan.pacman and not built.blockers:
            res = run(["pacman", "-Sp", "--needed", "--noconfirm", *plan.pacman], timeout=60)
            if not res.ok:
                reason = " ".join(res.text.split())[:300] or f"pacman exited with code {res.code}"
                built.blockers.append(f"pacman says this cannot be installed together: {reason}")
        if plan.aur or any(step.interactive for step in plan.steps):
            if not terminal_candidates():
                built.warnings.append("No terminal emulator was found. The steps that need your input will show the "
                                      "command to run yourself instead.")
        if plan.needs_network and not s.online():
            built.warnings.append("The internet does not look reachable. Downloads will probably fail.")
        age = s.database_age_days() if plan.pacman else None
        if age is not None and age > 3:
            built.warnings.append(f"Your package databases are {age:.0f} days old. If a download fails with a 404, run "
                                  "a full update first: sudo pacman -Syu")

    def direction(self, item: Item, want: bool, check: Check) -> list[str]:
        """
        What turning an item on or off would run on this machine, as lines of text. A blocker is listed first and the
        commands still follow it, so you can read what an untick runs even while another row stands in its way.
        """
        if want and check.state is State.DONE:
            return ["Nothing: it is already set up. The reference on the site lists what it runs on a machine "
                    "that is not."]
        if not want and check.state in (State.TODO, State.NA, State.UNKNOWN):
            return ["Nothing: it is not set up."]
        built = self.build_plan({item.id: want}, dry=True)
        lines = [f"Not possible right now: {b}" for b in built.blockers]
        if built.included:
            lines.append("Also included, because something needs it: " + ", ".join(built.included))
        if not built.plan.empty:
            if built.blockers:
                lines.append("Once that is sorted out, it runs:")
            lines += ["", *render_plan(built.plan).splitlines()]
        facts = [f"Note: {note}" for note in built.plan.notes]
        if built.plan.reboot_for:
            facts.append("Needs a reboot: " + ", ".join(built.plan.reboot_for))
        if built.plan.relogin_for:
            facts.append("Needs logging out and back in: " + ", ".join(built.plan.relogin_for))
        return [*lines, "", *facts] if facts and not built.plan.empty else [*lines, *facts]

    def describe(self, item: Item) -> str:
        """
        Everything about one item as text: its status, its links, and the exact commands that ticking and unticking
        it would run on this machine, with a diff for every existing file they change. Both directions are listed.
        """
        check = self.check(item)
        lines = [item.title, "", item.summary, "", f"Status: {check.state.value}"
                 + (f" ({check.detail})" if check.detail else ""), f"Guide:  {item.url}",
                 f"Exact commands, with the way back: {reference_url(item.section, item.id)}"]
        reason = item.not_applicable(self.s) or (item.unavailable(self.s) if item.unavailable else None)
        if reason:
            lines += ["", f"Not available: {reason}"]
        if item.aur:
            lines.append("Source: " + ("the AUR (a community build script that paru shows for review)"
                                       if item.needs_aur(self.s) else "the repositories"))
        if item.advanced:
            lines.append("Advanced: left out of 'Select recommended'")
        if item.requires:
            lines.append("Needs: " + ", ".join(self.by_id[i].title for i in item.requires))
        if item.toggleable and not reason:
            if self.read_only:
                lines += ["", f"Not worked out here: {self.read_only}"]
            else:
                for want, label in ((True, "Ticking it runs"), (False, "Unticking it runs")):
                    lines += ["", f"{label}:", *[f"  {line}".rstrip() for line in self.direction(item, want, check)]]
        for steps, label in ((item.manual_steps(self.s), "By hand, to set it up" if item.guide_only
                              else "Left for you after ticking it"),
                             (item.manual_off_steps(self.s), "By hand, to undo it" if item.guide_only
                              else "Left for you after unticking it")):
            if steps:
                lines += ["", f"{label}:", *[f"  {n}. {step}" for n, step in enumerate(steps, 1)]]
        return "\n".join(lines) + "\n"


# --- applying ----------------------------------------------------------------------------------------

@dataclass
class Outcome:
    item: Item
    wanted: bool
    check: Check
    state: str      # ok, partial or failed


@dataclass
class RunReport:
    failures: list[str] = field(default_factory=list)
    outcomes: list[Outcome] = field(default_factory=list)
    stopped: bool = False

    @property
    def ok(self) -> bool:
        return not self.failures and all(o.state == "ok" for o in self.outcomes)


def judge(state: State, wanted: bool) -> str:
    """Did a change end up the way it was asked? 'ok', 'partial' or 'failed'."""
    if wanted:
        return {State.DONE: "ok", State.PARTIAL: "partial"}.get(state, "failed")
    return {State.TODO: "ok", State.NA: "ok", State.UNKNOWN: "ok", State.PARTIAL: "partial"}.get(state, "failed")


class Executor:
    """Runs a plan. Blocking: call it from a worker thread. Output goes to emit, one line at a time."""

    def __init__(self, backend: Backend, emit: Callable[[str], None], phase: Callable[[str], None],
                 stop: Callable[[], bool], waiting: Callable[[bool], None] | None = None) -> None:
        self.b = backend
        self.emit = emit
        self.phase = phase
        self.stop = stop
        self.waiting = waiting or (lambda _on: None)

    def _terminal(self, argv: list[str], title: str) -> int | None:
        """Run a program in a terminal window while the progress dialog says that you are being waited for."""
        self.waiting(True)
        try:
            return run_in_terminal(argv, title, self.stop)
        finally:
            self.waiting(False)

    def run(self, built: Built) -> RunReport:
        plan, report = built.plan, RunReport()
        log.info("apply: on=%s off=%s", [i.id for i in built.turn_on], [i.id for i in built.turn_off])
        failures = report.failures
        failures += [f for f in (self._step(step) for step in plan.steps if step.early) if f]

        root_failed = False
        if plan.pacman or plan.root or plan.root_early or plan.remove_pacman:
            self.phase("Steps that need root")
            self.emit("==> Steps that need root: one password prompt covers all of them")
            code = stream(["pkexec", "bash", "-c", root_script(built.plan)], self.emit)
            if code != 0:
                root_failed = True
                why = PKEXEC_CODES.get(code, "")
                failures.append("The steps that need root did not all work" + (f": {why}" if why else "")
                                + f" (exit code {code}). The messages above say which one.")
                if code in PKEXEC_CODES:
                    report.stopped = True
                    return report

        if plan.aur and not root_failed:
            self.phase("AUR packages")
            self.emit("==> AUR packages with paru, in a terminal window")
            command = [*PARU_INSTALL, *plan.aur]
            code = self._terminal(command, "AUR packages: review each PKGBUILD before you let it build")
            if code is None:
                failures.append("The AUR packages need a terminal window, and none could be opened. Run this yourself: "
                                + shlex.join(command))
            elif code != 0:
                failures.append(f"paru exited with code {code} for: {' '.join(plan.aur)}")
        elif plan.aur:
            failures.append("The AUR packages were skipped because the root steps failed: " + " ".join(plan.aur))

        if plan.flatpak:
            self.phase("Flatpaks")
            self.emit("==> Flatpaks from Flathub")
            code = stream([*FLATPAK_INSTALL, *plan.flatpak], self.emit)
            if code != 0:
                failures.append(f"flatpak exited with code {code} for: {' '.join(plan.flatpak)}")
        if plan.remove_flatpak:
            self.emit("==> Removing Flatpaks")
            code = stream([*FLATPAK_REMOVE, *plan.remove_flatpak], self.emit)
            if code != 0:
                failures.append(f"flatpak exited with code {code} for: {' '.join(plan.remove_flatpak)}")

        self.phase("Your own settings")
        failures += [f for f in (self._step(step) for step in plan.steps if not step.early) if f]

        self.phase("Checking the result")
        self.b.refresh()
        for items, wanted in ((built.turn_on, True), (built.turn_off, False)):
            for item in items:
                check = self.b.check(item)
                report.outcomes.append(Outcome(item, wanted, check, judge(check.state, wanted)))
        return report

    def _step(self, step: Step) -> str | None:
        """Run one step as you. Returns what went wrong, or None."""
        if step.when is not None and not step.when():
            self.emit(f"-- already in place, skipped: {step.desc}")
            return None
        self.emit(f"==> {step.desc}")
        try:
            if step.interactive:
                argv = step.argv_factory() if step.argv_factory else step.argv or []
                code = self._terminal(argv, step.desc)
                if code is None:
                    raise SetupError("this needs a terminal window and none could be opened. Run this yourself: "
                                     + shlex.join(argv))
                if code != 0:
                    raise SetupError(f"{step.name or (Path(argv[-1]).name if argv else 'the command')} "
                                     f"exited with code {code}")
            elif step.call is not None:
                step.call()
            elif step.argv:
                code = stream(step.argv, self.emit)
                if code != 0:
                    raise SetupError(f"{step.argv[0]} exited with code {code}")
        except (SetupError, OSError, subprocess.SubprocessError, ValueError) as exc:
            self.emit(f"[FAILED] {exc}")
            log.error("step failed: %s: %s", step.desc, exc)
            return f"{step.desc}: {exc}"
        except Exception as exc:  # a bug in a step must end up in the report and the log, not kill the run
            log.exception("step crashed: %s", step.desc)
            self.emit(f"[FAILED] unexpected error: {exc}")
            return f"{step.desc}: unexpected error ({exc})"
        return None


# --- the window ---------------------------------------------------------------------------------
#
# Nothing below runs unless the window opens, and the classes inherit from object when GTK is missing, so this
# file can still be imported (to test the logic, or to print a useful message) on a machine without it.

CSS = """
.zs-pill { padding: 1px 9px; border-radius: 999px; font-size: 0.82em; font-weight: 600; }
.zs-pill.done { color: @success_color; background: alpha(@success_color, 0.14); }
.zs-pill.partial { color: @warning_color; background: alpha(@warning_color, 0.16); }
.zs-pill.dim { color: alpha(@window_fg_color, 0.62); background: alpha(@window_fg_color, 0.07); }
.zs-pill.add { color: @accent_color; background: alpha(@accent_color, 0.15); }
.zs-pill.remove { color: @error_color; background: alpha(@error_color, 0.14); }
.zs-log { font-family: monospace; font-size: 0.92em; }
.zs-swatch { min-width: 34px; min-height: 26px; border-radius: 6px; }
.zs-swatch.red { background-color: #ff0000; }
.zs-swatch.green { background-color: #00ff00; }
.zs-swatch.blue { background-color: #0000ff; }
.zs-swatch.yellow { background-color: #ffff00; }
.zs-swatch.skin { background-color: #f1c8a8; }
"""


def guarded(method):
    """A signal handler that logs what goes wrong and tells the person, instead of dying quietly."""
    def wrapper(self, *args):
        try:
            return method(self, *args)
        except Exception as exc:  # the window must survive a bug in one handler
            log.exception("handler %s failed", method.__name__)
            self.fail("Something went wrong", f"{exc}\n\nDetails are in the log file.")
    return wrapper


def background(work: Callable[[], object], done: Callable[[object, Exception | None], None]) -> None:
    """Run work in a thread and call done(result, error) back on the main loop."""
    def target() -> None:
        try:
            result, error = work(), None
        except SetupError as exc:             # expected: the message is for the person
            log.warning("background work: %s", exc)
            result, error = None, exc
        except Exception as exc:  # a bug: log the traceback, and let done() tell the person something went wrong
            log.exception("background work failed")
            result, error = None, exc
        GLib.idle_add(lambda: done(result, error) and False)

    threading.Thread(target=target, daemon=True).start()


def call_in_ui(fn: Callable[..., object], *args) -> None:
    GLib.idle_add(lambda: fn(*args) and False)


def icon_or(*names: str) -> str:
    """The first icon name the current theme has, so a theme without one shows a neighbour instead of a blank."""
    theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
    return next((name for name in names if theme.has_icon(name)), names[-1])


def plural(count: int, one: str, many: str) -> str:
    return f"{count} {one if count == 1 else many}"


PILL_CLASSES = ("done", "partial", "dim", "add", "remove")


def make_pill(text: str = "", kind: str = "dim") -> "Gtk.Label":
    label = Gtk.Label(label=text, valign=Gtk.Align.CENTER, visible=bool(text))
    label.add_css_class("zs-pill")
    label.add_css_class(kind)
    return label


def set_pill(label: "Gtk.Label", text: str, kind: str) -> None:
    for name in PILL_CLASSES:
        label.remove_css_class(name)
    label.add_css_class(kind)
    label.set_label(text)
    label.set_visible(bool(text))


class ItemRow:
    """One checkbox row: shows the state, remembers what you want it to be, and says what will happen."""

    def __init__(self, window: "SetupWindow", item: Item) -> None:
        self.window, self.item = window, item
        self.baseline: bool | None = False
        self.value: bool | None = False
        self._guard = False
        self.phase = 0
        self.marker = None
        self.row = Adw.ActionRow(title=item.title, use_markup=False, subtitle_lines=0, title_lines=0)
        self.check = Gtk.CheckButton(valign=Gtk.Align.CENTER)
        self.pill = make_pill()
        self.tags = Gtk.Box(spacing=6, valign=Gtk.Align.CENTER)
        self.row.add_prefix(self.check)
        self.row.set_activatable_widget(self.check)
        self.row.add_suffix(self.tags)
        self.row.add_suffix(self.pill)
        guide = Gtk.Button(icon_name=icon_or("adw-external-link-symbolic", "web-browser-symbolic",
                                             "help-about-symbolic"),
                           valign=Gtk.Align.CENTER, tooltip_text="Open the guide for this")
        guide.add_css_class("flat")
        guide.connect("clicked", lambda _b: window.open_url(item.url))
        details = Gtk.Button(icon_name=icon_or("help-about-symbolic", "dialog-information-symbolic"),
                             valign=Gtk.Align.CENTER, tooltip_text="The exact commands for ticking and unticking it")
        details.add_css_class("flat")
        details.connect("clicked", lambda _b: window.show_details(item))
        self.row.add_suffix(details)
        self.row.add_suffix(guide)
        self.check.connect("toggled", self._toggled)
        self.refresh()

    # --- state -------------------------------------------------------------

    def refresh(self, keep: bool = False) -> None:
        """Re-read the state from the machine. With keep=True a pending choice survives, otherwise it is dropped."""
        backend, item = self.window.backend, self.item
        check = backend.check(item)
        self.baseline = backend.baseline(item)
        self.blocked = backend.blocked_reason(item)
        pending = self.window.wanted.get(item.id) if keep else None
        value = pending if pending is not None else self.baseline
        self._show(value, pending is not None)
        self.check.set_visible(not item.guide_only)
        self.check.set_sensitive(self.blocked is None and item.toggleable)
        if item.guide_only and self.marker is None:
            self.marker = Gtk.Image(icon_name=icon_or("document-edit-symbolic", "help-about-symbolic"),
                                    tooltip_text="A guide: you do these steps yourself")
            self.marker.add_css_class("dim-label")
            self.row.add_prefix(self.marker)
        lines = [item.summary]
        if self.blocked and not item.guide_only and self.blocked != "read-only here":
            lines.append(self.blocked)
        elif check.detail and check.state is not State.DONE and check.detail != "not installed":
            lines.append(check.detail)
        self.row.set_subtitle("\n".join(lines))
        self.row.set_tooltip_text(self.blocked if self.blocked and self.blocked != "guide only" else None)
        child = self.tags.get_first_child()
        while child is not None:
            following = child.get_next_sibling()
            self.tags.remove(child)
            child = following
        for label, show in (("AUR", item.needs_aur(self.window.backend.s) and not item.guide_only),
                            ("Advanced", item.advanced)):
            if show:
                self.tags.append(make_pill(label, "dim"))

    def _show(self, value: bool | None, pending: bool) -> None:
        self.value = value
        self.phase = {None: 0, True: 1, False: 2}[value] if self.baseline is None else 0
        self._guard = True
        self.check.set_inconsistent(value is None)
        self.check.set_active(bool(value))
        self._guard = False
        self._pill(pending)

    def _pill(self, pending: bool) -> None:
        state = self.window.backend.check(self.item).state
        if self.item.guide_only:
            text, kind = {State.DONE: ("Done", "done"), State.PARTIAL: ("Partly", "partial"),
                          State.TODO: ("To do", "dim")}.get(state, ("Guide", "dim"))
        elif pending:
            text, kind = ("Will turn on" if self.value else "Will turn off"), ("add" if self.value else "remove")
        elif state is State.PARTIAL:
            text, kind = "Partly", "partial"
        elif state is State.NA or self.blocked not in (None, "read-only here"):
            text, kind = "Not here", "dim"
        else:
            text, kind = "", "dim"
        set_pill(self.pill, text, kind)

    def set_value(self, value: bool | None) -> None:
        """Set the wish from code (a requirement, 'select recommended'). Same bookkeeping as a click."""
        if not self.check.get_sensitive() and value is not None:
            return
        self._apply(value)

    def _apply(self, value: bool | None) -> None:
        changed = value != self.baseline
        if changed:
            self.window.wanted[self.item.id] = bool(value)
        else:
            self.window.wanted.pop(self.item.id, None)
        self._show(value, changed)
        self.window.update_bar()

    @guarded
    def _toggled(self, check: "Gtk.CheckButton") -> None:
        if self._guard:
            return
        if self.baseline is None:
            self.phase = (self.phase + 1) % 3
            value = {0: None, 1: True, 2: False}[self.phase]
        else:
            value = check.get_active()
        self._apply(value)
        self.window.link(self.item, value)

    def fail(self, heading: str, body: str) -> None:
        self.window.fail(heading, body)


# --- the color mode section ---------------------------------------------------------------------

COLOR_INTRO = "Switches right away, no apply step. It is saved, so it survives a restart."


class ColorSection:
    """The live color mode switch, G-Helper style, plus what we know about this screen."""

    def __init__(self, window: "SetupWindow") -> None:
        self.window = window
        self.controller = ColorController(window.backend.s)
        self.info: ColorInfo | None = None
        self.checks: dict[str, "Gtk.CheckButton"] = {}
        self.rows: dict[str, "Adw.ActionRow"] = {}
        self.group_rows: list["Adw.ActionRow"] = []
        self.group = Adw.PreferencesGroup(title="Color mode", description=COLOR_INTRO)
        self.status = Adw.ActionRow(title="Reading this screen", use_markup=False, subtitle_lines=0)
        self.spinner = Gtk.Spinner(spinning=True, valign=Gtk.Align.CENTER)
        self.status.add_prefix(self.spinner)
        self.group.add(self.status)
        self.facts = Adw.PreferencesGroup(title="This screen")
        self.facts.set_visible(False)
        self.fact_rows: list["Adw.ActionRow"] = []
        self._guard = False
        self._busy = False

    def widgets(self) -> list["Adw.PreferencesGroup"]:
        return [self.group, self.facts]

    def load(self) -> None:
        if not self.window.backend.s.is_gnome:
            self._elsewhere()
            return
        background(self.controller.info, self._loaded)

    def _elsewhere(self) -> None:
        """The switch talks to GNOME's compositor, so under any other desktop there is nothing to switch."""
        desktop = self.window.backend.s.desktop
        self.spinner.set_visible(False)
        self.facts.set_visible(False)
        self.status.set_visible(True)
        self.status.set_title("The color switch needs GNOME")
        note = f" This session runs {desktop}." if desktop else ""
        self.status.set_subtitle("It talks to GNOME's compositor." + note)

    def _loaded(self, info: ColorInfo | None, error: Exception | None) -> None:
        self.spinner.set_visible(False)
        if error is not None or info is None:
            self.status.set_title("Could not read this screen")
            self.status.set_subtitle(str(error))
            return
        self.info = info
        self.status.set_visible(False)
        self._build(info)

    def _add_row(self, row: "Adw.ActionRow") -> None:
        self.group.add(row)
        self.group_rows.append(row)

    def _swatch_row(self) -> "Adw.ActionRow":
        """Saturated colors to look at while switching: the window itself goes through the color mode."""
        row = Adw.ActionRow(title="Compare the colors", use_markup=False, subtitle_lines=0,
                            subtitle="Switch modes and watch these. In sRGB the reds and greens should look calmer.")
        swatches = Gtk.Box(spacing=6, valign=Gtk.Align.CENTER)
        for name in ("red", "green", "blue", "yellow", "skin"):
            swatch = Gtk.Box()
            swatch.add_css_class("zs-swatch")
            swatch.add_css_class(name)
            swatches.append(swatch)
        row.add_suffix(swatches)
        return row

    def _why_row(self) -> "Adw.ActionRow":
        row = Adw.ActionRow(title="Why no DCI-P3 or Display P3?", use_markup=False, subtitle_lines=0, title_lines=0,
                            subtitle="Native already shows everything this panel can do, so a P3 mode would look "
                                     "the same. On Windows those two switch a mode that Linux does not have.")
        more = Gtk.Button(label="Read more", valign=Gtk.Align.CENTER)
        more.add_css_class("flat")
        more.connect("clicked",
                     lambda _b: self.window.open_url(doc_url("hardware/color-profiles#why-no-dci-p3-or-display-p3")))
        row.add_suffix(more)
        return row

    def _runs_row(self, info: ColorInfo) -> "Adw.ActionRow":
        row = Adw.ActionRow(title="What a switch runs", use_markup=False, subtitle_lines=0, title_lines=0,
                            subtitle="The two calls behind it, and the way back")
        show = Gtk.Button(label="Show", valign=Gtk.Align.CENTER)
        show.add_css_class("flat")
        connector = info.panel.connector if info.panel else "the built-in screen"
        show.connect("clicked", lambda _b: self.window.show_text(
            "What a color switch runs", color_runs(connector),
            [("Exact description on the site", reference_url("display", "color-mode"))]))
        row.add_suffix(show)
        return row

    def _build(self, info: ColorInfo) -> None:
        for row in self.group_rows:
            self.group.remove(row)
        self.group_rows.clear()
        self.rows.clear()
        self.checks.clear()
        first = None
        for mode in info.modes:
            row = Adw.ActionRow(title=mode.title, subtitle=mode.summary, use_markup=False, subtitle_lines=0)
            check = Gtk.CheckButton(valign=Gtk.Align.CENTER)
            if first is None:
                first = check
            else:
                check.set_group(first)
            row.add_prefix(check)
            row.set_activatable_widget(check)
            check.connect("toggled", self._picked, mode.key)
            self._add_row(row)
            self.rows[mode.key], self.checks[mode.key] = row, check
        self._select(info.current)
        if info.compositor_ok:
            self._add_row(self._swatch_row())
        self._add_row(self._why_row())
        self._add_row(self._runs_row(info))
        notes = []
        if not info.compositor_ok:
            notes.append(info.compositor_note or "The sRGB color mode is not available here.")
        if not info.colord_ok:
            notes.append("colord (colormgr) is not installed, so color-managed apps are not told.")
        elif info.native and not info.profiles_installed:
            notes.append("Tick 'ASUS color profiles' below to also tell color-managed apps which profile is active.")
        if info.current is None and info.current_detail:
            notes.append(f"Right now: {info.current_detail}.")
        self.group.set_description("\n".join([COLOR_INTRO, *notes]))
        self._facts(info)

    def _select(self, key: str | None) -> None:
        self._guard = True
        for name, check in self.checks.items():
            check.set_active(name == key)
        self._guard = False

    def _facts(self, info: ColorInfo) -> None:
        for row in self.fact_rows:
            self.facts.remove(row)
        self.fact_rows.clear()
        rows = []
        model = info.model or "unknown"
        rows.append(("Model", model, f"from the BIOS version {info.bios}" if info.bios else ""))
        if info.panel:
            edid = info.panel.edid
            rows.append(("Panel", edid.name or edid.pnp, f"{info.panel.connector}, EDID {edid.panel_id}"))
            rows.append(("Graphics", {"1002": "AMD", "10DE": "NVIDIA"}.get(info.panel.gpu, info.panel.gpu),
                         "the GPU this screen hangs off right now"))
        if info.coverage_srgb is not None and info.coverage_p3 is not None:
            rows.append(("Gamut", f"{info.coverage_srgb * 100:.0f}% of sRGB, {info.coverage_p3 * 100:.0f}% of DCI-P3",
                         "from the primaries the panel reports in its EDID"))
        rows.append(("Profiles", info.native or "none for this panel", "the factory profile this setup would use"))
        offered = ", ".join(info.compositor_offers) or "none"
        rows.append(("GNOME color mode", info.compositor_mode or "unknown", f"GNOME offers: {offered}"))
        rows.append(("Active profile", info.active_profile or "none", "in colord, for color-managed apps"))
        for title, value, subtitle in rows:
            row = Adw.ActionRow(title=title, subtitle=subtitle, use_markup=False)
            label = Gtk.Label(label=value, wrap=True, xalign=1, selectable=True, valign=Gtk.Align.CENTER)
            label.add_css_class("dim-label")
            row.add_suffix(label)
            self.facts.add(row)
            self.fact_rows.append(row)
        copy = Adw.ActionRow(title="Copy details", use_markup=False, activatable=True,
                             subtitle="For a bug report: everything above plus the GNOME and colord state")
        copy.add_suffix(Gtk.Image(icon_name=icon_or("edit-copy-symbolic", "document-save-symbolic")))
        copy.connect("activated", lambda _r: self.window.copy_text(self.controller.report(info)))
        self.facts.add(copy)
        self.fact_rows.append(copy)
        self.facts.set_visible(True)

    @guarded
    def _picked(self, check: "Gtk.CheckButton", key: str) -> None:
        if self._guard or not check.get_active() or self._busy or self.info is None:
            return
        previous = self.info.current
        self._busy = True
        self.group.set_sensitive(False)
        mode = next(m for m in self.info.modes if m.key == key)
        background(lambda: self.controller.switch(key, self.info),
                   lambda notes, error: self._switched(mode, previous, notes, error))

    def _switched(self, mode: ColorMode, previous: str | None, notes: list[str] | None,
                  error: Exception | None) -> None:
        self._busy = False
        self.group.set_sensitive(True)
        if error is not None:
            self._select(previous)
            self.window.fail(f"Could not switch to {mode.title}", str(error))
            return
        if self.info is not None:
            self.info.current = mode.key
        toast = Adw.Toast(title=f"Switched to {mode.title}", timeout=8, button_label="Undo" if previous else None)
        if previous:
            toast.connect("button-clicked", lambda _t: self._undo(previous))
        self.window.toasts.add_toast(toast)
        if notes:
            self.group.set_description("\n".join([COLOR_INTRO, *notes]))

    def _undo(self, key: str) -> None:
        check = self.checks.get(key)
        if check is not None:
            check.set_active(True)

    def fail(self, heading: str, body: str) -> None:
        self.window.fail(heading, body)


# --- dialogs --------------------------------------------------------------------------------------

def dialog_shell(title: str, width: int = 760, height: int = 680,
                 can_close: bool = True) -> tuple["Adw.Dialog", "Adw.ToolbarView"]:
    dialog = Adw.Dialog(title=title, content_width=width, content_height=height, can_close=can_close)
    view = Adw.ToolbarView()
    view.add_top_bar(Adw.HeaderBar())
    dialog.set_child(view)
    return dialog, view


def info_row(title: str, subtitle: str = "", icon: str = "") -> "Adw.ActionRow":
    row = Adw.ActionRow(title=title, subtitle=subtitle, use_markup=False, title_lines=0, subtitle_lines=0)
    if icon:
        row.add_prefix(Gtk.Image(icon_name=icon_or(icon, "dialog-information-symbolic")))
    return row


def rows_group(title: str, rows: list["Adw.ActionRow"], description: str = "") -> "Adw.PreferencesGroup":
    group = Adw.PreferencesGroup(title=title, description=description)
    for row in rows:
        group.add(row)
    return group


def scrolled(child: "Gtk.Widget", height: int = -1) -> "Gtk.ScrolledWindow":
    box = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER, min_content_height=height)
    box.set_child(child)
    return box


def text_view(text: str = "", monospace: bool = True) -> "Gtk.TextView":
    view = Gtk.TextView(editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD_CHAR, left_margin=12,
                        right_margin=12, top_margin=10, bottom_margin=10, monospace=monospace)
    view.get_buffer().set_text(text)
    return view


class ProgressDialog:
    """What is happening while a plan runs: the phase, the live output, and afterwards what came out of it."""

    def __init__(self, window: "SetupWindow", on_stop_waiting: Callable[[], None]) -> None:
        self.window = window
        self.dialog, view = dialog_shell("Applying changes", 780, 700, can_close=False)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=6, margin_bottom=12,
                       margin_start=14, margin_end=14)
        self.spinner = Gtk.Spinner(spinning=True)
        self.phase_label = Gtk.Label(label="Starting", xalign=0, hexpand=True)
        self.phase_label.add_css_class("heading")
        head = Gtk.Box(spacing=10)
        head.append(self.spinner)
        head.append(self.phase_label)
        body.append(head)
        self.banner = Adw.Banner(title="A terminal window is open and waiting for you. Finish there.",
                                 button_label="Stop waiting", revealed=False)
        self.banner.connect("button-clicked", lambda _b: on_stop_waiting())
        body.append(self.banner)
        self.result = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, visible=False)
        body.append(self.result)
        self.log_view = text_view(monospace=True)
        self.log_view.add_css_class("zs-log")
        frame = Gtk.Frame(child=scrolled(self.log_view), vexpand=True)
        body.append(frame)
        buttons = Gtk.Box(spacing=8, halign=Gtk.Align.END)
        self.log_button = Gtk.Button(label="Open the log file", sensitive=LOG_FILE.exists())
        self.log_button.connect("clicked", lambda _b: window.open_url(LOG_FILE.as_uri()))
        self.close_button = Gtk.Button(label="Close", sensitive=False)
        self.close_button.add_css_class("suggested-action")
        self.close_button.connect("clicked", lambda _b: self.dialog.force_close())
        buttons.append(self.log_button)
        buttons.append(self.close_button)
        body.append(buttons)
        view.set_content(body)
        self.dialog.present(window)

    def line(self, text: str) -> None:
        buffer = self.log_view.get_buffer()
        buffer.insert(buffer.get_end_iter(), text + "\n")
        if buffer.get_line_count() > 4000:
            _found, end = buffer.get_iter_at_line(1000)
            buffer.delete(buffer.get_start_iter(), end)
        mark = buffer.create_mark(None, buffer.get_end_iter(), False)
        self.log_view.scroll_mark_onscreen(mark)
        buffer.delete_mark(mark)

    def phase(self, text: str) -> None:
        self.phase_label.set_label(text)

    def waiting(self, on: bool) -> None:
        self.banner.set_revealed(on)

    def finish(self, report: RunReport | None, error: Exception | None, built: Built) -> None:
        self.spinner.set_spinning(False)
        self.spinner.set_visible(False)
        self.banner.set_revealed(False)
        self.close_button.set_sensitive(True)
        self.dialog.set_can_close(True)
        if error is not None:
            self.phase_label.set_label("Stopped by a problem")
            self.line(f"[FAILED] {error}")
            return
        if report is None:
            return
        self.phase_label.set_label("Done" if report.ok else "Done, with problems")
        groups: list["Gtk.Widget"] = []
        rows = []
        for outcome in report.outcomes:
            icon = {"ok": "emblem-ok-symbolic",
                    "partial": "dialog-warning-symbolic"}.get(outcome.state, "dialog-error-symbolic")
            verb = "On" if outcome.wanted else "Off"
            rows.append(info_row(outcome.item.title, f"{verb}: {outcome.check.state.value}"
                                 + (f" ({outcome.check.detail})" if outcome.check.detail else ""), icon))
        if rows:
            groups.append(rows_group("Result", rows))
        if report.failures:
            groups.append(rows_group("What went wrong", [info_row(f, icon="dialog-error-symbolic")
                                                         for f in report.failures]))
        follow = []
        if built.plan.reboot_for:
            follow.append(info_row("Reboot to finish", ", ".join(built.plan.reboot_for), "system-reboot-symbolic"))
        if built.plan.relogin_for:
            follow.append(info_row("Log out and back in to finish", ", ".join(built.plan.relogin_for),
                                   "system-log-out-symbolic"))
        for title, steps in built.manual:
            follow.append(info_row(f"By hand: {title}", "\n".join(f"{n}. {s}" for n, s in enumerate(steps, 1)),
                                   "document-edit-symbolic"))
        if follow:
            groups.append(rows_group("Still to do", follow))
        for group in groups:
            self.result.append(group)
        self.result.set_visible(bool(groups))


# --- the window -----------------------------------------------------------------------------------

_Window = Adw.ApplicationWindow if Adw is not None else object


class SetupWindow(_Window):
    def __init__(self, app: "SetupApplication", backend: Backend) -> None:
        super().__init__(application=app, title=TITLE, default_width=1120, default_height=780)
        self.backend = backend
        self.wanted: dict[str, bool] = {}
        self.rows: dict[str, ItemRow] = {}
        self.counters: dict[str, "Gtk.Label"] = {}
        self.pages: dict[str, "Adw.NavigationPage"] = {}
        self.busy = False
        self._stop_waiting = False
        self.color: ColorSection | None = None
        self.toasts = Adw.ToastOverlay()
        self.set_content(self.toasts)
        self.set_size_request(360, 400)
        self._actions()
        self._build_shell()
        self.connect("close-request", self._close_request)
        background(self.backend.check_all, self._checked)

    # --- plumbing ----------------------------------------------------------

    def _actions(self) -> None:
        for name, handler in (("recommended", self._recommended), ("refresh", self._refresh),
                              ("log", lambda *_: self.open_url(LOG_FILE.as_uri())), ("about", self._about)):
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", handler)
            self.add_action(action)

    def _build_shell(self) -> None:
        self.split = Adw.NavigationSplitView(min_sidebar_width=250, max_sidebar_width=330, sidebar_width_fraction=0.28)
        self.toasts.set_child(self.split)
        narrow = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 720sp"))
        narrow.add_setter(self.split, "collapsed", True)
        self.add_breakpoint(narrow)
        # sidebar
        side = Adw.ToolbarView()
        header = Adw.HeaderBar(title_widget=Adw.WindowTitle(title=TITLE, subtitle=""))
        menu = Gio.Menu()
        menu.append("Select recommended", "win.recommended")
        menu.append("Check again", "win.refresh")
        menu.append("Open the log file", "win.log")
        menu.append("About", "win.about")
        header.pack_end(Gtk.MenuButton(icon_name="open-menu-symbolic", menu_model=menu, primary=True,
                                       tooltip_text="Menu"))
        side.add_top_bar(header)
        self.sidebar = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.sidebar.add_css_class("navigation-sidebar")
        self.sidebar.connect("row-selected", self._section_selected)
        side.set_content(scrolled(self.sidebar))
        self.split.set_sidebar(Adw.NavigationPage(title=TITLE, child=side))
        # content
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        loading = Adw.StatusPage(title="Looking at this machine", description="Checking what is already set up.")
        loading.set_child(Gtk.Spinner(spinning=True, width_request=32, height_request=32, halign=Gtk.Align.CENTER))
        self.stack.add_named(loading, "loading")
        self.content_title = Adw.WindowTitle(title="", subtitle="")
        content = Adw.ToolbarView()
        content.add_top_bar(Adw.HeaderBar(title_widget=self.content_title))
        self.banner = Adw.Banner(revealed=False)
        content.add_top_bar(self.banner)
        content.set_content(self.stack)
        self.bar = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_UP, reveal_child=False)
        bar = Gtk.ActionBar()
        self.bar_label = Gtk.Label(label="")
        clear = Gtk.Button(label="Clear")
        clear.add_css_class("flat")
        clear.connect("clicked", lambda _b: self.clear_selection())
        self.review_button = Gtk.Button(label="Review and apply")
        self.review_button.add_css_class("suggested-action")
        self.review_button.add_css_class("pill")
        self.review_button.connect("clicked", self._review)
        bar.pack_start(self.bar_label)
        bar.pack_end(self.review_button)
        bar.pack_end(clear)
        self.bar.set_child(bar)
        content.add_bottom_bar(self.bar)
        self.split.set_content(Adw.NavigationPage(title=TITLE, child=content))

    def _checked(self, _result: object, error: Exception | None) -> None:
        if error is not None:
            self.fail("Could not look at this machine", str(error))
        for key, title, icon, about in SECTIONS:
            self._add_section(key, title, icon, about)
        reason = self.backend.read_only
        if reason:
            self.banner.set_title(reason)
            self.banner.set_revealed(True)
        elif not self.backend.s.is_gnome:
            self.banner.set_title("This is not a GNOME session, so the items that need GNOME are switched off.")
            self.banner.set_revealed(True)
        self.sidebar.select_row(self.sidebar.get_row_at_index(0))
        if self.color is not None:
            self.color.load()
        background(self.backend.refresh_extensions, self._extensions_known)

    def _extensions_known(self, _result: object, _error: Exception | None) -> None:
        for spec in EXTENSIONS:
            if (row := self.rows.get(f"ext-{spec.key}")) is not None:
                row.refresh(keep=True)

    def _add_section(self, key: str, title: str, icon: str, about: str) -> None:
        page = Adw.PreferencesPage()
        if key == "display":
            self.color = ColorSection(self)
            for group in self.color.widgets():
                page.add(group)
        groups: dict[str, "Adw.PreferencesGroup"] = {}
        for item in self.backend.items_in(key):
            group = groups.get(item.group)
            if group is None:
                group = groups[item.group] = Adw.PreferencesGroup(title=item.group)
                page.add(group)
            row = self.rows[item.id] = ItemRow(self, item)
            group.add(row.row)
        self.stack.add_named(page, key)
        sidebar_row = Gtk.ListBoxRow()
        sidebar_row.key = key
        box = Gtk.Box(spacing=12, margin_top=10, margin_bottom=10, margin_start=6, margin_end=6)
        box.append(Gtk.Image(icon_name=icon_or(icon, "application-x-executable-symbolic")))
        label = Gtk.Label(label=title, xalign=0, hexpand=True, ellipsize=Pango.EllipsizeMode.END)
        box.append(label)
        counter = Gtk.Label(label="")
        counter.add_css_class("dim-label")
        counter.add_css_class("caption")
        box.append(counter)
        sidebar_row.set_child(box)
        sidebar_row.set_tooltip_text(about)
        self.counters[key] = counter
        self.sidebar.append(sidebar_row)
        self._count(key)

    def _count(self, key: str) -> None:
        done, total = self.backend.section_counts(key)
        self.counters[key].set_label(f"{done}/{total}" if total else "")

    @guarded
    def _section_selected(self, _box: "Gtk.ListBox", row: "Gtk.ListBoxRow | None") -> None:
        if row is None:
            return
        title = next(t for k, t, _i, _a in SECTIONS if k == row.key)
        about = next(a for k, _t, _i, a in SECTIONS if k == row.key)
        self.stack.set_visible_child_name(row.key)
        self.content_title.set_title(title)
        self.content_title.set_subtitle(about)
        self.split.set_show_content(True)

    # --- what the person asks for ----------------------------------------------

    def link(self, item: Item, value: bool | None) -> None:
        """Ticking something ticks what it needs. Unticking something unticks what needs it."""
        if value is True:
            for needed in item.requires:
                row = self.rows[needed]
                if row.value is not True:
                    row.set_value(True)
                    self.toast(f"Also ticked {row.item.title}: {item.title} needs it")
                    self.link(row.item, True)
        elif value is False:
            for other in self.backend.items:
                if item.id in other.requires:
                    row = self.rows[other.id]
                    if row.value is True:
                        row.set_value(False)
                        self.toast(f"Also unticked {other.title}: it needs {item.title}")
                        self.link(other, False)

    def update_bar(self) -> None:
        count = len(self.wanted)
        self.bar.set_reveal_child(count > 0)
        self.bar_label.set_label(plural(count, "change selected", "changes selected"))
        for key in self.counters:
            self._count(key)

    def clear_selection(self) -> None:
        for row in self.rows.values():
            row.refresh()
        self.wanted.clear()
        self.update_bar()

    @guarded
    def _recommended(self, *_args) -> None:
        ids = self.backend.recommended_ids()
        for item_id in ids:
            self.rows[item_id].set_value(True)
        if ids:
            self.toast(f"Ticked {plural(len(ids), 'recommended item', 'recommended items')}. "
                       "Nothing changes until you apply")
        else:
            self.toast("Everything recommended is already done")

    @guarded
    def _refresh(self, *_args) -> None:
        self.wanted.clear()
        self.stack.set_visible_child_name("loading")
        self.backend.refresh()
        self._recheck()

    def _recheck(self) -> None:
        """Read every item again in a thread, because the checks run commands, then bring the rows up to date."""
        def done(_r: object, _e: Exception | None) -> None:
            for row in self.rows.values():
                row.refresh()
            self.update_bar()
            selected = self.sidebar.get_selected_row()
            self.stack.set_visible_child_name(selected.key if selected else SECTIONS[0][0])
            if self.color is not None:
                self.color.load()
            background(self.backend.refresh_extensions, self._extensions_known)

        background(self.backend.check_all, done)

    def toast(self, text: str) -> None:
        self.toasts.add_toast(Adw.Toast(title=text, timeout=4))

    def copy_text(self, text: str) -> None:
        self.get_clipboard().set(text)
        self.toast("Copied to the clipboard")

    def open_url(self, url: str) -> None:
        try:
            Gio.AppInfo.launch_default_for_uri(url, None)
        except GLib.Error as exc:
            self.fail("Could not open the link", f"{exc.message}\n\n{url}")

    def fail(self, heading: str, body: str) -> None:
        dialog = Adw.AlertDialog(heading=heading, body=body)
        dialog.add_response("ok", "OK")
        dialog.present(self)

    # --- details ------------------------------------------------------------

    def link_bar(self, links: list[tuple[str, str]]) -> "Gtk.Box":
        """The buttons under a dialog full of commands: the pages that explain them."""
        bar = Gtk.Box(spacing=8, halign=Gtk.Align.END, margin_top=8, margin_bottom=10, margin_end=12)
        for label, url in links:
            button = Gtk.Button(label=label)
            button.connect("clicked", lambda _b, link=url: self.open_url(link))
            bar.append(button)
        return bar

    def show_text(self, title: str, text: str, links: list[tuple[str, str]]) -> None:
        dialog, view = dialog_shell(title, 700, 560)
        view.set_content(scrolled(text_view(text)))
        view.add_bottom_bar(self.link_bar(links))
        dialog.present(self)

    @guarded
    def show_details(self, item: Item) -> None:
        dialog, view = dialog_shell(item.title, 780, 700)
        spinner = Adw.StatusPage(title="Working it out", child=Gtk.Spinner(spinning=True, width_request=32,
                                                                           height_request=32))
        view.set_content(spinner)
        dialog.present(self)

        def done(text: object, error: Exception | None) -> None:
            body = str(text) if error is None else f"Could not work this out: {error}"
            view.set_content(scrolled(text_view(body)))
            reference = reference_url(item.section, item.id)
            view.add_bottom_bar(self.link_bar([("Open the guide", item.url),
                                               ("Exact commands on the site", reference)]))

        background(lambda: self.backend.describe(item), done)

    # --- review and apply -----------------------------------------------------

    @guarded
    def _review(self, _button: "Gtk.Button") -> None:
        if self.busy or not self.wanted:
            return
        self.review_button.set_sensitive(False)
        self.review_button.set_label("Working it out")
        wanted = dict(self.wanted)

        def done(built: object, error: Exception | None) -> None:
            self.review_button.set_sensitive(True)
            self.review_button.set_label("Review and apply")
            if error is not None:
                self.fail("Could not prepare the changes", str(error))
                return
            self._show_review(built)  # type: ignore[arg-type]

        background(lambda: self.backend.build_plan(wanted), done)

    def _show_review(self, built: Built) -> None:
        dialog, view = dialog_shell("Review changes", 780, 720)
        page = Adw.PreferencesPage()
        plan = built.plan
        if built.blockers:
            page.add(rows_group("This cannot run yet",
                                [info_row(b, icon="dialog-error-symbolic") for b in built.blockers]))
        if built.warnings:
            page.add(rows_group("Good to know", [info_row(w, icon="dialog-warning-symbolic") for w in built.warnings]))
        if built.turn_on:
            page.add(rows_group("Turning on",
                                [info_row(i.title, i.summary, "list-add-symbolic") for i in built.turn_on]))
        if built.included:
            page.add(rows_group("Included because something needs it", [info_row(t) for t in built.included]))
        if built.turn_off:
            page.add(rows_group("Turning off", [info_row(i.title, i.summary, "list-remove-symbolic")
                                                for i in built.turn_off]))
        software = []
        groups = (("Install from the repositories", plan.pacman),
                  ("Install from the AUR, in a terminal window", plan.aur),
                  ("Install from Flathub", plan.flatpak),
                  ("Remove", [*plan.remove_pacman, *plan.remove_flatpak]))
        for label, names in groups:
            if names:
                software.append(info_row(label, ", ".join(names), "package-x-generic-symbolic"))
        if software:
            page.add(rows_group("Software", software))
        notes = [info_row(n, icon="dialog-information-symbolic") for n in plan.notes]
        if plan.reboot_for:
            notes.append(info_row("Needs a reboot", ", ".join(plan.reboot_for), "system-reboot-symbolic"))
        if plan.relogin_for:
            notes.append(info_row("Needs logging out and back in", ", ".join(plan.relogin_for),
                                  "system-log-out-symbolic"))
        if notes:
            page.add(rows_group("Notes", notes))
        if built.manual:
            page.add(rows_group("Left for you afterwards", [
                info_row(title, "\n".join(f"{n}. {s}" for n, s in enumerate(steps, 1)), "document-edit-symbolic")
                for title, steps in built.manual]))
        commands = Adw.PreferencesGroup()
        commands.add(self._command_expander("Show the exact commands",
                                            "Everything that will run, in order, nothing cut short",
                                            render_plan(built.plan)))
        if plan.pacman or plan.root or plan.root_early or plan.remove_pacman:
            commands.add(self._command_expander("Show the root script, word for word",
                                                "The one script that goes to pkexec, as it is passed on",
                                                root_script(plan)))
        reference = Adw.ActionRow(title="Every item with its commands and the way back", use_markup=False,
                                  activatable=True, subtitle="The reference on the site")
        reference.add_suffix(Gtk.Image(icon_name=icon_or("adw-external-link-symbolic", "web-browser-symbolic")))
        reference.connect("activated", lambda _r: self.open_url(f"{SITE}/docs/setup-script/reference/"))
        commands.add(reference)
        page.add(commands)
        view.set_content(page)
        bar = Gtk.Box(spacing=8, halign=Gtk.Align.END, margin_top=8, margin_bottom=10, margin_end=12)
        cancel = Gtk.Button(label="Cancel")
        cancel.connect("clicked", lambda _b: dialog.close())
        apply_button = Gtk.Button(label="Apply", sensitive=built.ok and not plan.empty)
        apply_button.add_css_class("suggested-action")
        apply_button.connect("clicked", lambda _b: (dialog.close(), self._apply(built)))
        bar.append(cancel)
        bar.append(apply_button)
        view.add_bottom_bar(bar)
        dialog.present(self)

    def _command_expander(self, title: str, subtitle: str, text: str) -> "Adw.ExpanderRow":
        """A row that unfolds into commands you can select."""
        expander = Adw.ExpanderRow(title=title, subtitle=subtitle)
        label = Gtk.Label(label=text.rstrip(), selectable=True, xalign=0, wrap=True, margin_top=10,
                          margin_bottom=10, margin_start=12, margin_end=12)
        label.add_css_class("zs-log")
        expander.add_row(Gtk.ListBoxRow(activatable=False, selectable=False, child=label))
        return expander

    def _apply(self, built: Built) -> None:
        self.busy = True
        self._stop_waiting = False
        progress = ProgressDialog(self, lambda: setattr(self, "_stop_waiting", True))

        def emit(text: str) -> None:
            log.info("| %s", text)
            call_in_ui(progress.line, text)

        executor = Executor(self.backend, emit, lambda text: call_in_ui(progress.phase, text),
                            lambda: self._stop_waiting, lambda on: call_in_ui(progress.waiting, on))

        def finished(report: object, error: Exception | None) -> None:
            self.busy = False
            progress.finish(report, error, built)  # type: ignore[arg-type]
            self.wanted.clear()
            self.update_bar()
            self._recheck()

        background(lambda: executor.run(built), finished)

    # --- the rest ---------------------------------------------------------------

    def _close_request(self, _window: "Gtk.Window") -> bool:
        if self.busy:
            self.fail("Changes are running", "Wait until they are done. Closing now could leave things half set up.")
            return True
        return False

    def _about(self, *_args) -> None:
        about = Adw.AboutDialog(application_name=TITLE, developer_name="Stensel8", website=SITE,
                                issue_url=f"https://github.com/{REPO}/issues", license_type=Gtk.License.MIT_X11,
                                comments="A checklist for the setups described in the Zephyrus Linux guides.",
                                application_icon="preferences-system-symbolic")
        about.present(self)


_Application = Adw.Application if Adw is not None else object


class SetupApplication(_Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID)
        self.connect("activate", self._activate)

    def _activate(self, _app: "SetupApplication") -> None:
        window = self.props.active_window
        if window is None:
            provider = Gtk.CssProvider()
            if hasattr(provider, "load_from_string"):
                provider.load_from_string(CSS)
            else:
                provider.load_from_data(CSS.encode())
            Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider,
                                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            window = SetupWindow(self, Backend())
        window.present()


def main() -> None:
    if sys.version_info < MIN_PYTHON:
        need = ".".join(str(n) for n in MIN_PYTHON)
        have = ".".join(str(n) for n in sys.version_info[:3])
        print(f"This script needs Python {need} or newer; this is {have}.", file=sys.stderr)
        sys.exit(1)
    if os.geteuid() == 0:
        print("Run this as your normal user. It asks for root when it needs it.", file=sys.stderr)
        sys.exit(1)
    if Gtk is None or Adw is None:
        print("The window needs PyGObject with GTK 4 and libadwaita.\n"
              "On Arch and CachyOS: sudo pacman -S python-gobject gtk4 libadwaita\n"
              f"({TOOLKIT_ERROR})", file=sys.stderr)
        sys.exit(1)
    if (Adw.get_major_version(), Adw.get_minor_version()) < MIN_ADW:
        print(f"libadwaita {MIN_ADW[0]}.{MIN_ADW[1]} or newer is needed; this is {Adw.get_major_version()}."
              f"{Adw.get_minor_version()}.", file=sys.stderr)
        sys.exit(1)
    if not (os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")):
        print("This opens a window, and there is no graphical session to open it in.", file=sys.stderr)
        sys.exit(1)
    setup_logging()
    log.info("start: %s, python %s, %s", read_os_release().get("PRETTY_NAME", "?"), sys.version.split()[0], APP_ID)
    sys.exit(SetupApplication().run([sys.argv[0]]))


if __name__ == "__main__":
    main()
