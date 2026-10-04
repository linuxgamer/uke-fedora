# Сборка (пайплайн в стиле gts9wifi)

Всё собирается на хосте; userland — Fedora, ядро — mainline (palawan + uke).

## 1. Ядро
```sh
kernel/build.sh
```
- `kernel/prepare.sh` — клонирует базу `palawan-mainline` (`build/src/linux-palawan`),
  создаёт worktree `build/linux-uke`, применяет `kernel/patches/series`, кладёт
  DTS/драйверы из `kernel/files/`, коммитит (чистый KVER).
- Сборка: `ARCH=arm64 LLVM=1 LOCALVERSION=-uke` → `Image` + DTB + модули.
- Итог: `KVER=7.2.0-rc2-uke`, `build/uke-build/arch/arm64/boot/Image`,
  `build/uke-modules/usr/lib/modules/<kver>`.

## 2. Initramfs (dracut)
```sh
boot/build-initramfs.sh
```
- В arm64 Fedora-контейнере (`docker --platform linux/arm64 --network host`).
- `boot/dracut/dracut.conf.d/uke.conf`: `hostonly=no`, USB-gadget драйверы,
  GPU firmware в `install_items`.
- `boot/dracut/90uke-usbnet/`: RNDIS-gadget `172.16.42.1` для отладки до root.
- Итог: `build/initramfs.img` (~30 МБ).

## 3. Boot-бандл (Android boot-image v4)
```sh
boot/build-bundle.sh --image <Image> --dtb <uke.dtb> --initramfs <initramfs.img> \
    --cmdline boot/cmdline.txt --bootconfig boot/bootconfig.txt --out build/fedora-boot
```
- `boot`: `Image.gz` + appended DTB, пустой cmdline.
- `init_boot`: пустой ramdisk (8 МиБ).
- `vendor_boot`: полный initramfs + DTB + cmdline + bootconfig.
- `dtbo`: невалиден → ABL берёт appended DTB.
- `vbmeta`: flags 2. Размеры под разделы uke (96/8/96/24 МиБ, 128 КиБ).

## 4. Rootfs
```sh
docker run --rm --network host -v "$PWD:/work" -w /work \
    quay.io/fedora/fedora:44 ./rootfs/build-rootfs.sh
```
- Fedora 44 `@core` (первый bring-up), overlay, модули, firmware.
- Итог: `build/fedora/uke-fedora-rootfs.tar.gz`.

## Требования к хосту
`docker` + `qemu-user-static-binfmt` (arm64-эмуляция), `bc`, `clang`, `llvm`,
`lld`, `dtc`, `pahole`, `flex`, `bison`, `lz4`, `cpio`, `python3`.
