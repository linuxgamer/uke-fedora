#!/usr/bin/env bash
# Check relative links in published umbrella documentation.
#
# Rules:
#   - links must resolve to a tracked path in the umbrella repository;
#   - links into a submodule are rejected: GitHub renders them as 404;
#   - links into private/, build/ or artifacts/ are rejected: not published;
#   - external links, mail links and same-page anchors are skipped.
set -Eeuo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"

fail=0
checked=0

report() {
    printf '%s:%s: %s\n' "$1" "$2" "$3" >&2
}

while IFS= read -r -d '' file; do
    while IFS= read -r match; do
        line=${match%%:*}
        target=${match#*:}
        [[ -n $target ]] || continue
        target=${target#']('}
        target=${target%')'}
        target=${target%%#*}
        target=${target#<}
        target=${target%>}
        [[ -n $target ]] || continue
        case $target in
            http://*|https://*|mailto:*|tel:*|\#*) continue ;;
        esac
        if [[ $target == /* ]]; then
            report "$file" "$line" "absolute path link: $target"
            fail=1
            continue
        fi
        checked=$((checked + 1))
        resolved=$(realpath -m --relative-to="$root" -- "$(dirname "$file")/$target")
        case $resolved in
            ../*)
                report "$file" "$line" "link escapes the repository: $target"
                fail=1
                continue
                ;;
            senemos-uke-kernel/*|senemos-uke-kernel|uke-fedora-builder/*|uke-fedora-builder|uke-linux-hardware-support/*|uke-linux-hardware-support)
                report "$file" "$line" "link into a submodule (404 on GitHub): $target"
                fail=1
                continue
                ;;
            private/*|build/*|artifacts/*|\<*)
                report "$file" "$line" "link to an unpublished path: $target"
                fail=1
                continue
                ;;
        esac
        if [[ ! -e $resolved ]]; then
            report "$file" "$line" "missing target: $target ($resolved)"
            fail=1
        fi
    done < <(grep -noE '\]\([^)]*\)' -- "$file")
done < <(git ls-files -z --cached --others --exclude-standard '*.md')

printf 'check-docs: %d link(s) checked in %s\n' "$checked" "$root"
if ((fail)); then
    printf 'check-docs: broken links found\n' >&2
    exit 1
fi
printf 'check-docs: ok\n'
