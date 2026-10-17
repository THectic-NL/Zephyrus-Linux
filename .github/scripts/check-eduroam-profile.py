#!/usr/bin/env python3
# Copyright (C) 2026 Sten Tijhuis
# SPDX-License-Identifier: MIT
"""Watch what Saxion publishes about its eduroam network.

saxion-eduroam.py hard-codes Saxion's eduroam setup: PEAP with MSCHAPv2
inside, the RADIUS server name, the realm. Saxion can change any of that
without telling anyone, and until now the first sign was a reader whose
connection stopped working. Issue #109 went exactly like that.

Two public sources say what Saxion publishes today:

  1. discovery.eduroam.app, the feed the geteduroam apps read. It lists every
     profile an institution offers. A profile with "oauth": true is
     geteduroam's certificate route: EAP-TLS with a personal certificate,
     issued after a login in the browser. Most Dutch institutions already
     have one. Saxion getting one is the sign that it is moving off
     PEAP/MSCHAPv2, and saxion-eduroam.py cannot follow it there.
  2. cat.eduroam.org, Saxion's CAT profile: the EAP methods, server names and
     CA certificates the official installers are built from, plus the date
     the profile was last edited.

Both are compared with saxion-eduroam-baseline.json, which is itself checked
against the constants in saxion-eduroam.py. A change on Saxion's side fails
this check. So does a script edit that leaves the baseline describing
something the script no longer does.

The CA certificates in the CAT profile are not the ones the script trusts.
The profile still pins the pre-migration USERTrust chain (#109). They are
watched anyway: the day Saxion corrects them, the guide's explanation of why
the official installers fail is out of date.

What this cannot see is the certificate the RADIUS server itself presents.
That only shows up in an EAP handshake on campus, not from a CI runner.

Usage:
  check-eduroam-profile.py                  # compare, exit 1 on a difference
  check-eduroam-profile.py --apply          # rewrite the baseline from live data
  check-eduroam-profile.py --report FILE    # also write the findings as Markdown

Exit status: 0 nothing changed, 1 something changed or the baseline and the
script disagree, 2 a source could not be fetched or read. The workflow opens
an issue only on 1, so an outage at CAT does not open one.
"""
from __future__ import annotations

import argparse
import ast
import base64
import gzip
import hashlib
import io
import json
import pathlib
import shutil
import ssl
import subprocess
import sys
import time
import urllib.parse
import urllib.request
# The eap-config comes from CAT over HTTPS, not from a stranger, and expat has
# refused external entities and capped entity expansion since 2.4.1. The size
# cap in fetch() is the rest of the defence.
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASELINE = ROOT / ".github" / "scripts" / "saxion-eduroam-baseline.json"
SCRIPT = ROOT / "src" / "static" / "scripts" / "saxion-eduroam.py"

DISCOVERY_URL = "https://discovery.eduroam.app/v1/discovery.json"
CAT_API = "https://cat.eduroam.org/user/API.php"
USER_AGENT = "Zephyrus-Linux eduroam watch (+https://github.com/THectic-NL/Zephyrus-Linux)"

# The discovery feed is about 2 MB unpacked. Anything far beyond that is not
# the file we think it is.
MAX_BYTES = 32 * 1024 * 1024

# Saxion's identity provider in CAT. The baseline holds everything else.
CAT_IDP = 2446

# IANA EAP method types, and the eap-config schema's non-EAP inner methods.
EAP_NAMES = {4: "MD5", 6: "GTC", 13: "EAP-TLS", 21: "EAP-TTLS", 25: "PEAP",
             26: "MSCHAPv2", 43: "EAP-FAST", 55: "TEAP"}
NON_EAP_NAMES = {1: "PAP", 2: "MSCHAP", 3: "MSCHAPv2"}

# The nmcli settings saxion-eduroam.py writes, and the CAT method they are.
# A script that moves to another method needs an entry here first.
SCRIPT_METHODS = {("peap", "mschapv2"): (25, "eap:26")}


class FetchError(Exception):
    """A source could not be fetched or did not contain what it should."""


# ── Reading the sources ──────────────────────────────────────────────────────

def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            # Fixed https:// URLs only, never one read from a response.
            with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
                body = response.read(MAX_BYTES + 1)
            break
        except OSError as error:  # URLError, HTTPError, timeouts, resets
            if attempt == 2:
                raise FetchError(f"{url}: {error}") from error
            time.sleep(5 * (attempt + 1))
    # The discovery feed is stored gzipped and served that way whether or not
    # the client asked for it, so look at the bytes rather than the headers.
    if len(body) <= MAX_BYTES and body[:2] == b"\x1f\x8b":
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(body)) as packed:
                body = packed.read(MAX_BYTES + 1)
        except (OSError, EOFError) as error:
            raise FetchError(f"{url}: broken gzip ({error})") from error
    if len(body) > MAX_BYTES:
        raise FetchError(f"{url}: larger than {MAX_BYTES} bytes")
    return body


def fetch_json(url: str) -> dict:
    try:
        data = json.loads(fetch(url))
    except ValueError as error:
        raise FetchError(f"{url}: not JSON ({error})") from error
    if not isinstance(data, dict):
        raise FetchError(f"{url}: expected a JSON object")
    return data


def cat_url(**params: str | int) -> str:
    return f"{CAT_API}?{urllib.parse.urlencode({**params, 'lang': 'en'})}"


def read_discovery() -> list[dict]:
    """Every discovery entry for Saxion: its CAT IdP, or a name that says so."""
    feed = fetch_json(DISCOVERY_URL)
    if not isinstance(feed.get("instances"), list):
        raise FetchError(f"{DISCOVERY_URL}: no instance list")
    found = []
    for instance in feed["instances"]:
        if instance.get("cat_idp") != CAT_IDP and "saxion" not in str(instance.get("name", "")).lower():
            continue
        profiles = [{"id": str(p.get("id")), "name": str(p.get("name")), "oauth": bool(p.get("oauth"))}
                    for p in instance.get("profiles", [])]
        found.append({"id": str(instance.get("id")), "name": str(instance.get("name")),
                      "profiles": sorted(profiles, key=lambda p: p["id"])})
    return sorted(found, key=lambda i: i["id"])


def read_cat(profile: int, ders: dict[str, bytes]) -> dict:
    attributes = fetch_json(cat_url(action="profileAttributes", profile=profile))
    data = attributes.get("data")
    if attributes.get("status") != 1 or not isinstance(data, dict):
        raise FetchError(f"CAT profile {profile}: no profile attributes")
    linux = next((d for d in data.get("devices", []) if d.get("id") == "linux"), None)
    config = parse_eap_config(fetch(cat_url(action="downloadInstaller", device="eap-config",
                                            profile=profile, generatedfor="user")), ders)
    return {
        "profile": profile,
        "last_changed": data.get("last_changed"),
        # A redirect here would send Linux users of the official CAT page
        # somewhere else, most likely to geteduroam.
        "linux_device": None if linux is None else {"status": linux.get("status"),
                                                    "redirect": linux.get("redirect")},
        **config,
    }


def parse_eap_config(document: bytes, ders: dict[str, bytes]) -> dict:
    """The parts of an eap-config the script depends on.

    CA certificates are kept as SHA-256 digests; the certificates themselves
    go into ders, to name them in the report.
    """
    try:
        # Trusted enough, see the import.
        root = ET.fromstring(document)  # nosec B314
    except ET.ParseError as error:
        raise FetchError(f"eap-config: not XML ({error})") from error
    provider = root.find("EAPIdentityProvider")
    if provider is None:
        raise FetchError("eap-config: no EAPIdentityProvider")

    methods = []
    for method in provider.iter("AuthenticationMethod"):
        try:
            outer = int(method.findtext("EAPMethod/Type", ""))
            inner = []
            for inner_method in method.findall("InnerAuthenticationMethod"):
                if (eap := inner_method.findtext("EAPMethod/Type")) is not None:
                    inner.append(f"eap:{int(eap)}")
                if (non_eap := inner_method.findtext("NonEAPAuthMethod/Type")) is not None:
                    inner.append(f"non-eap:{int(non_eap)}")
            cas = []
            for ca in method.findall("ServerSideCredential/CA"):
                der = base64.b64decode(ca.text or "")
                ders[hashlib.sha256(der).hexdigest()] = der
                cas.append(hashlib.sha256(der).hexdigest())
        except ValueError as error:  # bad numbers and bad base64 alike
            raise FetchError(f"eap-config: unreadable authentication method ({error})") from error
        methods.append({
            "outer": outer,
            "inner": inner,
            "server_ids": sorted(text(e) for e in method.findall("ServerSideCredential/ServerID")),
            "ca_sha256": sorted(cas),
            "outer_identity": method.findtext("ClientSideCredential/OuterIdentity"),
            "inner_identity_suffix": method.findtext("ClientSideCredential/InnerIdentitySuffix"),
        })
    if not methods:
        raise FetchError("eap-config: no authentication methods")

    return {
        "realm": provider.get("ID"),
        "methods": methods,
        "ssids": sorted(text(e) for e in provider.iter("SSID")),
        "consortium_oids": sorted(text(e) for e in provider.iter("ConsortiumOID")),
    }


def text(element: ET.Element) -> str:
    return (element.text or "").strip()


def read_live(baseline: dict, ders: dict[str, bytes]) -> dict:
    discovery = read_discovery()
    profile = baseline["cat"]["profile"]
    listed = {p["id"] for i in discovery for p in i["profiles"]}
    # A profile that is gone from the feed is gone from CAT too, and CAT
    # answers for it with a bare 500. Report the first, do not fail on the second.
    cat = read_cat(profile, ders) if f"cat_{profile}" in listed else None
    return {"discovery": discovery, "cat": cat}


def read_script() -> dict:
    """The constants and nmcli settings saxion-eduroam.py connects with.

    Parsed, never imported: importing would run the script's top level.
    """
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"), filename=str(SCRIPT))
    constants = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
            constants[node.targets[0].id] = node.value.value

    # The nmcli argument lists: "802-1x.eap", "peap", "802-1x.phase2-auth", ...
    settings = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.List):
            values = [e.value if isinstance(e, ast.Constant) else None for e in node.elts]
            for key, value in zip(values, values[1:]):
                if isinstance(key, str) and key.startswith("802-1x.") and isinstance(value, str):
                    settings[key] = value

    pinned = {}
    try:
        for block in constants.get("SAXION_CA_PEM", "").split("-----END CERTIFICATE-----")[:-1]:
            pem = block[block.index("-----BEGIN CERTIFICATE-----"):] + "-----END CERTIFICATE-----"
            der = ssl.PEM_cert_to_DER_cert(pem)
            pinned[hashlib.sha256(der).hexdigest()] = der
    except ValueError as error:
        raise FetchError(f"SAXION_CA_PEM in {SCRIPT.relative_to(ROOT)} is not PEM ({error})") from error

    missing = [name for name in ("SSID", "REALM", "SERVER_DOMAIN") if name not in constants]
    missing += [] if pinned else ["SAXION_CA_PEM"]
    missing += [] if "802-1x.eap" in settings else ["802-1x.eap"]
    if missing:
        raise FetchError(f"could not read {', '.join(missing)} from {SCRIPT.relative_to(ROOT)}; "
                         "teach read_script() its new layout")
    return {**{k: constants[k] for k in ("SSID", "REALM", "SERVER_DOMAIN")},
            "eap": settings["802-1x.eap"], "phase2": settings.get("802-1x.phase2-auth"),
            "pinned": pinned}


# ── Comparing ────────────────────────────────────────────────────────────────

def code(value: object) -> str:
    """A value from the internet, made inert for a GitHub issue."""
    flat = " ".join(str(value).replace("`", "'").split())
    return f"`{flat[:200]}`"


def method_name(method: dict) -> str:
    inner = []
    for item in method["inner"]:
        kind, _, number = item.partition(":")
        names = EAP_NAMES if kind == "eap" else NON_EAP_NAMES
        inner.append(names.get(int(number), item))
    outer = EAP_NAMES.get(method["outer"], f"EAP type {method['outer']}")
    return f"{outer}/{'+'.join(inner)}" if inner else outer


def method_key(method: dict) -> tuple:
    return (method["outer"], tuple(method["inner"]))


def describe_cas(digests: list[str], ders: dict[str, bytes], pinned: dict[str, bytes]) -> list[str]:
    lines = []
    for digest in digests:
        name = certificate_name(ders[digest]) if digest in ders else None
        trust = "pinned by saxion-eduroam.py" if digest in pinned else "not pinned by saxion-eduroam.py"
        lines.append(f"  - {code(name or digest[:16] + '…')} ({trust})")
    return lines


def certificate_name(der: bytes) -> str | None:
    openssl = shutil.which("openssl")
    if openssl is None:
        return None
    # Fixed arguments, the certificate on stdin.
    result = subprocess.run(
        [openssl, "x509", "-inform", "DER", "-noout", "-subject", "-enddate", "-nameopt", "oneline"],
        input=der, capture_output=True, check=False)
    if result.returncode != 0:
        return None
    return "; ".join(line.strip() for line in result.stdout.decode(errors="replace").splitlines())


def compare(old: dict, new: dict, script: dict, ders: dict[str, bytes]) -> list[str]:
    ders = {**script["pinned"], **ders}
    findings = []
    findings += compare_discovery(old["discovery"], new["discovery"])
    if new["cat"] is None:
        findings.append(
            f"**CAT profile {old['cat']['profile']} is no longer listed.** The script's parameters came "
            "from it. Find out where Saxion's eduroam configuration lives now.")
    else:
        findings += compare_cat(old["cat"], new["cat"], script, ders)
    return findings


def compare_discovery(old: list[dict], new: list[dict]) -> list[str]:
    findings = []
    if not new:
        return ["**Saxion is gone from the geteduroam discovery feed.** The geteduroam apps no longer "
                "offer it, which usually means its eduroam configuration moved or was removed."]
    old_profiles = {p["id"]: p for i in old for p in i["profiles"]}
    new_profiles = {p["id"]: p for i in new for p in i["profiles"]}
    for profile_id, profile in new_profiles.items():
        was = old_profiles.get(profile_id)
        if profile["oauth"] and not (was and was["oauth"]):
            findings.append(
                f"**Saxion now offers a geteduroam profile with OAuth**: {code(profile['name'])} "
                f"({code(profile_id)}). That is EAP-TLS with a personal certificate, issued after a "
                "browser login. saxion-eduroam.py cannot do that. If PEAP is being phased out, the "
                "guide should send readers to the geteduroam Linux app instead.")
        elif was is None:
            findings.append(f"New discovery profile {code(profile['name'])} ({code(profile_id)}).")
        elif profile != was:
            changes = [f"{field} {code(was[field])} → {code(profile[field])}"
                       for field in ("name", "oauth") if profile[field] != was[field]]
            findings.append(f"Discovery profile {code(profile_id)} changed: {', '.join(changes)}.")
    for profile_id, profile in old_profiles.items():
        if profile_id not in new_profiles:
            findings.append(f"Discovery profile {code(profile['name'])} ({code(profile_id)}) was removed.")
    old_names = {i["id"]: i["name"] for i in old}
    for instance in new:
        if instance["id"] not in old_names:
            findings.append(f"New discovery entry matching Saxion: {code(instance['name'])} "
                            f"({code(instance['id'])}).")
        elif instance["name"] != old_names[instance["id"]]:
            findings.append(f"Discovery entry {code(instance['id'])} renamed to {code(instance['name'])}.")
    return findings


def compare_cat(old: dict, new: dict, script: dict, ders: dict[str, bytes]) -> list[str]:
    findings = []
    old_methods = {method_key(m): m for m in old["methods"]}
    new_methods = {method_key(m): m for m in new["methods"]}
    used = SCRIPT_METHODS.get((script["eap"], script["phase2"]))

    for key, method in new_methods.items():
        if key not in old_methods:
            findings.append(f"CAT now offers **{method_name(method)}** as well.")
    for key, method in old_methods.items():
        if key in new_methods:
            continue
        if used and key[0] == used[0] and used[1] in key[1]:
            findings.append(
                f"**CAT no longer offers {method_name(method)}, the method saxion-eduroam.py uses.** "
                "Expect the script to stop authenticating once the RADIUS server follows.")
        else:
            findings.append(f"CAT no longer offers {method_name(method)}.")

    for key, method in new_methods.items():
        if key not in old_methods:
            continue
        was, name = old_methods[key], method_name(method)
        if method["server_ids"] != was["server_ids"]:
            findings.append(
                f"**Server name for {name} changed**: {code(', '.join(was['server_ids']))} → "
                f"{code(', '.join(method['server_ids']))}. The script's `domain-suffix-match` "
                f"({code(script['SERVER_DOMAIN'])}) has to follow, or it rejects the server.")
        if method["ca_sha256"] != was["ca_sha256"]:
            lines = [f"**CA certificates for {name} changed.** Now listed:"]
            lines += describe_cas(method["ca_sha256"], ders, script["pinned"])
            if any(digest in script["pinned"] for digest in method["ca_sha256"]):
                lines.append("  CAT now lists a root the script already pins, so the official installer "
                             "may work again. The guide's \"Why the official installers fail\" section "
                             "(EN and NL) is then out of date.")
            findings.append("\n".join(lines))
        for field, label in (("outer_identity", "Anonymous identity"),
                             ("inner_identity_suffix", "Inner identity suffix")):
            if method[field] != was[field]:
                findings.append(f"{label} for {name}: {code(was[field])} → {code(method[field])}.")

    for field, label in (("realm", "Realm"), ("ssids", "SSIDs"), ("consortium_oids", "Consortium OIDs"),
                         ("linux_device", "The Linux entry on the CAT page")):
        if new[field] != old[field]:
            findings.append(f"{label}: {code(old[field])} → {code(new[field])}.")

    if new["last_changed"] != old["last_changed"]:
        quiet = not findings
        findings.append(
            f"The CAT profile was edited: {code(old['last_changed'])} → {code(new['last_changed'])}."
            + (" Nothing this check reads changed with it." if quiet else ""))
    return findings


def check_script(baseline: dict, script: dict) -> list[str]:
    """Whether the baseline still describes what saxion-eduroam.py does."""
    problems = []
    cat = baseline.get("cat") or {}
    used = SCRIPT_METHODS.get((script["eap"], script["phase2"]))
    if used is None:
        return [f"saxion-eduroam.py connects with {code(script['eap'])}/{code(script['phase2'])}, which "
                "SCRIPT_METHODS does not know. Add it there."]
    method = next((m for m in cat.get("methods", []) if m["outer"] == used[0] and used[1] in m["inner"]), None)
    if method is None:
        return [f"The baseline has no {method_name({'outer': used[0], 'inner': [used[1]]})} method, but "
                "saxion-eduroam.py still connects with it."]
    domain = script["SERVER_DOMAIN"]
    if not any(s == domain or s.endswith("." + domain) for s in method["server_ids"]):
        problems.append(f"saxion-eduroam.py matches the server on {code(domain)}, but the baseline names "
                        f"{code(', '.join(method['server_ids']))}.")
    for realm in (cat.get("realm"), method.get("inner_identity_suffix")):
        if realm is not None and realm != script["REALM"]:
            problems.append(f"saxion-eduroam.py uses realm {code(script['REALM'])}, the baseline "
                            f"{code(realm)}.")
    if script["SSID"] not in cat.get("ssids", []):
        problems.append(f"saxion-eduroam.py connects to SSID {code(script['SSID'])}, which the baseline "
                        "does not list.")
    return problems


# ── Output ───────────────────────────────────────────────────────────────────

def render(findings: list[str], problems: list[str]) -> str:
    profile_page = "https://cat.eduroam.org/?idp=" + str(CAT_IDP)
    lines = []
    if findings:
        lines += ["## Saxion's published eduroam configuration changed", ""]
        lines += [f"- {f}" for f in findings]
        lines += ["", "Read what changed against the eduroam guide and `saxion-eduroam.py`. Once it is "
                  "understood, and the script follows where it has to, record the new state:", "",
                  "```bash", "python3 .github/scripts/check-eduroam-profile.py --apply", "```", "",
                  "and commit `.github/scripts/saxion-eduroam-baseline.json`.", ""]
    if problems:
        lines += ["## The baseline and saxion-eduroam.py disagree", ""]
        lines += [f"- {p}" for p in problems]
        lines += [""]
    lines += [f"Sources: [geteduroam discovery]({DISCOVERY_URL}), [Saxion on CAT]({profile_page})."]
    body = "\n".join(lines) + "\n"
    # Lets the workflow tell this report from one it already posted.
    return body + f"\n<!-- eduroam-watch:{hashlib.sha256(body.encode()).hexdigest()} -->\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="rewrite the baseline from live data")
    parser.add_argument("--report", type=pathlib.Path, help="write the findings as Markdown to this file")
    args = parser.parse_args()

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    ders: dict[str, bytes] = {}
    try:
        script = read_script()
        live = read_live(baseline, ders)
    except FetchError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.apply:
        if live["cat"] is None:
            print(f"error: CAT profile {baseline['cat']['profile']} is gone. Put the profile that replaces "
                  f"it into {BASELINE.relative_to(ROOT)} by hand, then --apply again.", file=sys.stderr)
            return 1
        BASELINE.write_text(json.dumps(live, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {BASELINE.relative_to(ROOT)}.")
        baseline, findings = live, []
    else:
        findings = compare(baseline, live, script, ders)

    problems = check_script(baseline, script)
    report = render(findings, problems)
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    if findings or problems:
        print(report)
        return 1
    print("Saxion's published eduroam configuration matches the baseline and saxion-eduroam.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
