# Installing Fedora on Xiaomi Pad 7 (`uke`)

This guide describes the currently working experimental path: Linux v6.12 from
`build/ztsubaki/`, a small `init_boot` initramfs, and a Fedora rootfs in
`userdata`.

> [!WARNING]
> This is bring-up software. Installing the rootfs destroys Android user data.
> Keep a stock firmware package and a known-good recovery path before proceeding.

## Prerequisites

- Unlocked bootloader.
- A Linux host with `fastboot`; flashing is performed manually by the user.
- Built `boot.img`, `init_boot.img`, and `dtbo.img` from the v6.12 path.
- A Fedora rootfs image built as described in [docs/BUILD.md](docs/BUILD.md).

## Flashing

The active-slot `boot`, `init_boot`, and `dtbo` images are part of the supported
boot path. Keep the stock `vendor_boot` and `vbmeta` images. Verify the active
slot before replacing its images; the examples below are for slot `a`.

```sh
# Run these commands yourself after reviewing the paths and active slot.
fastboot flash boot_a build/ztsubaki/dist/boot.img
fastboot flash init_boot_a build/ztsubaki/dist/init_boot.img
fastboot flash dtbo_a build/ztsubaki/dist/dtbo.img
```

Release bundles provide the raw rootfs compressed as `uke-rootfs.img.zst`:

```sh
zstd -d uke-rootfs.img.zst
sha256sum -c uke-rootfs.img.sha256
```

The rootfs is a 3 GiB raw ext4 image. ABL fastboot has an approximately 4 GiB
transfer limit and skips zero blocks, so erase or zero `userdata` before flashing
the raw image:

```sh
# From the initramfs shell, or use an equivalent manual erase operation.
dd if=/dev/zero of=/dev/sda32 bs=1M count=4096 conv=fsync

# Run this command yourself after the device is in fastboot mode.
# Release users: uke-rootfs.img; local builders: build/fedora/uke-rootfs.img.
fastboot flash userdata uke-rootfs.img
```

Do not flash `uke-rootfs.sparse.img` through ABL fastboot.

## First Boot and Debugging

- The initramfs finds the rootfs by UUID and switches to Fedora systemd.
- USB ACM is the supported serial console: `/dev/ttyACM0` on the host and
  `/dev/ttyGS0` on the tablet.
- The initramfs writes an early-boot summary to `/status.txt`.
- RNDIS is under active bring-up and is not yet a supported Fedora networking path.

## Recovery

Restore the stock firmware or reformat `userdata` from recovery. Never modify
XBL, ABL, TZ, modem, DSP, GPT, `persist`, or radio firmware for this port.
