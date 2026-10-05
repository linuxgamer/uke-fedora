# AGENTS.md

Fedora (mainline Linux) port for the **Xiaomi Pad 7** (`uke`, **SM7675**).
Boot uses the stock Android ABL chain. Keep the repository layout and workflow
aligned with [gts9wifi-fedora](https://github.com/nacht20-de/gts9wifi-fedora)
where device requirements allow it.

## Kernel Tracks

- **Working primary track: ztsubaki 6.12** (`build/ztsubaki/`). Upstream v6.12
  plus `references/ztsubaki-uke-linux/patches/uke/` for GCC/TCSR/RPMh/GDSC/SMMU/
  USB/UFS. **Fedora boots to a login prompt.** The supported scheme modifies
  `boot` and `init_boot`; stock `vendor_boot`, `dtbo`, and `vbmeta` stay in place.
- **Palawan 7.2** (`references/archive/palawan-7.2/kernel/`, `build/linux-uke/`, KVER `7.2.0-rc2-uke`) is a
  parked mainline fork with its own DTS and drivers. It does not boot. Retain it
  as a reference for moving the O82 panel, NT36532 touchscreen, and board DTS to
  v6.12.

## Layout

| Path | Purpose |
|---|---|
| `references/archive/` | Parked Palawan 7.2 work, legacy boot/rootfs tooling, and historical notes |
| `boot/` | Working `build-initramfs-usb.sh`, image builders, cmdline, bootconfig, dracut |
| `rootfs/` | Fedora rootfs build and `userdata` image scripts |
| `tools/` | mkbootimg, avbtool, stock extraction, and conversion utilities |
| `docs/` | Build, status, hardware, and stock-firmware documentation |
| `.github/workflows/` | Kernel, rootfs, boot bundle, and full-set CI |
| `references/`, `attic/` | Uncommitted donor clones and archives |

## Working Build

```sh
make -C build/ztsubaki/linux O="$PWD/build/ztsubaki/out" ARCH=arm64 LLVM=1 Image.gz
make -C build/ztsubaki/linux O="$PWD/build/ztsubaki/out" ARCH=arm64 LLVM=1 modules
boot/build-initramfs-usb.sh
rootfs/mk-internal-storage-fastboot.sh 3
```

See `docs/BUILD.md` for image construction and the `userdata` zeroing requirement.
`references/archive/palawan-7.2/kernel/build.sh` is the archived Palawan build path.

## Rules

- **Never run `fastboot`.** The user performs every flashing operation.
- Do not commit `build/`, `references/`, `attic/`, `rootfs/firmware.tar.gz`,
  backups, or generated `*.img`, `*.dtb`, and `*.ko` files. Do not commit firmware blobs.
- ztsubaki v6.12 is the working kernel. Palawan 7.2 is archived reference material only.
- Follow the gts9wifi layout and process; implement device-specific behavior locally.
- Update `docs/Known-Issues.md` whenever a hardware or boot finding changes status.

## Key Values

- Working KVER: `6.12.0-dirty`; Palawan KVER: `7.2.0-rc2-uke` with `LOCALVERSION=-uke`.
- Root UUID: `19364720-0ee1-4715-b30a-51a47d4a814c`; label: `uke_root`.
- Partition sizes: `boot`/`vendor_boot` 96 MiB, `init_boot` 8 MiB, `dtbo` 24 MiB,
  `vbmeta` 128 KiB.
- Device: `uke`, model `2410CRP4CG`; UFS host `1d84000.ufshc`; `userdata` is `/dev/block/sda32`.
- Host requirements: `docker`, `qemu-user-static-binfmt`, `clang`, `llvm`, `lld`,
  `bc`, `dtc`, `pahole`, `flex`, `bison`, `lz4`, `cpio`, and `python3`.
