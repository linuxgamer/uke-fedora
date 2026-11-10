#!/usr/bin/env bash
# The Fedora release target is config/fedora-release.
set -Eeuo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
release=$(<"$root/config/fedora-release") || {
    printf '%s\n' 'Missing config/fedora-release' >&2
    exit 1
}
[[ $release =~ ^[0-9]+$ ]] || {
    printf 'Invalid Fedora release in config/fedora-release: %s\n' "$release" >&2
    exit 1
}
export FEDORA_RELEASE=$release
builder=$root/uke-fedora-builder/build-fedora44-images.sh
[[ -x $builder ]] || {
    printf '%s\n' 'Initialize the image builder: git submodule update --init uke-fedora-builder' >&2
    exit 1
}
exec "$builder" "$@"
