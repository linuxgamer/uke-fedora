# uke-linux-port

Порт **Nura (postmarketOS)** на **Xiaomi Pad 7** (кодовое имя `uke`, SoC `SM7675`
Snapdragon 7+ Gen 3) с **mainline-ядром**. Загрузка — через стоковую Android
boot-цепочку (ABL), без второго загрузчика и без UEFI. Сборка — `pmbootstrap` +
device-пакеты Nura.

Статус: **ядро и драйверы собираются; устройство получено (разблокирован bootloader)**.
Дальше — `pmbootstrap` и первая загрузка.

## Документы

| Документ | Содержимое |
|---|---|
| [`docs/RESEARCH.md`](docs/RESEARCH.md) | железо, разделы, состояние mainline, источники |
| [`docs/PLAN.md`](docs/PLAN.md) | поэтапный план и открытые техвопросы |
| [`docs/PRIOR-ART.md`](docs/PRIOR-ART.md) | разбор palawan-mainline / ztsubaki / MCC45TR |
| [`docs/BRINGUP-NOTES.md`](docs/BRINGUP-NOTES.md) | gap-анализ palawan 7.2 vs ztsubaki, что уже есть |
| [`docs/STOCK-DTB.md`](docs/STOCK-DTB.md) | разбор стоковой прошивки: DTB/DTBO, железо uke |
| [`docs/STOCK-SUPER.md`](docs/STOCK-SUPER.md) | `super.img`: модули, fstab, firmware-раскладка |
| [`docs/PANEL-TOUCH.md`](docs/PANEL-TOUCH.md) | панель O82 (сделано) и план по тачу NT36532 |
| [`pmos/README.md`](pmos/README.md) | пакеты Nura и порядок сборки/установки |
| [`etc/TODO.md`](etc/TODO.md) | ближайшие задачи |

## Layout

| Путь | Содержимое |
|---|---|
| `docs/` | исследование, план, prior art |
| `kernel/` | mainline-ядро: база, патчи, DTS, драйверы, скрипты |
| `pmos/` | пакеты Nura (APKBUILD) |
| `device/` | `deviceinfo`, udev, UCM, списки firmware |
| `etc/boot/` | `cmdline`, `bootconfig` |
| `etc/tools/` | host-скрипты (извлечение стока, firmware, конвертеры) |
| `etc/references/` | клоны доноров (не коммитятся) |
| `etc/TODO.md` | задачи |

`kernel/` и `device/` — источники; `pmos/` упаковывает их в пакеты Nura.

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
