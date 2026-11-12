# State

Updated: 2026-11-11 (documentation pass, then the kernel `%prep` fix). Verify
with commands before relying on it; update this file at the end of every
session. Long history and decisions live in the private notes; this file records
only facts.

## Upstream and forks

Upstream: `MCC45TR/uke-linux`, branch `Fedora`, pin `5786c9c` (2026-11-06),
recorded in [`upstream.lock`](../upstream.lock). Model: vendored fork with three
rebased component forks; patches are exported for review only. See
[UPSTREAM.md](UPSTREAM.md).

| Component | Branch | Head | State |
| --- | --- | --- | --- |
| umbrella | `main` | this handoff commit | docs, AGENTS and dev-tooling pass |
| `senemos-uke-kernel` | `main` | `57d7fbb3` (gitlink and worktree) | video series active; native `%prep` fixed; `referances/` removed and its last path strings scrubbed from manifests |
| `uke-fedora-builder` | `main` | `3662473` (gitlink and worktree) | apps, ru locale, COPR repo; internal source cache renamed to `source-cache/` |
| `uke-linux-hardware-support` | `main` | `847a004` (gitlink and worktree) | firmware payload; top-level docs removed, internal caches renamed |

Verify with `git submodule status` and `git ls-tree HEAD -- <component>`; compare
the worktree head with the recorded gitlink before moving a pointer.

## Kernel preparation fix and build unblocking (2026-11-11, later)

- Root-caused the kernel COPR `%prep` failure from the public COPR builder log
  (no API token needed): `packaging/native/prepare.sh` invoked
  `src/video/prepare-source.sh` twice. The first call applied
  `patches/video/*.patch`, whose `0012` creates
  `include/linux/qcom-uke-video.h`; the second call met the bare
  `[[ ! -e ... ]]` re-entry guard and exited 1 without output, which is why the
  log ended after the DP ELD receipt. Fixed in kernel `4ed80615`; a failing
  preparation step now names its line and command through an ERR trap, and
  `tests/native-prepare-steps-contract.sh` rejects a duplicated source step.
- Kernel `e942f625` makes ten sanitizer contracts inherit the builder's
  `ASAN_OPTIONS` (`${ASAN_OPTIONS:-detect_leaks=1}`). They forced
  `detect_leaks=1`, which LeakSanitizer cannot do under qemu-user aarch64, so
  the kernel `%prep` also failed on x86_64 hosts and CI runners that emulate
  aarch64.
- Builder `9b83d79` defines `cache_dir=/build-cache` inside the SRPM container
  heredoc. The "skip unchanged kernel SRPM" change used the host variable there,
  so every image build stopped at stage 0 with "cache_dir: unbound variable".
- Local evidence: `./ukelinux.sh --profiles tty --cross-kernel --output
  build/video13-check` logged `UKE_BUILD_STAGE source_prepare elapsed_s=1090`,
  so the kernel `%prep` passes. The run was stopped before the cross-compile,
  RPM packaging and rootfs stages; no image, RPM or on-device result exists yet.

## Last session (2026-11-11, documentation and agent-rules pass)

- Published the contributor rules as [AGENTS.md](../AGENTS.md) (removed from
  `.gitignore`) and added [docs/DEVELOPING.md](DEVELOPING.md): environment,
  checks, submodule flow, contribution targets, troubleshooting.
- Added `tools/check-dev-env.sh` (clone shape and host tools) and
  `tools/check-docs.sh` (relative links in published docs).
- Added `.github/PULL_REQUEST_TEMPLATE.md` and a developer-guide contact link in
  the issue template config.
- Fixed developer docs: CONTRIBUTING now has a code-contribution section and no
  longer claims the release image is untested on a tablet; UPSTREAM no longer
  claims `SECURITY.md` is vendored, records the real CI situation and the
  missing evidence paths; README links into submodules (404 on GitHub) replaced
  with repository URLs and dev/user entry points separated.
- Updated the three component `AGENTS.md`: removed links to the dropped
  `referances/` and `uke-linux-docs/` trees, retired the OrangeFox and missing
  ACCESSORY paths, added the real checks with host prerequisites and the
  umbrella gitlink/PR flow (component commits `0a0a2631`, `0a48226` and `88ffc06`).
  Also moved `INSTALL.md` to `docs/INSTALL.md`, fixed every link and restored the
  Fedora 44 and CSOT wording in README (`531d154`).
- Findings recorded in the backlog: builder CI parity runner (B12), kernel
  check prerequisites (B13, partly covered by `tools/check-dev-env.sh`), docs
  and link CI (B14), stale component `AGENTS.md` evidence paths (B15), the
  user-facing release/docs refresh (B16, release polish B9 reopened), newcomer
  labels (B17), the security reporting channel (B18) and tooling nits (B19).
- Split the private journal: decisions and host quirks stay in `private/NOTES.md`,
  owner-only actions moved to `private/TODO.md`; public work remains here and in
  the backlog.
- Component source-contracts CI passed for the AGENTS commits (`0a48226`,
  `88ffc06`) and the cleanup commits (`facd4e1`, `8d95e01`); the kernel
  workflow runs on pull requests only.
- Renamed the remaining internal builder and hardware-support caches from
  `referances/` to `source-cache/`, including the staging loop, pinned source
  inputs, component/family caches, manifests' local evidence paths and the
  nested AGENTS policy (builder `3662473`, hardware `847a004`). The unsupported
  Ubuntu packaging route keeps its external source-layout names.
- Removed the trees that kept reappearing: the kernel `referances/` cache and
  OEM evidence, the kernel and builder `reports/`, and the hardware-support
  top-level `docs/`. The kernel SRPM cache moved to the ignored
  `source-cache/releases/`; the Makefile and two native object checks now use
  it (all entry points: kernel `96ee63a6`), and scrubbed the last
  `referances/` path strings from the research/source-plan manifests (kernel
  `57d7fbb3`). Added `tools/check-forbidden-paths.sh` and documented the policy
  in AGENTS/UPSTREAM/DEVELOPING; component commits `2d6ed7b8`/`96ee63a6`/
  `57d7fbb3`, `e9d0cca`, `604b443`/`bd04ec9`.
- Rewrote all three component `AGENTS.md` from the umbrella template and
  removed October documents: 26 kernel, 3 builder and 18 hardware-support
  files created in October 2026 or earlier that were unreferenced and not
  maintained in November (component commits `8d968d14`, `facd4e1`, `8d95e01`).
  README/AGENTS/BUILDING/SECURITY, November-maintained and referenced documents
  remain; removed files are recoverable from git history.

## Previous session (2026-11-11, earlier)

- Added the first version of the root `AGENTS.md`, `docs/STATE.md` and
  `docs/BACKLOG.md`; rewrote the private notes as a decision/host journal.
- Created the COPR project and published eight userland packages. The kernel
  `%prep` failure was later root-caused from the public builder log and fixed
  in `e942f625`; the COPR upload is still pending.
- The image CI run 43008866968 was cancelled; the extended workflow has not run.
- No image has been built after the broad native archive fix (`30dfa729`).

## Working now

- Kernel video bring-up is source-complete: the candidate series applies on
  7.3.1, all contracts pass, Iris/VIDEOCC/interconnect objects compile, and the
  OEM `vpu30_2v.mbn` firmware is packaged.
- COPR project <https://copr.fedorainfracloud.org/coprs/linuxgamer/uke-fedora/>
  has `uke-boot-integration`, `uke-console-input`, `uke-core-meta`,
  `uke-battery-observer`, `uke-touchscreen`, `libssc`, `iio-sensor-proxy` and
  `uke-ssc-fileservice`.
- Images get an optional COPR repo (`UKE_COPR=0` disables it), excluding kernel
  and OEM packages.
- Desktop profiles install Firefox, a text editor, the store, an archive manager
  and a calculator, plus `ru_RU.UTF-8`.
- Release packaging and issue templates exist; screenshots are in the README.
- Build speed: kernel SRPM reuse, locked status file, `--parallel N`, CI caches.

## Blockers

- **Kernel COPR build needs a rebuild.** The `%prep` failure is fixed and the
  native preparation passes locally, but the fixed SRPM has not been uploaded;
  that needs the rotated token (B2).
- **Image CI run `43008866968` was cancelled.** The extended workflow (cache,
  `--parallel`, release packaging) has not run successfully yet.
- **No image has been built after the broad native archive fix** (`30dfa729`).
  The blockers found on that path are fixed (kernel `4ed80615`/`e942f625`,
  builder `9b83d79`) and the local cheap stage passes the kernel `%prep`, but no
  full run has completed.
- **COPR API credentials need rotation**; do not repeat the value in public.
- OEM firmware and sensor blobs stay out of public repositories; see
  [COPR.md](COPR.md).
- The removed upstream evidence trees are documented in
  [DEVELOPING.md](DEVELOPING.md#missing-evidence-paths); do not recreate them.

## Next action

Rotate the COPR token (B2), then upload the fixed kernel SRPM and confirm a green
COPR build (B1), then run the first image build (B3/B4). All three are in the
backlog.
