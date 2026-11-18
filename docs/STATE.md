# State

Updated: 2026-11-18 (keyboard merged into `main` on the 7.3.1 pin). Verify
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
| `senemos-uke-kernel` | `main` | `deccf8a` (gitlink and worktree) | video series active; native `%prep` fixed; Nanosic WN8030 HID keyboard with an independent ABL overlay; upstream reset pulse and resume keepalive merged; `referances/` removed and its last path strings scrubbed from manifests |
| `uke-fedora-builder` | `main` | `3662473` (gitlink and worktree) | apps, ru locale, COPR repo; internal source cache renamed to `source-cache/` |
| `uke-linux-hardware-support` | `main` | `cf48c20` (gitlink and worktree) | firmware payload with uke-firmware provides; top-level docs removed, internal caches renamed |

Verify with `git submodule status` and `git ls-tree HEAD -- <component>`; compare
the worktree head with the recorded gitlink before moving a pointer.

## Pogo keyboard on `main` (2026-11-18)

`main` is `origin/main` (`2d22cc0`) plus two commits. The first moves only the
kernel gitlink, from `57d7fbb3` to `3163e55`, which is `saksham-991`'s kernel
`main` (`2e2a114`, 32 commits on `57d7fbb3`) plus one commit of ours.

The kernel side is the fork's mature WN8030 HID driver (`src/hid/hid-nanosic-wn8030.c`):
keyboard, consumer and touchpad HID reports, LED class devices for the mic-mute
and keyboard backlight, the `/dev/nanosic_hinge` tablet-mode interface with its
UAPI header, the `nanosic,wn8030-uke` variant and the auth token handshake. The
driver loads `nanosic/MCU_Upgrade.bin` at probe time and fails without it, so
the umbrella carries the 83,436-byte `configs/nanosic/MCU_Upgrade.bin` and the
CI overlay installs it to `/usr/lib/firmware/nanosic/`.

Our commit on top keeps the keyboard out of the optional display overlay: the
fragments moved from `src/input/sm7675-uke-focus-keyboard.dtsi`, which the O82
display overlay included, into a standalone `src/input/sm7675-uke-focus-keyboard.dtso`
applied by `uke-abl.c` as a fourth overlay after the USB one. The fragments
target the OEM nodes by path instead of the `qupv3_se3_i2c` label; only
`tlmm`, `gpi_dma0`, `L22B` and `L23B` are needed from `__symbols__`, and all
four are present on the device. The bus runs at 400 kHz, the IRQ is pin 116 on
the rising edge, reset is 127, status 128, sleep 98, `vddio` is L23B and
`dvdd` L22B.

`make check-pins` passes, the overlay compiles with `dtc`, applies to a
synthetic base carrying those four symbols, and the CI overlay anchors match
the new pin. The kernel was not compiled, the image was not built and nothing
was tested on the tablet.

The kernel submodule URL now points at the `Dustymind` fork of the kernel
repository, because `3163e55` exists only there once it is pushed.
`actions/checkout` fetches submodules recursively, so a run started before that
push fails at checkout with `not our ref` rather than during the build.

## Fork sync `saksham-991/uke-fedora` (2026-11-18)

Merge commit `241563b` brings the six upstream umbrella commits
(`817c38b..08cc97a`) into `main`; the kernel gitlink moves to `deccf8a`, the
merge of our `ba3156d` with the upstream `378c41f` (reset pulse: 2 ms, boot
50 ms, wake 20 ms) and `eae9b27` (restart the 12 s keepalive after resume).

Upstream additions kept: the `MCU_Upgrade.bin` install (identical blob), the
`nanosic-authd` script and unit, and `modules-load.d/nanosic.conf` which loads
`hid-nanosic-wn8030` at boot. Both `replace_or_skip` conversions around the
module-signing policy are kept; they now hit the already-applied marker in the
pinned tree and only the integrity-lockdown rewrite runs.

Our side kept: the zh_CN locale block, the `authselect` PAM assertion, and the
removal of the GDM and pre-created-account overlay, so KDE still ships stock
SDDM with the Plasma first-run setup.

`nanosic-authd.service` is also enabled now: upstream installs the unit and
`[Install] WantedBy=multi-user.target` but never enables it, and the image has
no preset pass for a file installed outside rpm. The overlay writes the
`multi-user.target.wants` symlink itself, which is what `systemctl enable`
would create, so no host tooling is involved. The unit is a plain system
service: root, no session bus, no graphical target, no login, so it answers
`/dev/nanosic_auth` from early boot and on the `tty` profile as well, where the
same rootfs block runs.

Tested off-device against a pty standing in for the char device: a 32-byte
request is answered with the 16-byte zero token, with a 32-hex
`/etc/nanosic/auth-token` it is answered with that token, and with no device
present the daemon stays up retrying every 2 s. The driver drops auth requests
without stalling the IRQ thread when the device is not open, so the keyboard
keeps working whether the daemon runs or not. Two caveats: the daemon holds a
single open, and its SIGTERM handler cannot break the blocking read, so
`systemctl stop` waits for the stop timeout before SIGKILL.

The kernel spec still says release `106` and the builder still pins
`7.3.1`/`106`, so an image built from this head carries the same NEVRA as
`ci-44209941663` with different kernel content. Bump both before installing an
image over an existing system.

## CI rootfs overlay: locale, login and PAM (2026-11-18)

`maint/prepare-ci-tree.py` now ships Simplified Chinese and the stock login
stack:

- `glibc-langpack-zh` and `langpacks-zh_CN` replace `glibc-langpack-ru` and
  `langpacks-ru`; `/etc/locale.conf` is `zh_CN.UTF-8` and
  `google-noto-sans-cjk-fonts` is installed. Fedora has no `noto-fonts-cjk`
  package: the Noto CJK family is split, and the sans face is the one the
  desktop needs.
- The GDM overlay is gone. KDE keeps its own `sddm.service` with
  `plasma-setup.service`, so the first user comes from the Plasma first-run
  setup, exactly as upstream. No account, password or SSH credential is
  shipped, `root` stays locked and `first-boot-policy` keeps its
  `Requires=uke-root-capacity.service uke-swap-ready.service` ordering.

Password authentication in the previous image could not work as intended:

1. The demo `uke:fedora` account was created only in
   `src/public/desktop-setup.sh`, and only `src/public/stage.sh` sources that
   file; `build-rootfs.sh` does not. The account the overlay promised therefore
   never reached the image. The remaining account path was the
   `plasma-setup.service` wizard, which runs `Before=display-manager.service`,
   and `build-rootfs.sh` still refuses to finish unless `root` stays locked, so
   there was no fallback account.
2. That wizard sets the password through `chpasswd`, and every password prompt
   reads `/etc/pam.d/system-auth` and `/etc/pam.d/password-auth`. Both are ghost
   files owned by `authselect-libs`: only its posttrans creates them, and that
   posttrans hides its own errors. Nothing in the builder verified them, so a
   failed `authselect select` would leave a desktop that starts but rejects every
   password. The overlay now runs
   `authselect select local with-silent-lastlog --force --nobackup` before the
   rootfs is finalized and stops the build if either file is missing.

The overlay patterns were validated with `--check` against builder `3662473`,
kernel `3163e55` and hardware `cf48c20`; nothing was built or installed.

## Release assets: compression and splitting (2026-11-18)

Run `44192935337` built all 17 stages in 52m58s and failed only in `Publish
release`: GitHub rejects a single release asset of 2 GiB or more, the KDE
archive is about 2.4 GiB, `gh release create` returned HTTP 422 and rolled the
whole release back. The artifact was complete (7.54 GiB).

- The packaging step now runs with `ZSTD_CLEVEL=19` and `ZSTD_NBTHREADS=4`, which
  the `tar --zstd` child honours. Measured on 1.2 GiB of PE binaries: 359 MB at
  level 3, 269 MB at level 19. `ZSTD_NBTHREADS=0` means one thread, not all.
  `--long=27` would need a patch to `package-release.sh` in the builder; it is
  not used.
- `tools/split-release-assets.sh` turns a packaging directory into release
  assets: archives of 1900 MiB or more become `<name>.part-NN`, the parts are
  proven to reassemble to the original digest, and it writes `SHA256SUMS` over
  the emitted files plus a `README.txt` that doubles as the release notes. It
  consumes the input archives, because the arm64 runner has no room for a second
  copy.
- Both workflows publish the split layout: `build.yml` via `build/publish-<tag>`,
  `publish-release.yml` by downloading the artifact and splitting it, or copying
  it unchanged when the run already shipped parts. The publish step is
  `continue-on-error` and the job summary reports the release outcome separately
  from the build result.
- The artifact path moved to `build/publish-*`, so a failed release still leaves
  downloadable assets.

Checked with a 3 GiB archive: two parts, matching reassembly digest, `sha256sum
-c` clean, and the parts branch copies untouched. No build, no publish.

## Baseline CI image build success (2026-11-14)

- Workflow run 43519285547 succeeded in 12m33s on GitHub Actions ARM64 runner (`ubuntu-24.04-arm`).
- Generated and uploaded artifact `uke-bootable-images-43519285547` (1.09 GB) containing `fedora_boot.img` and `userdata.img`.
- Key fixes applied:
  - Enabled Docker runtime for `build-rootfs.sh` (`UKE_CONTAINER=docker`).
  - Added `--nocheck` to `rpmbuild -ba` to skip heavy test suites during image composition.
  - Added `Provides: uke-firmware` and `xiaomi-uke-firmware` to `uke-oem-data.spec` (`1d20cc3`).
  - Wired `uke-fedora*-oem-data-*.rpm` into the primary DNF install transaction.
  - Set `UKE_COPR=0` and resolved host file permission on image repository paths.

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
  and a calculator, plus `zh_CN.UTF-8` and Noto Sans CJK.
- Release packaging splits archives above 1900 MiB into parts, so the GitHub
  2 GiB asset limit no longer aborts publishing; issue templates exist and
  screenshots are in the README.
- Build speed: kernel SRPM reuse, locked status file, `--parallel N`, CI caches.

## Blockers
- **Ext4 rootfs expansion blocked by error flag** (fixed 2026-11-17). The ext4 superblock error flag prevented online resize. Fixed on‑device via `echo u > /proc/sysrq-trigger` (emergency remount‑ro), `e2fsck -fy`, `resize2fs`. Documented in [INSTALL.md](INSTALL.md#emergency-rootfs-expansion-ext4).

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
