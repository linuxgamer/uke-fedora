# Backlog

Ordered work for the next sessions. One item per session unless it is a small
follow-up. Update the status in the same commit as the work; details go to
`private/NOTES.md`, facts to [STATE](STATE.md).

Status: `todo`, `in progress`, `blocked`, `done`.

| ID | Prio | Item | Status | Notes |
| --- | --- | --- | --- | --- |
| B1 | P0 | Fix the kernel COPR `%prep` failure | blocked | Builds `11307436`/`11307449`/`11307468` fail after the ELD test at `src/video/prepare-source.sh`. The series applies locally, so reproduce the native preparation with tracing (`bash -x`) in a clean tree. |
| B2 | P0 | Rotate the COPR API token | todo | Token was pasted into chat. Replace `build/.copr` (mode 600, gitignored); update no committed file. |
| B3 | P0 | First image build and tablet test | todo | `UKE_VIDEO_OVERLAY=1 ./ukelinux.sh --profiles tty --cross-kernel --parallel 2 --output build/video11`. Check `status.json`, flash TTY, `dmesg \| grep iris`, `/dev/video*`. Also validates the parallel option. |
| B4 | P1 | Run the image CI workflow | todo | [`build-image.yml`](../.github/workflows/build-image.yml) now has cache, `--parallel` and release packaging. Run it manually for `tty`; fix the workflow, not the builder, if it fails on setup. |
| B5 | P1 | Validate userland OTA through COPR | todo | Build an image with the repo, `dnf upgrade`, confirm kernel and OEM packages are excluded and the system still boots. |
| B6 | P1 | Host/device test automation | todo | One script for the cheap host checks and a short on-device checklist; do not automate flashing. |
| B7 | P2 | Fedora 45 bump | todo | Follow [FEDORA-BUMP](FEDORA-BUMP.md); finish spec conditionals and version literals, regenerate pins. |
| B8 | P2 | Triage the remaining issues | todo | #1 keyboard, #5 Bluetooth, #7 battery, #10 energy estimate, #11 video; #8 closed as a tablet fault. |
| B9 | P2 | Release polish | done | Packager, pre-release flag, return-to-Android, screenshots and issue templates are in place. |
| B10 | P2 | Kernel update without flashing | todo | COPR can carry the kernel, but the boot payload must match. Design the boot bundle flow before publishing a kernel. |

## Next

Take B1 or B3. Both need the tablet or a long build; B2 is a two-minute task and
should be done before the next COPR upload.
