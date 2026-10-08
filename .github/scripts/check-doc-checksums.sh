#!/usr/bin/env bash
#
# Verify that every SHA-256 the documentation publishes for a script in
# src/static/scripts/ still matches the script that is actually shipped.
#
# The eduroam guide tells readers to check their download against a hash that
# is written out in the page itself. Nothing recomputed that hash when the
# script changed, so an edit to saxion-eduroam.py silently invalidated the
# published checksum and `sha256sum -c` started failing for everyone who
# followed the guide (issue #104).
#
# update-tool-checksums.sh covers the pinned CI tools and only runs on
# Renovate's own pull requests. This one covers the other direction: hashes
# that live in the content and go stale when a human edits a script. It runs on
# every pull request, and it fails instead of committing, because a job that
# pushes onto a branch someone is working on is exactly what that workflow
# avoids.
#
# quicksetup.py has the same problem one level down: it only runs the
# dedicated scripts and installs the color profiles whose SHA-256 is written
# into its own source. Those tables are checked first, because rewriting them
# changes the setup script and with it the hash the documentation publishes.
#
# Usage:
#   .github/scripts/check-doc-checksums.sh           # verify only
#   .github/scripts/check-doc-checksums.sh --apply   # rewrite stale hashes
#

set -euo pipefail

readonly RED='\033[0;31m' GREEN='\033[0;32m' YELLOW='\033[1;33m' BLUE='\033[0;34m' NC='\033[0m'

Write-Log() {
    local level=$1; shift
    local color=$NC
    case $level in
        INFO)    color=$BLUE ;;
        SUCCESS) color=$GREEN ;;
        WARN)    color=$YELLOW ;;
        ERROR)   color=$RED ;;
    esac
    if [[ $level == ERROR ]]; then
        echo -e "${color}[$level]${NC} $*" >&2
    else
        echo -e "${color}[$level]${NC} $*"
    fi
}

Show-Usage() {
    cat <<'EOF'
Usage: check-doc-checksums.sh [--apply]

Options:
  --apply     Rewrite stale checksums in the content instead of failing
  -h, --help  Show this help
EOF
}

APPLY=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --apply) APPLY=true; shift ;;
        -h|--help) Show-Usage; exit 0 ;;
        *) Write-Log ERROR "Unknown argument: $1"; Show-Usage; exit 1 ;;
    esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly REPO_ROOT
cd "$REPO_ROOT"

readonly SCRIPT_DIR="src/static/scripts"
readonly CONTENT_DIR="src/content"

[[ -d $SCRIPT_DIR ]]  || { Write-Log ERROR "$SCRIPT_DIR does not exist"; exit 1; }
[[ -d $CONTENT_DIR ]] || { Write-Log ERROR "$CONTENT_DIR does not exist"; exit 1; }

stale=0       # hashes that were wrong, whether or not --apply rewrote them
unfixable=0   # hashes that were wrong and that --apply cannot rewrite

# ── Hashes built into the setup script ──────────────────────────────────────
#
# Every entry in TOOL_SHA256 and PROFILE_SHA256 is a "file name": "hash" line.
# The file is looked up next to the setup script and in the color profile
# folder, and the hash has to be the one of the file as it is committed.

readonly SETUP_SCRIPT="$SCRIPT_DIR/quicksetup.py"
readonly PROFILE_DIR="src/static/icc-profiles"

embedded=0
if [[ -f $SETUP_SCRIPT ]]; then
    while IFS=: read -r line name hash; do
        embedded=$((embedded + 1))
        file=""
        for folder in "$SCRIPT_DIR" "$PROFILE_DIR"; do
            [[ -f $folder/$name ]] && file="$folder/$name" && break
        done
        if [[ -z $file ]]; then
            stale=$((stale + 1))
            unfixable=$((unfixable + 1))
            Write-Log ERROR "$SETUP_SCRIPT:$line lists $name, which is not in $SCRIPT_DIR or $PROFILE_DIR"
            [[ -n ${GITHUB_ACTIONS:-} ]] && \
                echo "::error file=$SETUP_SCRIPT,line=$line::$name is listed here but does not exist"
            continue
        fi
        want="$(sha256sum "$file" | awk '{print $1}')"
        [[ $hash == "$want" ]] && continue

        stale=$((stale + 1))
        if [[ $APPLY == true ]]; then
            sed -i "${line}s/$hash/$want/" "$SETUP_SCRIPT"
            Write-Log SUCCESS "$SETUP_SCRIPT:$line updated to $want ($name)"
        else
            Write-Log ERROR "$SETUP_SCRIPT:$line has $hash for $name, the file is $want"
            [[ -n ${GITHUB_ACTIONS:-} ]] && \
                echo "::error file=$SETUP_SCRIPT,line=$line::SHA-256 of $name is stale. Run .github/scripts/check-doc-checksums.sh --apply"
        fi
    done < <(grep -nE '^[[:space:]]+"[A-Za-z0-9_.-]+": "[a-f0-9]{64}",$' "$SETUP_SCRIPT" \
             | sed -E 's/^([0-9]+):[[:space:]]+"([^"]+)": "([a-f0-9]{64})",$/\1:\2:\3/' || true)
    Write-Log INFO "$embedded hash(es) are built into $SETUP_SCRIPT."
    echo
fi

# ── The scripts the documentation can publish a hash for ────────────────────

declare -A HASH_OF
while IFS= read -r -d '' script; do
    HASH_OF["$(basename "$script")"]="$(sha256sum "$script" | awk '{print $1}')"
done < <(find "$SCRIPT_DIR" -type f -print0)

if [[ ${#HASH_OF[@]} -eq 0 ]]; then
    Write-Log WARN "No scripts in $SCRIPT_DIR, nothing to check."
    exit 0
fi

Write-Log INFO "Checksums of the shipped scripts:"
for name in "${!HASH_OF[@]}"; do
    echo "  $name  ${HASH_OF[$name]}"
done
echo

# ── Every hash a page publishes has to be one of those ──────────────────────
#
# A page is only checked when it names one of the scripts, so an unrelated
# 64-character hex string elsewhere in the documentation is left alone. Within
# such a page every hash has to match one of the scripts that page mentions.
#
# The pages under setup-script/reference/ are left out: they are generated from
# quicksetup.py at build time, hashes included.

checked=0

while IFS= read -r -d '' page; do
    referenced=()
    for name in "${!HASH_OF[@]}"; do
        grep -qF -- "$name" "$page" && referenced+=("$name")
    done
    [[ ${#referenced[@]} -gt 0 ]] || continue
    checked=$((checked + 1))

    expected=()
    for name in "${referenced[@]}"; do
        expected+=("${HASH_OF[$name]}")
    done

    while IFS=: read -r line hash; do
        for want in "${expected[@]}"; do
            [[ $hash == "$want" ]] && continue 2
        done

        stale=$((stale + 1))
        if [[ ${#referenced[@]} -eq 1 ]]; then
            local_fix="${expected[0]}"
            if [[ $APPLY == true ]]; then
                sed -i "s/$hash/$local_fix/g" "$page"
                Write-Log SUCCESS "$page:$line updated to $local_fix"
            else
                Write-Log ERROR "$page:$line publishes $hash, ${referenced[0]} is $local_fix"
                [[ -n ${GITHUB_ACTIONS:-} ]] && \
                    echo "::error file=$page,line=$line::Published SHA-256 is stale. Run .github/scripts/check-doc-checksums.sh --apply"
            fi
        else
            unfixable=$((unfixable + 1))
            Write-Log ERROR "$page:$line publishes $hash, which matches none of: ${referenced[*]}"
            [[ -n ${GITHUB_ACTIONS:-} ]] && \
                echo "::error file=$page,line=$line::Published SHA-256 matches none of the scripts this page references"
        fi
    done < <(grep -Eno '\b[a-f0-9]{64}\b' "$page" || true)
done < <(find "$CONTENT_DIR" -type f -name '*.md' -not -path '*/setup-script/reference/*' -print0)

echo
if [[ $stale -eq 0 ]]; then
    Write-Log SUCCESS "$checked page(s) publish a script checksum, all of them current."
    exit 0
fi

if [[ $APPLY == true && $unfixable -eq 0 ]]; then
    Write-Log SUCCESS "Rewrote $stale stale checksum(s)."
    exit 0
fi

if [[ $APPLY == true ]]; then
    Write-Log ERROR "$unfixable checksum(s) cannot be rewritten automatically, fix them by hand."
    exit 1
fi

Write-Log ERROR "$stale stale checksum(s). Fix them with:"
echo "  .github/scripts/check-doc-checksums.sh --apply"
exit 1
