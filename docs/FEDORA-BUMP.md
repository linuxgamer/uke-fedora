# Moving the port to another Fedora release

The port is pinned to one Fedora release at a time. A bump should be a small,
reviewed change, not a hunt through hardcoded strings. This page records the
plan and the ownership boundaries.

## Principle

- One machine-readable knob: `config/fedora-release`.
- Scripts and specs read the knob; they do not embed the number in names.
- Rawhide is removed from the supported build path and docs. Rawhide mentions
  in upstream-owned data, manifests and the old `boot-pair` development route
  stay where they are: deleting them only creates conflicts on the next sync.

## Current inventory

| Area | Hardcoded `44` | Rawhide mentions |
| --- | --- | --- |
| builder | ~170 | ~235 |
| hardware-support | ~80 | ~480 |
| kernel | ~16 | ~106 |
| root workspace | 7 | 0 |

Most rawhide hits are package-tracking data and the old development route, not
the Fedora image path.

## Steps for a bump (example: 44 → 45)

1. **Set the knob.** `config/fedora-release` holds the number; `ukelinux.sh`
   exports it as `FEDORA_RELEASE`. The builder scripts do not read it yet, so the
   next step is to replace their embedded `fedora44` names and tags with it.
2. **Rename the builder scripts.** `build-fedora44-images.sh`,
   `build-fedora44-rootfs.sh`, `build-fedora44-boot-a.sh` become
   `build-images.sh`, `build-rootfs.sh`, `build-boot-a.sh`; replace the embedded
   `fedora44` in tags, paths and messages with `fedora${FEDORA_RELEASE}`.
3. **Specs.** Replace `%if 0%{?fedora} == 44` blocks with a comparison against
   `%{fedora}` (for example `>= 45`) or drop the conditional entirely; package
   pins that name a release should use `%{fedora}` instead of a literal.
4. **Manifests.** `packaging/families/families.json`, source locks and
   `native-runtime.json` carry `fcNN` values and counts. Regenerate them with the
   project scripts; do not hand-edit lists.
5. **Docs.** State the release once, in `README.md` and `INSTALL.md`; do not
   repeat it in every paragraph.
6. **Rawhide.** Remove `--release rawhide` from the supported path and the
   mentions in our docs. Leave upstream's rawhide data, manifests and the
   `boot-pair` development route untouched.
7. **Verify.** Build TTY first, then KDE and GNOME. Check package availability
   before starting a full build; a missing package should fail fast.

## Risks

- Fedora bumps change package names, versions and Python policy; the native
  runtime catalog is the usual casualty.
- Kernel packaging depends on the release's toolchain and RPM macros.
- Source locks and checksums go stale; regenerate them instead of editing hashes.
- Do the bump as one dedicated branch, after the sync model is settled. Bumping
  in the middle of a rebase means doing the work twice.
