#!/usr/bin/env python3
# Copyright (C) 2026 Sten Tijhuis
# SPDX-License-Identifier: MIT
"""
Write the reference of the setup script: for every item, the exact commands that ticking it runs and that unticking
it runs to put things back, a diff for every existing file they change, and a link to the code behind them.

    .github/scripts/generate-setup-reference.py

The pages are not committed: the site build runs this first, so they always describe the script they are built from.
Nothing about what an item runs is written down here. The script is imported and every item's own builders run, the
same functions the window runs, on a machine that is described instead of read: a fresh CachyOS install for turning
things on, and the same install with everything set up for turning things off. The files the script edits are fed what
a fresh Arch install ships (STOCK), so a diff on the site is what happens on a stock machine. The window shows the
diff against your own files before it applies one.
"""

import ast
import importlib.util
import os
import subprocess
import sys
import tempfile
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "src" / "static" / "scripts" / "quicksetup.py"
OUT_DIR = REPO_ROOT / "src" / "content" / "docs" / "setup-script" / "reference"
USER = "your-username"
LOADERS = ("limine", "grub", "systemd-boot")
HOOKS = ("extra_on", "extra_off", "on_blocker", "off_blocker")

# The files the script edits, as a fresh Arch install ships them: gdm's gdm.conf-custom.in, the sudo.pam of Arch's sudo
# package, gdm's pam-arch/gdm-password.pam (in /etc/pam.d), and polkit's polkit-1 (in /usr/lib/pam.d, system-auth).
STOCK = {
    "etc/gdm/custom.conf": (
        "# GDM configuration storage\n\n[daemon]\n\n[security]\n\n[debug]\n"
        "# Uncomment the line below to turn on debugging\n#Enable=true\n"),
    "etc/pam.d/sudo": (
        "#%PAM-1.0\nauth\t\tinclude\t\tsystem-auth\naccount\t\tinclude\t\tsystem-auth\n"
        "session\t\tinclude\t\tsystem-auth\nsession\t\toptional\tpam_systemd.so class=none\n"),
    "etc/pam.d/gdm-password": (
        "#%PAM-1.0\n\nauth       include                     system-local-login\n"
        "auth       optional                    pam_gnome_keyring.so\n\n"
        "account    include                     system-local-login\n\n"
        "password   include                     system-local-login\n"
        "password   optional                    pam_gnome_keyring.so use_authtok\n\n"
        "session    include                     system-local-login\n"
        "session    optional                    pam_gnome_keyring.so auto_start\n"),
    "usr/lib/pam.d/polkit-1": (
        "#%PAM-1.0\n\nauth       include      system-auth\naccount    include      system-auth\n"
        "password   include      system-auth\nsession    include      system-auth\n"),
}

# What a visitor reads around the commands. The commands and their descriptions are not translated: they are what the
# window shows, and the window is in English.
TEXT = {
    "en": {
        "intro": "The exact commands behind the **{title}** section of the [setup script]({setup}): what ticking an "
                 "item runs, and what unticking it runs to put things back. Generated from "
                 "[`quicksetup.py`]({source}), so it cannot say anything the window does not do. "
                 "[How to read this page]({reference}).",
        "on": "Turning it on", "off": "Turning it off (the way back)",
        "also": "Ticking it also ticks what it needs, so the commands below include theirs.",
        "guide": "Guide", "needs": "Needs", "conflicts": "Cannot be on together with", "only": "Only on",
        "source": "Source", "entry": "the entry", "diff": "The edit, as a diff:",
        "reboot": "Needs a reboot", "relogin": "Needs logging out and back in",
        "by_hand_on": "By hand, to set it up", "by_hand_off": "By hand, to undo it",
        "after_on": "Left for you after ticking it", "after_off": "Left for you after unticking it",
        "guide_only": "This row is a guide and has no checkbox: the steps stay yours, because a mistake in them can "
                      "stop the machine from booting.",
        "hardware": {"asus": "an ASUS laptop", "g16": "the Zephyrus G16 (GA605WV)", "gnome": "the GNOME desktop",
                     "nvidia": "a machine with an NVIDIA GPU",
                     "mt7925": "a machine with the MediaTek MT7925 Wi-Fi card"},
        "packages": "From the AUR unless a repository you use carries the package: then it is the `pacman` line.",
        "color_title": "Color mode",
        "color": "The Native and sRGB switch in the Display section works right away, without an apply step. There is "
                 "no checkbox to untick: switching to the other mode is the way back.",
    },
    "nl": {
        "intro": "De exacte commando's achter de sectie **{title}** van het [setup-script]({setup}): wat aanvinken "
                 "van een onderdeel draait, en wat uitvinken draait om alles terug te zetten. Gegenereerd uit "
                 "[`quicksetup.py`]({source}), dus er kan niets op staan wat het venster niet doet. "
                 "[Zo lees je deze pagina]({reference}).",
        "on": "Aanzetten", "off": "Uitzetten (het terugdraaien)",
        "also": "Aanvinken vinkt ook aan wat het nodig heeft, dus de opdrachten daarvan staan hieronder ook.",
        "guide": "Handleiding", "needs": "Vereist", "conflicts": "Kan niet tegelijk aan met", "only": "Alleen op",
        "source": "Bron", "entry": "de regel", "diff": "De wijziging, als diff:",
        "reboot": "Herstart nodig", "relogin": "Opnieuw inloggen nodig",
        "by_hand_on": "Met de hand, om het in te richten", "by_hand_off": "Met de hand, om het terug te draaien",
        "after_on": "Voor jou over na het aanvinken", "after_off": "Voor jou over na het uitvinken",
        "guide_only": "Deze rij is een handleiding en heeft geen vinkje: de stappen blijven van jou, omdat een fout "
                      "erin de machine kan laten stoppen met opstarten.",
        "hardware": {"asus": "een ASUS-laptop", "g16": "de Zephyrus G16 (GA605WV)", "gnome": "het GNOME-bureaublad",
                     "nvidia": "een machine met een NVIDIA-GPU",
                     "mt7925": "een machine met de MediaTek MT7925 Wi-Fi-kaart"},
        "packages": "Uit de AUR, tenzij een repository die je gebruikt het pakket heeft: dan is het de `pacman`-regel.",
        "color_title": "Kleurstand",
        "color": "De schakelaar tussen Native en sRGB in de sectie Display werkt meteen, zonder toepassen. Er is geen "
                 "vinkje om weg te halen: overschakelen naar de andere stand is de weg terug.",
    },
}


def load_setup(home: Path):
    """Import the setup script with a home folder that is not yours, so the paths it works out never differ."""
    os.environ["HOME"] = str(home)
    for name in ("XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME"):
        os.environ.pop(name, None)
    spec = importlib.util.spec_from_file_location("quicksetup", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["quicksetup"] = module
    spec.loader.exec_module(module)
    return module


def machine(home, installed=(), aur=(), flatpaks=(), settings=None, loader="limine"):
    """A CachyOS install on a Zephyrus G16 under GNOME that is described, not read. What is installed is given."""
    settings = settings or {}
    return SimpleNamespace(
        os_name="CachyOS Linux", is_arch=True, is_ostree=False, user=USER, home=home, vendor="ASUSTeK COMPUTER INC.",
        board="GA605WV", bios="GA605WV.309", product="ROG Zephyrus G16", desktop="GNOME", session_type="wayland",
        is_gnome=True, is_asus=True, is_g16=True, model="GA605WV", has_nvidia=True, has_mt7925=True, cmdline="",
        pacman_installed=lambda: set(installed), flatpaks=lambda: set(flatpaks), in_repos=lambda name: name not in aur,
        has_flathub=lambda: True, has_cmd=lambda name: True, bootloader=lambda: loader,
        unit_state=lambda unit: "enabled", unit_active=lambda unit: True, out=lambda cmd: "",
        gsettings=lambda schema, key: settings.get((schema, key)), kernel_package=lambda: "linux-cachyos",
        shell_version=lambda: (51, "51.0"), shell_extensions=lambda: set(), in_group=lambda group: False,
        refresh=lambda: None)


@dataclass
class Recipe:
    """What one item runs, one way and the other (a quicksetup.Plan), and the steps left to you per boot loader."""
    on: object = None
    off: object = None
    manual_on: dict = field(default_factory=dict)
    manual_off: dict = field(default_factory=dict)


def write_files(root: Path, files: dict) -> None:
    for name, content in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(content, encoding="utf-8")


def build_recipes(q, workdir: Path):
    """Run every builder of every item on the two stand-in machines. Returns the items, recipes and path swaps."""
    home = Path(os.environ["HOME"])
    swaps = [(str(home), f"/home/{USER}"), (str(workdir / "fresh"), ""), (str(workdir / "configured"), "")]
    items = q.build_items()
    aur = {name for item in items for name in item.aur}
    by_id = {item.id: item for item in items}
    recipes = {item.id: Recipe() for item in items}
    panel = q.Panel("eDP-1", "1002", q.Edid("SHP", "104D", "158E", "", None, None))

    def needs(item):
        """The item and everything it needs: the window ticks those too, and plans them in catalogue order."""
        return {item.id}.union(*(needs(by_id[other]) for other in item.requires))

    def run_all(way, who, root, git, copies):
        """One direction of every item, with the script's own constants and probes pointed at a stand-in root."""
        with ExitStack() as stack:
            for name, where in (("GDM_CONF", "etc/gdm/custom.conf"), ("PAM_DIR", "etc/pam.d"),
                                ("PAM_VENDOR_DIR", "usr/lib/pam.d")):
                stack.enter_context(mock.patch.object(q, name, root / where))
            for name, value in (("internal_panel", lambda: panel), ("git_config", lambda key: git.get(key, "")),
                                ("system_color_copies", lambda s, retired_only=False: [] if retired_only else copies)):
                stack.enter_context(mock.patch.object(q, name, value))
            stack.enter_context(mock.patch.object(
                q.shutil, "disk_usage", lambda path: SimpleNamespace(total=10**12, used=0, free=10**12)))
            for item in items:
                if item.guide_only:
                    continue
                if getattr(item, way) is None:
                    sys.exit(f"{item.id}: there is no way to turn it {way}")
                plan, wanted = q.Plan(), needs(item) if way == "on" else {item.id}
                try:
                    for part in (other for other in items if other.id in wanted):
                        getattr(part, way)(who, plan)
                except Exception as exc:  # whatever it is, the person fixing it needs to know which item it was
                    sys.exit(f"{item.id}: turning it {way} fails on the stand-in machine: {type(exc).__name__}: {exc}")
                if plan.empty:
                    sys.exit(f"{item.id}: turning it {way} runs nothing")
                setattr(recipes[item.id], way, plan)

    # A fresh machine: nothing installed, nothing set, the stock files where the packages put them.
    write_files(workdir / "fresh", STOCK)
    run_all("on", machine(home, aur=aur), workdir / "fresh", {"user.signingkey": "<your key id>"}, [])

    # The same machine with all of that done: what is installed and set is what turning everything on did.
    plans = [recipe.on for recipe in recipes.values() if recipe.on]
    settings = {(step.argv[2], step.argv[3]): step.argv[4] for plan in plans for step in plan.steps
                if step.argv and step.argv[:2] == ["gsettings", "set"]}
    configured = {**STOCK, "etc/gdm/custom.conf.zephyrus-setup.bak": STOCK["etc/gdm/custom.conf"],
                  "etc/pam.d/polkit-1": STOCK["usr/lib/pam.d/polkit-1"]}
    for name in ("sudo", "gdm-password", "polkit-1"):
        configured[f"etc/pam.d/{name}"] = q.pam_with_u2f(configured[f"etc/pam.d/{name}"])
    configured["etc/gdm/custom.conf"] = q.set_ini_keys(STOCK["etc/gdm/custom.conf"], "daemon", {
        "AutomaticLoginEnable": "True", "AutomaticLogin": USER})
    write_files(workdir / "configured", configured)
    done = machine(home, {name for plan in plans for name in (*plan.pacman, *plan.aur)}, aur,
                   {name for plan in plans for name in plan.flatpak}, settings)
    git = {"user.signingkey": "<your key id>", "commit.gpgsign": "true", "tag.gpgsign": "true"}
    run_all("off", done, workdir / "configured", git, [q.COLORD_STORE / name for _, name in q.profile_set(done, panel)])

    # The steps left for you can depend on the boot loader, so they are worked out for each one.
    for item in items:
        for loader in LOADERS:
            who = machine(home, aur=aur, loader=loader)
            recipes[item.id].manual_on[loader] = item.manual_steps(who)
            recipes[item.id].manual_off[loader] = item.manual_off_steps(who)
    return items, recipes, swaps


def source_map() -> dict:
    """Where the code behind every item is, as (label, first line, last line): its entry and the functions it names."""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    functions = {node.name: (node.lineno, node.end_lineno) for node in tree.body if isinstance(node, ast.FunctionDef)}
    found = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.args
                and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            continue
        item_id, name = node.args[0].value, node.func.id
        if name == "ExtensionSpec":  # the extensions are made in a loop over the EXTENSIONS table
            item_id, refs = f"ext-{item_id}", ["extension_item", "install_extension", "remove_extension"]
        elif name in ("Item", "package_item"):
            hooks = [*node.args[6:8], *(kw.value for kw in node.keywords if kw.arg in HOOKS)]
            refs = [hook.id for hook in hooks if isinstance(hook, ast.Name)]
        else:
            continue
        found[item_id] = [("entry", node.lineno, node.end_lineno)] + [
            (ref, *functions[ref]) for ref in refs if ref in functions]
    return found


def source_url(q) -> str:
    """The script on GitHub at the commit the pages are built from, so a line range in a link stays right."""
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        head = "main"
    return f"https://github.com/{q.REPO}/blob/{head}/src/static/scripts/quicksetup.py"


def fence(language: str, text: str) -> str:
    return f"```{language}\n{text.rstrip()}\n```"


def tidy(text: str, swaps: list) -> str:
    """Put the paths of the stand-in machine back as the paths of a real one."""
    for needle, replacement in swaps:
        text = text.replace(needle, replacement)
    return text


def direction(ctx, plan, text: dict) -> list:
    """One direction of one item: its commands as the window lists them, the diffs of the files it changes, notes."""
    commands = ctx.q.plan_commands(plan)
    lines = []
    for phase, title in ctx.q.PHASE_TITLES.items():
        group = [command for command in commands if command.phase == phase]
        lines += [f"# --- {title} ---", ""] if group else []
        for command in group:
            lines += [f"# {command.desc}", command.text, ""]
    out = [fence("bash", tidy("\n".join(lines), ctx.swaps)), ""]
    diffs = [command.diff for command in commands if command.diff]
    if diffs:
        out += [text["diff"], ""]
        for diff in diffs:
            out += [fence("diff", tidy(diff, ctx.swaps)), ""]
    facts = [tidy(note, ctx.swaps) for note in plan.notes]
    facts += [f"{text[key]}: {', '.join(names)}." for key, names in
              (("reboot", plan.reboot_for), ("relogin", plan.relogin_for)) if names]
    return out + [f"- {fact}" for fact in facts] + [""] * bool(facts)


def steps_block(label: str, by_loader: dict) -> list:
    """Steps left to you. When the boot loader changes them, each boot loader gets its own list."""
    lists = {loader: steps for loader, steps in by_loader.items() if steps}
    if len({tuple(steps) for steps in lists.values()}) == 1:
        lists = {"": next(iter(lists.values()))}
    out = []
    for loader, steps in lists.items():
        out += [f"**{label}{f' ({loader})' if loader else ''}**", ""]
        out += [f"{number}. {step}" for number, step in enumerate(steps, 1)] + [""]
    return out


def item_markdown(ctx, item, lang: str) -> list:
    """One item: where it comes from and what it needs, then the commands for turning it on and off."""
    text, recipe = TEXT[lang], ctx.recipes[item.id]

    def link(other_id):
        other = ctx.by_id[other_id]
        return f"[{other.title}]({'' if other.section == item.section else f'../{other.section}/'}#{other_id})"

    # The anchors are those of the English guides. The Dutch guides have translated headings, so a Dutch page links to
    # the guide itself: an anchor that is not there is a link that does not work.
    page, _, anchor = item.doc.partition("#")
    page = page.strip("/")
    guide = '{{< relref "/docs/' + page + '" >}}' + (f"#{anchor}" if anchor and lang == "en" else "")
    facts = {text["guide"]: f"[`{page}`]({guide})"}
    if item.requires:
        facts[text["needs"]] = ", ".join(map(link, item.requires))
    if item.conflicts:
        facts[text["conflicts"]] = ", ".join(map(link, item.conflicts))
    only = [item.hardware] * bool(item.hardware) + ["gnome"] * item.needs_gnome
    if only:
        facts[text["only"]] = ", ".join(text["hardware"][name] for name in only)
    facts[text["source"]] = " · ".join(
        f"[{text['entry'] if label == 'entry' else '`' + label + '`'}]({ctx.source}#L{first}-L{last})"
        for label, first, last in ctx.sources[item.id])
    out = [f"### {item.title} {{#{item.id}}}", "", item.summary, ""]
    out += [f"- **{label}:** {value}" for label, value in facts.items()] + [""]
    if item.guide_only:
        return (out + [text["guide_only"], ""] + steps_block(text["by_hand_on"], recipe.manual_on)
                + steps_block(text["by_hand_off"], recipe.manual_off))
    out += [text["also"], ""] if item.requires else []
    out += [f"**{text['on']}**", ""] + direction(ctx, recipe.on, text)
    out += [text["packages"], ""] if item.aur else []
    out += steps_block(text["after_on"], recipe.manual_on)
    out += [f"**{text['off']}**", ""] + direction(ctx, recipe.off, text)
    return out + steps_block(text["after_off"], recipe.manual_off)


def section_page(ctx, key: str, title: str, weight: int, lang: str) -> str:
    """One page of the reference: a section of the window, with a heading per item."""
    text = TEXT[lang]
    edit = f"https://github.com/{ctx.q.REPO}/edit/main/src/static/scripts/quicksetup.py"
    out = ["---", f'title: "{title}"', f"weight: {weight}", f"editURL: {edit}", "---", "",
           "<!-- markdownlint-disable MD010 -->", "",  # the stock PAM files in the diffs are indented with tabs
           text["intro"].format(title=title, source=ctx.source, setup='{{< relref "/docs/setup-script" >}}',
                                reference='{{< relref "/docs/setup-script/reference" >}}'), ""]
    if key == "display":
        out += [f"## {text['color_title']} {{#color-mode}}", "", text["color"], "",
                fence("text", ctx.q.color_runs("eDP-1")), ""]
    groups = {}
    for item in ctx.items:
        if item.section == key:
            groups.setdefault(item.group or title, []).append(item)
    for group, members in groups.items():
        out += [f"## {group}", ""]
        for item in members:
            out += item_markdown(ctx, item, lang)
    return "\n".join(out).rstrip() + "\n"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="zs-") as tmp:
        workdir = Path(tmp)
        (workdir / "home" / USER).mkdir(parents=True)
        q = load_setup(workdir / "home" / USER)
        items, recipes, swaps = build_recipes(q, workdir)
        sources = source_map()
        missing = [item.id for item in items if item.id not in sources]
        if missing:
            sys.exit(f"No entry found in build_items() for: {', '.join(missing)}")
        ctx = SimpleNamespace(q=q, items=items, recipes=recipes, swaps=swaps, sources=sources, source=source_url(q),
                              by_id={item.id: item for item in items})
        for old in OUT_DIR.glob("*.md"):
            if not old.name.startswith("_index"):
                old.unlink()
        for weight, (key, title, _icon, _about) in enumerate(q.SECTIONS, start=1):
            for lang, suffix in (("en", ""), ("nl", ".nl")):
                page = section_page(ctx, key, title, weight, lang)
                (OUT_DIR / f"{key}{suffix}.md").write_text(page, encoding="utf-8")
        print(f"Wrote {len(q.SECTIONS) * 2} pages to {OUT_DIR.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
