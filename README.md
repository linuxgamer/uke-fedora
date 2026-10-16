# uke-fedora

Fedora for Xiaomi Pad 7 and POCO Pad X1 (`uke`, Snapdragon 7+ Gen 3 / SM7675).
This port is **not suitable for daily use.** Boot reliability, display
artifacts, power management and several hardware functions remain unresolved.

The kernel, rootfs and boot image recipes target Fedora 44. Local builds and
package checks do not establish tablet compatibility.

## Status — 15 October 2026

The results below describe upstream's POCO Pad X1 development installation
running Fedora Rawhide and Linux 7.2.9 revision 1.39.

Linux 7.2.9 successfully boots from slot B. Wi-Fi and SSH work. Experimental Freedreno and Turnip graphics now work in KDE.
Touchscreen and multitouch work. Bluetooth, audio and USB host mode do not work yet.
Manual backlight control and power/volume buttons also work. The paired backlight now uses the OEM mapping, retains a visible minimum
while on, and reaches zero when blanked. Smooth adjustment still
needs testing. Battery readings are available.
Experimental sensor tests return acceleration, gyroscope and rear-light
readings, but automatic screen rotation and automatic brightness control are
not ready. Display scanout still uses simpledrm and the bootloader framebuffer. The native
DPU/DSI trial now registers a DRM connector and framebuffer, but the panel stays
black with DSI errors. Native refresh-rate
switching and adaptive sync do not work yet.

## Hardware support

🟢 Working means a successful
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

The hardware results above are reported by upstream; this fork has not repeated
the tablet tests.

## Project repositories

| Repository | Purpose |
|---|---|
| [Uke Fedora](https://github.com/linuxgamer/uke-fedora) | Workspace and project overview |
| [Kernel](uke-mainline-linux/README.md) | Kernel, device trees and Fedora RPMs |
| [Fedora root filesystem](uke-fedora-rootfs/README.md) | Image recipes and validation tools |
| [Hardware support](uke-hardware/README.md) | Device integration and platform packages |

## Differences from upstream

- Simplified build entry points and pinned component revisions.
- Fedora 44 kernel, hardware packages and image recipes. The kernel builder
  retains an explicit Rawhide option.
- Optional KDE and GNOME package selections; Plasma Mobile and Phosh are
  experimental. Their RPMs have been built for Fedora 44 AArch64; desktop
  sessions have not been tested on the tablet in this fork.
- Release names use `fedora-<version>-uke-r<N>`.

Image recipes now target the entire Android `userdata` partition by default;
`--root-partlabel linux` keeps the dedicated Linux partition option. Installing
to `userdata` destroys Android user data. The stock boot pair targets slot A;
Android slot B requires userdata restoration before rollback. Builders never
flash or change slots. See the [rootfs build guide](uke-fedora-rootfs/docs/BUILDING.md).

Source checks and package builds are recorded separately from image, VM and
tablet tests. No image from this fork has been validated on the device.

On 16 October 2026, Linux 7.2.9-1.39 built for Fedora 44 AArch64 in an x86_64
container: four binary RPMs and one SRPM. Image, DTB, all 1,144 modules and
package payload checks passed, as did installation, upgrade and removal in an
emulated AArch64 container. These unsigned development packages have not been
booted on the tablet. Local results are in
`uke-mainline-linux/artifacts/fedora-44/7.2.9/`.

The Fedora 44 Core filesystem build also passed package, initramfs, SELinux,
EXT4/FAT and UKI readback checks on 16 October. Its local outputs are in
`uke-fedora-rootfs/build/images/core-fedora-44-a7f9bb256b8a19b4/candidate/`.

The Fedora 44 stock-ABL boot pair also passed five generic ARM64 QEMU scenarios,
including enforcing SELinux, local USB-keyboard TTY input, root selection
and automatic EXT4 growth on userdata. Outputs are in
`uke-fedora-rootfs/build/boot-pair/pair-d92003ac3b71e7b3/`.
These VM checks do not validate tablet boot or peripherals.

## Development

Clone the workspace with its three submodules:

```sh
git clone --recurse-submodules https://github.com/linuxgamer/uke-fedora.git
cd uke-fedora
```

Use `build.sh` to select a build target:

```sh
./build.sh --help
./build.sh kernel --build 7.2.9 --offline --dry-run
./build.sh kernel --build 7.2.9 --release rawhide --offline --dry-run
./build.sh core --offline --dry-run
./build.sh boot-pair --help
```

`kernel` builds kernel RPMs; `core` builds the console root and UEFI images;
`boot-pair` builds the stock bootloader pair. `boot` is the older initramfs-only
debug image. `check-device --pair DIRECTORY` checks only local files and never
contacts the tablet. A normal build can install some host prerequisites;
dry-run and offline modes do not. See [kernel build guide](uke-mainline-linux/docs/BUILDING.md) and
[root filesystem image guide](uke-fedora-rootfs/docs/IMAGES.md) for required
inputs. In a standalone kernel checkout, run
`./build.sh --build 7.2.9 --offline --dry-run` from `uke-mainline-linux`.
From this workspace, use `./build.sh kernel` followed by the kernel options.
Running either entry without arguments displays its help.
