# Uke Fedora

[![Build images](https://github.com/linuxgamer/uke-fedora/actions/workflows/build-image.yml/badge.svg)](https://github.com/linuxgamer/uke-fedora/actions/workflows/build-image.yml)

Fedora Linux port made for **Xiaomi Pad 7** and **POCO Pad X1**, based on [MCC45TR's port](https://github.com/MCC45TR/uke-linux).

This port is **work in progress**. Differences are: Fedora 44, `/userdata` install, more DEs, build optimisations, polishing and extra QoL stuff.

> [!WARNING]
> This is not ready for daily use. Installing to `userdata` overwrites Android user data. Back up any data you have!

## Start here

- **Installing the port:** read the [installation guide](docs/INSTALL.md) and the
  [releases](https://github.com/linuxgamer/uke-fedora/releases).
- **Developing the port:** read [docs/DEVELOPING.md](docs/DEVELOPING.md) for the
  environment, checks and contribution flow, then [AGENTS.md](AGENTS.md) for the
  rules. Current facts are in [docs/STATE.md](docs/STATE.md), ordered work in
  [docs/BACKLOG.md](docs/BACKLOG.md).

## Hardware support

| Component | Status | Notes |
| --- | --- | --- |
| Fedora KDE desktop | 🟢 Working | Boots into KDE; basic use and touch-only setup tested. |
| GNOME desktop | 🟢 Working | The GNOME image boots and works. |
| Other desktops | ⚪ Not verified | TTY, Phosh and Plasma Mobile still need tablet testing. |
| TTY touch keyboard | ⚪ Not verified | An experimental framebuffer keyboard is included in TTY images; it has not been tested on the tablet. |
| Display | 🟡 Partial | Native TM display works; a brief grey screen appears during boot. CSOT is untested on this port. |
| Refresh rate |  🟢 Working  | Manual Refresh rate switching works and is reliable, (KDE verified), VRR is disabled. |
| Touchscreen |  🟢 Working | Works,10 Point MultiTouch is working. |
| Graphics (GPU) | 🟡 Working, needs more testing | OpenGL works (~10K Glmark2), Vulkan is experimental (~7K Vkmark). |
| CPU and storage | 🟢 Working | All CPU cores are available, internal storage works. |
| Wi-Fi | 🟢 Working | Connects to networks and supports normal data transfers. |
| Bluetooth |  🟢 Working  | Bluetooth devices work, Tested Keyboard, Mouse and headphones. |
| Auto-rotation | 🟢 Working | Screen and touch orientation follow tablet rotation. |
| Other sensors | 🟡 Partial | Motion, compass, proximity not verified but cover detection works.|
| USB-C accessories | 🟡 Partial | An OTG mouse works through a USB-A-to-USB-C adapter; manual USB ACM on/off works. Other accessories need testing. |
| External display | ⚪ Not verified | Video output over USB-C/HDMI/DP has not been tested. |
| Charging | 🟡 Partial | Charging and battery percentage are detected, fast charging, charge limits and bypass may not work. |
| Sleep and wake | 🟡 Partial | Basic suspend exists, but wake is unreliable. |
| Reboot and shutdown |  🟢 Working  | Reboot works, shutdown can hang or restart the tablet. |
| Built-in speakers | 🟢 Working | All four amplifiers play. ACP rejects a UCM profile when any mapping fails to open, and the speaker verb carried a DisplayPort device on `hw:0,0` that this kernel does not open - that discarded the whole HiFi profile and left the desktop with a dummy output. Without that device the profile is accepted and the UCM sequence enables the amplifiers itself. |
| Built-in microphones | 🟢 Working | The four-channel array records; the UCM routes it through the same HiFi profile that carries playback. |
| Cameras | 🔴 Not working | Neither camera has a verified working capture. |
| Stylus | 🔴 Not working | Pen input, pressure and tilt are unavailable. |
| Magnetic keyboard | 🟡 Partial | Keys work for about a minute, then the MCU stops scanning them. It asks for an MiAuth token on a timer of its own and gives up when the window closes; the token comes from the Android devauth TA over RPMB and Linux has no way to produce one, so the answer is not to fake it - a zero-token reply is worse than none. The workaround cycles the I2C driver, which re-arms the window in about a second and costs the keys typed during it; a userspace helper does that once the keyboard has been idle past the window. A reset pulse that skips the regulators arms the window in roughly 70 ms and the driver downloads the MCU firmware again after it, so the helper tries the pulse first and falls back to the driver cycle when the pulse or the reload fails; two pulse periods in a row without a key event force a cycle. Each reset costs the MCU its Caps Lock state, and a reset that lands mid-typing loses those keystrokes. |

🟢 Working · 🟡 Partial · 🔴 Not working · ⚪ Not verified

Developer-level evidence and blockers: [docs/HARDWARE.md](docs/HARDWARE.md).

## Screenshots

| KDE Plasma | GPU and Vulkan |
| --- | --- |
| ![KDE Plasma on the tablet](.github/assets/screenshots/uke-fedora-kde-2026-10-17.png) | ![Chromium GPU status](.github/assets/screenshots/Fedora_Rawhide_PAD7_UKE_Chromium_GPU_Status.png) |

Screenshots are from upstream and will be replaced; they are not evidence that every block works in the current release.

## Downloads and building

Go to [releases](https://github.com/linuxgamer/uke-fedora/releases) and download the KDE or GNOME image. Then look at the [installation guide](docs/INSTALL.md).

To build separate Fedora 44 images on an x86_64 PC, use
`./uke-fedora-builder/build-images.sh --cross-kernel --output build/<DESIRED FOLDER>`.
By default all desktop variants are built, add `--profiles <ANY DE YOU WANT>,<DE 2>` to select DEs.
`--cross-kernel` speeds up the kernel compilation by running Clang natively
on the x86 PC, other packages and rootfs still use AArch64 containers. On an ARM64
host, omit the flag. Host requirements and the first-hour setup are in
[docs/DEVELOPING.md](docs/DEVELOPING.md); see the
[build guide](https://github.com/linuxgamer/uke-fedora-builder/blob/main/docs/BUILDING.md) and the
[cache guide](https://github.com/linuxgamer/uke-fedora-builder/blob/main/docs/BUILD-CACHE.md)
for cache, resume and rebuild options.

Package updates can be published to COPR; see [docs/COPR.md](docs/COPR.md).

## Source

This repository brings together the following components as submodules:

| Component | Repository |
| --- | --- |
| Kernel and device trees | [senemos-uke-kernel-mainline](https://github.com/linuxgamer/senemos-uke-kernel-mainline) |
| Hardware support and packages | [uke-linux-hardware-support](https://github.com/linuxgamer/uke-linux-hardware-support) |
| Fedora image builder | [uke-fedora-builder](https://github.com/linuxgamer/uke-fedora-builder) |

To clone with the submodules:

```sh
git clone --recurse-submodules https://github.com/linuxgamer/uke-fedora.git
```
