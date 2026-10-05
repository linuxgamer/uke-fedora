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
Два режима:
- **ztsubaki** (рабочий для uke): только `boot`+`init_boot`; стоковые
  `vendor_boot`/`dtbo`/`vbmeta` не трогаем. `boot/build-bundle-ztsubaki.sh`.
- **gts9wifi** (не подошёл Xiaomi ABL): все пять + невалидный `dtbo`.
  `boot/build-bundle.sh`.

```sh
boot/build-bundle.sh --image <Image> --dtb <uke.dtb> --initramfs <initramfs.img> \
    --cmdline boot/cmdline.txt --bootconfig boot/bootconfig.txt --out build/fedora-boot
```
- `boot`: `Image.gz` + appended DTB, пустой cmdline.
- `init_boot`: пустой ramdisk (8 МиБ).
- `vendor_boot`: полный initramfs + DTB + cmdline + bootconfig.
- `dtbo`: невалиден → ABL берёт appended DTB.
- `vbmeta`: flags 2. Размеры под разделы uke (96/8/96/24 МиБ, 128 КиБ).

## 3a. ztsubaki-путь (рабочий)
Ядро upstream v6.12 + ztsubaki-патч (`references/ztsubaki-uke-linux/patches/uke/`),
сборка в `build/ztsubaki/{linux,out}`:
```sh
make -C build/ztsubaki/linux O="$PWD/build/ztsubaki/out" ARCH=arm64 LLVM=1 Image.gz
make -C build/ztsubaki/linux O="$PWD/build/ztsubaki/out" ARCH=arm64 LLVM=1 modules
```
- `boot.img`: `tools/mkbootimg.py --kernel .../Image.gz --cmdline "<min>" --header_version 4`
  + AVB hash footer (размер раздела 100663296). Cmdline: `regulator_ignore_unused
  clk_ignore_unused pd_ignore_unused console=tty0 fbcon=map:0 fbcon=font:TER16x32
  consoleblank=0 root=UUID=19364720-… rootwait rw`.
- `dtbo.img`: из стокового `dtbo.img` через `references/ztsubaki-uke-linux/images/dtbo/Makefile`
  (fdtput-правки UFS/GDSC) → `mkdtboimg create --page_size=4096`.
- `init_boot.img`: `boot/build-initramfs-usb.sh` (busybox + USB ACM + диагностика) →
  `mkbootimg.py --ramdisk` + AVB footer (8388608).

## 4. Rootfs
Два режима:
```sh
# A) host-native (быстро): dnf x86_64, scriptlets через qemu/binfmt
sudo DNF_FORCEARCH=aarch64 DNF_REPOSDIR="$PWD/rootfs/fedora-repos" ./rootfs/build-rootfs.sh

# B) в arm64 Fedora-контейнере (нативно, но требует контейнер)
docker run --rm --network host -v "$PWD:/work" -w /work \
    quay.io/fedora/fedora:44 ./rootfs/build-rootfs.sh
```
- Fedora 44 `@core`, overlay, модули, firmware. Итог: `build/fedora/uke-fedora-rootfs.tar.gz` (~460 МБ).
- Host-режим: `rootfs/fedora-repos/` (repo-файлы Яндекс-зеркала + GPG).

### 4a. Прошивка rootfs в userdata (важно!)
```sh
rootfs/mk-internal-storage-fastboot.sh 3      # → build/fedora/uke-rootfs.img (3 ГБ, raw)
```
- Размер **3 ГБ**: у ABL `fastboot flash` лимит ~4 ГБ (дальше образ обрезается).
- `-E lazy_itable_init=0,lazy_journal_init=0` — метаданные инициализированы.
- **Перед прошивкой занулить раздел** (ABL пропускает нулевые блоки → остаётся мусор):
  ```sh
  # в initramfs (или fastboot erase userdata):
  dd if=/dev/zero of=/dev/sda32 bs=1M count=4096 conv=fsync
  # fastboot:
  fastboot flash userdata build/fedora/uke-rootfs.img   # raw, не sparse!
  ```
- UUID root: `19364720-0ee1-4715-b30a-51a47d4a814c`, метка `uke_root`.


## Требования к хосту
`docker` + `qemu-user-static-binfmt` (arm64-эмуляция), `bc`, `clang`, `llvm`,
`lld`, `dtc`, `pahole`, `flex`, `bison`, `lz4`, `cpio`, `python3`.
