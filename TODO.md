# TODO

Пайплайн: [`docs/BUILD.md`](docs/BUILD.md) · Проблемы: [`docs/Known-Issues.md`](docs/Known-Issues.md) ·
Пивот: [`docs/FEDORA-PIVOT.md`](docs/FEDORA-PIVOT.md) · Установка: [`INSTALL.md`](INSTALL.md).
База ядра: palawan-mainline `palawan/v7.2-rc2` (`0d9f7fdf7`) + uke-специфика.

## Сделано
- [x] Исследование, план, prior art, gap-анализ, разбор стока (`docs/`).
- [x] Board-DTS `kernel/files/sm7675-xiaomi-uke.dts` (lamma + O82 + NT36532).
- [x] Драйверы: `panel-xiaomi-o82.c` (dual-DSI DSC), `nt36532-uke.c` (протокол + fw update).
- [x] 2 фикса базы palawan (`kernel/patches/`).
- [x] Ядро: `kernel/build.sh` → `Image` + DTB + 1643 модуля, `KVER=7.2.0-rc2-uke`.
- [x] Initramfs: `boot/build-initramfs.sh` (dracut в arm64-контейнере, USB-net).
- [x] Boot-бандл: `boot/build-bundle.sh` (boot/init_boot/vendor_boot/dtbo/vbmeta).
- [x] Полный бэкап планшета (`~/uke-backup`, `tools/backup-device.sh`).
- [x] Пивот на Fedora, реорганизация под раскладку gts9wifi.
- [x] Удалён pmbootstrap (архив pmOS в `attic/`).

## Следующее
- [ ] Rootfs: собрать минимальный Fedora `@core` (`rootfs/build-rootfs.sh`).
- [ ] `mk-internal-storage.sh` (TWRP): формат `userdata` + распаковка rootfs.
- [ ] Прошивка boot-бандла (пользователь, fastboot/TWRP).
- [ ] Первая загрузка: консоль `ttyMSM0` / USB-net `172.16.42.1`.
- [ ] Панель: проверить dual-DSI/DSC на железе (issues 1–3).
- [ ] Тач: проверить протокол (issue 4).
- [ ] WCD939x USB-роут (issue 5).
- [ ] Wi-Fi WCN6750 (issue 6), аудио (7), датчики/зарядка (8).
- [ ] Графика (GNOME/Plasma) после консоли.

## Открытые техвопросы
- Примет ли ABL uke наш `vendor_boot`/`dtbo` (issue 9); иначе — стоковый vendor_boot + overlay.
- Нужны ли USB handoff quirks (GCC clock hold, SMMU, GDSC) поверх palawan.
- Покрывает ли generic `qcom,snps-dwc3` palawan.
