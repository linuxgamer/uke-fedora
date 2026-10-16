# Uke Linux

Linux for Xiaomi Pad 7 and POCO Pad X1 (`uke`, Snapdragon 7+ Gen 3 / SM7675).
This page records the Fedora Rawhide development state on 15 October 2026.
Fedora 44 is the planned next base and has not been built or tested here.

## Earlier Fedora Rawhide Alpha 1 release

**Experimental alpha — not suitable for daily use.** Boot reliability, display
artifacts, power management and several hardware functions remain unresolved.

[Release files and checksums](https://github.com/MCC45TR/uke-linux/releases/tag/fedora-rawhide-alpha-1):

| File | Purpose |
|---|---|
| `fedora-rawhide-uke-system-alpha-1.img` | Fedora Rawhide root filesystem |
| `fedora-linux-uke-senemos-729-boot-lp.img` | Boot image targeting `PARTLABEL=linux` |
| `fedora-linux-uke-senemos-729-kernel-up.img` | Experimental boot image targeting `PARTLABEL=userdata`; not tested on the tablet |

The software baseline is Linux 7.2.9 revision 1.39. Both public boot
variants and the exported root filesystem are rebuilt and have not been booted
on the tablet. The hardware results below refer to the separate development
installation. Installation instructions will follow.

OEM firmware and device calibration files are not distributed. The public image
does not include their provisioning workflow, so hardware that requires those
files cannot be assumed to work. The status table describes the separately
provisioned development system. Using `userdata` for Fedora replaces Android
user data; this variant is not an Android data-preserving dual-boot route.

## Status — 15 October 2026

Linux 7.2.9 revision 1.39 boots from slot B to a local console and the original
Fedora KDE desktop. Wi-Fi, SSH and
signed DNF updates work. Experimental Freedreno graphics now work in KDE,
Xwayland/OpenGL and a Turnip Vulkan test at 255 MHz. Finger input and ten
simultaneous touch contacts worked in the 14 October tablet test. Bluetooth,
audio and USB host mode do not work yet.

Manual backlight control and power/volume buttons also worked in the 14 October
test. The paired backlight now uses the OEM mapping, retains a visible minimum
while on, and reaches zero when blanked. Smooth full-range adjustment still
needs testing. Battery readings are available.
Experimental sensor tests return acceleration, gyroscope and rear-light
readings, but automatic screen rotation and automatic brightness control are
not ready.

Revision **1.39** starts Adreno rendering and touch input automatically from the
installed Fedora root. Touch registered on the first attempt at about seven
seconds in the measured boot. Earlier RAM trials remain separate evidence.
Repeated cold boots, full GPU workloads, thermal limits and suspend still need
testing. Android slot A and the working Linux rollback are retained.
This was the tested slot layout. The planned layout is Linux in slot A and
Android rollback in slot B, subject to device verification.

Display scanout still uses simpledrm and the bootloader framebuffer. The native
DPU/DSI trial now registers a DRM connector and framebuffer, but the panel stays
black with DSI errors. It is kept outside the normal build. Native refresh-rate
switching and adaptive sync do not work yet. Linux 7.2.10 remains a separate
candidate; the working tablet baseline is 7.2.9.

On 15 October, [COPR build 11125451](https://copr.fedorainfracloud.org/coprs/mcc45tr/uke-linux-test/build/11125451/)
produced signed 7.2.9-1.39 Rawhide AArch64 RPMs and a signed SRPM. Downloaded
packages passed signature, architecture and payload checks. This COPR build
has not yet been installed and tested on the tablet.

This repository contains the project overview and workspace. Sources are in the
[component repositories](#project-repositories); detailed test records are private.

## Hardware support

These results are from the separately provisioned **POCO Pad X1 (8 GB / 512 GB)**
development installation: Fedora Rawhide AArch64, Linux 7.2.9 revision 1.39,
stock Android bootloader, tested through **15 October 2026**. The Linux model
label is configured as Xiaomi Pad 7. Other variants, the public Alpha 1 images,
and Fedora 44 have not been tested on the tablet. 🟢 Working means a successful
tablet test; 🟡 Partial means limited or experimental use; 🔴 Broken means no
working function in this build; ⚪ Untested means no functional test.

| Feature | Status | Notes |
|---|---|---|
| Boot to Fedora KDE | 🟡 Partial | Boots from the tested slot-B installation; repeated cold boots and recovery are unverified. |
| CPU and internal storage | 🟢 Working | Eight CPU cores online; Fedora root reads and writes on UFS. |
| Screen and backlight | 🟡 Partial | Firmware framebuffer displays KDE; manual brightness and one screen-off/on cycle worked. Native panel control and refresh switching do not work. |
| 3D graphics | 🟡 Partial | Experimental Adreno rendering works in KDE, OpenGL and a short Vulkan test; stability under sustained load is unknown. |
| Touchscreen | 🟢 Working | Finger input and ten simultaneous contacts tested on 14 October. |
| Stylus | 🔴 Broken | No pen input, pressure or tilt. |
| Power and volume buttons | 🟢 Working | Input tested on 14 October. |
| Pogo keyboard and touchpad | ⚪ Untested | No attachment or input test. |
| Wi-Fi | 🟢 Working | Connection, SSH, DNS and a 16 MiB transfer tested. |
| Bluetooth | 🔴 Broken | No controller available for scanning or pairing. |
| USB device mode | 🟡 Partial | Serial shell works; USB networking worked in earlier manual tests and is off by default. Reconnect reliability is unverified. |
| USB host / keyboard / mouse | 🔴 Broken | No accessory power; a mouse dongle was not detected. |
| USB-C video output | ⚪ Untested | No successful external-display test. |
| Speakers and microphones | 🔴 Broken | No usable playback or recording route. |
| Cameras | ⚪ Untested | No verified front or rear camera capture. |
| Hardware video codecs | ⚪ Untested | No verified decode or encode workload. |
| Motion sensors | 🟡 Partial | Accelerometer and gyroscope samples worked in experimental RAM boots; automatic rotation does not work. |
| Ambient light / automatic brightness | 🟡 Partial | Experimental rear-light readings exist; front-light readings and automatic brightness do not work. |
| Compass and proximity | 🔴 Broken | No usable readings or events. |
| Battery level | 🟡 Partial | Percentage, voltage and temperature reach the desktop; accuracy across battery states is unverified. |
| Charging | 🟡 Partial | USB power is detected, but the running tablet discharged during a short computer-USB trial. Sustained net charging and fast charging are unverified. |
| Suspend and wake | ⚪ Untested | System sleep is disabled; screen blanking alone is not suspend. |
| Thermal protection | ⚪ Untested | Sensor readings exist, but throttling and protective shutdown have not been verified. |

These statuses describe the dated development installation, not a validated
release image. Reading a sensor or seeing a charging indicator does not establish
working automatic control or net charging.

## Project repositories

| Repository | Purpose |
|---|---|
| [Uke Fedora](https://github.com/linuxgamer/uke-fedora) | Workspace and project overview |
| [Kernel](uke-mainline-linux/README.md) | Kernel, device trees and Fedora RPMs |
| [Fedora root filesystem](uke-fedora-rootfs/README.md) | Image recipes and validation tools |
| [Hardware support](uke-hardware/README.md) | Device integration and platform packages |

## Build and test scope

Earlier Core and KDE image candidates passed host and VM checks, but their exact
root filesystems have not been booted on this tablet. Tablet results above come
from a separate development installation. DNF does not flash Android partitions
or select a boot slot.

KDE applications come from Fedora; no Uke clones or rebuilds are used. Python
is allowed in project tools and Fedora packages, including target payloads.
No image has been rebuilt or tested under the revised package and payload rules.

## Release names

Future release tags use `fedora-<version>-uke-r<N>`, for example
`fedora-44-uke-r1`. Use `rawhide` in place of a numbered Fedora version
for a Rawhide build. The Uke release number starts at 1 for each Fedora version
and increases for each published release. Release notes state whether the result
is an alpha and which device tests, if any, passed. Kernel RPM versions such as
`1.39` remain package versions, not names for a complete image release.

Published images start with the same tag and end in `-stock-boot.img` and
`-stock-system.img` for a stock bootloader pair, or `-uefi-root.img.zst` and
`-uefi-esp.img.zst` for a UEFI pair. Publish checksums for those exact filenames.
Run `./stage-release.sh VERSION NUMBER stock|uefi CANDIDATE_DIRECTORY` to put
one checked image pair in `artifacts/releases/<tag>/`. For example, a current
Rawhide stock pair uses `VERSION=rawhide` and the directory produced by the
`boot-pair` recipe. The script verifies the candidate checksums and Fedora
version, copies both images, and writes checksums for their release filenames.
It only stages local candidates; release notes and device qualification remain
separate. Build recipes keep their internal filenames. The earlier Alpha 1
downloads above retain their original names.

## Development

Clone the workspace with its three submodules:

```sh
git clone --recurse-submodules https://github.com/linuxgamer/uke-fedora.git
cd uke-fedora
```

Use `build.sh` from this workspace to select a build target:

```sh
./build.sh --help
./build.sh kernel --build 7.2.9 --offline --dry-run
./build.sh core --offline --dry-run
./build.sh boot-pair --help
```

`kernel` builds kernel RPMs; `core` builds the console root and UEFI/ESP images;
`boot-pair` builds the stock bootloader pair. `boot` is the older initramfs-only
debug recipe. `check-device --offline --pair DIRECTORY` checks a built pair's
local files. The entry requires Bash. All image recipes still target Rawhide.
A normal build can install
host prerequisites; dry-run and offline modes do not. See the
[kernel build guide](uke-mainline-linux/docs/BUILDING.md) and
[root filesystem image guide](uke-fedora-rootfs/docs/IMAGES.md) for required
inputs and validation limits. From a standalone kernel checkout, use
`./build.sh --build 7.2.9 --offline --dry-run`; from this workspace, use
`./build.sh kernel` followed by the kernel options. Running either entry without
arguments displays its help.

This is an independent community project. It is not an official Fedora, Xiaomi,
POCO or Qualcomm product. Original files use MIT; components retain their own licenses.
