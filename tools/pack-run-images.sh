#!/usr/bin/env bash
# Pack the images a build run uploaded into release archives.
#
# build.yml uploads a flat set of files: fedora_boot-<profile>-<run>.img,
# userdata-<profile>-<run>.img and manifest-<profile>-<run>.json. This script
# turns each profile back into the archive layout package-release.sh produces
# on the runner, so a release made from an artifact has the same shape as one
# the build published itself.
#
# It reads whatever the artifact holds: a boot-only run has no userdata image,
# and an older run may have no manifest. Nothing is required beyond the boot
# image for the profile to be packed.
set -Eeuo pipefail

die() { printf 'pack-run-images: %s\n' "$*" >&2; exit 1; }
usage() {
    cat >&2 <<'USAGE'
Usage: pack-run-images.sh --run-id ID --tag TAG --output DIR ASSET_DIR

ASSET_DIR is the unpacked uke-images artifact. Every fedora_boot-<profile>-<run>.img
becomes DIR/fedora-44-uke-<tag>-<profile>.tar.zst holding fedora_boot.img and,
when the run produced them, userdata.img and manifest.json, with an inner
SHA256SUMS over those files.
USAGE
    exit 2
}

run_id=''
tag=''
output=''
assets=''
while (($#)); do
    case $1 in
        --run-id) (($# >= 2)) || usage; run_id=$2; shift 2 ;;
        --tag) (($# >= 2)) || usage; tag=$2; shift 2 ;;
        --output) (($# >= 2)) || usage; output=$2; shift 2 ;;
        -h|--help) usage ;;
        -*) die "Unknown option: $1" ;;
        *)
            [[ -z $assets ]] || die "Unexpected argument: $1"
            assets=$1
            shift
            ;;
    esac
done
[[ -n $run_id && -n $tag && -n $output && -n $assets ]] || usage
[[ $run_id =~ ^[0-9]+$ ]] || die "Invalid run id: $run_id"
[[ $tag =~ ^[A-Za-z0-9._-]+$ ]] || die "Invalid tag: $tag"
[[ -d $assets && ! -L $assets ]] || die "Missing asset directory: $assets"
[[ ! -e $output ]] || die "Output already exists: $output"
command -v zstd >/dev/null || die 'zstd is not installed'

shopt -s nullglob
boots=("$assets"/fedora_boot-*.img)
((${#boots[@]})) || die "No fedora_boot-*.img in $assets"

mkdir -p -- "$output"
for boot in "${boots[@]}"; do
    name=$(basename -- "$boot")
    [[ $name == fedora_boot-*-"$run_id".img ]] ||
        die "Image name does not belong to run $run_id: $name"
    profile=${name#fedora_boot-}
    profile=${profile%-"$run_id".img}
    [[ $profile =~ ^(tty|kde|gnome|phosh|plasma-mobile)$ ]] || die "Unexpected profile: $profile"

    userdata=$assets/userdata-$profile-$run_id.img
    manifest=$assets/manifest-$profile-$run_id.json
    [[ -s $boot ]] || die "Empty boot image: $boot"
    [[ ! -e $userdata || -s $userdata ]] || die "Empty userdata image: $userdata"

    stage=$(mktemp -d)
    cp -- "$boot" "$stage/fedora_boot.img"
    files=(fedora_boot.img)
    if [[ -e $userdata ]]; then
        cp -- "$userdata" "$stage/userdata.img"
        files+=(userdata.img)
    fi
    if [[ -e $manifest ]]; then
        cp -- "$manifest" "$stage/manifest.json"
        files+=(manifest.json)
    fi
    (cd "$stage" && sha256sum -- "${files[@]}" > SHA256SUMS &&
        sha256sum -c --status -- SHA256SUMS) ||
        { rm -rf -- "$stage"; die "Checksum failure for $profile"; }

    archive=$output/fedora-44-uke-$tag-$profile.tar.zst
    tar --zstd -cf "$archive" -C "$stage" . || { rm -rf -- "$stage"; die "Cannot write $archive"; }
    rm -rf -- "$stage"
    printf 'Packed %s from %s (%s)\n' "$(basename -- "$archive")" "$profile" "${files[*]}"
done
