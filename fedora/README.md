# Fedora на Xiaomi Pad 7 (uke)

Федеральный (Fedora) порт: mainline-ядро + Fedora aarch64 userland, загрузка через
**стоковую Android boot-цепочку** (ABL). Никакого второго загрузчика. Root — на
внутреннем UFS (`userdata`).

Подход и пайплайн перенесены из эталона
[gts9wifi-fedora](https://github.com/nacht20-de/gts9wifi-fedora) (Samsung Tab S9),
адаптированы под uke.

## Компоненты

| Путь | Что |
|---|---|
| `kernel/` (корень репо) | наше mainline-ядро: DTS, драйверы панели/тача, патчи, `build-kernel.sh` |
| `fedora/boot/build-bundle.sh` | Android boot-image-v4 бандл (boot/init_boot/vendor_boot/dtbo/vbmeta) |
| `fedora/boot/cmdline.txt`, `bootconfig.txt` | kernel cmdline (root=UUID) и vendor_boot bootconfig |
| `fedora/rootfs/build-rootfs.sh` | минимальный Fedora aarch64 rootfs (@core) |
| `fedora/rootfs/overlay/` | device-specific файлы (hostname, fstab, NM, systemd) |
| `fedora/tools/` | `mkbootimg.py`, `avbtool` (из gts9wifi) |

## Сборка

```sh
# 1. Ядро (Image + модули + DTB)
kernel/scripts/build-kernel.sh

# 2. Boot-бандл
fedora/boot/build-bundle.sh \
    --image build/uke-build/arch/arm64/boot/Image \
    --dtb   build/uke-build/arch/arm64/boot/dts/qcom/sm7675-xiaomi-uke.dtb \
    --initramfs <dracut-initramfs.gz> \
    --cmdline fedora/boot/cmdline.txt \
    --bootconfig fedora/boot/bootconfig.txt \
    --out build/fedora-boot

# 3. Rootfs (в arm64 Fedora-контейнере; хост x86_64 + qemu binfmt)
docker run --rm --network host -v "$PWD:/work" -w /work \
    quay.io/fedora/fedora:44 ./fedora/rootfs/build-rootfs.sh
```

## Загрузка (делает пользователь, НЕ автоматизировано)

- Прошивка бандла: `boot`/`init_boot`/`vendor_boot`/`dtbo`/`vbmeta` через
  **fastboot** (пользователь) или recovery.
- Rootfs: форматирование `userdata` в ext4 с UUID из `cmdline.txt` и распаковка
  rootfs. **Уничтожает Android-данные.**
- `dtbo` намеренно невалиден → ABL использует appended DTB из `boot`.

## Статус

- [x] Boot-бандл собирается (проверено: правильные размеры разделов, gzip-kernel + DTB).
- [ ] initramfs (dracut) с нужными модулями.
- [ ] Rootfs собирается и грузится.
- [ ] Панель/тач/дальше — на железе.

См. [`../docs/FEDORA-PIVOT.md`](../docs/FEDORA-PIVOT.md).
