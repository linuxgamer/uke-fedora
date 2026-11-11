#!/usr/bin/env bash
# Create the Uke COPR project and its chroots. Requires a configured copr-cli.
set -Eeuo pipefail

die() { printf 'copr-bootstrap: %s\n' "$*" >&2; exit 1; }
usage() {
    cat >&2 <<'USAGE'
Usage: copr-bootstrap.sh [--dry-run|--apply] [PROJECT]

Creates PROJECT (default: uke-fedora) with the fedora-44-aarch64 and
fedora-44-x86_64 chroots. Defaults to --dry-run.
USAGE
    exit 2
}

mode=dry
project=uke-fedora
for arg in "$@"; do
    case $arg in
        --dry-run) mode=dry;;
        --apply) mode=apply;;
        -h|--help) usage;;
        -*) die "Unknown option: $arg";;
        *) project=$arg;;
    esac
done
[[ $project =~ ^[A-Za-z0-9._-]+$ ]] || die "Invalid project name: $project"
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [[ -n ${COPR_CLI:-} ]]; then
    cli=$COPR_CLI
elif command -v copr-cli >/dev/null; then
    cli=copr-cli
elif [[ -x $root/build/.venv-copr/bin/copr-cli ]]; then
    cli=$root/build/.venv-copr/bin/copr-cli
else
    die 'Install copr-cli first (or set COPR_CLI)'
fi
config=${COPR_CONFIG:-$HOME/.config/copr}
[[ $mode == dry ]] || [[ -f $config ]] || die "Missing COPR config: $config"

chroots=(fedora-44-aarch64 fedora-44-x86_64)
create=("$cli" create "$project"
    --description 'Uke Fedora packages for Xiaomi Pad 7 (SM7675)'
    --instructions 'Enable with: dnf copr enable <login>/'"$project"
)
for chroot in "${chroots[@]}"; do
    create+=(--chroot "$chroot")
done

if "$cli" get "$project" >/dev/null 2>&1; then
    printf 'Project %s already exists; check its chroots with: copr-cli get %s\n' "$project" "$project"
    exit 0
fi

printf '%q ' "${create[@]}"; printf '\n'
if [[ $mode == apply ]]; then
    "${create[@]}"
    printf 'Created %s. Enable it on the tablet with: sudo dnf copr enable <login>/%s\n' "$project" "$project"
fi
