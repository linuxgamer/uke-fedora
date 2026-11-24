# Uke Fedora


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
| Fedora KDE desktop | 🟢 Working | Boots and Works |
| GNOME desktop | 🟢 Working | The GNOME image boots and works. |
| Other desktops | 🟢 Working | Sway, Hyprland, i3wm xfce, lxqt , cinnamon are verified working.
| Display | 🟢 Working| Display is working 30-144hz supported, a brief 2-3 second white screen appears on boot. |
| Refresh rate |  🟢 Working  | Manual Refresh rate switching works and is reliable, (KDE verified), VRR is disabled. |
| Touchscreen |  🟢 Working | Works,10 Point MultiTouch is working. |
| Graphics (GPU) | 🟢 Working | OpenGL: glmark2 ≈ 5–6K. Vulkan: vkmark ≈ 8K (KDE Plasma Wayland). 8K+ Glmark2 , 10K+ vkmark on minimal Hyprland |
| CPU and storage | 🟢 Working | All CPU cores are available, internal storage works and root partition expands to device storage.|
| Wi-Fi | 🟢 Working | Connects to networks and supports normal data transfers. |
| Bluetooth |  🟢 Working  | Bluetooth devices work, Tested Keyboard, Mouse and headphones. |
| Auto-rotation | 🟢 Working | Screen and touch orientation follow tablet rotation. |
| USB-C accessories |🟢 Working | An OTG mouse/Keyboard works through a USB-A-to-USB-C adapter; Usb Hub also working. |
| Sleep and wake |🟢 Working  | Basic suspend exists. |
| Reboot and shutdown |  🟢 Working  | Reboot works, shutdown can hang or restart the tablet. |
| Built-in speakers and microphones | 🟢 Working | Playback and recording work for all speakers, including the first-boot root KDE session and normal user sessions. |
| Magnetic keyboard | 🟢 Working | Xiaomi Focus Keyboard WN8030 keyboard/touchpad, Caps Lock and backlight work. MiAuth is disabled in the driver (`mi_auth=0`), so no token daemon is needed. Ctrl+Alt+3/4 sets backlight 0/50/100%; wake fades up over 300 ms. |
| External display | ⚪ WIP | Video output over USB-C/HDMI/DP has not been tested. |
| Cameras | ⚪WIP | Neither camera has a verified working capture. |
| Other sensors | 🟡 Partial | Motion, compass, proximity not verified but cover detection works.|
| Charging | 🟡 Partial | Charging and battery percentage are detected, fast charging, charge limits and bypass may not work. Detected 20-25Watt of charging instead of full 45 Watt. |
| Stylus | 🔴 Not working | Pen input, pressure and tilt are unavailable. |

🟢 Working · 🟡 Partial · 🔴 Not working · ⚪ Not verified/WIP

Developer-level evidence and blockers: [docs/HARDWARE.md](docs/HARDWARE.md).

## Downloads and building

Go to [releases](https://github.com/linuxgamer/uke-fedora/releases) and download the KDE or GNOME image. Then look at the [installation guide](docs/INSTALL.md).

To build separate Fedora 44 images on an x86_64 PC, use:-
```
./uke-fedora-builder/build-images.sh --cross-kernel --output build/<DESIRED FOLDER>
```
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
| Kernel and device trees | [senemos-uke-kernel-mainline](https://github.com/saksham-991/senemos-uke-kernel-mainline) |
| Hardware support and packages | [uke-linux-hardware-support](https://github.com/saksham-991/uke-linux-hardware-support) |
| Fedora image builder | [uke-fedora-builder](https://github.com/saksham-991/uke-fedora-builder) |

To clone with the submodules:

```sh
git clone --recurse-submodules https://github.com/saksham-991/uke-fedora.git
```
