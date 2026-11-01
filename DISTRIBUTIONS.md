# Distribution roadmap and consolidated development history

**Recorded: 1 November 2026.** This file describes project organization, not a
new hardware qualification or release.

## Distribution editions

| Edition | Status | Development branch |
| --- | --- | --- |
| Fedora Rawhide (AArch64) | Active community port; experimental alpha | `Fedora` |
| Ubuntu (AArch64) | Planned; no qualified image, installer or device result | Not created |
| Arch Linux (AArch64) | Planned; no qualified image, installer or device result | Not created |

Keep **one active branch, `Fedora`, for now**. Only establish dedicated
`Ubuntu` and `ArchLinux` branches when there is real distribution-specific
source to maintain; do not create empty placeholder branches.

The kernel, device trees, firmware boundary, hardware-support components and
platform-level boot experiments may be reused between editions, subject to
licensing and compatibility. Each edition must independently define its
userspace, package manager, image/build integration, initramfs, upgrade path,
recovery strategy, and installation/test evidence. A Fedora working status
does not imply an Ubuntu or Arch Linux working status.

## Historical branches incorporated into Git ancestry

These branches were consolidated with a **history-preserving merge that keeps
the reviewed Fedora file tree**. Both experiment heads are merge parents.
Changes in these older snapshots remain accessible through their commit
histories; their older component pins were **not** substituted for the
currently reviewed Fedora pins.

| Former branch | Head commit | Preserved work and limits |
| --- | --- | --- |
| `TEST` | `7dda75304c3d51eeea61a12ceca89995cdfc7a8f` | Historical cohort validation and hardware XML prerequisites, with older builder/hardware submodule pins. Retained for reference; not promoted to the active Fedora source snapshot. |
| `work/kvm73-el2-20261025` | `568dd75a780d328f75f1f0e45e645ea7b39b2e29` | Linux 7.3 KVM/EL2 preparation and host-side AArch64 package evidence. No verified firmware-to-EL2 handoff, tablet KVM guest, or installed-device acceptance. |
| `release/release-readiness-main-20261101` | `d8ec6e1af0ca51d2e5e5d9179b5a111a4a3381e2` | Already merged into the Fedora baseline through [PR #13](https://github.com/MCC45TR/uke-linux/pull/13). No repeat merge required. |

### Reproducible historical submodule references

| Component | Active Fedora baseline before consolidation | TEST snapshot | KVM snapshot |
| --- | --- | --- | --- |
| Kernel | `c9335a8fdd20a7ee2a33ce203fb5c0e85a2fddb3` | `3e677de9de2042a3cec97f0c606197bdab246235` | `70cdf4702331897820df5e66f82422b705c18ec0` |
| Fedora image builder | `ebaa570a69cb33592ce399f0265496c41e44bfe9` | `644acfbd98d1339871bbb4ae0847f7837fdec09d` | `50429cf487c63903c605e54454939b2d24ed8e81` |
| Hardware support | `c1b022880d8ff8a48fed830a43a05ab047aeae65` | `009730cf848b3733ae3ce0c6dcb4940ad539d02f` | `aa332160c2d2a6d455383d0a7942db88e42af4c6` |

The **active** pins can advance later through the normal reviewed workspace
refresh process. This table only records what was present at consolidation.

Review an experiment without recreating a public development branch:

```sh
git show --stat 7dda75304c3d51eeea61a12ceca89995cdfc7a8f
git show --stat 568dd75a780d328f75f1f0e45e645ea7b39b2e29
git show 568dd75a780d328f75f1f0e45e645ea7b39b2e29:README.md
```

## EL2 / KVM follow-up

The current Fedora device observations were made at **EL1**. The historical
KVM preparation documented host-side packaging and an `el2-require` profile
that requires EL2 to have been entered already; it does not make firmware
release EL2 to Linux. Before enabling KVM as a supported feature, separately
establish boot-stage ownership, all-CPU EL2 entry, hypervisor initialization,
a guest launch, suspend/resume and recovery behaviour, and device test evidence.

Do not enable unverified EL2/KVM profiles or re-pin the active kernel solely
because these histories were consolidated.

## Branch operations and integrations

GitHub Actions image composition and component refresh now target `Fedora`
in this edition. The component repositories intentionally continue to track
their own `main` branches (OrangeFox tracks `R12.0`); **their default
branches are independent of this parent repository**.

After selecting `Fedora` as this repository's GitHub default branch, retire
`main`, `TEST`, `work/kvm73-el2-20261025` and
`release/release-readiness-main-20261101` from the remote branch list.
Their commit histories remain reachable from `Fedora` because they were
either merged previously or incorporated as additional merge parents.
Verify external scripts, links and consumers before deleting the old default.
