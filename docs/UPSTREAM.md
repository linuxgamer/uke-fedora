# Upstream pin and sync model

This workspace is a **vendored fork** of [MCC45TR/uke-linux](https://github.com/MCC45TR/uke-linux).
It does not merge upstream branches. Upstream commits are applied one at a time
onto a `sync/*` branch, and the paths this fork owns are never overwritten.

For the environment, checks and contribution flow see
[DEVELOPING.md](DEVELOPING.md); the rules are in [AGENTS.md](../AGENTS.md).

## Pin

| Field | Value |
| --- | --- |
| Repository | `https://github.com/MCC45TR/uke-linux.git` |
| Branch | `Fedora` — the upstream default branch, not `main` |
| Commit | `5786c9cdf3c4af557d4c9bff10e1c93fc0ed774f` |
| Date | 2026-11-06 |

The machine-readable copy is [upstream.lock](../upstream.lock). `tools/sync-upstream.sh`
reads only that file; edit the pin with `tools/sync-upstream.sh pin --to <rev>`.

## Why not merge

A merge looks cheaper than it is:

- Upstream carries **7 submodules**, this fork carries **3**. A merge rewrites
  `.gitmodules` and every gitlink, so those conflicts return on every sync.
- Most upstream commits on the pinned range are bot commits titled
  "Update component branch snapshots" that only move submodule pointers. They
  carry no content, but they do carry conflict noise.
- The umbrella diverges little; the port lives in the three submodule forks, not
  here. Run `tools/sync-upstream.sh status` for the current ahead/behind rather
  than trusting a number copied into this document. Merging the umbrella does
  not sync the port.

## Ownership

| Path | Owner | Sync rule |
| --- | --- | --- |
| `README.md`, `docs/INSTALL.md`, `docs/UPSTREAM.md` | this fork | never taken from upstream |
| `.gitignore`, `.gitmodules`, `.github/` | this fork | never taken; edit by hand |
| `tools/`, `upstream.lock` | this fork | not in upstream at all |
| `AGENTS.md`, `docs/DEVELOPING.md`, `docs/STATE.md`, `docs/BACKLOG.md` | this fork | never taken from upstream |
| `docs/CONTRIBUTING.md` | upstream | vendored, then adjusted locally |
| `senemos-uke-kernel`, `uke-fedora-builder`, `uke-linux-hardware-support` | upstream + fork patches | pointers moved by hand only |
| `recovery-uke-ofox`, `uke-linux-images`, `uke-project-aloha`, `uke-desktop-environment-support` | upstream | dropped by this fork |

Dropped submodules are not used by the image builder in this workspace. If one
becomes required, add it to `upstream.lock` and to `.gitmodules` by hand; the
sync tool will not do it. Upstream's `SECURITY.md` is not carried either; report
security issues as described in [CONTRIBUTING.md](CONTRIBUTING.md).

## Fork drift

Snapshot measured against the MCC45TR repositories on 2026-11-10; remeasure
before relying on it. The umbrella itself was 128 commits ahead and 0 behind the
pin on 2026-11-11 (`tools/sync-upstream.sh status`).

| Component | Ahead | Behind |
| --- | --- | --- |
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

- Submodule forks are 139–272 commits behind (snapshot above). Converting them
  to patch series (`patches/` over a pinned upstream commit) is the next
  structural step.
- The umbrella has no pull-request CI; its only workflow is the manual image
  build. `tools/sync-upstream.sh verify` is the automated sync check, and a
  documentation link check in CI is planned (backlog B14).
- Bot pointer commits are filtered from history by `prepare` but still exist
  upstream; do not reintroduce the snapshot-bot workflow.

## Component rebases (2026-11-10)

Each component fork now has a local sync branch rebased onto the current
upstream tip. Push them before moving the umbrella gitlinks.

| Component | Branch | Upstream base | Net delta | Verification |
| --- | --- | --- | --- | --- |
| kernel | `sync/upstream-20261105` | `fd33b917` (2026-11-05) | 21 files, +85/−93 | `make validate` needs host `rpm`/`rpmspec`, `dtc` and `clang`; without them a late contract fails without a message. See [DEVELOPING.md](DEVELOPING.md#checks) |
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
- Check merged JSON lists for union contradictions. A merge can keep both sides
  of a list, so a package may end up admitted and withdrawn at once; the
  native-runtime catalog did exactly that after the hardware rebase.
- Regenerate source locks after a rebase. The kernel `boot-payload.json` had 29
  of 310 stale hashes that still described the pre-rebase tree.
- Keep upstream's `AGENTS.md`; a forked copy conflicts on every sync and belongs
  in the umbrella instead.

The umbrella gitlinks now point at these branches. The idea of replacing the
fork URLs with upstream repositories plus an applied patch stack was evaluated
on 2026-11-10 and rejected; see "Component model" below.

## Deletion policy

This fork deliberately drops upstream material that is documentation, reports or
policy the port does not use: `docs/`, `reports/`, `SECURITY.md`, per-component
`docs/lessons/`, the `referances/` trees, and the OrangeFox recovery packaging.
Donor sources and build inputs for the port live in `private/`, so `referances/`
only duplicated build files; upstream's Ubuntu recipes that point into it are
unused here.

Some component `AGENTS.md` files still reference the removed `referances/` and
donor-policy trees. That is a known documentation bug (backlog B15): use the
substitutes in [DEVELOPING.md](DEVELOPING.md#missing-evidence-paths) and do not
invent the missing evidence. Fix the rule in the component repository, not with
a forked copy in the umbrella.
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

## Component model (decided 2026-11-10)

The components stay as rebased forks. Patches are an export for review, not the
build mechanism.

Why not upstream URLs plus an applied patch stack: the delta is dominated by
binaries. The builder adds an 11.5 MB boot payload and the hardware component
carries roughly 35 MB of OEM firmware; the `referances` deletions alone encode
about 150 MB in a patch. Applying that from the umbrella would add hundreds of
megabytes and a second way to get the tree wrong.

- Sync: `git -C <component> rebase upstream/main`, resolve, push. The forks sit
  at their upstream base plus one delta commit.
- Review: `tools/export-patches.sh` writes text-only patches to
  `build/patches/` (gitignored, about 1.5 MB total).
- Never apply an exported patch to a pristine upstream tree; it is a review
  artifact, not a build input.
