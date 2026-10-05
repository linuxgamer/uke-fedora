# Build Guide

The supported path is Linux v6.12 from `build/ztsubaki/`. The Palawan 7.2 tree in
`references/archive/palawan-7.2/` is reference material and is not expected to boot.

## Host Requirements

Install `docker`, `qemu-user-static-binfmt`, `clang`, `llvm`, `lld`, `bc`, `dtc`,
`fdtput`, `fdtget`, `mkdtboimg`, `pahole`, `flex`, `bison`, `lz4`, `zstd`, `cpio`,
and `python3`.

## 1. Kernel

Build the working kernel and modules:

```sh
make -C build/ztsubaki/linux O="$PWD/build/ztsubaki/out" ARCH=arm64 LLVM=1 Image.gz
make -C build/ztsubaki/linux O="$PWD/build/ztsubaki/out" ARCH=arm64 LLVM=1 modules
```

The kernel is upstream v6.12 plus
`references/ztsubaki-uke-linux/patches/uke/`. The patch covers the GCC/TCSR,
RPMh, GDSC, SMMU, USB, and UFS bring-up required by this device.

## 2. Initramfs and Boot Images

Build the busybox initramfs with USB ACM and early boot diagnostics:

```sh
boot/build-initramfs-usb.sh
```

Set `STOCK_DTBO` to the `dtbo.img` from the exact stock firmware matching the
installed stock `vendor_boot`. Transform it, then package all boot images:

```sh
STOCK_DTBO=/path/to/stock-firmware/images/dtbo.img
boot/build-initramfs-usb.sh
boot/build-dtbo.sh --stock-dtbo "$STOCK_DTBO" --out build/ztsubaki/dist/dtbo.img
boot/build-bundle-ztsubaki.sh \
    --kernel build/ztsubaki/out/arch/arm64/boot/Image.gz \
    --init-boot build/initramfs-usb.lz4 \
    --dtbo build/ztsubaki/dist/dtbo.img \
    --cmdline boot/cmdline.txt \
    --out build/ztsubaki/dist
```

The stock DTBO is not tracked. Do not combine a DTBO from one stock firmware with
`vendor_boot` from another; use the validated release `dtbo.img` when rebuilding
from the exact matching firmware is not possible.

The supported layout is:

- `boot.img`: `Image.gz`, its command line, and an AVB hash footer.
- `init_boot.img`: LZ4 busybox initramfs with an AVB hash footer; partition size
  is 8 MiB.
- `dtbo.img`: stock DTBO transformed for the v6.12 driver bindings.
- `vendor_boot` and `vbmeta`: leave the stock images untouched. Flash the custom
  `dtbo.img` together with `boot.img` and `init_boot.img`.

The root command line uses UUID `19364720-0ee1-4715-b30a-51a47d4a814c`.

## 3. Fedora Rootfs

Build the Fedora 44 `@core` rootfs:

```sh
sudo DNF_FORCEARCH=aarch64 ./rootfs/build-rootfs.sh
```

Create a 3 GiB raw ext4 image suitable for ABL fastboot:

```sh
rootfs/mk-internal-storage-fastboot.sh 3
```

This produces `build/fedora/uke-rootfs.img`. It uses UUID
`19364720-0ee1-4715-b30a-51a47d4a814c` and label `uke_root`.

## 4. Release Bundle

Create the uploadable release files without manually copying images or generating
checksums:

```sh
boot/package-release.sh \
    --bundle build/ztsubaki/dist \
    --rootfs build/fedora/uke-rootfs.img \
    --out build/release
```

This produces `boot.img`, `init_boot.img`, `dtbo.img`, compressed
`uke-rootfs.img.zst`, `SHA256SUMS`, and `uke-rootfs.img.sha256`. The compressed
rootfs must be decompressed before flashing; do not upload the sparse rootfs.

### ABL Fastboot Constraint

ABL fastboot is reliable only below roughly 4 GiB and skips zero blocks. Before
flashing the raw rootfs, zero `userdata` from the initramfs shell:

```sh
dd if=/dev/zero of=/dev/sda32 bs=1M count=4096 conv=fsync
```

Then manually flash the raw image. Do not use the sparse image with ABL fastboot.

## Archived Palawan Path

`references/archive/palawan-7.2/kernel/build.sh` builds the Palawan 7.2 reference
tree and its DTS/driver work, but that path does not boot. Preserve it as a source
for a future display and touchscreen port; do not use it for installation.
