# Установка Fedora на Xiaomi Pad 7 (uke)

Краткий гайд. Порт — **bring-up**: сначала консоль/USB-net, затем графика.
Прошивка — **fastboot или TWRP** (у пользователя есть TWRP под uke).

> **Установка уничтожает данные Android** (`userdata` переформатируется).
> Бэкап: `tools/backup-device.sh`. Android восстановим из стоковой прошивки.

## Предпосылки
- Разблокированный bootloader, TWRP в recovery.
- Linux-PC с `adb`/`fastboot`.
- Артефакты: `boot/` бандл, rootfs, модули, firmware.

## 1. Ядро и boot-бандл
```sh
kernel/build.sh
boot/build-bundle.sh \
    --vmlinuz build/uke-build/arch/arm64/boot/vmlinuz.efi \
    --dtb   build/uke-build/arch/arm64/boot/dts/qcom/sm7675-xiaomi-uke.dtb \
    --initramfs <initramfs.gz> \
    --cmdline boot/cmdline.txt --bootconfig boot/bootconfig.txt \
    --out build/fedora-boot
```

## 2. Rootfs
```sh
sudo DNF_FORCEARCH=aarch64 DNF_REPOSDIR="$PWD/rootfs/fedora-repos" ./rootfs/build-rootfs.sh
```

## 3. Прошивка (ztsubaki-схема)
Меняем **только** `boot` + `init_boot`; стоковые `vendor_boot`/`dtbo`/`vbmeta`
**не трогаем** (Xiaomi ABL их не принимает — см. Known-Issues #9).
```sh
boot/build-initramfs-minimal.sh
boot/build-bundle-ztsubaki.sh \
    --vmlinuz build/uke-build/arch/arm64/boot/vmlinuz.efi \
    --dtb build/uke-build/arch/arm64/boot/dts/qcom/sm7675-xiaomi-uke.dtb \
    --init-boot build/initramfs-minimal.lz4 \
    --cmdline boot/cmdline.txt --out build/fedora-boot-z
# fastboot (активный слот a):
fastboot flash boot_a      build/fedora-boot-z/boot.img
fastboot flash init_boot_a build/fedora-boot-z/init_boot.img
```
- `userdata`: ext4 с меткой `uke_root` (initramfs находит по ней, fallback).

## 4. Первая загрузка
- Консоль `ttyMSM0`, USB-net `172.16.42.1` (SSH).

## Откат
Стоковая прошивка (Global 3.0.303.0.WOZMIXM) или TWRP Format Data.
