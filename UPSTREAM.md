# Upstream pin and sync model

This workspace is a **vendored fork** of [MCC45TR/uke-linux](https://github.com/MCC45TR/uke-linux).
It does not merge upstream branches. Upstream commits are applied one at a time
onto a `sync/*` branch, and the paths this fork owns are never overwritten.

## Pin

| Field | Value |
| --- | --- |
| Repository | `https://github.com/MCC45TR/uke-linux.git` |
| Branch | `Fedora` — the upstream default branch, not `main` |
| Commit | `5786c9cdf3c4af557d4c9bff10e1c93fc0ed774f` |
| Date | 2026-11-06 |

The machine-readable copy is [upstream.lock](upstream.lock). `tools/sync-upstream.sh`
reads only that file; edit the pin with `tools/sync-upstream.sh pin --to <rev>`.

## Why not merge

A merge looks cheaper than it is:

- Upstream carries **7 submodules**, this fork carries **3**. A merge rewrites
  `.gitmodules` and every gitlink, so those conflicts return on every sync.
- Most upstream commits on the pinned range are bot commits titled
  "Update component branch snapshots" that only move submodule pointers. They
  carry no content, but they do carry conflict noise.
- The umbrella barely diverges: 26 files, +155/−1006 against the pin. The port
  lives in the three submodule forks, not here. Merging the umbrella does not
  sync the port.

## Ownership

| Path | Owner | Sync rule |
| --- | --- | --- |
| `README.md`, `INSTALL.md`, `UPSTREAM.md` | this fork | never taken from upstream |
| `.gitignore`, `.gitmodules`, `.github/` | this fork | never taken; edit by hand |
| `tools/`, `upstream.lock` | this fork | not in upstream at all |
| `CONTRIBUTING.md`, `SECURITY.md` | upstream | vendored, then adjusted locally |
| `senemos-uke-kernel`, `uke-fedora-builder`, `uke-linux-hardware-support` | upstream + fork patches | pointers moved by hand only |
| `recovery-uke-ofox`, `uke-linux-images`, `uke-project-aloha`, `uke-desktop-environment-support` | upstream | dropped by this fork |

Dropped submodules are not used by the image builder in this workspace. If one
becomes required, add it to `upstream.lock` and to `.gitmodules` by hand; the
sync tool will not do it.

## Fork drift

Measured against the MCC45TR repositories on 2026-11-10:

| Component | Ahead | Behind |
| --- | --- | --- |
| umbrella `uke-fedora` | 72 | 11 |
| `senemos-uke-kernel` | 23 | 139 |
| `uke-fedora-builder` | 54 | 141 |
| `uke-linux-hardware-support` | 36 | 272 |

The three forks are the real sync problem. Until they become patch series over
a pinned upstream commit, this tool only guards the umbrella; moving a submodule
pointer stays a deliberate manual act.

## Workflow

```sh
tools/sync-upstream.sh status          # pin, position, submodule drift
tools/sync-upstream.sh fetch           # fetch the pinned branch
tools/sync-upstream.sh plan            # what is content, what is pointer noise
tools/sync-upstream.sh prepare --dry-run
tools/sync-upstream.sh prepare         # vendor content onto sync/<pin>
tools/sync-upstream.sh verify          # policy checks on the sync branch
```

`prepare` refuses a dirty tree, creates `sync/<pin-short>` from `main`, and
applies each upstream content commit with its own message. Protected paths are
reported and skipped; resolve them by hand in a follow-up commit. Nothing is
pushed and `main` is never touched.

After the branch passes `verify` and the image smoke test, merge it into `main`,
then move the pin with `tools/sync-upstream.sh pin --to <new-rev>`.

## Known open items

- Submodule forks are 139–272 commits behind. Converting them to patch series
  (`patches/` over a pinned upstream commit) is the next structural step.
- The umbrella has no CI; `verify` is the only automated check in this file.
- Bot pointer commits are filtered from history by `prepare` but still exist
  upstream; do not reintroduce the snapshot-bot workflow.

## Component rebases (2026-11-10)

Each component fork now has a local sync branch rebased onto the current
upstream tip. Push them before moving the umbrella gitlinks.

| Component | Branch | Upstream base | Net delta | Verification |
| --- | --- | --- | --- | --- |
| kernel | `sync/upstream-20261105` | `fd33b917` (2026-11-05) | 21 files, +85/−93 | `make validate` passes until a test that needs host `rpm`; that test fails on clean upstream too |
| builder | `sync/upstream-20261102` | `781079d` (2026-11-02) | 80 files, +2128/−9965 | `device-preflight` passes; two image tests require root and fail on clean upstream too |
| hardware | `sync/upstream-20261106` | `5903eb7` (2026-11-06) | 414 files, +6858/−2779 | `make validate` passes |

Exported delta: `build/patches-<component>/0001-port-delta.patch` (build output,
not committed).

Rules learned from the first rebase:

- Rebase with `git merge` (or a merge in a worktree), not by applying a
  whole-tree patch. Upstream deletes and renames paths, and a patch generated
  from the old tree fails on modifications to files upstream removed.
- Do not union upstream's package sets blindly. `uke-orangefox-packaging` has no
  `validate` target here, and upstream's `python_target_payload` check requires
  the field to exist in `xiaomi-uke-firmware/manifests/component.json`.
- Regenerate source locks after a rebase. The kernel `boot-payload.json` had 29
  of 310 stale hashes that still described the pre-rebase tree.
- Keep upstream's `AGENTS.md`; a forked copy conflicts on every sync and belongs
  in the umbrella instead.

Next: push the branches, move the umbrella gitlinks, then replace the fork
URLs in `.gitmodules` with the upstream repositories plus a `patches/` stack
applied by the build.

## Deletion policy

This fork deliberately drops upstream material that is documentation, reports or
policy the port does not use: `docs/`, `reports/`, `SECURITY.md`, per-component
`docs/lessons/` and `referances/README.md`, and the OrangeFox recovery packaging.
Conflicts in those paths are resolved by keeping them deleted; do not restore
them just to silence a conflict.

Functional files are different. Before accepting a deletion during a rebase,
check that nothing in the tree still references the path:

```sh
git grep -n '<deleted-file-name>' <sync-branch>
```

The first rebase caught one such regression: the builder had deleted
`src/audit/check-target-payload.sh` and `tests/original-kde-payload.sh`, while
`src/public/stage.sh`, `packaging/uke-image-tools.spec` and three tests still
invoked them. Both files were restored from upstream. The deleted builder
manifests (`source-plan.json`, runtime locks, stale reports) have no references
and stay deleted.
