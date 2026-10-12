# Uke Linux

This project is an experimental Linux port for the Xiaomi Pad 7, codename
**uke**. It is based on MCC45TR's work and now lives in owner forks.

**It is not a ready-to-use tablet distribution.** A Fedora console candidate
has been built and checked on the build machine. Its installation and boot on
the tablet have not been accepted yet. A working desktop is not promised.

## Start here

- [Hardware and current limits](HARDWARE.md)
- [What the candidate contains](uke-fedora-builder/docs/USERDATA-BOOT.md)
- [Owner installation and rollback](uke-fedora-builder/docs/USERDATA-INSTALL.md)
- [Software dependency policy](RUNTIME-POLICY.md)

Installation uses **userdata** and boot **A**. Formatting userdata destroys
Android data shared by both slots. Keeping B's firmware does not keep its
Android data. Do not flash anything before reading the installation guide.

## What each folder does

| Folder | Plain-language role |
| --- | --- |
| `senemos-uke-kernel` | Builds the Linux kernel and its device drivers. |
| `uke-fedora-builder` | Builds Fedora userspace and combines it with the kernel into installable candidates. Also chooses optional desktops. |
| `uke-linux-hardware-support` | Packages Linux-side device services and integration. It does not choose a desktop. |
| `private` | Local inputs, old-port archive, backups and test results. Not published. |

These three components are separate Git repositories joined by submodules.
Most work happens in a component repository; the root records which component
commits belong together. Recovery, Aloha and the old Images repository are no
longer active workspace modules; their sources and history are archived locally.

Existing TWRP is still used by the owner installer. Removing the recovery source
module does not remove the installation or rollback requirement. Image release
policy now lives in `uke-fedora-builder/configs/release-policy.json`.

## Get the sources

```sh
git clone --branch port/fedora-userdata --recurse-submodules https://github.com/linuxgamer/uke-linux.git
cd uke-linux
```

Already cloned the root without its components?

```sh
git submodule update --init --recursive
```

Do not use `git submodule update --remote` to recreate a tested candidate:
it can select different component versions.

## Build, install, or read the code?

- **Build the kernel:** [kernel guide](senemos-uke-kernel/docs/BUILDING.md).
- **Build Fedora:** [builder guide](uke-fedora-builder/docs/BUILDING.md).
- **Install the current candidate:** [owner guide](uke-fedora-builder/docs/USERDATA-INSTALL.md).
  There is no unattended installer or public binary release for it.
- **Understand the pieces:** use the table above and each component's README.

Building successfully is different from booting successfully. Older test
results do not prove that a new image works.

## Upstream and planned work

Upstream's [2026-10-12 hardware summary](https://github.com/MCC45TR/uke-linux/blob/bd1c311/README.md)
reports Wi-Fi/USB networking, firmware-framebuffer display and original Fedora
KDE with software rendering on its separately tested POCO Pad X1 profile.
Touch, accelerated graphics and audio remain unavailable there; DSP stability
and repeated-start acceptance remain open. Those observations concern an
upstream `linux`-partition/boot-B route, not acceptance of our userdata/boot-A
candidate. Our dependencies, storage plan and archived component boundaries
are unchanged.

Linux 7.2.9, the initial hardware patches and stock-ABL boot work come from
[MCC45TR/uke-linux](https://github.com/MCC45TR/uke-linux) and its components.
Our additions mainly cover Fedora builds, userdata installation, checks,
package ownership and repository layout.

The earlier independent 6.12 port is archived locally. Its changes have **not**
all been imported here. Planned work is: clearer documentation, a review of the
component boundaries, then selective transfer of useful 6.12 changes. Each
driver change will need its own comparison and tests.
