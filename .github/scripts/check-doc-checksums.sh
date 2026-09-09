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

stale=0
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
            Write-Log ERROR "$page:$line publishes $hash, which matches none of: ${referenced[*]}"
            [[ -n ${GITHUB_ACTIONS:-} ]] && \
                echo "::error file=$page,line=$line::Published SHA-256 matches none of the scripts this page references"
        fi
    done < <(grep -Eno '\b[a-f0-9]{64}\b' "$page" || true)
done < <(find "$CONTENT_DIR" -type f -name '*.md' -print0)

echo
if [[ $stale -eq 0 ]]; then
    Write-Log SUCCESS "$checked page(s) publish a script checksum, all of them current."
    exit 0
fi

if [[ $APPLY == true ]]; then
    Write-Log SUCCESS "Rewrote $stale stale checksum(s)."
    exit 0
fi

Write-Log ERROR "$stale stale checksum(s). Fix them with:"
echo "  .github/scripts/check-doc-checksums.sh --apply"
exit 1
