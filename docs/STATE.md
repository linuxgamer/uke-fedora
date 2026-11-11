# State

Updated: 2026-11-11 (documentation and agent-rules pass). Verify with commands
before relying on it; update this file at the end of every session. Long history
and decisions live in the private notes; this file records only facts.

## Upstream and forks

Upstream: `MCC45TR/uke-linux`, branch `Fedora`, pin `5786c9c` (2026-11-06),
recorded in [`upstream.lock`](../upstream.lock). Model: vendored fork with three
rebased component forks; patches are exported for review only. See
[UPSTREAM.md](UPSTREAM.md).

| Component | Branch | Head | State |
| --- | --- | --- | --- |
| umbrella | `main` | this handoff commit | docs, AGENTS and dev-tooling pass |
| `senemos-uke-kernel` | `main` | umbrella gitlink `80c0af3e`; fork worktree advanced to `e942f625` | video series active, kernel COPR prep failing |
| `uke-fedora-builder` | `main` | umbrella gitlink `d2c3393`; fork worktree advanced to `9b83d79` | apps, ru locale, COPR repo, parallel build |
| `uke-linux-hardware-support` | `main` | `1fdc4af` (gitlink and worktree) | firmware payload, Python rule removed |

Verify with `git submodule status` and `git ls-tree HEAD -- <component>`; compare
the worktree head with the recorded gitlink before moving a pointer.

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
- Findings recorded in the backlog: builder CI parity runner (B12), kernel
  check prerequisites (B13, partly covered by `tools/check-dev-env.sh`), docs
  and link CI (B14), stale component `AGENTS.md` evidence paths (B15), the
  user-facing release/docs refresh (B16, release polish B9 reopened), newcomer
  labels (B17), the security reporting channel (B18) and tooling nits (B19).
- Split the private journal: decisions and host quirks stay in `private/NOTES.md`,
  owner-only actions moved to `private/TODO.md`; public work remains here and in
  the backlog.

## Previous session (2026-11-11, earlier)

- Added the first version of the root `AGENTS.md`, `docs/STATE.md` and
  `docs/BACKLOG.md`; rewrote the private notes as a decision/host journal.
- Created the COPR project and published eight userland packages. The kernel
  still fails in `%prep` (latest attempts: 11307436, 11307449, 11307468).
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

- **Kernel COPR build fails in `%prep`** after the ELD test, at
  `src/video/prepare-source.sh`, with no error line in the log. The same series
  applies locally. Needs a local reproduction of the native preparation or a
  mock log with tracing.
- **Image CI run `43008866968` was cancelled.** The extended workflow (cache,
  `--parallel`, release packaging) has not run successfully yet.
- **No image has been built after the broad native archive fix** (`30dfa729`).
  The last local attempts failed during `%prep`; validation and pin checks now
  pass, but the first successful build is still pending.
- **COPR API credentials need rotation**; do not repeat the value in public.
- OEM firmware and sensor blobs stay out of public repositories; see
  [COPR.md](COPR.md).
- **Component `AGENTS.md` files reference evidence paths that this fork removed**
  (backlog B15); use [DEVELOPING.md](DEVELOPING.md#missing-evidence-paths).

## Next action

Rotate the COPR token (B2), then debug the kernel COPR `%prep` failure (B1) or
run the first image build (B3). All three are in the backlog.
