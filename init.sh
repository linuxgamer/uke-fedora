#!/bin/sh
# shellcheck shell=bash
# One host-only entry point. This preamble also works on minimal Alpine hosts.
if [ "${UKE_IMAGE_ENTRY_LOADED:-0}" != 1 ]; then
    if ! command -v bash >/dev/null 2>&1; then
        for bootstrap_argument in "$@"; do
            if [ "$bootstrap_argument" = --dry-run ] || [ "$bootstrap_argument" = --offline ]; then
                printf '%s\n' 'Bash is missing; dry-run/offline mode will not install it.' >&2
                exit 1
            fi
        done
        bootstrap_root() {
            if [ "$(id -u)" = 0 ]; then "$@";
            elif command -v sudo >/dev/null 2>&1; then sudo -- "$@";
            elif command -v doas >/dev/null 2>&1; then doas -- "$@";
            else printf '%s\n' 'Bash is missing; root, sudo or doas is required.' >&2; exit 1; fi
        }
        # shellcheck disable=SC1091
        . /etc/os-release
        case " $ID ${ID_LIKE:-} " in
            *' alpine '*|*' postmarketos '*) bootstrap_root apk add --no-cache bash;;
            *' debian '*|*' ubuntu '*) bootstrap_root apt-get update; bootstrap_root apt-get -y install bash;;
            *' fedora '*|*' rhel '*) bootstrap_root dnf -y install bash;;
            *' opensuse '*|*' opensuse-tumbleweed '*|*' suse '*) bootstrap_root zypper --non-interactive install bash;;
            *' arch '*) bootstrap_root pacman -S --needed --noconfirm bash;;
            *) printf '%s\n' 'Unsupported Bash bootstrap host.' >&2; exit 1;;
        esac
    fi
    # Bash receives one immutable copy; queued invocations tolerate later edits.
    UKE_IMAGE_ENTRY_LOADED=1 exec bash -c "$(cat "$0")" "$0" "$@"
fi
unset UKE_IMAGE_ENTRY_LOADED
set -Eeuo pipefail
umask 022
root=$(cd -- "$(dirname -- "$0")" && pwd)
entry=$root/uke-fedora-builder/src/image/core.sh
[[ -f $entry ]] || { printf '%s\n' 'Initialize uke-fedora-builder before building: git submodule update --init uke-fedora-builder' >&2; exit 1; }
# shellcheck source=uke-fedora-builder/src/image/core.sh
# shellcheck disable=SC1091
source "$entry"
image_main "$@"
