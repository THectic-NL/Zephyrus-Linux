#!/usr/bin/env python3
# Copyright (C) 2026 Sten Tijhuis
# SPDX-License-Identifier: MIT
"""Watch Saxion's eduroam setup and the certificate chain under it.

saxion-eduroam.py hard-codes Saxion's eduroam setup: PEAP with MSCHAPv2
inside, the RADIUS server name, the realm, and the four HARICA roots it
trusts. Saxion can change any of that without telling anyone, and until now
the first sign was a reader whose connection stopped working. Issue #109 went
exactly like that.

Public sources say what Saxion publishes today:

  1. discovery.eduroam.app, the feed the geteduroam apps read. It lists every
     profile an institution offers. A profile with "oauth": true is
     geteduroam's certificate route: EAP-TLS with a personal certificate,
     issued after a login in the browser. Most Dutch institutions already
     have one. Saxion getting one is the sign that it is moving off
     PEAP/MSCHAPv2, and saxion-eduroam.py cannot follow it there.
  2. cat.eduroam.org, Saxion's CAT profile: the EAP methods, server names,
     CA certificates and minimum Wi-Fi cipher the official installers are
     built from, plus the date the profile was last edited.
  3. Certificate Transparency, through Cert Spotter: every publicly trusted
     certificate is logged when it is issued, the RADIUS server's included.
     This checks who issued the unexpired ones, whether that issuer sits
     under a root the script pins, and the key, signature algorithm and
     purposes of the certificates themselves. A certificate from another CA shows up
     here when it is issued, which is usually before Saxion deploys it. In
     #109 this would have been the warning.
  4. CCADB, the database behind Mozilla's root store: whether the pinned
     roots are still trusted or have a distrust date set, and the GEANT
     intermediates and cross-certificates under them. That is where a HARICA
     problem, or a new intermediate for Saxion's next certificate, shows up.

All of it is compared with saxion-eduroam-baseline.json, which is itself
checked against the constants in saxion-eduroam.py. A change upstream fails
this check. So does a script edit that leaves the baseline describing
something the script no longer does.

A renewed server certificate from the same intermediate is not a change: the
script pins roots, not the certificate, and renewals come every few months.

The CA certificates in the CAT profile are not the ones the script trusts.
The profile still pins the pre-migration USERTrust chain (#109). They are
watched anyway: the day Saxion corrects them, the guide's explanation of why
the official installers fail is out of date.

What this cannot see is which certificate the RADIUS server actually
presents, or which TLS versions and cipher suites it negotiates. That only
shows up in an EAP handshake on campus, not from a CI runner. The logs say
what exists, not what is deployed.

Usage:
  check-saxion-eduroam.py                   # compare, exit 1 on a difference
  check-saxion-eduroam.py --apply           # rewrite the baseline from live data
  check-saxion-eduroam.py --report FILE     # also write the findings as Markdown

Exit status: 0 nothing changed, 1 something changed or the baseline and the
script disagree, 2 a source could not be fetched or read. The workflow opens
an issue only on 1, so an outage at a source does not open one.
"""
from __future__ import annotations

import argparse
import ast
import base64
import csv
import gzip
import hashlib
import io
import json
import os
import pathlib
import re
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
CERTSPOTTER_URL = "https://api.certspotter.com/v1/issuances"
CCADB_REPORTS = "https://ccadb.my.salesforce-sites.com/mozilla/"
CCADB_ROOTS = CCADB_REPORTS + "IncludedCACertificateReportPEMCSV"
CCADB_INTERMEDIATES = CCADB_REPORTS + "PublicAllIntermediateCertsWithPEMCSV"
CCADB_REVOKED = CCADB_REPORTS + "PublicIntermediateCertsRevokedWithPEMCSV"
USER_AGENT = "Zephyrus-Linux eduroam watch (+https://github.com/THectic-NL/Zephyrus-Linux)"

# The discovery feed is about 2 MB unpacked, CCADB's reports 6 to 8 MB.
# Anything far beyond that is not the file we think it is.
MAX_BYTES = 32 * 1024 * 1024
# CCADB's reports carry every certificate as PEM in one column.
csv.field_size_limit(MAX_BYTES)

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

def fetch(url: str, timeout: int = 30, headers: dict[str, str] | None = None) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    for attempt in range(3):
        try:
            # Fixed https:// URLs only, never one read from a response.
            with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
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


def fetch_json(url: str, kind: type = dict, headers: dict[str, str] | None = None):
    try:
        data = json.loads(fetch(url, headers=headers))
    except ValueError as error:
        raise FetchError(f"{url}: not JSON ({error})") from error
    if not isinstance(data, kind):
        raise FetchError(f"{url}: expected a JSON {kind.__name__}")
    return data


def fetch_csv(url: str, columns: tuple[str, ...]) -> list[dict]:
    """A CCADB report. These are generated on request, hence the long timeout."""
    try:
        rows = list(csv.DictReader(io.StringIO(fetch(url, timeout=180).decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error) as error:
        raise FetchError(f"{url}: not a CSV report ({error})") from error
    if not rows or any(column not in rows[0] for column in columns):
        raise FetchError(f"{url}: empty, or the report no longer has the columns {', '.join(columns)}")
    return rows


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
        # The weakest Wi-Fi cipher Saxion allows. CCMP is AES, as in WPA2.
        "min_rsn_proto": sorted({text(e) for e in provider.iter("MinRSNProto")}),
    }


def text(element: ET.Element) -> str:
    return (element.text or "").strip()


# ── Reading the certificate chain ────────────────────────────────────────────

INTERMEDIATE_COLUMNS = ("Parent Name", "Certificate Name", "Certificate Subject Common Name",
                        "Certificate Subject Organization", "SHA-256 Fingerprint", "Valid To [GMT]",
                        "Public Key Algorithm", "Signature Hash Algorithm")


def read_root_store(pinned: dict[str, bytes], previous: list[dict]) -> list[dict]:
    """Mozilla's view of each pinned root: trusted for what, distrusted from when."""
    rows = {r["SHA-256 Fingerprint"].lower(): r
            for r in fetch_csv(CCADB_ROOTS, ("SHA-256 Fingerprint", "Common Name or Certificate Name",
                                             "Trust Bits", "Distrust for TLS After Date"))}
    # A root that leaves the store leaves the report, and its name with it.
    known = {r["sha256"]: r["name"] for r in previous}
    roots = []
    for digest in sorted(pinned):
        row = rows.get(digest)
        roots.append({
            "sha256": digest,
            "name": row["Common Name or Certificate Name"] if row else known.get(digest),
            "mozilla": None if row is None else {
                "trust_bits": row["Trust Bits"],
                "distrust_tls_after": row["Distrust for TLS After Date"] or None,
            },
        })
    return roots


def read_server_certificates(domain: str, rows: list[dict], pinned_names: set[str]) -> tuple[dict, list[dict]]:
    """Who issued the unexpired certificates for the RADIUS server, per the CT logs.

    Also returns the CCADB rows of those issuers, so they get watched too.
    """
    # Cert Spotter answers a few queries an hour without a key, counted per IP,
    # and GitHub's runners share theirs. A key, if the repository has one,
    # takes that out of the equation.
    token = os.environ.get("CERTSPOTTER_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else None
    issuances: list[dict] = []
    after = None
    for _ in range(20):
        params = [("domain", domain), ("expand", "issuer"), ("expand", "revocation"), ("expand", "cert")]
        params += [("after", after)] if after else []
        page = fetch_json(f"{CERTSPOTTER_URL}?{urllib.parse.urlencode(params)}", list, headers)
        if not page:
            break
        issuances += page
        after = page[-1].get("id")
    else:
        raise FetchError(f"{CERTSPOTTER_URL}: more than 20 pages of certificates for {domain}")

    by_subject: dict[str, list[dict]] = {}
    by_name: dict[str, list[dict]] = {}
    for row in rows:
        by_subject.setdefault(row["Certificate Subject Common Name"], []).append(row)
        by_name.setdefault(row["Certificate Name"], []).append(row)

    issuers: dict[tuple, dict] = {}
    profiles: list[dict] = []
    revoked, matched = set(), []
    for issuance in issuances:
        try:
            der = base64.b64decode((issuance.get("cert") or {})["data"])
        except (KeyError, TypeError, ValueError) as error:
            raise FetchError(f"{CERTSPOTTER_URL}: an issuance without its certificate ({error})") from error
        if (profile := certificate_profile(der)) not in profiles:
            profiles.append(profile)
        issuer = issuance.get("issuer") or {}
        name, key = str(issuer.get("name")), str(issuer.get("pubkey_sha256"))
        if (name, key) not in issuers:
            candidates = by_subject.get(dn_field(name, "CN") or "", [])
            # Narrow by organisation where that leaves anything; names repeat across CAs.
            candidates = [r for r in candidates
                          if r["Certificate Subject Organization"] == dn_field(name, "O")] or candidates
            matched += candidates
            issuers[(name, key)] = {"name": name, "pubkey_sha256": key, "in_ccadb": bool(candidates),
                                    "under_pinned_roots": roots_above(name, candidates, by_name, pinned_names)}
        if issuance.get("revoked"):
            revoked.add(str(issuance.get("cert_sha256")))
    certificates = {"name": domain,
                    "issuers": sorted(issuers.values(), key=lambda i: (i["name"], i["pubkey_sha256"])),
                    "profiles": sorted(profiles, key=lambda p: json.dumps(p, sort_keys=True)),
                    "revoked": sorted(revoked)}
    return certificates, matched


def certificate_profile(der: bytes) -> dict:
    """The key, signature algorithm and purposes of a certificate, as openssl names them.

    A renewal keeps these, so a change here is a change of crypto: RSA to
    ECDSA, a post-quantum algorithm, a certificate no longer meant for TLS.
    """
    openssl = shutil.which("openssl")
    if openssl is None:
        raise FetchError("openssl is needed to read the server's certificates")
    # Fixed arguments, the certificate on stdin.
    result = subprocess.run([openssl, "x509", "-inform", "DER", "-noout", "-text"],
                            input=der, capture_output=True, check=False)
    if result.returncode != 0:
        raise FetchError("openssl could not read a certificate from the CT logs")
    dump = result.stdout.decode(errors="replace")

    def first(pattern: str) -> str | None:
        match = re.search(pattern, dump)
        return match.group(1).strip() if match else None

    key = [first(r"Public Key Algorithm: (.+)"), first(r"Public-Key: \((\d+ bit)\)"),
           first(r"NIST CURVE: (.+)") or first(r"ASN1 OID: (.+)")]
    return {"key": " ".join(part for part in key if part),
            "signature": first(r"Signature Algorithm: (.+)"),
            "extended_key_usage": first(r"Extended Key Usage:[^\n]*\n\s*(.+)")}


def dn_field(dn: str, field: str) -> str | None:
    """One attribute of a name like "C=GR, O=Hellenic ... CA, CN=GEANT TLS RSA 1"."""
    for part in re.split(r",\s*(?=[A-Za-z0-9.]+=)", dn):
        key, _, value = part.partition("=")
        if key.strip().upper() == field:
            return value.strip()
    return None


def roots_above(issuer: str, candidates: list[dict], by_name: dict[str, list[dict]],
                pinned_names: set[str]) -> list[str]:
    """The pinned roots an issuer chains up to, walking CCADB's parent names."""
    reached = {dn_field(issuer, "CN")} & pinned_names
    seen: set[str] = set()
    frontier = list(candidates)
    while frontier:
        parent = frontier.pop()["Parent Name"]
        if parent in pinned_names:
            reached.add(parent)
        elif parent not in seen:
            seen.add(parent)
            frontier += by_name.get(parent, [])
    return sorted(reached)


def read_intermediates(rows: list[dict], pinned_names: set[str], matched: list[dict],
                       previous: list[dict]) -> list[dict]:
    """The intermediates Saxion's certificate comes, or could come, from.

    That is the GEANT intermediates and the cross-certificates directly under
    the pinned roots, plus whatever issued the server's current certificates.
    HARICA's other sub-CAs (EV, QWAC, S/MIME, ...) are left out: a new one of
    those says nothing about Saxion. Once watched, an intermediate stays
    watched for as long as CCADB lists it.
    """
    def entry(row: dict) -> dict:
        return {"name": row["Certificate Name"], "parent": row["Parent Name"],
                "sha256": row["SHA-256 Fingerprint"].lower(), "valid_to": row["Valid To [GMT]"],
                "key": row["Public Key Algorithm"], "signature": row["Signature Hash Algorithm"],
                "revoked": None}

    listed = {row["SHA-256 Fingerprint"].lower(): row for row in rows}
    tracked = {}
    for digest, row in listed.items():
        name = row["Certificate Name"]
        if row["Parent Name"] in pinned_names and ("GEANT" in name.upper() or name in pinned_names):
            tracked[digest] = entry(row)
    for row in matched:
        tracked.setdefault(row["SHA-256 Fingerprint"].lower(), entry(row))
    for old in previous:
        if old["sha256"] in listed:
            tracked.setdefault(old["sha256"], entry(listed[old["sha256"]]))

    gone = [old for old in previous if old["sha256"] not in listed]
    if gone:
        # CCADB moves a revoked certificate out of the report above, into one of its own.
        revoked = {r["SHA-256 Fingerprint"].lower(): r
                   for r in fetch_csv(CCADB_REVOKED, ("SHA-256 Fingerprint", "Revocation Status",
                                                      "Date of Revocation"))}
        for old in gone:
            row = revoked.get(old["sha256"])
            if row is not None:
                reason = row.get("RFC 5280 Revocation Reason Code") or row["Revocation Status"]
                tracked[old["sha256"]] = {**old, "revoked": f"{row['Date of Revocation']}, {reason}"}
    return sorted(tracked.values(), key=lambda e: (e["parent"], e["name"], e["sha256"]))


def read_live(baseline: dict, script: dict, ders: dict[str, bytes]) -> dict:
    discovery = read_discovery()
    profile = baseline["cat"]["profile"]
    listed = {p["id"] for i in discovery for p in i["profiles"]}
    # A profile that is gone from the feed is gone from CAT too, and CAT
    # answers for it with a bare 500. Report the first, do not fail on the second.
    cat = read_cat(profile, ders) if f"cat_{profile}" in listed else None

    roots = read_root_store(script["pinned"], baseline.get("root_store", []))
    pinned_names = {r["name"] for r in roots if r["name"]}
    rows = fetch_csv(CCADB_INTERMEDIATES, INTERMEDIATE_COLUMNS)
    certificates, matched = read_server_certificates(script["SERVER_DOMAIN"], rows, pinned_names)
    intermediates = read_intermediates(rows, pinned_names, matched, baseline.get("intermediates", []))
    return {"discovery": discovery, "cat": cat, "server_certificates": certificates,
            "root_store": roots, "intermediates": intermediates}


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


def compare(old: dict, new: dict, script: dict, ders: dict[str, bytes]) -> dict[str, list[str]]:
    """What changed, per source. Only sections with findings are returned."""
    ders = {**script["pinned"], **ders}
    eduroam = compare_discovery(old["discovery"], new["discovery"])
    if new["cat"] is None:
        eduroam.append(
            f"**CAT profile {old['cat']['profile']} is no longer listed.** The script's parameters came "
            "from it. Find out where Saxion's eduroam configuration lives now.")
    else:
        eduroam += compare_cat(old["cat"], new["cat"], script, ders)
    pinned_names = {r["name"] for r in new["root_store"] if r["name"]}
    sections = {
        "geteduroam and CAT": eduroam,
        "The server's certificate (Certificate Transparency)":
            compare_certificates(old.get("server_certificates"), new["server_certificates"]),
        "HARICA and Mozilla's root store (CCADB)":
            compare_roots(old.get("root_store", []), new["root_store"])
            + compare_intermediates(old.get("intermediates", []), new["intermediates"],
                                    new["server_certificates"], pinned_names),
    }
    return {title: findings for title, findings in sections.items() if findings}


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

    if new.get("min_rsn_proto") != old.get("min_rsn_proto"):
        finding = (f"**The minimum Wi-Fi cipher changed**: {code(', '.join(old.get('min_rsn_proto') or []))} → "
                   f"{code(', '.join(new['min_rsn_proto']))}.")
        if any("GCMP" in proto for proto in new["min_rsn_proto"]):
            finding += (" GCMP points at WPA3-Enterprise, possibly its 192-bit mode. That needs "
                        "`wifi-sec.key-mgmt wpa-eap-suite-b-192` instead of the script's `wpa-eap`, and that "
                        "mode allows EAP-TLS only.")
        findings.append(finding)

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


def compare_certificates(old: dict | None, new: dict) -> list[str]:
    old = old or {"issuers": [], "revoked": []}
    findings = []
    domain = code(new["name"])
    if not new["issuers"] and old["issuers"]:
        findings.append(
            f"**No unexpired certificate for {domain} is in the CT logs any more.** It expired without a "
            "renewal, or Saxion moved to a certificate that is not publicly logged, such as one from its "
            "own CA. saxion-eduroam.py trusts neither.")
    known = {(i["name"], i["pubkey_sha256"]): i for i in old["issuers"]}
    for issuer in new["issuers"]:
        was = known.get((issuer["name"], issuer["pubkey_sha256"]))
        if was is not None and was["under_pinned_roots"] == issuer["under_pinned_roots"]:
            continue
        name = code(dn_field(issuer["name"], "CN") or issuer["name"])
        if issuer["under_pinned_roots"]:
            findings.append(
                f"**{domain} has a certificate from {name}**, under {code(', '.join(issuer['under_pinned_roots']))}, "
                "which saxion-eduroam.py pins. The script keeps working, but the chain the server sends "
                "changes once Saxion deploys it.")
        else:
            findings.append(
                f"**{domain} has a certificate from {name}, which is not under any root saxion-eduroam.py "
                "pins.** Once Saxion deploys it, the script rejects the server, as in #109. Pin that CA's "
                f"root in `SAXION_CA_PEM` before then. Full issuer: {code(issuer['name'])}."
                + ("" if issuer.get("in_ccadb", True) else " CCADB does not list this issuer, so it is "
                   "new, or not publicly trusted at all."))
    current = {(i["name"], i["pubkey_sha256"]) for i in new["issuers"]}
    for key, issuer in known.items():
        if key not in current and new["issuers"]:
            findings.append(f"{code(dn_field(issuer['name'], 'CN') or issuer['name'])} no longer has an "
                            f"unexpired certificate for {domain}.")
    old_profiles = old.get("profiles", [])
    for profile in new["profiles"]:
        if profile not in old_profiles:
            findings.append(describe_profile(domain, profile, old_profiles))
    for profile in old_profiles:
        if profile not in new["profiles"] and new["profiles"]:
            findings.append(f"No unexpired certificate for {domain} has key {code(profile['key'])} with "
                            f"{code(profile['signature'])} any more.")
    for digest in new["revoked"]:
        if digest not in old["revoked"]:
            findings.append(
                f"**A certificate for {domain} was revoked** ({code(digest[:16] + '…')}). That usually means "
                "a replacement is coming, or the key leaked.")
    return findings


def describe_profile(domain: str, profile: dict, old_profiles: list[dict]) -> str:
    usage = profile["extended_key_usage"] or ""
    finding = (f"**{domain} has a certificate with different crypto**: key {code(profile['key'])}, signed with "
               f"{code(profile['signature'])}, for {code(usage or 'any purpose')}.")
    if not profile["key"].startswith(("rsaEncryption", "id-ecPublicKey")):
        finding += (" That is neither RSA nor ECDSA. wpa_supplicant only accepts it if its OpenSSL knows the "
                    "algorithm; post-quantum ML-DSA, for one, needs OpenSSL 3.5 or newer.")
    if usage and "TLS Web Server Authentication" not in usage:
        finding += " It is no longer marked for TLS servers, and some EAP clients, Windows among them, refuse that."
    elif "Client Authentication" not in usage and any("Client Authentication" in (p["extended_key_usage"] or "")
                                                      for p in old_profiles):
        finding += (" Client Authentication was dropped, as the browser root programs require. That part does "
                    "not affect saxion-eduroam.py.")
    return finding


def compare_roots(old: list[dict], new: list[dict]) -> list[str]:
    findings = []
    known = {r["sha256"]: r for r in old}
    for root in new:
        was = known.get(root["sha256"])
        if was is None:
            continue  # a newly pinned root; check_script asks for --apply
        name = code(root["name"] or root["sha256"][:16] + "…")
        now, then = root["mozilla"], was["mozilla"]
        if now is None and then is not None:
            findings.append(
                f"**{name} is no longer in Mozilla's root store.** saxion-eduroam.py still trusts it, but "
                "GÉANT will not keep issuing under a root the browsers drop, so Saxion's certificate is "
                "going to come from another CA. Find out which, and pin its root before the switch.")
        elif now is not None and then is None:
            findings.append(f"{name} is back in Mozilla's root store.")
        elif now is not None and then is not None:
            if now["distrust_tls_after"] != then["distrust_tls_after"]:
                if now["distrust_tls_after"]:
                    findings.append(
                        f"**Mozilla distrusts {name} for TLS certificates issued after "
                        f"{code(now['distrust_tls_after'])}.** That is how a CA gets wound down. Saxion's "
                        "certificate is going to come from elsewhere; find out where, and pin its root "
                        "before then.")
                else:
                    findings.append(f"Mozilla lifted the TLS distrust date of {name}.")
            if now["trust_bits"] != then["trust_bits"]:
                findings.append(
                    f"Mozilla's trust bits for {name}: {code(then['trust_bits'])} → {code(now['trust_bits'])}."
                    + (" It is no longer trusted for TLS." if "Websites" not in now["trust_bits"] else ""))
    return findings


def compare_intermediates(old: list[dict], new: list[dict], certificates: dict,
                          pinned_names: set[str]) -> list[str]:
    findings = []
    known = {e["sha256"]: e for e in old}
    in_use = {dn_field(i["name"], "CN") for i in certificates["issuers"]}
    for entry in new:
        was = known.get(entry["sha256"])
        name = code(entry["name"])
        if entry["revoked"] and not (was and was["revoked"]):
            findings.append(
                f"**{name} was revoked** ({code(entry['revoked'])}). Certificates under it no longer "
                "validate wherever revocation is checked."
                + (" Saxion's current certificate is one of them." if entry["name"] in in_use else ""))
        elif was is None:
            findings.append(
                f"New intermediate {name} under {code(entry['parent'])}, key {code(entry.get('key'))}, "
                f"signed with {code(entry.get('signature'))}. Saxion's next certificate may come from it."
                + (" Its parent is pinned, so the script keeps working." if entry["parent"] in pinned_names
                   else ""))
        elif entry["valid_to"] != was["valid_to"]:
            findings.append(f"{name} now runs until {code(entry['valid_to'])}, was {code(was['valid_to'])}.")
    current = {e["sha256"] for e in new}
    for digest, entry in known.items():
        if digest not in current:
            findings.append(f"{code(entry['name'])} ({code(digest[:16] + '…')}) is no longer listed in "
                            "CCADB, not even as revoked.")
    return findings


def check_script(baseline: dict, script: dict) -> list[str]:
    """Whether the baseline still describes what saxion-eduroam.py does."""
    problems = []
    certificates = baseline.get("server_certificates") or {}
    if certificates.get("name") != script["SERVER_DOMAIN"]:
        problems.append(f"saxion-eduroam.py validates {code(script['SERVER_DOMAIN'])}, but the baseline "
                        f"watches the certificates of {code(certificates.get('name'))}.")
    if {r["sha256"] for r in baseline.get("root_store", [])} != set(script["pinned"]):
        problems.append("`SAXION_CA_PEM` in saxion-eduroam.py and the baseline's root store name different "
                        "roots. Run `--apply` after changing the pinned roots.")
    return problems + check_script_method(baseline, script)


def check_script_method(baseline: dict, script: dict) -> list[str]:
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

def render(sections: dict[str, list[str]], problems: list[str], domain: str) -> str:
    lines = []
    if sections:
        lines += ["## Saxion's eduroam setup or its certificate chain changed", ""]
        for title, findings in sections.items():
            lines += [f"### {title}", ""] + [f"- {f}" for f in findings] + [""]
        lines += ["Read what changed against the eduroam guide and `saxion-eduroam.py`. Once it is "
                  "understood, and the script follows where it has to, record the new state:", "",
                  "```bash", "python3 .github/scripts/check-saxion-eduroam.py --apply", "```", "",
                  "and commit `.github/scripts/saxion-eduroam-baseline.json`.", ""]
    if problems:
        lines += ["## The baseline and saxion-eduroam.py disagree", ""]
        lines += [f"- {p}" for p in problems]
        lines += [""]
    lines += [f"Sources: [geteduroam discovery]({DISCOVERY_URL}), "
              f"[Saxion on CAT](https://cat.eduroam.org/?idp={CAT_IDP}), "
              f"[certificates for {domain}](https://crt.sh/?q={urllib.parse.quote(domain)}), "
              "[CCADB](https://www.ccadb.org/resources)."]
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
        live = read_live(baseline, script, ders)
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
        baseline, sections = live, {}
    else:
        sections = compare(baseline, live, script, ders)

    problems = check_script(baseline, script)
    report = render(sections, problems, script["SERVER_DOMAIN"])
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    if sections or problems:
        print(report)
        return 1
    print("Saxion's eduroam setup and its certificate chain match the baseline and saxion-eduroam.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
