#!/usr/bin/env bash
# Fedora 44 is the only image target in this workspace.
set -Eeuo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
builder=$root/uke-fedora-builder/build-fedora44-images.sh
[[ -x $builder ]] || {
    printf '%s\n' 'Initialize the image builder: git submodule update --init uke-fedora-builder' >&2
    exit 1
}
exec "$builder" "$@"
