#!/usr/bin/env bash
# Turn release archives into assets GitHub will accept.
#
# GitHub rejects a release asset of 2 GiB or more, and a KDE image archive is
# larger than that. This script moves every archive from --input into --output,
# splits the oversized ones into fixed-size parts, checks that the parts join
# back to the original bytes, and writes the checksums and a README with the
# reassembly commands.
#
# The input archives are consumed instead of copied: the arm64 build runner has
# little room to spare once the boot and userdata images are on disk.
set -Eeuo pipefail

die() { printf 'split-release-assets: %s\n' "$*" >&2; exit 1; }
usage() {
    cat >&2 <<'USAGE'
Usage: split-release-assets.sh --input DIR --output DIR [--limit-mib N]

Moves every *.tar.zst from DIR into a new output directory. An archive of N MiB
or more becomes <name>.part-00, <name>.part-01, ... and the original is removed
after the parts are proven to reassemble to the same bytes. Writes SHA256SUMS
over the emitted assets and README.txt with the reassembly steps.

The limit defaults to 1900 MiB, below the 2 GiB per-asset limit GitHub enforces.
USAGE
    exit 2
}

input=''
output=''
limit=1900
while (($#)); do
    case $1 in
        --input) (($# >= 2)) || usage; input=$2; shift 2 ;;
        --output) (($# >= 2)) || usage; output=$2; shift 2 ;;
        --limit-mib) (($# >= 2)) || usage; limit=$2; shift 2 ;;
        -h|--help) usage ;;
        -*) die "Unknown option: $1" ;;
        *) die "Unexpected argument: $1" ;;
    esac
done
[[ -n $input && -n $output ]] || usage
[[ $limit =~ ^[0-9]+$ ]] || die "Invalid --limit-mib: $limit"
((limit >= 64 && limit < 2048)) || die '--limit-mib must be between 64 and 2047'
[[ -d $input && ! -L $input ]] || die "Missing input directory: $input"
[[ ! -e $output ]] || die "Output already exists: $output"

shopt -s nullglob
archives=("$input"/*.tar.zst)
parts=("$input"/*.tar.zst.part-*)
((${#archives[@]})) || die "No *.tar.zst in $input"
((${#parts[@]} == 0)) || die "Input is already split: $input"

mkdir -p -- "$output"
limit_bytes=$((limit * 1024 * 1024))
emitted=()
split_names=()
split_sums=()

for archive in "${archives[@]}"; do
    [[ -f $archive && ! -L $archive ]] || die "Not a regular file: $archive"
    name=$(basename -- "$archive")
    bytes=$(stat -c %s -- "$archive")
    sum=$(sha256sum -- "$archive")
    sum=${sum%% *}

    if ((bytes < limit_bytes)); then
        mv -- "$archive" "$output/$name"
        emitted+=("$name")
        printf 'Kept %s (%d bytes)\n' "$name" "$bytes"
        continue
    fi

    split --bytes="${limit}m" --numeric-suffixes=0 --suffix-length=2 \
        -- "$archive" "$output/$name.part-" || die "Cannot split $name into $output"
    parts=("$output/$name".part-*)
    ((${#parts[@]} >= 2)) || die "Split produced no parts for $name"
    joined=$(cat -- "${parts[@]}" | sha256sum)
    joined=${joined%% *}
    [[ $joined == "$sum" ]] || die "Reassembly mismatch for $name"
    rm -f -- "$archive"
    for part in "${parts[@]}"; do
        emitted+=("$(basename -- "$part")")
    done
    split_names+=("$name")
    split_sums+=("$sum")
    printf 'Split %s (%d bytes) into %d parts\n' "$name" "$bytes" "${#parts[@]}"
done

(cd "$output" && sha256sum -- "${emitted[@]}" > SHA256SUMS &&
    sha256sum -c --status -- SHA256SUMS) || die "Checksum failure in $output"

{
    printf 'Uke Fedora images\n\n'
    printf 'GitHub rejects a release asset of 2 GiB or more, so archives above\n'
    printf '%s MiB are shipped as numbered parts. Join a split archive before\n' "$limit"
    printf 'extracting it:\n\n'
    for ((i = 0; i < ${#split_names[@]}; i++)); do
        printf '  cat %s.part-* > %s\n' "${split_names[i]}" "${split_names[i]}"
        printf '  echo "%s  %s" | sha256sum -c -\n\n' \
            "${split_sums[i]}" "${split_names[i]}"
    done
    printf 'Then extract with: tar --zstd -xf <archive>\n\n'
    printf 'Check the downloaded files themselves with: sha256sum -c SHA256SUMS\n'
} > "$output/README.txt"

printf 'Release assets and SHA256SUMS are in %s\n' "$output"
