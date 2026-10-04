# uke-linux-port

Порт **Nura (postmarketOS)** на **Xiaomi Pad 7** (кодовое имя `uke`, SoC `SM7675`
Snapdragon 7+ Gen 3) с **mainline-ядром**. Загрузка — через стоковую Android
boot-цепочку (ABL), без второго загрузчика и без UEFI. Сборка — `pmbootstrap` +
device-пакеты Nura.

Статус: **ядро, initramfs и boot-бандл собираются**; rootfs Fedora — следующий шаг;
прошивка — вручную (fastboot/TWRP).

## Документы

| Документ | Содержимое |
|---|---|
| [`docs/RESEARCH.md`](docs/RESEARCH.md) | железо, разделы, состояние mainline, источники |
| [`docs/PLAN.md`](docs/PLAN.md) | поэтапный план и открытые техвопросы |
| [`docs/PRIOR-ART.md`](docs/PRIOR-ART.md) | разбор palawan-mainline / ztsubaki / MCC45TR |
| [`docs/BRINGUP-NOTES.md`](docs/BRINGUP-NOTES.md) | gap-анализ palawan 7.2 vs ztsubaki, что уже есть |
| [`docs/STOCK-DTB.md`](docs/STOCK-DTB.md) | разбор стоковой прошивки: DTB/DTBO, железо uke |
| [`docs/STOCK-SUPER.md`](docs/STOCK-SUPER.md) | `super.img`: модули, fstab, firmware-раскладка |
| [`docs/PANEL-TOUCH.md`](docs/PANEL-TOUCH.md) | панель O82 и тач NT36532 |
| [`docs/FEDORA-PIVOT.md`](docs/FEDORA-PIVOT.md) | обоснование и план перехода на Fedora |
| [`docs/BUILD.md`](docs/BUILD.md) | пайплайн сборки (kernel → initramfs → bundle → rootfs) |
| [`docs/Known-Issues.md`](docs/Known-Issues.md) | реестр проблем |
| [`docs/Hardware-Notes.md`](docs/Hardware-Notes.md) | заметки по подсистемам |
| [`docs/PORT-KIT.md`](docs/PORT-KIT.md) | инвентарь извлечения из стока |
| [`INSTALL.md`](INSTALL.md) | установка (Fedora, TWRP/fastboot) |
| [`TODO.md`](TODO.md) | задачи |

## Layout

| Путь | Содержимое |
|---|---|
| `kernel/` | mainline-ядро: `files/` (DTS, драйверы, config-mainline+fragment), `patches/`, `prepare.sh`, `build.sh`, `kernel.spec` |
| `boot/` | Android boot-image-v4 бандл (`build-bundle.sh`), initramfs (`build-initramfs.sh`), dracut |
| `rootfs/` | Fedora rootfs (`build-rootfs.sh`), `mk-internal-storage.sh`, `mk-sd-card.sh`, overlay |
| `tools/` | mkbootimg, avbtool, make-twrp-zip, извлечение стока, конвертеры |
| `.github/workflows/` | CI: kernel, rootfs, boot-bundle, full-set |
| `docs/` | исследование, план, prior art |
| `references/` | клоны доноров (не коммитятся) |
| `attic/` | старые наработки (pmOS-пакеты) |

## Выбранная стратегия

- **Ядро:** форк [palawan-mainline](https://codeberg.org/palawan-mainline/linux)
  (`palawan/v7.2-rc2`) + патч [ztsubaki](https://github.com/ztsubaki/uke-linux)
  (USB/clock/SMMU/simplefb). Обоснование — `docs/PRIOR-ART.md`.
- **Загрузка:** стоковый ABL; ядро в `boot.img`, initramfs в `init_boot.img`,
  `vendor_boot`/`dtbo` не трогаем. Так уже заведён simplefb на реальном железе.
- **Rootfs:** `userdata` (ext4, root=UUID).
- **Дистрибутив:** **Fedora aarch64** (пивот с pmOS/Nura — см.
  [`docs/FEDORA-PIVOT.md`](docs/FEDORA-PIVOT.md); из-за региональных ограничений
  и AI-политики). Пайплайн — по мотивам `gts9wifi-fedora`, код в `fedora/`.
- **Загрузка:** стоковый ABL, Android boot-image-v4 бандл
  (`boot`/`init_boot`/`vendor_boot`/`dtbo`/`vbmeta`), `dtbo` невалиден → appended DTB.

## Ключевые источники

- palawan-mainline: <https://codeberg.org/palawan-mainline/linux>
- ztsubaki/uke-linux (доказанный bring-up): <https://github.com/ztsubaki/uke-linux>
- MCC45TR/uke-linux (план/чек-лист): <https://github.com/MCC45TR/uke-linux>
- Вики Nura: <https://wiki.nura.eco/wiki/Xiaomi_Pad_7_(xiaomi-uke)>
