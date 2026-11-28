# uke-fedora

A Fedora 45 port for the Xiaomi Pad 7 and POCO Pad X1 (`uke`).

**Each preview image includes a touch-first mobile mode and a desktop mode.** Choose an image by the two sessions it offers.

| Preview image | Mobile mode | Desktop mode |
| --- | --- | --- |
| `kde` | Plasma Mobile | Plasma |
| `phosh-gnome` | Phosh | GNOME |

Use the same account in both modes. To switch, sign out and choose a session at the login screen. Installing Fedora erases Android and any existing Fedora files in `userdata`.

- [Install Fedora and prepare recovery](docs/INSTALL.md)
- [Check profile and hardware status](docs/BRINGUP.md#preview-status)
- [Test a desktop profile](docs/TESTING.md#desktop-support-checklist)
- [Build your own image](docs/build/README.md)

The previous port is available on the [legacy branch](https://github.com/linuxgamer/uke-fedora/tree/legacy) and in the [legacy releases](https://github.com/linuxgamer/uke-fedora/releases).

## Hardware support

<details>
<summary>Expand the hardware support table</summary>

| Feature | Xiaomi Pad 7 | POCO Pad X1 | Notes |
| --- | --- | --- | --- |
| Boot, internal display and touchscreen | Works | Untested | Slot A boot and touch setup verified on Xiaomi Pad 7. |
| Adreno graphics | Works | Untested | Freedreno FD735 verified in Plasma and Plasma Login. |
| Wi-Fi | Partial | Untested | Internet access and one suspend reconnect passed. LAN peers can time out after idle. |
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

## What this rewrite adds

- One image per desktop family, with a touch-first session and a desktop session available at sign-in.
- A single cached Python builder using stock Fedora packages directly and a small, checksum-pinned firmware bundle.
- Uke Debug diagnostics from a PC over SSH, an authenticated USB console, or TWRP recovery.
- Tablet-oriented Plasma defaults with 250% scaling, cover blanking, touch wake, and the Adreno render path at login.

The rewrite builds on [uke-linux](https://github.com/MCC45TR/uke-linux) and Senemos. See [remaining feature parity](docs/PARITY.md) for upstream features we still need to qualify.

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

The rootfs source is the [common Fedora package list](rootfs/packages.txt), [profile definitions](rootfs/profiles.toml), and device configuration under `rootfs/`. Run `git submodule update --init --recursive --depth 1` to populate the [Senemos](kernel/senemos), [hardware-support](rootfs/device-helpers/hardware-support), [HexagonRPC](rootfs/device-helpers/hexagonrpc), and [BuffyBox](rootfs/tty/buffybox) source trees. Bring-up images use the [pinned Senemos RPM](kernel/senemos-prebuilt.json). Builds run in WSL2 write their outputs inside the Linux checkout.

## License

Original port work is licensed under [GPL-3.0-only](LICENSE). The kernel and code imported from other ports retain their applicable licenses and notices.
