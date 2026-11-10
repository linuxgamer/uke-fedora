#!/usr/bin/env bash
# Export each component's port delta as a reviewable text patch.
#
# The build keeps the rebased forks; patches are an export only. Binary payloads
# (firmware blobs, boot template) are excluded: they dominate the diff and are
# not usable as patches.
set -Eeuo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
out=${1:-$root/build/patches}
mkdir -p "$out"

declare -A names=(
    [senemos-uke-kernel]=kernel
    [uke-fedora-builder]=builder
    [uke-linux-hardware-support]=hardware-support
)

for sub in senemos-uke-kernel uke-fedora-builder uke-linux-hardware-support; do
    repo=$root/$sub
    base=$(git -C "$repo" rev-parse upstream/main)
    mapfile -t files < <(git -C "$repo" diff --numstat "$base"..main | awk '$1 != "-" {print $3}')
    if ((${#files[@]} == 0)); then
        printf 'export: %s has no text delta\n' "$sub" >&2
        continue
    fi
    patch=$out/${names[$sub]}.patch
    git -C "$repo" diff "$base"..main -- "${files[@]}" >"$patch"
    printf '%-18s %8s  %s files\n' "${names[$sub]}" \
        "$(du -h "$patch" | cut -f1)" "$(grep -c '^diff --git' "$patch")"
done
