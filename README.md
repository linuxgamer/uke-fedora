# uke-fedora

Fedora 44 for Xiaomi Pad 7 and POCO Pad X1 (`uke`, Snapdragon 7+ Gen 3 / SM7675).
This port is **not suitable for daily use.** Boot reliability, display
artifacts, power management and some hardware may not work.

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

- Simplified build.
- Fedora 44 kernel, hardware packages and image recipes.
- Optional KDE and GNOME package selections. Plasma Mobile and Phosh are experimental.
- Installs into /userdata by default

## Installing a stock bootloader image

Each Fedora 44 release has `tty/`, `kde/` and `gnome/`
directories. Choose only **one** directory.

Installation erases the entire Android `userdata` partition. Keep a data
backup, the original `boot_a` image and matching OEM firmware. Slot B boot
images remain available, but returning to Android requires restoring
`userdata`; switching slots alone is insufficient.

From the chosen variant directory, verify its files:

```sh
sha256sum -c SHA256SUMS
```

On the unlocked `uke` device, enter **bootloader fastboot** (NOT
fastbootD). Check its identity, state and partition sizes before any
write:

```sh
fastboot getvar product
fastboot getvar unlocked
fastboot getvar is-userspace
fastboot getvar current-slot
fastboot getvar partition-size:boot_a
fastboot getvar partition-size:userdata
```

Proceed only if the device is `uke`, unlocked, in bootloader fastboot, and
`boot_a` is at least 96 MiB while `userdata` is at least 3 GiB for TTY or
8 GiB for KDE/GNOME. From that same
variant directory, set `prefix` to the prefix of its two image files (the
example below is for release r4, TTY). Check that each command reports success
before running the next:

```sh
prefix=fedora-44-uke-r4-tty
fastboot flash userdata "${prefix}-stock-system.img"
fastboot flash boot_a "${prefix}-stock-boot.img"
fastboot set_active a
fastboot reboot
```

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
contacts the tablet. A normal build can install some host prerequisites,
dry-run and offline modes dont do that. See [kernel build guide](uke-mainline-linux/docs/BUILDING.md) and
[root filesystem image guide](uke-fedora-rootfs/docs/IMAGES.md) for required
inputs. In a standalone kernel checkout, run
`./build.sh --build 7.2.9 --offline --dry-run` from `uke-mainline-linux`.
From this workspace, use `./build.sh kernel` followed by the kernel options.
Running either entry without arguments displays its help.
