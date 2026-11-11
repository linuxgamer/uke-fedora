#!/usr/bin/env bash
# Development preflight for the uke-fedora umbrella workspace.
#
#   tools/check-dev-env.sh            full check (source contracts + build hints)
#   tools/check-dev-env.sh --quick    clone shape only, enough for docs work
#
# The script never installs anything and never modifies the tree.
set -Eeuo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"

mode=full
case ${1:-} in
    '') ;;
    --quick) mode=quick ;;
    -h|--help)
        sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
        exit 0
        ;;
    *)
        printf 'check-dev-env: unknown argument: %s\n' "$1" >&2
        exit 2
        ;;
esac

fail=0
missing_required=0
warn=0

hard_fail() {
    printf 'FAIL: %s\n' "$*" >&2
    fail=1
    missing_required=$((missing_required + 1))
}

warning() {
    printf 'WARN: %s\n' "$*"
    warn=$((warn + 1))
}

have() {
    command -v "$1" >/dev/null 2>&1
}

note_missing() {
    local tool=$1 area=$2
    if have "$tool"; then
        printf 'ok      %-12s %s\n' "$tool" "$area"
    else
        hard_fail "$tool is missing ($area)"
    fi
}

printf 'check-dev-env: %s (%s)\n' "$root" "$mode"

# --- base tools and clone shape ---------------------------------------------
for tool in git bash grep sed awk realpath sha256sum python3; do
    note_missing "$tool" 'base tools'
done

if [[ ! -f .gitmodules ]]; then
    hard_fail '.gitmodules is missing; this is not the umbrella checkout'
fi

if [[ ! -f config/fedora-release ]]; then
    hard_fail 'config/fedora-release is missing'
elif [[ ! $(<config/fedora-release) =~ ^[0-9]+$ ]]; then
    hard_fail "config/fedora-release is not a release number: $(<config/fedora-release)"
fi

if have git && [[ -f .gitmodules ]]; then
    while IFS= read -r line; do
        [[ -n $line ]] || continue
        prefix=${line:0:1}
        sha=$(awk '{print $1}' <<<"$line")
        path=$(awk '{print $2}' <<<"$line")
        case $prefix in
            -)
                hard_fail "submodule is not initialized: $path (run: git submodule update --init --recursive)"
                ;;
            U)
                hard_fail "submodule has unresolved conflicts: $path"
                ;;
            +)
                warning "submodule worktree differs from the umbrella gitlink: $path (${sha:0:7}); commit or checkout intentionally"
                ;;
            ' ')
                if [[ ! -e $path/.git ]]; then
                    hard_fail "submodule directory looks empty: $path (run: git submodule update --init --recursive)"
                fi
                ;;
        esac
    done < <(git submodule status)
fi

if ((fail)); then
    printf 'check-dev-env: fix the clone first; host tool checks were not run.\n' >&2
    exit 1
fi

if [[ $mode == quick ]]; then
    printf 'check-dev-env: quick check ok (docs work)\n'
    [[ $warn -gt 0 ]] && printf 'check-dev-env: %d warning(s)\n' "$warn"
    exit 0
fi

# --- source contract tools ---------------------------------------------------
printf '\nSource contracts (kernel validate):\n'
for tool in jq rpm rpmspec dtc clang clang++; do
    note_missing "$tool" 'kernel validate'
done

# --- optional tooling --------------------------------------------------------
printf '\nBuilder CI parity (needed only for builder changes):\n'
for tool in shellcheck zstd zip unzip rg make; do
    if have "$tool"; then
        printf 'ok      %-12s builder CI\n' "$tool"
    else
        warning "$tool is missing (builder CI parity); see docs/DEVELOPING.md#checks"
    fi
done

printf '\nImage and kernel builds (needed only for builds):\n'
if have docker || have podman; then
    printf 'ok      %-12s container engine\n' "$(have docker && echo docker || echo podman)"
else
    warning 'neither docker nor podman is installed (image build)'
fi
for tool in avbtool g++ zstd; do
    if have "$tool"; then
        printf 'ok      %-12s build\n' "$tool"
    else
        warning "$tool is missing (image build); see docs/DEVELOPING.md#what-you-need"
    fi
done

printf '\nNext: tools/check-docs.sh, then the check for the component you edit\n'
printf '(docs/DEVELOPING.md#checks).\n'

if ((fail)); then
    printf 'check-dev-env: %d required check(s) failed; install missing tools or use --quick for docs-only work.\n' "$missing_required" >&2
    exit 1
fi

printf 'check-dev-env: ok'
[[ $warn -gt 0 ]] && printf ' (%d warning(s))' "$warn"
printf '\n'
