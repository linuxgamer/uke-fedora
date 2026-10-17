#!/usr/bin/env bash
# Gather one verified image pair under a public release name. No device access.
set -euo pipefail
umask 022

usage() {
    echo 'Usage: stage-release.sh VERSION NUMBER stock|stock-tty|stock-kde|stock-gnome|uefi CANDIDATE_DIRECTORY [OUTPUT_ROOT]' >&2
    echo 'Example: stage-release.sh 44 1 stock uke-fedora-rootfs/build/boot-pair/pair-...' >&2
    echo 'Variant example: stage-release.sh 44 4 stock-tty uke-fedora-rootfs/build/boot-pair/pair-...' >&2
}

if [[ $# != 4 && $# != 5 ]]; then usage; exit 2; fi
version=$1 number=$2 mode=$3 source_dir=$4
[[ $version == rawhide || $version =~ ^[1-9][0-9]*$ ]] || { usage; exit 2; }
[[ $number =~ ^[1-9][0-9]*$ ]] || { usage; exit 2; }
[[ $mode == stock || $mode == stock-tty || $mode == stock-kde || $mode == stock-gnome || $mode == uefi ]] || { usage; exit 2; }
[[ -d $source_dir && ! -L $source_dir ]] || { echo 'Candidate directory is missing or is a symlink' >&2; exit 1; }
source_dir=$(realpath -e -- "$source_dir")
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
output_root=${5:-$script_dir/artifacts/releases}
tag=fedora-$version-uke-r$number
target=$output_root/$tag
variant=''
if [[ $mode == stock-* ]]; then
    variant=${mode#stock-}
    target=$target/$variant
    mode=stock
fi

for tool in jq sha256sum cp mktemp mv realpath; do
    command -v "$tool" >/dev/null || { printf 'Missing tool: %s\n' "$tool" >&2; exit 2; }
done
[[ -f $source_dir/SHA256SUMS && ! -L $source_dir/SHA256SUMS ]] || { echo 'Candidate SHA256SUMS is missing' >&2; exit 1; }
(cd "$source_dir"; sha256sum -c --status SHA256SUMS) || { echo 'Candidate checksum verification failed' >&2; exit 1; }

case $mode in
    stock)
        files=(fedora_boot.img system.img)
        name_prefix=$tag
        [[ -z $variant ]] || name_prefix=$tag-$variant
        names=("$name_prefix-stock-boot.img" "$name_prefix-stock-system.img")
        [[ -f $source_dir/manifest.json && ! -L $source_dir/manifest.json &&
           -f $source_dir/qemu/result.json && ! -L $source_dir/qemu/result.json ]] || { echo 'Stock pair evidence is missing' >&2; exit 1; }
        boot_hash=$(sha256sum "$source_dir/${files[0]}"); boot_hash=${boot_hash%% *}
        system_hash=$(sha256sum "$source_dir/${files[1]}"); system_hash=${system_hash%% *}
        vm_hash=$(sha256sum "$source_dir/qemu/result.json"); vm_hash=${vm_hash%% *}
        jq -e --arg version "$version" --arg variant "$variant" --arg boot "$boot_hash" --arg system "$system_hash" --arg vm "$vm_hash" '
            .schema_version==1 and .profile.device=="uke" and
            .profile.distribution=="fedora" and .profile.release==$version and
            ($variant=="" or .profile.variant==$variant) and
            .sha256.boot==$boot and .sha256.system==$system and
            .qemu_tested==true and .qemu_evidence.sha256==$vm
        ' "$source_dir/manifest.json" >/dev/null || { echo 'Stock pair evidence does not match the images or Fedora version' >&2; exit 1; }
        ;;
    uefi)
        files=(uke-linux.img.zst uke-esp.img.zst)
        names=("$tag-uefi-root.img.zst" "$tag-uefi-esp.img.zst")
        [[ -f $source_dir/manifest.json && ! -L $source_dir/manifest.json &&
           -f $source_dir/partition-contract.json && ! -L $source_dir/partition-contract.json ]] || { echo 'UEFI candidate evidence is missing' >&2; exit 1; }
        jq -e '.schema_version==1 and .static_checks_passed==true' "$source_dir/manifest.json" >/dev/null || { echo 'UEFI candidate checks are incomplete' >&2; exit 1; }
        jq -e --arg version "$version" '.device=="uke" and .distribution=="fedora" and .release==$version' "$source_dir/partition-contract.json" >/dev/null || { echo 'UEFI candidate Fedora version does not match' >&2; exit 1; }
        ;;
esac

for file in "${files[@]}"; do
    [[ -f $source_dir/$file && ! -L $source_dir/$file ]] || { printf 'Missing regular image: %s\n' "$file" >&2; exit 1; }
    actual_hash=$(sha256sum "$source_dir/$file"); actual_hash=${actual_hash%% *}
    matched=0
    while read -r expected listed; do
        listed=${listed#\*}; listed=${listed#./}
        if [[ $listed == "$file" && $expected == "$actual_hash" ]]; then matched=1; fi
    done < "$source_dir/SHA256SUMS"
    ((matched)) || { printf 'Image is not covered by candidate checksums: %s\n' "$file" >&2; exit 1; }
done
mkdir -p -- "$output_root"
if [[ -n $variant ]]; then
    release_dir=$output_root/$tag
    [[ ! -L $release_dir && ( ! -e $release_dir || -d $release_dir ) ]] || { echo 'Release parent is not a directory or is a symlink' >&2; exit 1; }
    mkdir -p -- "$release_dir"
fi
[[ ! -e $target && ! -L $target ]] || { echo 'Release directory already exists' >&2; exit 1; }
stage_parent=$output_root
[[ -z $variant ]] || stage_parent=$release_dir
stage=$(mktemp -d "$stage_parent/.$tag.XXXXXX")
trap 'rm -rf -- "$stage"' EXIT
for index in 0 1; do
    cp --reflink=auto -- "$source_dir/${files[$index]}" "$stage/${names[$index]}"
done
(cd "$stage"; sha256sum "${names[@]}" > SHA256SUMS; sha256sum -c --status SHA256SUMS)
chmod 0644 -- "$stage/${names[0]}" "$stage/${names[1]}" "$stage/SHA256SUMS"
chmod 0755 -- "$stage"
mv -T -- "$stage" "$target"
trap - EXIT
printf 'Staged local candidate: %s\n' "$target"
