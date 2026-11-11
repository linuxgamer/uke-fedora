# Reporting a problem

The Fedora images are an **alpha release, not suitable for daily use**. Check the
[hardware status](../README.md#hardware-support) and
[existing issues](https://github.com/linuxgamer/uke-fedora/issues) before reporting a
problem. A listed limitation can still have useful new evidence.

Open a [bug report](https://github.com/linuxgamer/uke-fedora/issues/new)
for one problem at a time. Include:

- Device model, RAM/storage variant and stock firmware version, if known.
- Release tag, exact system and boot filenames, and their SHA-256 values. State
  whether files were changed or packages were updated after installation.
- Intended root partition label (`userdata` for the release images, `linux` for
  older development images) and selected boot slot. Write “unknown” if unsure;
  no partition changes are needed to report a bug.
- The smallest safe steps that show the problem, expected behavior, actual
  behavior and how often it happens. Do not repeat a crash or unsafe charging test
  just to collect evidence.
- Date/time of the failure, whether the clock was synchronized, and relevant
  hardware conditions: power source, attached accessories, display mode and
  whether touch input or SSH remained available.

The released images install the Fedora root on `userdata` and the boot image on
`boot_a`; see the [installation guide](../INSTALL.md). Tested hardware and known
limitations are in the [README](../README.md#hardware-support) and
[HARDWARE.md](HARDWARE.md). A successful build or checksum check does not
establish that an image boots, and a boot does not prove a hardware block. Report
what you observed, on which device, with the exact image and kernel.

## Useful evidence from a running Fedora session

These commands only read system information and write local text files. Run the
ones available in the session; missing commands or a locked-up device need not
prevent a report. On the computer holding the downloaded images, use `sha256sum`
on each file and compare the result with the release checksums.

On Fedora, collect the kernel and distribution versions:

```sh
uname -r
cat /etc/os-release
```

For a recent failure in the current boot, collect a short journal window and
kernel warnings:

```sh
journalctl -b --since '-5 min' --no-pager -o short-monotonic > journal-recent.txt
sudo dmesg --level=emerg,alert,crit,err,warn > kernel-warnings.txt
```

If `sudo` access is unavailable, include the journal output you can read. If the
device has already restarted, `journalctl -b -1` may contain the preceding boot;
share only a relevant, reviewed excerpt. A photo of the last visible error is
also useful when no shell is available. Do not send memory dumps or complete
partition contents.

**Review every attachment before uploading it.** Remove passwords, keys, tokens,
serial numbers, unit identifiers, MAC addresses, SSIDs, IP addresses, usernames,
hostnames, home-directory paths and calibration data. Crop personal information
out of photos. Keep error codes, driver names and relative timestamps intact;
replace private values with `[redacted]`. Public issues are not a place for raw
private logs. Do not publish exploit details in an issue: use GitHub's private
vulnerability reporting on this repository when available, otherwise open a
minimal issue asking for a private channel.

# Contributing code

The rules for every change are in [AGENTS.md](../AGENTS.md); the environment,
checks and git flow are in [DEVELOPING.md](DEVELOPING.md). In short:

- The umbrella repository owns documentation, tools, the upstream pin and the
  submodule pointers. The port code lives in the three component forks.
- Open documentation, tooling and pin changes against
  `linuxgamer/uke-fedora`. Open kernel, builder and hardware-support changes
  against the matching component repository, and move the umbrella gitlink only
  after the component change is accepted.
- Run the checks that cover the change and state the exact commands and results
  in the pull request. A build is not a boot test.
- Keep component commits out of the umbrella pull request, do not rewrite
  published tags or release assets, and do not flash or repartition a device as
  part of a code change.
- Never commit credentials, private logs, serial numbers, calibration or OEM
  firmware blobs. See [COPR.md](COPR.md) for the firmware policy.
- Use the [pull request template](../.github/PULL_REQUEST_TEMPLATE.md); it asks
  for the checks, the limitations and whether a device or gitlink is involved.

# Hardware integration policy

5 November 2026. Use original distribution KDE and GNOME packages. Uke
repositories and COPR projects must not carry project forks or project-rebuilt
variants of those packages. Resolve hardware support in Device Tree and the
kernel whenever practical. Keep other package forks and userspace adaptations
to the necessary minimum, with a documented reason when a kernel/DT solution
cannot address the requirement.

Research relevant OSS sources comprehensively before implementation. For
hardware support, compare the exact Uke OEM source, relevant same-SoC or
shared-IP implementations, current upstream and their active patch queues.
Use the pinned source inventory and donor review policy. Record exact revisions,
files, licenses, attribution,
compatibility limits and remaining gaps; a similar device or successful build
does not establish support on Uke.

Build device candidates through COPR and install or update them through DNF.
Keep compilation off the tablet and deliver packaged changes instead of copied
binaries. Keep device-specific calibration private, access EEPROM read-only and
avoid full-image backups or unnecessary large artifacts during bring-up.

# Package delivery and COPR housekeeping

Publish only necessary runtime, integration and essential build/test packages.
Retire completed temporary/test-only and superseded packages when they no
longer serve a source/build dependency, supported upgrade or recovery route.
Keep concise source and test evidence reproducible after cleanup. Coordinate
cleanup with active builds and the shared kernel delivery queue.

Deliver fixes as correctly versioned RPM updates through the supported
repository and channel. Other users must receive the change through the normal
`sudo dnf update` workflow. Verify dependency closure, upgrade behavior and
preservation of persistent preferences. Stable kernel promotion remains a
separate decision; automatic seamless staging and the selected local rollback
preference must survive package upgrades.

# Branch management

Keep remote branches to the necessary minimum. Reuse an appropriate existing
workstream branch, and use local worktrees to isolate unrelated work. Track
successive trials with commits and unique COPR releases. Create another remote
branch only when a distinct review or integration requires it.

Remove completed branches after preserving their integrated work and required
source references. Check active work, builds and shared integration dependencies
before cleanup; the cumulative kernel baseline and recovery route remain
required.

# Documentation style

Use this report style across Uke repositories, including README status sections,
hardware tables, release notes, issues, pull requests and commit summaries.

State the report date, tested device and software, observed result and remaining
work. Name the device directly. For example: "The USB port did not supply power
to the ESP32-S3."

Use professional, concise, natural English. Write for a reader who has not
followed the development conversation. Omit boilerplate, personal ownership
labels, conversational narration, promotional wording and internal review jargon.
A configured model name is not a hardware identity; record the tested commercial
model separately.

Keep README introductions and project status brief. Group hardware tables in
collapsible sections with Feature, Status and Notes columns, following the
[project README](../README.md#hardware-support). Keep detailed development history
in the changelog and engineering evidence in the private records.

Keep source review, build, package, VM and tablet results separate. Preserve
checksums, source attribution, failures and test limitations. Shortening a report
must not broaden a hardware claim. Keep lengthy trial histories and raw logs in
the private engineering records.

## Commit authorship

Code contributions retain their authors and verified `Co-authored-by` credit.
Preserve contributor attribution, source references and license notices when
squashing changes or editing commit messages. Maintenance workflows retain
their normal service-account identity.
