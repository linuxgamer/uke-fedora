# Пивот на Fedora

## Почему

pmOS/Nura упёрся в два блокера:
1. **Регион**: `mirror.nura.eco` троттлится из РФ (~1 КБ/с), пакеты не скачать.
   Прокси/VPN нет; он был бы нужен и для обновлений готовой системы.
2. **AI-политика**: Nura запрещает AI-сгенерированные патчи в upstream.

Fedora обходит оба: есть российские зеркала (Яндекс и др.), политика мягче.
Апстрим не важен.

## Что переиспользуем

Ядро и драйверы **OS-агностичны** — они остаются:
- `kernel/dts/sm7675-xiaomi-uke.dts`
- `kernel/drivers/panel-xiaomi-o82.c`, `kernel/drivers/nt36532-uke.c`
- `kernel/patches/*`, `kernel/config/uke.fragment`
- `kernel/scripts/*` (сборка ядра)

Заменяется только слой упаковки: `pmos/` → `fedora/`.

## Архитектура (по мотивам gts9wifi)

- **Ядро**: наш mainline (palawan 7.2 + uke DTS + драйверы). `Image` + модули + DTB.
- **Загрузка**: стоковая ABL. Бандл Android boot-image-v4:
  - `boot`: `Image.gz` + appended DTB, пустой cmdline;
  - `init_boot`: пустой generic ramdisk (8 МиБ);
  - `vendor_boot`: полный dracut-initramfs (platform fragment) + DTB + cmdline + bootconfig;
  - `dtbo`: невалиден → ABL берёт appended DTB;
  - `vbmeta`: verification disabled (flags 2).
- **Rootfs**: Fedora aarch64 на `userdata` (ext4, root=UUID). Первый этап — `@core`
  (консоль/USB-net для отладки), затем GNOME/Plasma.

## Инструменты хоста (x86_64)

- `docker` + `qemu-user-static-binfmt` (эмуляция arm64) → сборка rootfs в
  `quay.io/fedora/fedora:44` с `--platform linux/arm64 --network host`.
- Fedora-зеркала из РФ доступны (mirror.yandex.ru).

## Этапы

1. [x] Адаптирован boot-бандл; собирается с нашим `Image` + DTB.
2. [ ] dracut-initramfs с модулями (UFS, USB-gadget, simplefb) и root=UUID.
3. [ ] Минимальный rootfs @core; загрузка в консоль/USB-net.
4. [ ] Панель/тач на железе.
5. [ ] Графика (GNOME/Plasma), звук, Wi-Fi/BT.

## Риски

- ABL uke может отличаться от Samsung: возможно, придётся оставить стоковый
  `vendor_boot`/`dtbo` (как ztsubaki), а менять только `boot`+`init_boot`.
- Установка rootfs: у пользователя crDroid recovery, не TWRP — метод прошивки
  `userdata` уточним.
