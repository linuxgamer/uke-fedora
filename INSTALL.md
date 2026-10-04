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
    --image build/uke-build/arch/arm64/boot/Image \
    --dtb   build/uke-build/arch/arm64/boot/dts/qcom/sm7675-xiaomi-uke.dtb \
    --initramfs <initramfs.gz> \
    --cmdline boot/cmdline.txt --bootconfig boot/bootconfig.txt \
    --out build/fedora-boot
```

## 2. Rootfs
```sh
docker run --rm --network host -v "$PWD:/work" -w /work \
    quay.io/fedora/fedora:44 ./rootfs/build-rootfs.sh
```

## 3. Прошивка
- **fastboot**: `boot`, `init_boot`, `vendor_boot`, `dtbo`, `vbmeta` (A/B: слот `a`).
- **TWRP**: zip-инсталлер (позже).
- `userdata`: ext4 с UUID из `boot/cmdline.txt`, распаковка rootfs.

## 4. Первая загрузка
- Консоль `ttyMSM0`, USB-net `172.16.42.1` (SSH).

## Откат
Стоковая прошивка (Global 3.0.303.0.WOZMIXM) или TWRP Format Data.
