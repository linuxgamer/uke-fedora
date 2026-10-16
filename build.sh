#!/usr/bin/env bash
set -Eeuo pipefail
umask 022
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

usage() {
    cat <<'HELP'
Usage: ./build.sh TARGET [options]

  kernel        Kernel RPM/SRPM; select a version with --build VERSION
  core          Console root filesystem and UEFI/ESP images
  boot-pair     Stock bootloader boot and system image pair
  boot          Initramfs-only debug boot image
  check-device  Read-only checks for a built pair; --offline checks files only

Use ./build.sh TARGET --help for that target's options.
Current kernel and image recipes target Fedora 44.
Build commands may install missing host prerequisites. Read the build guides
before a full build. --dry-run and --offline do not install host packages.
HELP
}

if (($# == 0)); then
    usage
    exit 0
fi
target=$1
shift
case $target in
    --help|-h) usage; exit 0;;
    kernel) component=uke-mainline-linux; entry=$root/$component/build.sh;;
    core|boot|boot-pair|check-device)
        component=uke-fedora-rootfs; entry=$root/$component/src/image/core.sh;;
    *) printf 'Unknown target: %s\n' "$target" >&2; usage >&2; exit 2;;
esac
if [[ ! -f $entry ]]; then
    printf 'Missing %s. Run: git submodule update --init %s\n' "$entry" "$component" >&2
    exit 1
fi
if [[ $target == kernel ]]; then
    exec bash "$entry" "$@"
fi
for argument in "$@"; do
    case $argument in
        --build|--build=*|--check-device) printf 'Choose the image target with ./build.sh TARGET.\n' >&2; exit 2;;
    esac
done
# shellcheck source=uke-fedora-rootfs/src/image/core.sh
source "$entry"
if [[ $target == check-device ]]; then
    image_main --check-device "$@"
else
    image_main --build "$target" "$@"
fi
