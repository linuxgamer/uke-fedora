#!/usr/bin/env bash
# Fail when a removed tree reappears in the umbrella or a component fork.
#
# Forbidden paths (see docs/UPSTREAM.md, deletion policy):
#   every component : referances/
#   kernel          : reports/
#   builder         : reports/
#   hardware-support: top-level docs/ (per-component docs/ stay allowed)
#
# Checks both tracked paths and untracked directories on disk. Run before a
# commit and after every upstream sync.
set -Eeuo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
fail=0
checked=0

fail_path() {
    printf 'FAIL: %s: %s\n' "$1" "$2" >&2
    fail=1
}

check_repo() {
    local repo=$1
    shift
    local prefixes=("$@") prefix path
    if [[ ! -d $repo/.git && ! -e $repo/.git ]]; then
        printf 'SKIP: %s is not a clone\n' "$repo"
        return
    fi
    checked=$((checked + 1))
    for prefix in "${prefixes[@]}"; do
        if [[ -e $repo/$prefix ]]; then
            fail_path "$repo" "directory exists: $prefix"
        fi
        while IFS= read -r path; do
            case $path in
                "$prefix"*) fail_path "$repo" "tracked path: $path" ;;
            esac
        done < <(git -C "$repo" ls-files)
    done
}

check_repo "$root" referances/ Referances/
for component in senemos-uke-kernel uke-fedora-builder uke-linux-hardware-support; do
    case $component in
        uke-linux-hardware-support) check_repo "$root/$component" referances/ docs/ ;;
        *) check_repo "$root/$component" referances/ reports/ ;;
    esac
done

printf 'check-forbidden-paths: %d repositories checked\n' "$checked"
if ((fail)); then
    printf 'check-forbidden-paths: removed trees are back; see docs/UPSTREAM.md\n' >&2
    exit 1
fi
printf 'check-forbidden-paths: ok\n'
