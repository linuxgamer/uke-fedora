# Uke Linux

Linux development for **Xiaomi Pad 7 / POCO Pad X1** (`uke`, SM7675).
Target: Fedora Rawhide AArch64 with the stock Android bootloader.

The maintainer has recorded a visible framebuffer console, UFS root, USB serial
and USB SSH on POCO Pad X1. Native graphics, touch, Wi-Fi, Bluetooth, audio and
battery telemetry remain unavailable in that recorded profile. Repeated cold
boot and model/firmware compatibility need validation. See [hardware status](HARDWARE.md)
for the exact scope; a successful build is not a hardware result.

## Start here

| Component | Entry point |
|---|---|
| Kernel, Uke DT and RPMs | [Senemos kernel](senemos-uke-kernel/README.md) |
| Rootfs and stock-ABL boot images | [Fedora builder](uke-fedora-builder/README.md) |
| Runtime, firmware and device packages | [Hardware support](uke-linux-hardware-support/README.md) |
| Recovery and storage tools | [OrangeFox](recovery-uke-ofox/README.md) |
| Release assets and requirements | [Linux images](uke-linux-images/README.md) |
| Experimental UEFI (not required for stock ABL) | [Project Aloha](uke-project-aloha/README.md) |

Detailed engineering records are private. Local private material stays under
ignored `private/`; public records must exclude credentials, unit identifiers,
calibration and private logs.

## Checkout and build

```sh
git clone --recurse-submodules https://github.com/MCC45TR/uke-linux.git
cd uke-linux
git submodule update --init --recursive
./senemos-uke-kernel/build.sh --help
./ukelinux.sh --build boot-pair --distro=fedora --help
```

Submodules use the revisions pinned by this workspace, not automatically the
latest component HEAD. Read the producing component's build guide before a build.
Build recipes do not flash or activate slots.

## Storage and safety

**Planned collaboration profile: Linux rootfs in `userdata`, without creating a
separate GPT `linux` partition.** This profile is not implemented yet. The existing
boot-pair recipe still requires `PARTLABEL=linux`; do not use it as a userdata installer.
Installing Linux in userdata destroys Android user data shared by both slots.

Keep firmware-matched stock backups and a verified recovery route. Stock
`vendor_boot` and `vbmeta` stay untouched. Flashing and slot changes are manual
owner operations. Never infer an installable release from source or VM tests.

## Downloads and contributions

- [Development RPM channel](https://copr.fedorainfracloud.org/coprs/mcc45tr/uke-linux-test/)
- [Fedora image releases](https://github.com/MCC45TR/uke-linux-images/releases)
- [Recovery releases](https://github.com/MCC45TR/orangefox_device_xiaomi_uke/releases)

Check the producing repository's compatibility and rollback requirements.
Read component `AGENTS.md` before changes; retain original code attribution and
licenses. Use unmodified Fedora applications and their normal dependencies,
including Python. Desktop selectors live in the builder, not hardware-support.
See [runtime and desktop policy](RUNTIME-POLICY.md). Report source, package, VM and physical results separately.

Unofficial community project; not endorsed by Fedora, Xiaomi, POCO or Qualcomm.
[License](LICENSE) · [Security](SECURITY.md).
