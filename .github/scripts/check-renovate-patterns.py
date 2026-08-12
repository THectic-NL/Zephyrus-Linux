#!/usr/bin/env python3
# Copyright (C) 2026 Sten Tijhuis
# SPDX-License-Identifier: MIT
"""Flag Renovate file patterns that look like a regex but are not delimited.

managerFilePatterns and matchFileNames accept "RegEx (re2) and glob patterns".
A value counts as a regex only when it is wrapped in slashes; everything else
is read as a glob. So a pattern like

    "^\\.github/workflows/.*\\.ya?ml$"

matches no file at all, and the custom manager around it never fires. Nothing
reports this: renovate-config-validator says the config is valid, because it
is -- it just silently does nothing. The only visible symptom is a dependency
that stops receiving updates, which is easy to miss for months.

Usage: check-renovate-patterns.py [config.json ...]
Missing files are skipped, so the same call works in every repository.
"""
import json
import pathlib
import re
import sys

# Constructs that carry meaning in a regex but not in a glob.
REGEXY = re.compile(r"^\^|\$$|\\\.|\.\*|\.\+|\(\?|\[\^|\\d|\\w|\\s|[)?]\|")

# Renovate options whose values are matched as "regex or glob".
PATTERN_KEYS = {
    "managerFilePatterns",
    "matchFileNames",
    "fileMatch",
    "matchPackageNames",
}

problems = []


def walk(node, path, source):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in PATTERN_KEYS and isinstance(value, list):
                for index, pattern in enumerate(value):
                    if not isinstance(pattern, str):
                        continue
                    # A trailing "i" flag is allowed: /pattern/i
                    delimited = pattern.startswith("/") and pattern.rstrip("i").endswith("/")
                    if REGEXY.search(pattern) and not delimited:
                        problems.append((source, f"{path}.{key}[{index}]", pattern))
            walk(value, f"{path}.{key}", source)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            walk(item, f"{path}[{index}]", source)


files = [path for path in (pathlib.Path(a) for a in sys.argv[1:]) if path.is_file()]
if not files:
    print("No Renovate config found to check.")
    sys.exit(0)

for config in files:
    walk(json.loads(config.read_text()), "$", str(config))

if problems:
    print("Renovate file patterns that look like a regex but are not wrapped in slashes.")
    print("Renovate reads these as globs, so they match nothing and the rule never fires.\n")
    for source, where, pattern in problems:
        print(f"::error file={source}::{where}: {pattern!r} is read as a glob, not a regex")
        print(f"  {source}  {where}")
        print(f"    found:  {pattern!r}")
        print(f"    expect: '/{pattern}/'\n")
    sys.exit(1)

print(f"Checked {len(files)} Renovate config file(s): all file patterns are well formed.")
