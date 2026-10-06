# Installing Fedora 44 on Xiaomi Pad 7 (`uke`)

> [!WARNING]
> Backup any data you have before installing and keep working ROM to rollback to!

## Prerequisites

- Unlocked bootloader.
- computer with `fastboot`
- Downloaded release assets: `boot.img`, `init_boot.img`, `dtbo.img`,
  `uke-rootfs.img.zst`, `uke-rootfs.img.sha256`, and `SHA256SUMS`.

## Flashing

Verify the active
slot before replacing its images: the examples below are for slot `a`.

```sh
# CHANGE PATHS ACCORDINGLY.
fastboot flash boot_a boot.img
fastboot flash init_boot_a init_boot.img
fastboot flash dtbo_a dtbo.img
```

The rootfs is a 3 GiB raw ext4 image. Decompress and verify it before flashing:

```sh
zstd -d uke-rootfs.img.zst
sha256sum -c uke-rootfs.img.sha256
```

ABL fastboot has an approximately 4 GiB transfer limit and skips zero blocks, so
erase or zero `userdata` before flashing the image:

```sh
# From the initramfs serial console
dd if=/dev/zero of=/dev/sda32 bs=1M count=4096 conv=fsync

# Run this when in fastboot.
fastboot flash userdata uke-rootfs.img
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
