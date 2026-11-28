# uke-fedora

A Fedora 45 port for the Xiaomi Pad 7 and POCO Pad X1 (`uke`). The Xiaomi Pad 7 is the tested model. POCO Pad X1 testing is pending.

## Download and install

1. Open **Release 2** and expand **Assets**. Download one of the two install ZIPs below. [Release 2 downloads](https://github.com/linuxgamer/uke-fedora/releases/tag/r2)
2. Follow the install guide. You’ll need a computer, a USB data cable, and an unlocked tablet. **Installing replaces Android and erases the tablet’s apps and files.** [Install Fedora](docs/INSTALL.md)

| Download | Mobile mode | Desktop mode |
| --- | --- | --- |
| **KDE** (`uke-fedora-kde-…zip`) | Plasma Mobile | Plasma |
| **Phosh + GNOME** (`uke-fedora-phosh-gnome-…zip`) | Phosh | GNOME |

Each ZIP contains the ready-to-install files. To switch between mobile and desktop modes, sign out and choose a session at the login screen. Both modes share your account and files.

Release 1 is the previous port. [Legacy branch](https://github.com/linuxgamer/uke-fedora/tree/legacy) · [Release 1](https://github.com/linuxgamer/uke-fedora/releases/tag/r1)

## Hardware support

**Before switching.** Camera capture is unavailable. On the tested Wi-Fi network, the tablet could browse the web after waking, but other devices on the network sometimes lost access to it after idle. A low-power computer USB port can supply less power than the tablet uses, even when the battery icon shows charging.

<details>
<summary>Expand the hardware support table</summary>

| Feature | Xiaomi Pad 7 | POCO Pad X1 | Notes |
| --- | --- | --- | --- |
| Boot, internal display and touchscreen | Works | Untested | Slot A boot and touch setup verified on Xiaomi Pad 7. |
| Adreno graphics | Works | Untested | Freedreno FD735 verified in Plasma and Plasma Login. |
| Wi-Fi | Partial | Untested | Browsing worked after suspend. Connections from other devices on the same Wi-Fi sometimes timed out after idle. |
| Bluetooth | Works | Untested | Pairing was reported working. Accessory and reconnect coverage is limited. |
| Speakers and microphone | Works | Untested | Internal speaker playback and microphone capture tested. |
| Auto-rotation and magnetic cover | Works | Untested | Rotation and cover events tested. Cover blanking and reopening passed at Plasma Login. |
| Suspend and wake | Partial | Untested | Suspend-to-idle and power-button resume tested. Other wake sources need coverage. |
| Battery and charging | Partial | Untested | UPower reads the battery. The gauge can report Charging while the battery loses charge on low-power USB. |
| Clock without a network | Works | Untested | Verified on a cold boot after the first network time sync. |
| Hardware video | Partial | Untested | Native H.264 and HEVC tested with optional Iris firmware. The browser test was limited. |
| Focus Keyboard, stylus and USB-C docks | Untested | Untested | Accessory tests pending. |
| Cameras | Unavailable | Untested | Camera capture is outside the preview scope. |

</details>

## What’s new

- One download per desktop family, with mobile and desktop modes.
- KDE sign-in uses hardware graphics. Closing the cover turns off the login screen, and opening it brings it back.
- Larger controls and automatic rotation in Plasma. Discover can browse Fedora apps.
- Clock restoration on offline boots after the first network time sync.

<details>
<summary>Building, testing, and contributing</summary>

The rewrite builds on Senemos and uses a cached Python builder with stock Fedora packages and a checksum-pinned firmware bundle. Uke Debug supports SSH, an authenticated USB console, and TWRP recovery. [Upstream uke-linux](https://github.com/MCC45TR/uke-linux) · [Remaining feature parity](docs/PARITY.md)

- [Build your own image](docs/build/README.md)
- [Check release test status](docs/BRINGUP.md#preview-status)
- [Test a desktop profile](docs/TESTING.md#desktop-support-checklist)

Build from a fresh clone of `uke-fedora` with its pinned upstream submodules, documented host tools, and firmware and device inputs. The upstream `uke-linux` tree and the `legacy` branch are references for the rewrite.

See the [project policies](docs/POLICIES.md) for build and release requirements.

Build the Fedora 45 image pair with `python3 build/build.py` on Linux or WSL2. Use `--profile kde` or `--profile phosh-gnome` for a preview image. See the [build instructions](docs/build/README.md) for inputs, host setup, and other profiles.

Use [Uke Debug](docs/extra/README.md) to run tablet diagnostics, view live stats, and open a shell. It provides a desktop GUI and JSON commands for automation.

| Folder | What belongs there |
| --- | --- |
| `.github/` | GitHub Actions, issue templates, and images used in the README |
| `build/` | Python build scripts, build inputs, temporary work, cache, and outputs |
| `docs/` | Public documentation organized by the project folder it covers |
| `extra/` | Optional tools and materials that have no home elsewhere |
| `kernel/` | Senemos kernel integration, upstream revision, and any local patches |
| `private/` | Local notes, handoffs, reference material, and other unpublished files |
| `rootfs/` | Files and configuration intended for the installed root filesystem |

Build scripts and shareable inputs can be tracked under `build/`. Git ignores `build/cache/`, `build/work/`, `build/out/`, and `build/inputs/local/`. Use the last directory for local-only inputs and `private/` for unpublished reference material.

The rootfs source is the common Fedora package list, profile definitions, and device configuration under `rootfs/`. The build guide covers submodules and the pinned Senemos RPM. Builds run in WSL2 write their outputs inside the Linux checkout. [Packages](rootfs/packages.txt) · [Profiles](rootfs/profiles.toml) · [Kernel pin](kernel/senemos-prebuilt.json)

</details>

## License

Original port work is licensed under [GPL-3.0-only](LICENSE). The kernel and code imported from other ports retain their applicable licenses and notices.
