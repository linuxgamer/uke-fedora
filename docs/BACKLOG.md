# Backlog

Ordered work for the next sessions. One item per session unless it is a small
follow-up. Update the status in the same commit as the work; details go to the
private notes, facts to [STATE](STATE.md).

Status: `todo`, `in progress`, `blocked`, `done`.

| ID | Prio | Item | Status | Notes |
| --- | --- | --- | --- | --- |
| B1 | P0 | Fix the kernel COPR `%prep` failure | in progress | Root cause: `packaging/native/prepare.sh` called `src/video/prepare-source.sh` twice; the second call exited 1 silently at its re-entry guard after `patches/video/0012` created the header. Fixed in kernel `4ed80615` and guarded by `tests/native-prepare-steps-contract.sh`; the native preparation now passes locally. Upload the fixed SRPM and confirm a green COPR build after B2. |
| B2 | P0 | Rotate the COPR API token | todo | Replace `build/.copr` (mode 600, gitignored); update no committed file and do not repeat the value in public. |
| B3 | P0 | First image build and tablet test | todo | The local cheap stage now passes the kernel `%prep` (`UKE_BUILD_STAGE source_prepare elapsed_s=1090` after kernel `4ed80615`/`e942f625` and builder `9b83d79`). `UKE_VIDEO_OVERLAY=1 ./ukelinux.sh --profiles tty --cross-kernel --parallel 2 --output build/video11`, then check `status.json`, flash TTY, `dmesg \| grep iris`, `/dev/video*`. |
| B4 | P1 | Run the image CI workflow | todo | [`build-image.yml`](../.github/workflows/build-image.yml) now has cache, `--parallel` and release packaging. Run it manually for `tty`; fix the workflow, not the builder, if it fails on setup. The builder `cache_dir` bug (`9b83d79`) and the sanitizer `ASAN_OPTIONS` override (kernel `e942f625`) would have failed this workflow at stage 0 and in the kernel `%prep`; both are fixed. |
| B5 | P1 | Validate userland OTA through COPR | todo | Build an image with the repo, `dnf upgrade`, confirm kernel and OEM packages are excluded and the system still boots. |
| B6 | P1 | Host/device test automation | todo | `tools/check-dev-env.sh` covers the host preflight; still needed: one command that runs the cheap host checks and a short on-device checklist. Do not automate flashing. |
| B7 | P2 | Fedora 45 bump | todo | Follow [FEDORA-BUMP](FEDORA-BUMP.md); finish spec conditionals and version literals, regenerate pins. Component docs that still say Rawhide (kernel README/BUILDING) should be aligned in the same pass. |
| B8 | P2 | Triage the remaining issues | todo | #1 keyboard, #5 Bluetooth, #7 battery, #10 energy estimate, #11 video; #8 closed as a tablet fault. |
| B9 | P2 | Release polish | todo | Reopened: the published r1 page is still stale (not marked pre-release, old notes, broken inner `SHA256SUMS`, TWRP missing from the outer checksums), and the images were not repackaged with `tools/package-release.sh`. Details in the 2026-11-11 user audit; track the fix here. |
| B10 | P2 | Kernel update without flashing | todo | COPR can carry the kernel, but the boot payload must match. Design the boot bundle flow before publishing a kernel. |
| B11 | P1 | Developer docs and published agent rules | done | Published `AGENTS.md`, added [DEVELOPING.md](DEVELOPING.md), `tools/check-dev-env.sh`, `tools/check-docs.sh`, PR template, fixed CONTRIBUTING/UPSTREAM/README links. |
| B12 | P1 | Builder local check parity | todo | `uke-fedora-builder` has 76 contract tests and CI runs `shellcheck` plus the full suite, but the umbrella documents only `bash -n` and there is no local runner. Add `make check`/`tests/README.md` in the builder repo and link it from AGENTS/DEVELOPING. |
| B13 | P1 | Kernel check prerequisites | todo | `make -C senemos-uke-kernel validate` fails silently on a host without `rpm`/`rpmspec`, `dtc` and `clang`. `tools/check-dev-env.sh` now reports the missing tools; still add a preflight target in the kernel repo and per-test names in the `validate` recipe. |
| B14 | P1 | Umbrella docs and link CI | todo | The umbrella has no pull-request CI. Add a small workflow that runs `tools/check-docs.sh` (and markdown lint if cheap) on pull requests, as a model for docs-only contributions. |
| B15 | P1 | Fix component `AGENTS.md` evidence paths | done | Updated all three component `AGENTS.md`: removed the references to dropped `referances/` and `uke-linux-docs/` trees, retired the OrangeFox and missing ACCESSORY paths, added the real checks and the umbrella gitlink flow. Component commits: kernel `0a0a2631`, builder `0a48226`, hardware `88ffc06`; substitutes remain documented in [DEVELOPING.md](DEVELOPING.md#missing-evidence-paths). |
| B16 | P1 | User-facing docs and release refresh | todo | Follow-up to the 2026-11-11 user audit. INSTALL needs: `.tar.zst` extraction, TWRP source and format (`.tar.zst` vs `.img`), fastboot/recovery key combinations, Developer-options steps, stock-ROM/MiFlash links, Windows/platform-tools guidance, checksum verification, hex partition sizes, first-boot expectations and update guidance. README must not promise desktops the release does not carry and should name the exact supported models. Keep this separate from the developer-docs pass. |
| B17 | P2 | Newcomer labels and first tasks | todo | Add `good first issue` and `help wanted` labels and label 3–5 self-contained tasks (docs CI, builder check runner, component `AGENTS.md` paths, tooling nits), then link them from [DEVELOPING.md](DEVELOPING.md#where-to-start). |
| B18 | P2 | Security reporting channel | todo | `docs/CONTRIBUTING.md` points at GitHub private vulnerability reporting "when available". Enable it for the repository or add a `SECURITY.md` with a real private channel; the upstream `SECURITY.md` is not carried. |
| B19 | P3 | Small tooling nits | todo | `tools/export-patches.sh --help` prints `mkdir` usage; root `.gitignore` still ignores `/tests`, `/scripts`, `/manifests`, a trap for repo-level tooling; consider installation hints in `tools/check-dev-env.sh` for the Fedora-era toolchain. |

## Next

B2 is two minutes and unblocks the COPR rebuild of the fixed kernel (B1). B3 and
B4 then need a long build; the tablet test needs the device. Documentation and
tooling items B12–B19 are self-contained and suitable for a first contribution.
| B20 | P2 | Clean up October documentation | done | Removed 26 kernel, 3 builder and 18 hardware-support documents created in October 2026 or earlier that were not README/AGENTS/BUILDING/SECURITY, not maintained in November, and not referenced by code, manifests, the umbrella or a kept document. Component commits: kernel `8d968d14`, builder `facd4e1`, hardware `8d95e01`; recovery is git history. |
| B21 | P2 | Guard the removed trees | done | Removed the kernel `referances/` SRPM/OEM cache (moved to the ignored `source-cache/releases/`), the kernel and builder `reports/`, and the hardware-support top-level `docs/`; added `tools/check-forbidden-paths.sh` and documented the policy in [UPSTREAM.md](UPSTREAM.md#deletion-policy) and [DEVELOPING.md](DEVELOPING.md#tree-policy). Component commits: kernel `2d6ed7b8`/`96ee63a6`/`57d7fbb3`, builder `e9d0cca`, hardware `604b443`/`bd04ec9`; the manifests keep URLs and commits but no removed local paths. |
