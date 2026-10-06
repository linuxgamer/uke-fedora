# Fedora 44 on Xiaomi Pad 7 (`uke`)

**W.I.P** Fedora port for the Xiaomi Pad 7 (Qualcomm SM7675 aka `lamma` or `cliffs7`) using mainline 6.12 kernel.

## Status

**Fedora 44 successfully boots** from UFS into login prompt.

Working:
- 6.12 boot, simplefb console, RPMh, SMMU, UFS, and ext4 rootfs.
- Fedora 44 userspace.
- USB ACM serial console (`/dev/ttyACM0` on the host, `/dev/ttyGS0` on the device).

Not working or unverified:
- Display DRM/panel, touchscreen, Wi-Fi/Bluetooth, audio, sensors, cameras, suspend.
- RNDIS is in development, use USB ACM as debug channel right now.

> [!WARNING]
> Backup any data you have before installing it and have working ROM to rollback

## Useful

| Document | Contents |
|---|---|
| [docs/INSTALL.md](docs/INSTALL.md) | Install guide |
| [docs/BUILD.md](docs/BUILD.md) | reproducible v6.12 kernel, initramfs, and rootfs builds |
| [docs/known-issues.md](docs/known-issues.md) | feature status and current limitations |
| [docs/hardware-notes.md](docs/hardware-notes.md) | device hardware summary |
| [docs/stock-dtb.md](docs/stock-dtb.md) | stock boot image, partition, DTB, and DTBO analysis |
| [docs/stock-super.md](docs/stock-super.md) | stock `super.img`, modules, and firmware inventory analysis |
| [references/archive/](references/archive/) | archived 7.2, legacy boot, and historical research material |

## Supported boot path

replace only these partitions on the active slot:

- `boot`: mainline kernel and command line.
- `init_boot`: minimal busybox initramfs.
- `dtbo`: stock dtbo tuned for the v6.12 UFS, GDSC, and driver bindings.
- `userdata`: fedora 44 rootfs.

Do not replace `vendor_boot` or `vbmeta`. Xiaomi ABL doesnt like that and bootloops, so current setup replaces only `boot`, `init_boot`, and
`dtbo` alongside `userdata`.

## Repo layout

| Path | Purpose |
|---|---|
| `kernel/` | pinned Linux v6.12 base, complete Uke patch series, config, and source-release scripts |
| `build/ztsubaki/` | local kernel source, output, modules, and image artifacts (not committed) |
| `boot/` | Initramfs and Android boot images creation scripts |
| `rootfs/` | Fedora 44 rootfs creation and `userdata` image scripts |
| `references/archive/palawan-7.2/` | archived 7.2 kernel, DTS, drivers: reference only |
| `tools/` | host tools(extract/analyze images, log/info collection, hash validation |
| `docs/` | build, status, hardware, etc information |
| `references/` | references: code and moar information |

## Credits

- [ztsubaki/uke-linux](https://github.com/ztsubaki/uke-linux): It made this port possible!
- [gts9wifi-fedora](https://github.com/nacht20-de/gts9wifi-fedora): lots of concepts and scripts
- [palawan-mainline/linux](https://codeberg.org/palawan-mainline/linux): used in archived 7.2 work
