#!/usr/bin/env bash
#
# Recalculate and optionally apply the SHA-256 checksums of the pinned CI tools.
#
# Renovate bumps the version numbers but cannot compute a checksum, so without
# this the pinned hash keeps pointing at the previous release and every bump
# fails the build with "computed checksum did NOT match". The workflow in
# .github/workflows/update-checksums.yml runs this on Renovate's own pull
# requests and commits the result back onto the branch.
#
# The hash is not simply taken from whatever the download happened to return.
# Each project publishes its own checksum file next to the release; the
# download is verified against that first, and only a verified hash is written
# into the repository.
#
# Usage:
#   .github/scripts/update-tool-checksums.sh           # show, then ask
#   .github/scripts/update-tool-checksums.sh --apply    # write without asking
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

Stop-Script() {
    Write-Log ERROR "$1"
    exit 1
}

Show-Usage() {
    cat <<'EOF'
Usage: update-tool-checksums.sh [--apply]

Options:
  --apply     Write the checksums without prompting
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

readonly HUGO_ACTION=".github/actions/setup-hugo/action.yml"
readonly QUALITY=".github/workflows/quality.yml"

# ── Reading and writing the pinned values ───────────────────────────────────

# Usage: Get-KeyValue <file> <KEY>   ->  value of `KEY: "value"`
Get-KeyValue() {
    sed -n "s/^[[:space:]]*$2:[[:space:]]*\"\([^\"]*\)\".*/\1/p" "$1" | head -n1
}

# Usage: Set-KeyValue <file> <KEY> <value>
Set-KeyValue() {
    sed -i "s|^\([[:space:]]*$2:[[:space:]]*\"\)[^\"]*\"|\1$3\"|" "$1"
}

# Hugo's version and checksum are input defaults in the composite action, so
# there is no key to match on. The version is the `default:` directly under the
# renovate annotation; the checksum is the only `default:` holding 64 hex
# characters.
Get-HugoVersion() {
    grep -A1 'depName=gohugoio/hugo' "$HUGO_ACTION" | sed -n 's/.*default: "\([^"]*\)".*/\1/p' | head -n1
}

Set-HugoSha() {
    sed -i "s|^\([[:space:]]*default: \"\)[a-f0-9]\{64\}\"|\1$1\"|" "$HUGO_ACTION"
}

# ── Fetching and verifying ──────────────────────────────────────────────────

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf -- "$TEMP_DIR"' EXIT

# Usage: Get-VerifiedHash <name> <artifact-url> <expected-sha256>
# Downloads the artifact, checks it against the hash the project published, and
# echoes that hash. Refuses to return anything if the two disagree.
Get-VerifiedHash() {
    local name=$1 url=$2 expected=$3
    local file="$TEMP_DIR/$name"

    [[ "$expected" =~ ^[a-f0-9]{64}$ ]] || Stop-Script "$name: no valid checksum published upstream (got: '$expected')"

    curl -sSL --fail-with-body --retry 5 --retry-delay 3 --retry-all-errors -o "$file" "$url" \
        || Stop-Script "$name: download failed ($url)"

    local actual
    actual="$(sha256sum "$file" | awk '{print $1}')"

    if [[ "$actual" != "$expected" ]]; then
        Stop-Script "$name: download does not match the published checksum. published=$expected downloaded=$actual"
    fi

    echo "$actual"
}

# Usage: Get-PublishedHash <url> <grep-pattern>
# Pulls one line out of a checksums file and returns the hash on it.
Get-PublishedHash() {
    curl -sSL --fail-with-body --retry 5 --retry-delay 3 --retry-all-errors "$1" \
        | grep -- "$2" | awk '{print $1}' | head -n1
}

# ── The tools ───────────────────────────────────────────────────────────────

HUGO_VERSION="$(Get-HugoVersion)"
ACTIONLINT_VERSION="$(Get-KeyValue "$QUALITY" ACTIONLINT_VERSION)"
LYCHEE_VERSION="$(Get-KeyValue "$QUALITY" LYCHEE_VERSION)"

for pair in "Hugo:$HUGO_VERSION" "actionlint:$ACTIONLINT_VERSION" "lychee:$LYCHEE_VERSION"; do
    [[ -n "${pair#*:}" ]] || Stop-Script "Could not read the ${pair%%:*} version. Did the file layout change?"
done

Write-Log INFO "Versions found in the repository:"
echo "  Hugo:        $HUGO_VERSION"
echo "  actionlint:  $ACTIONLINT_VERSION"
echo "  lychee:      $LYCHEE_VERSION"
echo

Write-Log INFO "Downloading and verifying against the published checksums..."

HUGO_SHA256="$(Get-VerifiedHash "hugo.tar.gz" \
    "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz" \
    "$(Get-PublishedHash "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_${HUGO_VERSION}_checksums.txt" "hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz")")"
Write-Log SUCCESS "Hugo:       $HUGO_SHA256"

ACTIONLINT_SHA256="$(Get-VerifiedHash "actionlint.tar.gz" \
    "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz" \
    "$(Get-PublishedHash "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_checksums.txt" "linux_amd64.tar.gz")")"
Write-Log SUCCESS "actionlint: $ACTIONLINT_SHA256"

LYCHEE_SHA256="$(Get-VerifiedHash "lychee.tar.gz" \
    "https://github.com/lycheeverse/lychee/releases/download/lychee-v${LYCHEE_VERSION}/lychee-x86_64-unknown-linux-gnu.tar.gz" \
    "$(Get-PublishedHash "https://github.com/lycheeverse/lychee/releases/download/lychee-v${LYCHEE_VERSION}/lychee-x86_64-unknown-linux-gnu.tar.gz.sha256" "")")"
Write-Log SUCCESS "lychee:     $LYCHEE_SHA256"

echo
if [[ "$APPLY" != true ]]; then
    read -rp "Write these checksums into the repository? [y/N] " response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        Write-Log INFO "No changes made"
        exit 0
    fi
fi

Set-HugoSha "$HUGO_SHA256"
Set-KeyValue "$QUALITY" ACTIONLINT_SHA256 "$ACTIONLINT_SHA256"
Set-KeyValue "$QUALITY" LYCHEE_SHA256 "$LYCHEE_SHA256"

Write-Log SUCCESS "Updated:"
echo "  - $HUGO_ACTION"
echo "  - $QUALITY"
