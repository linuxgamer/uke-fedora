# Build Guide

The supported path is Linux v6.12 from `build/ztsubaki/`. The Palawan 7.2 tree in
`references/archive/palawan-7.2/` is reference material and is not expected to boot.

## Host Requirements

Install `docker`, `qemu-user-static-binfmt`, `clang`, `llvm`, `lld`, `bc`, `dtc`,
`pahole`, `flex`, `bison`, `lz4`, `cpio`, and `python3`.

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

Build `boot.img`, `init_boot.img`, and the stock-DT-derived `dtbo.img` using the
commands documented in the local ztsubaki image Makefile. The resulting artifacts
belong in `build/ztsubaki/dist/`.

The supported layout is:

- `boot.img`: `Image.gz` with an appended DTB and an AVB hash footer.
- `init_boot.img`: LZ4 busybox initramfs with an AVB hash footer; partition size
  is 8 MiB.
- `dtbo.img`: stock DTBO transformed for the v6.12 driver bindings.
- `vendor_boot` and `vbmeta`: leave the stock images untouched.

The root command line uses UUID `19364720-0ee1-4715-b30a-51a47d4a814c`.

## 3. Fedora Rootfs

Build the Fedora 44 `@core` rootfs:

```sh
sudo DNF_FORCEARCH=aarch64 DNF_REPOSDIR="$PWD/rootfs/fedora-repos" \
    ./rootfs/build-rootfs.sh
```

Create a 3 GiB raw ext4 image suitable for ABL fastboot:

```sh
rootfs/mk-internal-storage-fastboot.sh 3
```

This produces `build/fedora/uke-rootfs.img`. It uses UUID
`19364720-0ee1-4715-b30a-51a47d4a814c` and label `uke_root`.

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
