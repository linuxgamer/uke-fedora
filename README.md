# Uke Fedora

Fedora Linux port made mainly for the **Xiaomi Pad 7**, based on [MCC45TR's port](https://github.com/MCC45TR/uke-linux). It may not work on POCO Pad X1.

This port is **work in progress**. Differences are: Fedora 44, `/userdata` install, extra QoL stuff.

> [!WARNING]
> This is not ready for daily use. Installing to `userdata` overwrites Android user data. Back up any data you have!

### Hardware support (upstream POCO Pad X1 only)

Hardware status comes from [upstream hardware report](https://github.com/MCC45TR/uke-linux#hardware-support).

| Component | Status | Notes |
| --- | --- | --- |
| Fedora KDE desktop | 🟡 Partial | Boots into KDE and runs applications, but some desktop issues remain. |
| Other desktops | ⚪ Not verified | Only KDE images have been tested. |
| Display | 🟢 Working | Native 3200 × 2136 resolution and adjustable brightness. |
| Refresh rate | 🟡 Partial | Fixed 30–144 Hz modes work; adaptive refresh (VRR) is disabled. |
| Touchscreen | 🟡 Partial | Works for normal use; multitouch reliability still needs work. |
| Graphics (GPU) | 🟡 Partial | Desktop OpenGL works, Vulkan and some graphics features remain experimental. |
| CPU and storage | 🟢 Working | All CPU cores are available, internal storage works. |
| Wi-Fi | 🟢 Working | Connects to networks and supports normal data transfers. |
| Bluetooth | 🟢 Working | Tested with a mouse and wireless headphones, including audio playback. |
| Auto-rotation | 🟢 Working | Screen and touch orientation follow tablet rotation. |
| Other sensors | 🟡 Partial | Motion, compass, proximity and cover detection have varying levels of support. |
| USB-C accessories | 🟡 Partial | A powered hub and mouse work, other accessories need more testing. |
| External display | ⚪ Not verified | Video output over USB-C/HDMI/DP has not been tested. |
| Charging | 🟡 Partial | Charging and battery percentage are detected; fast charging, charge limits and bypass may not work. |
| Sleep and wake | 🟡 Partial | Basic suspend testing exists, but wake is unreliable. |
| Reboot and shutdown | 🟡 Partial | Reboot works in some tests; shutdown can hang or restart the tablet. |
| Built-in speakers and microphones | 🔴 Not working | No functional playback or recording yet. |
| Cameras | 🔴 Not working | Neither camera has a verified working capture. |
| Stylus | 🔴 Not working | Pen input, pressure and tilt are unavailable. |
| Magnetic keyboard | 🔴 Not working | Pogo keyboard and touchpad support have not been tested. |

🟢 Working · 🟡 Partial · 🔴 Not working · ⚪ Not verified

## Downloads and building

Go to [releases](https://github.com/linuxgamer/uke-fedora/releases) and download any desktop you want. Then look at [installation guide](INSTALL.md).

To build separate Fedora 44 images on an x86_64 PC, use
`./uke-fedora-builder/build-fedora44-images.sh --cross-kernel --output build/<DESIRED FOLDER>`.
By default all desktop variants are built, add `--profiles <ANY DE YOU WANT>,<DE 2>` to select DEs.
`--cross-kernel` speeds up the kernel compilation by running Clang natively
on the x86 PC, other packages and rootfs still use AArch64 containers. On an ARM64
host, omit the flag. See the [Fedora 44 build guide](uke-fedora-builder/docs/FEDORA44-BUILD-CACHE.md) for cache, resume and rebuild options.

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

Original files are licensed under [MIT](LICENSE). Submodules and other components retain their respective licenses. Including proprietary blobs is legal.
