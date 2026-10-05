# Linux on Xiaomi Pad 7 (`uke`)

Experimental Fedora port for the Xiaomi Pad 7 (`uke`, Qualcomm SM7675 / Snapdragon
7+ Gen 3) using the stock Android boot chain (ABL). No secondary bootloader or
UEFI is used.

## Status

**Fedora 44 boots from internal UFS to a login prompt.** The working path is
upstream Linux v6.12 with the ztsubaki `uke` patch set and the stock
`vendor_boot`, `dtbo`, and `vbmeta` images left in place.

Working:

- Kernel boot, simplefb console, RPMh, SMMU, UFS, and ext4 rootfs.
- Fedora userspace through `switch_root` to systemd.
- USB ACM serial console (`/dev/ttyACM0` on the host, `/dev/ttyGS0` on the device).

Not working or unverified:

- Display DRM/panel, touchscreen, Wi-Fi/Bluetooth, audio, sensors, cameras, and suspend.
- RNDIS is being brought up; USB ACM is the supported debug channel today.

This is bring-up software. It can erase Android data and may require recovery with
the stock firmware. Keep a known-good stock boot path before experimenting.

## Quick Links

| Document | Contents |
|---|---|
| [INSTALL.md](INSTALL.md) | Prerequisites, supported flashing path, and recovery notes |
| [docs/BUILD.md](docs/BUILD.md) | Reproducible v6.12 kernel, initramfs, and rootfs builds |
| [docs/Known-Issues.md](docs/Known-Issues.md) | Feature status, current limitations, and confirmed fixes |
| [docs/Hardware-Notes.md](docs/Hardware-Notes.md) | Device hardware summary |
| [docs/STOCK-DTB.md](docs/STOCK-DTB.md) | Stock boot image, partition, DTB, and DTBO analysis |
| [docs/STOCK-SUPER.md](docs/STOCK-SUPER.md) | Stock `super.img`, modules, and firmware inventory |
| [references/archive/](references/archive/) | Archived Palawan, legacy boot, and historical research material |

## Supported Boot Path

Only replace these partitions on the active slot:

- `boot`: mainline kernel with an appended DTB.
- `init_boot`: minimal busybox initramfs.
- `userdata`: Fedora rootfs.

Do not replace `vendor_boot`, `dtbo`, or `vbmeta`. Xiaomi ABL rejects the earlier
five-image approach; retaining the stock images is required for the working setup.

## Repository Layout

| Path | Purpose |
|---|---|
| `build/ztsubaki/` | Working Linux v6.12 source tree, output, and image artifacts (not committed) |
| `boot/` | Initramfs and Android boot-image construction scripts |
| `rootfs/` | Fedora rootfs creation and `userdata` image scripts |
| `references/archive/palawan-7.2/` | Archived Palawan 7.2 DTS, drivers, and build path; reference only |
| `tools/` | Host-side image extraction, backup, and conversion utilities |
| `docs/` | Build, status, hardware, and stock-firmware documentation |
| `references/` | Uncommitted donor checkouts and external source material |

## References

- [ztsubaki/uke-linux](https://github.com/ztsubaki/uke-linux): original v6.12
  bring-up and stock-DT workflow.
- [gts9wifi-fedora](https://github.com/nacht20-de/gts9wifi-fedora): Fedora boot
  pipeline reference.
- [palawan-mainline/linux](https://codeberg.org/palawan-mainline/linux): source
  for the archived Palawan 7.2 work.
