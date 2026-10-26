# Uke Fedora

Fedora Linux port made mainly for the **Xiaomi Pad 7**, based on [MCC45TR's port](https://github.com/MCC45TR/uke-linux).

This port is **work in progress**. Differences are: Fedora 44, `/userdata` install, more DEs, TM display support, build optimisations, extra QoL stuff.

> [!WARNING]
> This is not ready for daily use. Installing to `userdata` overwrites Android user data. Back up any data you have!

## Hardware support

| Component | Status | Notes |
| --- | --- | --- |
| Fedora KDE desktop | 🟢 Working | Boots into KDE; basic use and touch-only setup tested. |
| GNOME desktop | 🟢 Working | The GNOME image boots and works on the tested TM tablet. |
| Other desktops | ⚪ Not verified | TTY, Phosh and Plasma Mobile still need tablet testing. |
| TTY touch keyboard | ⚪ Not verified | An experimental framebuffer keyboard is included in TTY images; it has not been tested on the tablet. |
| Display | 🟡 Partial | Native TM display works; a brief grey screen appears during boot. CSOT is untested on this port. |
| Refresh rate | 🟡 Partial | TM switches between the modes offered in KDE; sustained operation is untested. VRR is disabled. |
| Touchscreen | 🟡 Partial | Works, multitouch is unreliable. |
| Graphics (GPU) | 🟡 Partial | OpenGL works, Vulkan is experimental. |
| CPU and storage | 🟢 Working | All CPU cores are available, internal storage works. |
| Wi-Fi | 🟢 Working | Connects to networks and supports normal data transfers. |
| Bluetooth | 🟢 Working | Tested with a mouse and wireless headphones, including audio playback. |
| Auto-rotation | 🟢 Working | Screen and touch orientation follow tablet rotation. |
| Other sensors | 🟡 Partial | Motion, compass, proximity and cover detection have varying levels of support. |
| USB-C accessories | 🟡 Partial | An OTG mouse works through a USB-A-to-USB-C adapter; manual USB ACM on/off works. Other accessories need testing. |
| External display | ⚪ Not verified | Video output over USB-C/HDMI/DP has not been tested. |
| Charging | 🟡 Partial | Charging and battery percentage are detected, fast charging, charge limits and bypass may not work. |
| Sleep and wake | 🟡 Partial | Basic suspend exists, but wake is unreliable. |
| Reboot and shutdown | 🟡 Partial | Reboot works in some tests, shutdown can hang or restart the tablet. |
| Built-in speakers and microphones | 🔴 Not working | No functional playback or recording yet. |
| Cameras | 🔴 Not working | Neither camera has a verified working capture. |
| Stylus | 🔴 Not working | Pen input, pressure and tilt are unavailable. |
| Magnetic keyboard | ⚪ Not verified | Pogo keyboard and touchpad support have not been tested. |

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
