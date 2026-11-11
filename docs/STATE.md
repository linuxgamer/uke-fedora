# State

Updated: 2026-11-11. Verify with commands before relying on it; update this file
at the end of every session. History and decisions live in `private/NOTES.md`.

## Upstream and forks

Upstream: `MCC45TR/uke-linux`, branch `Fedora`, pin `5786c9c` (2026-11-06),
recorded in [`upstream.lock`](../upstream.lock). Model B: three rebased forks,
patches are exported for review only.

| Component | Branch | Head | State |
| --- | --- | --- | --- |
| `senemos-uke-kernel` | `main` | `80c0af3e` | video series active, kernel COPR prep failing |
| `uke-fedora-builder` | `main` | `d2c3393` | apps, ru locale, COPR repo, parallel build |
| `uke-linux-hardware-support` | `main` | `1fdc4af` | firmware payload, Python rule removed |

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
- **COPR token was pasted into chat.** Rotate it and replace `build/.copr`
  (gitignored, mode 600).
- OEM firmware and sensor blobs stay out of public repositories; see
  [COPR](COPR.md).

## Next action

Debug the kernel COPR `%prep` failure or run the first image build
(`UKE_VIDEO_OVERLAY=1 ./ukelinux.sh --profiles tty --cross-kernel --parallel 2
--output build/video11`). Both are in the backlog.
