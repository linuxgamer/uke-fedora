# План: Nura на Xiaomi Pad 7 (`uke`)

Цель: рабочая Nura (postmarketOS) на Xiaomi Pad 7 с mainline-ядром, загрузка через
стоковую Android boot-цепочку, сборка через `pmbootstrap` + device-пакеты.
UEFI (Project Aloha) не используется.

**База ядра:** форк `palawan-mainline` (`palawan/v7.2-rc2`) + патч `ztsubaki`
(USB/clock/SMMU/simplefb). Обоснование выбора — [`PRIOR-ART.md`](PRIOR-ART.md).

Принципы:
- Не трогаем XBL / ABL / TZ / modem / DSP / GPT / `persist` / `secure`/`radio` firmware.
- Один эксперимент — одно изменение. Всегда остаётся загружаемый стоковый слот.
- Каждый результат фиксируется: хеши образов, профиль прошивки, слот, логи, дата.

---

## Структура репозитория

```
uke-linux-port/
├── docs/           # RESEARCH.md, PLAN.md, PRIOR-ART.md
├── kernel/         # mainline-ядро: база, патчи, DTS, конфиг
│   ├── config/     # config-фрагменты
│   ├── dts/        # uke.dts и оверлеи
│   ├── patches/    # серия патчей (из ztsubaki + свои)
│   └── scripts/    # fetch-base.sh, build.sh
├── boot/           # упаковка boot/init_boot, cmdline, bootconfig
├── device/         # deviceinfo, udev, UCM, списки firmware, раскладка
├── pmos/           # пакеты Nura (APKBUILD) + pmbootstrap
├── tools/          # host-скрипты (извлечение firmware, логи)
└── references/     # клоны доноров (gts9wifi и др.)
```

`kernel/` и `device/` — источники; `pmos/` упаковывает их для Nura.

---

## Открытые технические вопросы (решить в фазе 0–1)

1. **Куда класть mainline DTB.** В Android boot image v4 нет поля DTB (оно ушло в
   `vendor_boot`). Варианты: (а) заменить `vendor_boot` своим DTB + минимальный ramdisk;
   (б) использовать `dtbo`/appended DTB; (в) встроить DTB в образ ядра.
   ztsubaki обошёл это, оставив `vendor_boot`/`dtbo` нетронутыми. Надо понять, какой DTB
   реально попадает в mainline и как передать наш `uke.dtb`.
2. **Как pmbootstrap шьёт ядро на A/B GKI-устройстве.** Стандартный `flash_kernel` кладёт
   kernel+initramfs в один `boot.img`. ABL `uke` может ожидать ядро в `boot`, а ramdisk — в
   `init_boot`. Проверить, примет ли ABL совмещённый образ, или нужно разделять.
3. **Где будет rootfs.** Кандидат — `userdata` (переформатируется). Учесть A/B и dynamic `super`.
4. **Логирование без UART.** Пути: simplefb-консоль (доказано), pstore/ramoops,
   USB gadget network из initramfs (в pmOS есть `usb` feature).

---

## Фаза 0 — Офлайн-подготовка (устройства не требуется)

Цель: к моменту появления планшета иметь собранный инструментарий, исходники и черновики пакетов.

- [ ] Развернуть `pmbootstrap` на хосте (Linux, ≥ 20 ГБ на разделе, лучше 80+ ГБ).
- [ ] Скачать все три прошивочных профиля (CN / Global / Turkey), посчитать SHA-256,
      извлечь `boot`, `init_boot`, `vendor_boot`, `dtbo`, `vbmeta`, `super`, `persist`
      (только чтение). Инструменты: `unpack_bootimg`, `mkdtboimg`, `simg2img`, `lpunpack`,
      `avbtool`, `debugfs`.
- [ ] Извлечь и декомпилировать DTB (из `vendor_boot`) и DTBO; получить таблицу
      `compatible → драйвер → статус`.
- [ ] Собрать `modules.load`, `modules.dep`, vermagic и пути firmware из `vendor_dlkm` / `system_dlkm`.
- [ ] Изучить downstream DTS: MiCode `uke-sm8635.dtsi`, display/camera device tree, LineageOS uke.
- [ ] Клонировать и разобрать `ztsubaki/uke-linux` (патчи 6.12, simplefb, USB) и доки.
- [ ] Клонировать `palawan-mainline/linux` (ветка `palawan/v7.2-rc2`), изучить `lamma.dtsi`
      и найти, что уже есть для SM7675.
- [ ] Собрать baseline: palawan-форк + arm64 defconfig (проверить, что компилируется).
- [ ] Завести черновики пакетов в `pmos/`:
      `device-xiaomi-uke`, `linux-postmarketos-qcom-sm7675`, `firmware-xiaomi-uke`.
- [ ] Завести `device/` черновик board-DTS `sm7675-xiaomi-uke.dts` на базе downstream.
- [ ] Определиться с ядром: форк palawan сейчас, форвард-порт в upstream по мере мержа `lamma`.

**Гейт фазы 0:** собранный baseline-кернел + черновики пакетов + извлечённые DTB/DTBO/модули.
Без устройства дальше не двигаемся.

---

## Фаза 1 — Первый свет: mainline + simplefb-консоль (нужно устройство)

Цель: повторить успех ztsubaki — увидеть консоль на экране.

- [ ] Разблокировать bootloader (Xiaomi Mi Unlock; учесть срок ожидания и регион).
- [ ] Снять `fastboot getvar all`, `getvar unlocked`, `getvar current-slot`; сохранить.
- [ ] Забэкапить **все** разделы стока (особенно `persist`, `boot`, `vendor_boot`,
      `init_boot`, `dtbo`, `vbmeta`). Слот `a` — неприкосновенный recovery-базис.
- [ ] Собрать минимальное mainline-ядро с uke-DTS + built-in `simplefb`/`fbcon`.
- [ ] Упаковать: mainline kernel → `boot.img`; минимальный initramfs → `init_boot.img`;
      `vendor_boot`/`dtbo` пока не трогать.
- [ ] Прошить и получить консоль; сохранить `dmesg`, `/proc/cmdline`, runtime DTB.
- [ ] Настроить запасной лог-канал: pstore/ramoops и/или USB gadget network.

**Гейт:** стабильный вывод simplefb-консоли и сохранённый лог первого запуска.

---

## Фаза 2 — Nura: initramfs + rootfs (нужно устройство)

- [ ] Собрать initramfs Nura под mainline; решить вопрос совмещённого/раздельного `boot.img`
      (см. открытый вопрос 2).
- [ ] Разложить rootfs на `userdata`; загрузка до консоли Nura.
- [ ] Проверить работу `pmbootstrap flasher flash_kernel` / `flash_rootfs` на `uke`.
- [ ] Подтвердить USB gadget (telnet/SSH через USB net) как основной канал отладки.
- [ ] Довести до запуска UI-шелла (Weston/Phosh/GNOME — по выбору).

**Гейт:** Nura грузится в консоль/шелл с внутреннего UFS.

---

## Фаза 3 — Базовое железо

- [ ] Storage: UFS read-only → read-write, стабильность.
- [ ] USB: dwc3 + eUSB2 PHY/repeater, host/gadget, reconnect.
- [ ] Display: DRM/panel (dual DSI, KTZ8866 backlight), режимы 30–144 Гц.
- [ ] Touch: Novatek NT36532, все 4 ориентации, suspend/resume.
- [ ] Кнопки power/volume, hall/крышка.
- [ ] CPUfreq, thermal, RTC/watchdog, базовый suspend.

---

## Фаза 4 — Связь и мультимедиа

- [ ] GPU: Adreno 732, freedreno/DRM, firmware zap/GMU, Mesa Turnip.
- [ ] Wi-Fi/BT: WCN6750 (в mainline помечено ❌ — самый тяжёлый пункт).
- [ ] Audio: WCD/WSA/усилители, ALSA UCM, PipeWire, DSP-протекция.
- [ ] Датчики: IMU, ALS, магнитометр, SAR — определить реальную популяцию, mounting matrix.
- [ ] Батарея/зарядка: fuel gauge, PD/QC, thermal policy.
- [ ] Камеры: определение сенсоров, libcamera, ISP/CAMSS.

---

## Фаза 5 — Полировка и upstream

- [ ] Suspend/resume ≥ 100 циклов, энергопотребление, стабильность 24–72 ч.
- [ ] Локализация board-DTS → palawan-mainline / upstream Linux.
- [ ] Оформление device-пакетов для pmaports (с учётом AI-политики Nura — писать самостоятельно).
- [ ] Документация установки/отката, wiki-страница устройства.

---

## Источники для пиннинга

| Что | Откуда | Зачем |
|---|---|---|
| palawan-mainline/linux | `codeberg.org/palawan-mainline/linux` (`palawan/v7.2-rc2`) | база mainline |
| palawan-mainline/u-boot | `codeberg.org/palawan-mainline/u-boot` | справка по загрузке (не обязателен) |
| ztsubaki/uke-linux | `github.com/ztsubaki/uke-linux` (`master`) | доказанный bring-up, патчи 6.12 |
| MCC45TR/uke-linux | `github.com/MCC45TR/uke-linux` | чек-лист, `DEVICE-STATUS.md` |
| MiCode kernel_devicetree | `github.com/MiCode/kernel_devicetree` | downstream uke DTS |
| Uke-resources/device_xiaomi_uke | `github.com/Uke-resources/device_xiaomi_uke` | список блобов |
| gts9wifi-fedora | `github.com/nacht20-de/gts9wifi-fedora` | референс boot-бандла |
| pmaports | `gitlab.postmarketos.org/postmarketOS/pmaports` | структура device-пакетов |

---

## Риски

| Риск | Митигация |
|---|---|
| Wi-Fi/BT в mainline отсутствует | не блокер P0; рассчитывать на USB-Ethernet/USB-net |
| Нет UART, нет SD | simplefb + pstore + USB gadget net с первого дня |
| Сложный/региональный анлок bootloader | проверить до покупки/начала; CN-ROM анлочится тяжелее |
| AVB отвергает кастомный `boot`/`init_boot` | проверять только на разблокированном загрузчике |
| DTB не доходит до mainline | решить открытый вопрос 1 в фазе 0–1 |
| AI-политика Nura | финальные патчи для pmaports писать самостоятельно |
