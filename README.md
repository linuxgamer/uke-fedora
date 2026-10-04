# uke-linux-port

Порт **Nura (postmarketOS)** на **Xiaomi Pad 7** (кодовое имя `uke`, SoC `SM7675`
Snapdragon 7+ Gen 3) с **mainline-ядром**. Загрузка — через стоковую Android
boot-цепочку (ABL), без второго загрузчика и без UEFI. Сборка — `pmbootstrap` +
device-пакеты Nura.

Статус: **исследование и подготовка**. Устройства пока нет.

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
| [`todo.md`](todo.md) | ближайшие задачи офлайн-фазы |

## Layout

| Путь | Содержимое |
|---|---|
| `docs/` | исследование, план, prior art |
| `kernel/` | mainline-ядро: база, патчи, DTS, конфиг, скрипты |
| `boot/` | упаковка `boot`/`init_boot`, cmdline, bootconfig, флеш-скрипты |
| `device/` | `deviceinfo`, udev, UCM, списки firmware, раскладка разделов |
| `pmos/` | пакеты Nura (APKBUILD) и конфиг `pmbootstrap` |
| `tools/` | host-скрипты (извлечение firmware, сбор логов) |
| `references/` | клоны доноров (gts9wifi и др.) |

`kernel/` и `device/` — источники; `pmos/` упаковывает их в пакеты Nura.

## Выбранная стратегия

- **Ядро:** форк [palawan-mainline](https://codeberg.org/palawan-mainline/linux)
  (`palawan/v7.2-rc2`) + патч [ztsubaki](https://github.com/ztsubaki/uke-linux)
  (USB/clock/SMMU/simplefb). Обоснование — `docs/PRIOR-ART.md`.
- **Загрузка:** стоковый ABL; ядро в `boot.img`, initramfs в `init_boot.img`,
  `vendor_boot`/`dtbo` не трогаем. Так уже заведён simplefb на реальном железе.
- **Rootfs:** `userdata`.
- **Сборка:** `pmbootstrap` + `device-xiaomi-uke` / `linux-postmarketos-qcom-sm7675` /
  `firmware-xiaomi-uke`.

## Ключевые источники

- palawan-mainline: <https://codeberg.org/palawan-mainline/linux>
- ztsubaki/uke-linux (доказанный bring-up): <https://github.com/ztsubaki/uke-linux>
- MCC45TR/uke-linux (план/чек-лист): <https://github.com/MCC45TR/uke-linux>
- Вики Nura: <https://wiki.nura.eco/wiki/Xiaomi_Pad_7_(xiaomi-uke)>
