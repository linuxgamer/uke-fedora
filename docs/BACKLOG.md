# Backlog

Ordered work for the next sessions. One item per session unless it is a small
follow-up. Update the status in the same commit as the work; details go to the
private notes, facts to [STATE](STATE.md).

Status: `todo`, `in progress`, `blocked`, `done`.

| ID | Prio | Item | Status | Notes |
| --- | --- | --- | --- | --- |
| B1 | P0 | Fix the kernel COPR `%prep` failure | blocked | Builds `11307436`/`11307449`/`11307468` fail after the ELD test at `src/video/prepare-source.sh`. The series applies locally, so reproduce the native preparation with tracing (`bash -x`) in a clean tree. |
| B2 | P0 | Rotate the COPR API token | todo | Replace `build/.copr` (mode 600, gitignored); update no committed file and do not repeat the value in public. |
| B3 | P0 | First image build and tablet test | todo | `UKE_VIDEO_OVERLAY=1 ./ukelinux.sh --profiles tty --cross-kernel --parallel 2 --output build/video11`. Check `status.json`, flash TTY, `dmesg \| grep iris`, `/dev/video*`. Also validates the parallel option. |
| B4 | P1 | Run the image CI workflow | todo | [`build-image.yml`](../.github/workflows/build-image.yml) now has cache, `--parallel` and release packaging. Run it manually for `tty`; fix the workflow, not the builder, if it fails on setup. |
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
| B15 | P1 | Fix component `AGENTS.md` evidence paths | todo | Kernel and hardware `AGENTS.md` reference `referances/README.md`, `uke-linux-docs/docs/DONOR-POLICY.md`, `docs/research/ACCESSORY-LAB.md` and `docs/testing/ACCESSORY-TEST-PLAN.md`, none of which exist in this fork. Update the rules in the component repositories; use the substitutes in [DEVELOPING.md](DEVELOPING.md#missing-evidence-paths) meanwhile. |
| B16 | P1 | User-facing docs and release refresh | todo | Follow-up to the 2026-11-11 user audit: INSTALL needs extraction/TWRP/fastboot-entry/stock-ROM steps and Windows guidance, README must not promise unverified desktops, and the r1 release page must be brought in line with the local release notes. Keep this separate from the developer-docs pass. |

## Next

B2 is two minutes and unblocks COPR uploads. Then B1 or B3, both of which need
the tablet or a long build. Documentation and tooling items B12–B16 are
self-contained and suitable for a first contribution.
