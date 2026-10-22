# Uke Fedora

Fedora Linux for the Xiaomi Pad 7 (`uke`), based on [MCC45TR's port](https://github.com/MCC45TR/uke-linux).

This port is **work in progress**. Work is focused on Fedora 44, stock Android bootloader and `/userdata` install.

> [!WARNING]
> This is not ready for daily use. There is no tested Xiaomi Pad 7 release image from the current source. Installing to `userdata` overwrites Android user data. Back up your data and make sure you can restore the original boot images before experimenting.

Most of the hardware work linked below comes from **MCC45TR's separate POCO Pad X1 deve

### Hardware support (upstream POCO Pad X1 only)

These results come from the upstream Fedora Rawhide development setup on a **POCO Pad X1**, not from a tested Xiaomi Pad 7 image. “Partial” means the feature works with limitations or still needs testing.

| Component | Status | Notes |
| --- | --- | --- |
| Fedora KDE desktop | 🟡 Partial | Boots into KDE and runs applications, but some desktop issues remain. |
| Display | 🟢 Working | Native 3200 × 2136 resolution and adjustable brightness. |
| Refresh rate | 🟡 Partial | Fixed 30–144 Hz modes work; adaptive refresh (VRR) is disabled. |
| Touchscreen | 🟡 Partial | Works for normal use; multitouch reliability still needs work. |
| Graphics (GPU) | 🟡 Partial | Desktop OpenGL works; Vulkan and some graphics features remain experimental. |
| CPU and storage | 🟢 Working | All CPU cores are available, and internal storage works. |
| Wi-Fi | 🟢 Working | Connects to networks and supports normal data transfers. |
| Bluetooth | 🟢 Working | Tested with a mouse and wireless headphones, including audio playback. |
| Auto-rotation | 🟢 Working | Screen and touch orientation follow tablet rotation. |
| Automatic brightness | 🟢 Working | Brightness responds to ambient light. |
| Other sensors | 🟡 Partial | Motion, compass, proximity and cover detection have varying levels of support. |
| USB-C accessories | 🟡 Partial | A powered hub and mouse work, other accessories need more testing. |
| External display | ⚪ Not verified | Video output over USB-C/HDMI has not been tested. |
| Charging | 🟡 Partial | Charging and battery percentage are detected; fast charging, charge limits and bypass are not fully verified. |
| Sleep and wake | 🟡 Partial | Basic suspend testing exists, but reliable wake and power savings are unconfirmed. |
| Reboot and shutdown | 🟡 Partial | Reboot has works, shutdown can hang or restart the tablet. |
| Built-in speakers and microphones | 🔴 Not working | No functional playback or recording yet. |
| Cameras | ⚪ Not tested | Neither camera has a verified working capture. |
| Stylus | 🔴 Not working | Pen input, pressure and tilt are unavailable. |
| Magnetic keyboard | ⚪ Not tested | Pogo keyboard and touchpad support have not been tested. |

🟢 Working · 🟡 Partial · 🔴 Not working · ⚪ Not tested / verified

## Downloads and building

**There is no Xiaomi Pad 7 release image nor supported installation guide yet.**

The build uses the stock bootloader, a `boot_a` image and a Linux root on `userdata`. Keep a working boot image and a recovery. OEM firmware and calibration files are now included.

To build separate Fedora 44 images on an x86_64 PC, use
`./uke-fedora-builder/build-fedora44-images.sh --cross-kernel --output build/fedora44-images`.
`--cross-kernel` speeds up the ARM64 kernel compilation by running Clang natively
on the PC; other packages and rootfs still use AArch64 containers. On an ARM64
host, omit the flag. See the [Fedora 44 build guide](uke-fedora-builder/docs/FEDORA44-BUILD-CACHE.md)
for cache, resume and rebuild options.

## Source

This repository brings together the following components as submodules:

| Component | Repository |
| --- | --- |
| Kernel and device trees | [senemos-uke-kernel](senemos-uke-kernel/) |
| Hardware support and packages | [uke-linux-hardware-support](uke-linux-hardware-support/) |
| Fedora image builder | [uke-fedora-builder](uke-fedora-builder/) |

To clone with the submodules:

```sh
git clone --recurse-submodules https://github.com/linuxgamer/uke-fedora.git
```

## License

Original files are licensed under [MIT](LICENSE). Submodules and other components retain their respective licenses. Including proprietary blobs was legal.
