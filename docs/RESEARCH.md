# Исследование: Nura (postmarketOS) на Xiaomi Pad 7 (`uke`)

Собрано: 2026-10-03. Все ключевые источники в конце файла.

Цель проекта: запустить **Nura (postmarketOS)** на **Xiaomi Pad 7** с **mainline-ядром**,
используя **стоковую Android boot-цепочку** (ABL) и **pmbootstrap** с device-пакетами.
UEFI (Project Aloha) сознательно **не используется**.

---

## 1. Устройство

| Параметр | Значение |
|---|---|
| Кодовое имя | `uke` |
| Модели | Xiaomi Pad 7; POCO Pad X1 (тот же таргет). **Не** совместимы: Pad 7 Pro (`muyu`), Pad 5 (`nabu`) |
| SoC | Qualcomm **SM7675** Snapdragon 7+ Gen 3 |
| Внутренние имена | `cliffs7` / `lamma` (HLOS `cliffs7`), семейство `pineapple`, база SM7550 |
| Родственный SoC | SM8635 (cliffs / palawan), почти идентичен, другие частоты и LLCC |
| CPU | 1× 2.8 ГГц Cortex-X4 + 4× 2.6 ГГц A720 + 3× 1.9 ГГц A520 |
| GPU | Adreno 732 (950 МГц) |
| Экран | 11.2" LCD 3200×2136 @ 144 Гц, варианты панелей CSOT / TM, dual DSI, 2× KTZ8866 backlight |
| Память | 8 / 12 ГБ LPDDR5X |
| Накопитель | 128 ГБ UFS 3.1 / 256 ГБ UFS 4.0 |
| Тачскрин | Novatek NT36532 (`NVT-ts-spi`) |
| Wi-Fi/BT | WCN6750 |
| Аудио | WCD937x/939x, WSA883x/884x, усилители CS35L41/43 (кандидаты) |
| Датчики | LSM6DSO **или** QMI8658 (IMU), QMC6308 (магнитометр), SIP1328 / STK3BCX (ALS), SX937X (SAR) |
| Камеры | задняя OV13B10 (13 МП, кандидат), фронтальная 8 МП (идентичность не выяснена) |
| Батарея | 8850 мА·ч, зарядка до 45 Вт |
| Клавиатура | Nanosic 803 (pogo) |
| PMIC | PMK8550, PM8550VS, PM8550VE, PM7550BA, PMXR2230, PMR735A |

> Идентичность части железа (камеры, датчики, панель) — **кандидаты** из DTS/блобов,
> требует подтверждения на реальном устройстве.

---

## 2. Загрузка и разделы

- A/B, 2 слота. Слот `a` — единственный подтверждённо рабочий для стока.
- Формат: **Android boot image v4**.
- Размеры: `init_boot` — 8 МиБ, `boot` / `vendor_boot` — 96 МиБ, `dtbo` — 24 МиБ.
- Стоковое ядро: `6.1.138-android14-11-g0c3d559bcd85-ab14529422` (GKI, Clang 17.0.2).
- `boot.img`: только ядро, **без** ramdisk.
- `init_boot.img`: LZ4 generic ramdisk, **без** ядра.
- `vendor_boot.img`: vendor ramdisk (34 МБ LZ4) + область DTB (1.88 МБ, несколько DTB) + bootconfig.
- `dtbo.img`: один overlay 591 817 байт.
- AVB: RSA-2048/SHA-256; проверяет `boot`, `recovery`, `dtbo`, `init_boot`, `vendor_boot`;
  dm-verity на `system`/`vendor`/`product`/`mi_ext`.
- `super` — динамический (не A/B), `userdata`, `metadata`, `misc`, `persist` (32 МиБ ext4).
- UFS: сектор 4096 байт; раскладка в `rawprogram0..5.xml`.

### Прошивочные профили (не смешивать!)

| Профиль | Версия |
|---|---|
| China | `OS3.0.302.0.WOZCNXM` |
| Global | `OS3.0.303.0.WOZMIXM` |
| Turkey (recovery OTA) | `OS3.0.303.0.WOZTRXM` |

---

## 3. Состояние mainline

- Сообщество [palawan-mainline](https://codeberg.org/palawan-mainline) ведёт форк ядра
  (`palawan/v7.1`, `palawan/v7.2-rc2`), U-Boot и пакет firmware. Есть `lamma.dtsi`.
- **Board-DTS для `uke` в mainline отсутствует** — это главная работа порта.
- Статус по вики Nura для SM7675:

| Подсистема | Статус | | Подсистема | Статус |
|---|---|---|---|---|
| CPU | ✅ | | Video | ✅ |
| UART | ✅ | | Thermal | ✅ |
| Storage (UFS) | ✅ | | Audio | 🟡 частично |
| USB | ✅ | | Wi-Fi | ❌ |
| Display | ✅ | | Bluetooth | ❌ |
| GPU | ✅ | | Modem | ❌ |
| Pinctrl / I2C / SPI | ✅ | | Camera / NPU / Suspend | ❓ |

> «✅» относится к SoC-уровню в форке, а **не** к конкретной плате `uke`.

- **Реальный успех на железе:** [ztsubaki/uke-linux](https://github.com/ztsubaki/uke-linux)
  поднял upstream **v6.12** + **simplefb-консоль** и **torch** на настоящем планшете.
  Метод: заменить ядро в `boot.img`, положить минимальный initramfs в `init_boot.img`,
  `vendor_boot`/`dtbo` **не трогать**. Это ровно наша boot-стратегия.
- Ближайшие доноры подсистем: SM8650 TB520FU, SM8550 Tab S9 — их результаты на `uke` **не переносятся**.

---

## 4. Prior art (кто что уже сделал)

| Проект | Что это | Состояние |
|---|---|---|
| [ztsubaki/uke-linux](https://github.com/ztsubaki/uke-linux) | Linux 6.12 порт, доки на китайском | **simplefb-консоль + torch на реальном железе**; USB не подтверждён |
| [MCC45TR/uke-linux](https://github.com/MCC45TR/uke-linux) | Fedora Rawhide, recovery-first + UEFI, план на 100 шагов, матрица 143 пункта | **Нет устройства, нет загружаемого образа**; ценен как чек-лист |
| [MCC45TR/senemos-uke-kernel-mainline](https://github.com/MCC45TR/senemos-uke-kernel-mainline) | Ядро, база Linux 7.2.8 | Нет релиза |
| [MCC45TR/uke-project-aloha](https://github.com/MCC45TR/uke-project-aloha) | UEFI-платформа | Нет образа; **не используем** |
| [MCC45TR/orangefox_device_xiaomi_uke](https://github.com/MCC45TR/orangefox_device_xiaomi_uke) | OrangeFox recovery | Экспериментальная альфа, без тестов |
| [Thanick50/ofox_device_xiaomi_uke](https://github.com/Thanick50/ofox_device_xiaomi_uke) | OrangeFox | Сломанное форматирование F2FS |
| [Uke-resources/device_xiaomi_uke](https://github.com/Uke-resources/device_xiaomi_uke) | Список проприетарных файлов | Источник имён firmware/модулей |
| [MiCode/kernel_devicetree](https://github.com/MiCode/kernel_devicetree) | Downstream DTS (`uke-sm8635.dtsi`) | Ключевой источник для board-DTS |
| LineageOS uke (unofficial) | Android device tree | Источник DTS/config |

---

## 5. Референс загрузки: gts9wifi (Samsung Tab S9, Fedora)

`references/gts9wifi-fedora-linux/` — не целевая ОС, но **та же boot-стратегия**:

- Стоковая Android boot-цепочка Samsung загружает **mainline kernel + board DTB + dracut initramfs**
  из `boot`/`init_boot`/`vendor_boot`, без второго загрузчика.
- `vendor_boot` несёт рабочий DTB и cmdline с `root=UUID=…`; initramfs монтирует root по UUID.
- `dtbo` намеренно невалиден → bootloader падает на appended DTB; `vbmeta` обнулён → AVB выключен.
- Rootfs на внутреннем UFS (`userdata` переформатируется).
- GPU zap/GMU firmware кладётся в initramfs (GPU probe происходит до rootfs).
- `persist` монтируется read-write (калибровки датчиков/Wi-Fi).

Полезные файлы для изучения: `boot/build-bundle.sh`, `boot/cmdline.txt`, `boot/bootconfig.txt`,
`kernel/prepare.sh`, `kernel/files/config-gts9wifi.fragment`, `rootfs/mk-internal-storage.sh`,
`tools/mkbootimg.py`.

**Различия с `uke`:** другой SoC (SM8550 vs SM7675), Samsung vs Xiaomi ABL, Fedora vs Nura.
Переносим только идею и приёмы, не код.

---

## 6. Nura / postmarketOS

- Устройства описываются пакетами в [pmaports](https://gitlab.postmarketos.org/postmarketOS/pmaports):
  - `device-xiaomi-uke` — deviceinfo, udev, UCM;
  - `linux-*` — ядро (для mainline обычно общий `linux-postmarketos-qcom-*`);
  - `firmware-xiaomi-uke` — блобы.
- Сборка/прошивка — через `pmbootstrap`.
- В pmaports **`uke` пока нет** — порт с нуля.
- ⚠️ [AI-политика Nura](https://docs.nura.eco/policies-and-processes/development/ai-policy.html)
  **запрещает принимать патчи, сделанные с помощью генеративного ИИ**. Личному порту это не мешает,
  но код нельзя будет отправить в pmaports «как есть» — нужно переписать/оформить самостоятельно.

---

## 7. Источники

- Вики Nura: `https://wiki.nura.eco/wiki/Xiaomi_Pad_7_(xiaomi-uke)`
- Вики Nura, SoC: `https://wiki.nura.eco/wiki/Qualcomm_Snapdragon_8s_Gen_3/7%2B_Gen_3_(Palawan/Lamma)`
- Гайд по портированию: `https://wiki.nura.eco/wiki/Porting_to_a_new_device`
- AI-политика: `https://docs.nura.eco/policies-and-processes/development/ai-policy.html`
- palawan-mainline: `https://codeberg.org/palawan-mainline/{linux,u-boot,firmware-qualcomm-qrd8635}`
- ztsubaki/uke-linux: `https://github.com/ztsubaki/uke-linux` (ветка `master`, доки в `docs/`)
- MCC45TR/uke-linux: `https://github.com/MCC45TR/uke-linux` (`PLAN.md`, `DEVICE-STATUS.md`)
- MiCode DTS: `https://github.com/MiCode/kernel_devicetree/blob/.../qcom/uke-sm8635.dtsi`
- gts9wifi: `https://github.com/nacht20-de/gts9wifi-fedora` (локально в `references/`)
