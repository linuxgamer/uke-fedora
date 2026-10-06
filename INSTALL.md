# Installing Fedora 44 on Xiaomi Pad 7 (`uke`)

> [!WARNING]
> Backup any data you have before installing and keep working ROM to rollback to!

## Prerequisites

- Unlocked bootloader.
- computer with `fastboot`
- Downloaded(from releases) `boot.img`, `init_boot.img`, and `dtbo.img` (6.12 kernel)
- Downloaded Fedora rootfs image

## Flashing

Verify the active
slot before replacing its images: the examples below are for slot `a`.

```sh
# CHANGE PATHS ACCORDINGLY!!!
fastboot flash boot_a build/ztsubaki/dist/boot.img
fastboot flash init_boot_a build/ztsubaki/dist/init_boot.img
fastboot flash dtbo_a build/ztsubaki/dist/dtbo.img
```

rootfs is a 3 gb raw ext4 image. fastboot has ~4 GiB transfer limit(before bugging out) and skips zero blocks, so erase or zero `userdata` before flashing the image:

```sh
# From the initramfs serial console
dd if=/dev/zero of=/dev/sda32 bs=1M count=4096 conv=fsync

# Run this when in fastboot, CHANGE PATHS ACCORDINGLY
fastboot flash userdata /build/fedora/uke-rootfs.img
```

do not flash `uke-rootfs.sparse.img` through fastboot.

## Debugging

- The initramfs finds the rootfs by UUID and boots into Fedora.
- USB ACM is the only supported serial console: `/dev/ttyACM0` on the host and
  `/dev/ttyGS0` on the tablet.
- initramfs writes boot logs to `/status.txt`.
- RNDIS is in development and not usable yet.

## Recovery

Restore the stock firmware and/or reformat `userdata` partition with `fastboot -w`
