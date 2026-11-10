#!/usr/bin/env bash
# Vendor a pinned upstream snapshot into this workspace.
#
# The workspace never merges upstream branches. This tool applies the upstream
# content commits since the recorded base onto a sync/* branch, one commit at a
# time, and refuses to overwrite paths this fork owns. See UPSTREAM.md.
set -Eeuo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
lock_file=$root/upstream.lock
cd "$root"

die() { printf 'sync-upstream: %s\n' "$*" >&2; exit 1; }
say() { printf '%s\n' "$*"; }
pass() { printf 'PASS  %s\n' "$*"; }
fail() { printf 'FAIL  %s\n' "$*"; failures=$((failures + 1)); }

# Paths this fork owns or that would rewrite its structure. Upstream changes
# to these are reported, never applied automatically.
protected=(
    .gitignore .gitmodules .gitattributes .github
    README.md INSTALL.md UPSTREAM.md
    recovery-uke-ofox senemos-uke-kernel uke-fedora-builder
    uke-linux-hardware-support uke-linux-images uke-project-aloha
    uke-desktop-environment-support
)

usage() {
    cat <<'EOF'
usage: tools/sync-upstream.sh <command> [options]

  status                 show the pin, local position and submodule drift
  fetch                  fetch the pinned upstream branch
  plan                   list upstream commits and classify them
  prepare [--dry-run]    vendor content commits onto a sync/<pin> branch
  verify [BRANCH]        check the sync policy on BRANCH (default: current)
  pin --to REV           move the pin to REV (must be on the upstream branch)

The workspace vendors upstream; it does not merge it. Protected paths are never
written automatically. Nothing is pushed and main is never touched.
EOF
}

lock_get() {
    local key=$1 line
    line=$(grep -E "^[[:space:]]*${key}=" "$lock_file" | tail -n 1) || return 1
    printf '%s\n' "${line#*=}"
}

load_pin() {
    [[ -f $lock_file ]] || die "missing $lock_file"
    repo=$(lock_get repo) || die "upstream.lock: missing repo"
    branch=$(lock_get branch) || die "upstream.lock: missing branch"
    pin=$(lock_get commit) || die "upstream.lock: missing commit"
    pin_date=$(lock_get date) || pin_date=unknown
    git cat-file -e "${pin}^{commit}" 2>/dev/null ||
        die "pin ${pin:0:7} is not in this clone; run: $(basename "$0") fetch"
}

submodule_paths() {
    git config -f .gitmodules --get-regexp '^submodule\..*\.path$' 2>/dev/null |
        awk '{print $2}' || true
}

is_protected() {
    local p=$1 x
    for x in "${protected[@]}"; do
        if [[ $p == "$x" || $p == "$x/"* ]]; then
            return 0
        fi
    done
    return 1
}

is_submodule() {
    local p=$1 s mode
    while IFS= read -r s; do
        [[ $p == "$s" ]] && return 0
    done < <(submodule_paths)
    # Submodules upstream carries but this fork dropped still count as pointers.
    if [[ -n ${pin:-} ]]; then
        mode=$(git ls-tree "$pin" -- "$p" 2>/dev/null | awk '{print $1}')
        [[ $mode == 160000 ]] && return 0
    fi
    return 1
}

changed_paths() {
    git show --pretty=format: --name-only "$1" | sed '/^[[:space:]]*$/d'
}

commit_subject() {
    git log -1 --format='%s' "$1"
}

# Patch identity ignores commit metadata. If upstream ever re-lands a change
# that already exists in the fork, the patch ids match and we skip it instead
# of applying the same diff twice.
commit_patch_id() {
    git show --pretty=format: "$1" | git patch-id --stable | awk '{print $1}'
}

load_fork_patch_ids() {
    local pid rest
    declare -gA fork_pids=()
    while read -r pid rest; do
        [[ -n $pid ]] && fork_pids[$pid]=1
    done < <(git log -p --no-merges "$1..main" 2>/dev/null | git patch-id --stable)
}

# A commit that only moves submodule pointers or edits .gitmodules carries no
# content we want to replay; upstream emits many of these from its snapshot bot.
pointer_only() {
    local c=$1 p seen=0
    while IFS= read -r p; do
        seen=1
        [[ $p == .gitmodules ]] && continue
        is_submodule "$p" || return 1
    done < <(changed_paths "$c")
    ((seen)) || return 1
    return 0
}

require_clean() {
    local dirty
    dirty=$(git status --porcelain --ignore-submodules=all)
    if [[ -n $dirty ]]; then
        printf 'sync-upstream: working tree has changes; commit or stash them first:\n%s\n' "$dirty" >&2
        exit 1
    fi
}

cmd_status() {
    load_pin
    local head base ahead behind tree p wt link head_link pin_link
    head=$(git rev-parse --short HEAD)
    base=$(git merge-base main "$pin" 2>/dev/null || true)
    [[ -n $base ]] || die "no common base with the pin"
    ahead=$(git rev-list --count "$pin..HEAD")
    behind=$(git rev-list --count "HEAD..$pin")
    tree=clean
    [[ -z $(git status --porcelain --ignore-submodules=all) ]] || tree=dirty

    say "pin:    ${pin:0:7} ($pin_date) $repo $branch"
    say "base:   $(git log -1 --format='%h %ad %s' --date=short "$base")"
    say "local:  $head ($(git branch --show-current 2>/dev/null || echo detached)) tree=$tree"
    say "state:  $ahead ahead, $behind behind the pin"
    say ""
    say "submodules: path                       worktree  in-HEAD  in-pin"
    while IFS= read -r p; do
        [[ -n $p ]] || continue
        if [[ -d $p ]]; then
            wt=$(git -C "$p" rev-parse --short HEAD 2>/dev/null || echo unknown)
        else
            wt=missing
        fi
        link=$(git ls-tree HEAD -- "$p" | awk '{print substr($3, 1, 7)}')
        head_link=${link:-none}
        link=$(git ls-tree "$pin" -- "$p" | awk '{print substr($3, 1, 7)}')
        pin_link=${link:-none}
        printf '             %-26s %-9s %-8s %s\n' "$p" "$wt" "$head_link" "$pin_link"
    done < <(submodule_paths)
    say ""
    if ((behind > 0)); then
        say "next:   $(basename "$0") plan"
    else
        say "next:   pin is contained; nothing to vendor"
    fi
}

cmd_fetch() {
    load_pin
    say "fetching $repo $branch"
    git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=30 \
        fetch --prune upstream "$branch"
    local tip
    tip=$(git rev-parse "upstream/$branch")
    say "fetched ${tip:0:7} into upstream/$branch"
    if [[ $tip != "$pin" ]]; then
        say "pin is ${pin:0:7}; after review move it with: $(basename "$0") pin --to $tip"
    fi
}

cmd_plan() {
    load_pin
    local base c subj n=0 content=0 pointers=0 already=0 p pid
    base=$(git merge-base main "$pin") || die "no merge base"
    load_fork_patch_ids "$base"
    say "range ${base:0:7}..${pin:0:7} ($branch)"
    while IFS= read -r c; do
        n=$((n + 1))
        subj=$(commit_subject "$c")
        if pointer_only "$c"; then
            pointers=$((pointers + 1))
            printf '  pointer  %s  %s\n' "${c:0:7}" "$subj"
            continue
        fi
        pid=$(commit_patch_id "$c")
        if [[ -n $pid && -n ${fork_pids[$pid]:-} ]]; then
            already=$((already + 1))
            printf '  present  %s  %s\n' "${c:0:7}" "$subj"
            continue
        fi
        content=$((content + 1))
        printf '  content  %s  %s\n' "${c:0:7}" "$subj"
        while IFS= read -r p; do
            if is_protected "$p"; then
                printf '             protected  %s\n' "$p"
            else
                printf '             apply      %s\n' "$p"
            fi
        done < <(changed_paths "$c")
    done < <(git rev-list --reverse "$base..$pin")
    say ""
    say "summary: $n commits, $content content, $already already in fork, $pointers pointer-only"
    say "next:    $(basename "$0") prepare --dry-run"
}

cmd_prepare() {
    local dry=0 base branch c subj p patch pid
    while (($#)); do
        case $1 in
            --dry-run) dry=1 ;;
            -h | --help) usage; exit 0 ;;
            *) die "unknown option: $1" ;;
        esac
        shift
    done
    load_pin
    require_clean
    base=$(git merge-base main "$pin") || die "no merge base"
    load_fork_patch_ids "$base"
    branch="sync/${pin:0:7}"
    if git rev-parse --verify --quiet "refs/heads/$branch" >/dev/null; then
        die "branch $branch already exists; delete it or use verify"
    fi
    if ((dry)); then
        say "would create branch $branch from main and vendor:"
    else
        git switch -q -c "$branch" main
        say "branch $branch (from main)"
    fi

    while IFS= read -r c; do
        local paths=()
        subj=$(commit_subject "$c")
        if pointer_only "$c"; then
            say "skip pointer   ${c:0:7}  $subj"
            continue
        fi
        pid=$(commit_patch_id "$c")
        if [[ -n $pid && -n ${fork_pids[$pid]:-} ]]; then
            say "skip present   ${c:0:7}  $subj"
            continue
        fi
        local patch_paths=() new_paths=()
        while IFS= read -r p; do
            if is_protected "$p"; then
                continue
            fi
            # A file this fork does not have cannot be patched as a
            # modification; take the post-image from the commit instead.
            if git cat-file -e "HEAD:$p" 2>/dev/null; then
                patch_paths+=("$p")
            else
                new_paths+=("$p")
            fi
        done < <(changed_paths "$c")
        if ((${#patch_paths[@]} + ${#new_paths[@]} == 0)); then
            say "skip protected ${c:0:7}  $subj"
            continue
        fi
        if ((dry)); then
            say "apply          ${c:0:7}  $subj -> ${patch_paths[*]:-} ${new_paths[*]:-}"
            continue
        fi
        if ((${#patch_paths[@]})); then
            patch=$(mktemp)
            git show --pretty=format: "$c" -- "${patch_paths[@]}" >"$patch"
            if ! git apply --3way --index "$patch"; then
                rm -f "$patch"
                die "could not apply ${c:0:7} ($subj); branch $branch is left for inspection"
            fi
            rm -f "$patch"
        fi
        for p in "${new_paths[@]}"; do
            if git cat-file -e "$c:$p" 2>/dev/null; then
                mkdir -p -- "$(dirname -- "$p")"
                git show "$c:$p" >"$p"
                git add -- "$p"
                say "created        ${c:0:7}  $p"
            fi
        done
        if git diff --cached --quiet; then
            git reset -q
            say "skip applied   ${c:0:7}  $subj"
            continue
        fi
        git commit -q -C "$c"
        say "applied        ${c:0:7}  $subj"
    done < <(git rev-list --reverse "$base..$pin")

    say ""
    if ((dry)); then
        say "dry run: nothing changed"
    else
        say "next: review protected paths by hand, test, then: $(basename "$0") verify"
    fi
}

cmd_verify() {
    local target=${1:-} name base c subj missing=0 botcommits pid
    load_pin
    if [[ -n $target ]]; then
        name=$target
    else
        name=$(git rev-parse --abbrev-ref HEAD)
    fi
    base=$(git merge-base main "$pin") || die "no merge base"
    load_fork_patch_ids "$base"
    failures=0
    say "verify $name against ${pin:0:7}"

    if [[ -z $(git status --porcelain --ignore-submodules=all) ]]; then
        pass "working tree clean (submodules ignored)"
    else
        fail "working tree dirty"
    fi

    local want got
    want=$(lock_get submodules) || want=
    got=$(submodule_paths | sort | paste -sd, -)
    if [[ $got == "$(tr ',' '\n' <<<"$want" | sort | paste -sd, -)" ]]; then
        pass ".gitmodules matches the pinned submodule set ($got)"
    else
        fail ".gitmodules is [$got], expected [$want]"
    fi

    local p
    while IFS= read -r p; do
        [[ -n $p ]] || continue
        if git diff --quiet main "$name" -- "$p"; then
            pass "pointer $p unchanged"
        else
            fail "pointer $p changed (move it deliberately, not via sync)"
        fi
    done < <(submodule_paths)

    botcommits=$(git log --format='%ae' "main..$name" | grep -c 'github-actions' || true)
    if ((botcommits == 0)); then
        pass "no snapshot-bot commits vendored"
    else
        fail "$botcommits snapshot-bot commit(s) on $name"
    fi

    while IFS= read -r c; do
        if pointer_only "$c"; then
            continue
        fi
        pid=$(commit_patch_id "$c")
        if [[ -n $pid && -n ${fork_pids[$pid]:-} ]]; then
            continue
        fi
        subj=$(commit_subject "$c")
        if git log --format='%s' "main..$name" | grep -Fxq -- "$subj"; then
            :
        else
            missing=$((missing + 1))
            say "  not vendored: ${c:0:7}  $subj"
        fi
    done < <(git rev-list --reverse "$base..$pin")
    if ((missing == 0)); then
        pass "all upstream content commits are present"
    else
        fail "$missing upstream content commit(s) missing"
    fi

    say ""
    if ((failures > 0)); then
        die "$failures check(s) failed"
    fi
    say "ok"
}

cmd_pin() {
    local to= full date
    while (($#)); do
        case $1 in
            --to) shift; to=${1:-} ;;
            -h | --help) usage; exit 0 ;;
            *) die "unknown option: $1" ;;
        esac
        shift
    done
    [[ -n $to ]] || die "pin needs --to REV"
    load_pin
    full=$(git rev-parse --verify --quiet "${to}^{commit}") || die "unknown revision: $to"
    if ! git merge-base --is-ancestor "$full" "upstream/$branch"; then
        die "$full is not on upstream/$branch; refusing to pin it"
    fi
    date=$(git log -1 --format=%ad --date=short "$full")
    sed -i -e "s|^commit=.*|commit=$full|" -e "s|^date=.*|date=$date|" "$lock_file"
    say "pin moved to ${full:0:7} ($date)"
}

cmd=${1:-}
(($#)) && shift
case $cmd in
    status) cmd_status ;;
    fetch) cmd_fetch ;;
    plan) cmd_plan ;;
    prepare) cmd_prepare "$@" ;;
    verify) cmd_verify "$@" ;;
    pin) cmd_pin "$@" ;;
    '' | -h | --help | help) usage ;;
    *) die "unknown command: $cmd (try --help)" ;;
esac
