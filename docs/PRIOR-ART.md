# Разбор prior art: palawan-mainline, ztsubaki, MCC45TR

Три проекта решают разные задачи и **не конкурируют**, а дополняют друг друга.
Ключевое отличие — где проходит граница работы: SoC / плата / процесс.

| Проект | Кто | Цель | База | Есть железо? | Загружалось на `uke`? |
|---|---|---|---|---|---|
| **palawan-mainline** | Alexandr Zubtsov (devizure) + сообщество | Занести SM8635/SM7675 (Palawan/Lamma) в mainline Linux | upstream Linux (7.1 / 7.2-rc2) | QRD-референс, **не uke** | Нет |
| **ztsubaki/uke-linux** | ztsubaki | Личный рабочий Linux на uke, «снизу вверх» от upstream | upstream **v6.12** + патч | **Да, реальный Pad 7** | **Да** (simplefb-консоль + torch) |
| **MCC45TR/uke-linux** | MCC45TR | Fedora + recovery + UEFI, «OEM-качество», план на 100 шагов | Linux **v7.2.8** | **Нет** | Нет |

---

## 1. palawan-mainline — фундамент mainline для SoC

**Где:** `codeberg.org/palawan-mainline/{linux,u-boot,firmware-qualcomm-qrd8635}`

**Цель:** довести поддержку платформы Palawan (SM8635) / Lamma (SM7675) до уровня
upstream mainline. Это **SoC-уровень**, не конкретная плата.

**Что внутри `linux` (ветки `palawan/v7.1` — default, `palawan/v7.2-rc2`):**
- Полноценный форк ядра. Свежие коммиты (июнь 2026) — это `dt-bindings` для Palawan:
  USB dwc3, TSENS, SRAM/IMEM, LPASS-кодеки, PMIC-GLINK, AOSS-QMP, eUSB2 PHY,
  QMP USB43DP/UFS PHY, IPA, SDHCI, IPCC, ARM SMMU, PDC, interconnect OSM L3.
- `arch/arm64/boot/dts/qcom/palawan.dtsi` и `lamma.dtsi` (Lamma — «иначе
  сфьюженный» Palawan: другие частоты CPU/GPU и меньше LLCC).
- Платы — **только референсные**: `palawan-qrd.dts`, `lamma-qrd.dts`.
- PMIC-инклюды: `pm7550` (PMXR2230), `pm7550ba`, `pmr735a`, `pm8010`,
  `pm8550ve`, `pm8550vs`, `pmk8550` — ровно те, что в `uke`.
- **Board-DTS для `uke` отсутствует.** Есть только QRD.

**`u-boot`:** пустой репозиторий-заглушка (`empty: true`).
**`firmware-qualcomm-qrd8635`:** несвободные блобы для **QRD-референса**, не для uke.
Для uke firmware придётся извлекать из стоковой прошивки (как делает gts9wifi).

**Цели и ограничения:**
- Цель — upstream, а не порт планшета. Никаких board-специфичных костылей.
- Нет гарантий по панели/тачу/аудио конкретного uke.
- Wi-Fi/BT в вики Nura помечены ❌ — на уровне SoC ещё не готовы.

**Что взять:**
- **Базу ядра** (это наш mainline base вместо голого upstream).
- `palawan.dtsi` / `lamma.dtsi` и PMIC-инклюды — из них делаем `uke.dts`.
- Драйверы и bindings: clocks, pinctrl, RPMh, regulators, GDSC, NoC, SMMU,
  eUSB2, UFS PHY, display, GPU.
- Позже — форвард-порт board-DTS обратно в форк/upstream.

---

## 2. ztsubaki/uke-linux — единственный, кто реально завёл uke

**Где:** `github.com/ztsubaki/uke-linux` (ветка `master`, доки на китайском)

**Цель:** персональный, поддерживаемый из upstream Linux на uke. Явно **не** проект
по отправке в upstream. Принцип: не трогать XBL/ABL/TZ/modem/DSP/GPT/persist.

**База:** чистый **upstream v6.12** (submodule `torvalds/linux`) + **один** патч
`patches/uke/0001-uke-platform-and-usb-port.patch` (74 файла). `linux/` остаётся чистым.

**Что в патче (по подсистемам):**
- TLMM/GPIO с `gpio-reserved-ranges` (сохранить GPIO TrustZone);
- GCC + TCSRCC, clock handoff (`CLK_HOLD_STATE`), GDSC-regulator с последовательностью;
- RPMh/RSC, ARC/VRM регуляторы, proxy-consumer;
- NoC interconnect (USB пути, BCM, QoS);
- apps-SMMU handoff (`qcom,sm7675-usb-smmu`) — не сбрасывать маппинги ABL;
- EUSB2 PHY + PMIC repeater;
- DWC3 gadget (USB2 peripheral);
- WCD939x фиксированный USB2 D+/D- роут;
- bindings, Kconfig, KUnit `clk_uke_handoff`.

**Что в `images/dtbo/Makefile` (это отдельный, не менее важный артефакт):**
- Берёт **стоковый DTBO** и через `fdtput`/`fdtoverlay` правит под mainline-compatible.
- Добавляет **simplefb**: `/chosen/framebuffer@e3940000`, 3200×2136, stride 12800,
  `a8r8g8b8`, `stdout-path`, `no-map` для 43 МиБ splash-region.
- Правит torch LED (`qcom,pm8350c-flash-led`, `led-sources 1 4`);
- Настраивает USB2 peripheral-топологию, GPIO-резервы, GENI I2C, GPI DMA.

**Важное наблюдение:** ztsubaki **не пишет board-DTS с нуля**. Он использует
**стоковый DTB из `vendor_boot` + свой overlay** (4 базовых DTB). Это
«stock-DT transition profile» — быстрый путь. Полноценный standalone mainline
`uke.dts` из `palawan.dtsi` пока не сделан никем.

**Сборка:** `Makefile` + `flake.nix` (кросс aarch64 gnu + musl). Выход:
- `dist/boot.img` — ядро, Android boot image v4, AVB hash footer;
- `dist/init_boot.img` — busybox + статический C `/init` (PID 1) + USB-модули, LZ4;
- `dist/dtbo.img` — overlay.

**initramfs:** статический C `/init`, монтирует proc/sys/dev, грузит USB-модули в
фиксированном порядке, пишет в `ttyGS0`; torch как индикатор статуса.

**Артефакты (то, что обычно теряется):**
- `artifacts/device-tree/runtime/uke-runtime.dts` — runtime FDT с реального устройства;
- декомпилированные stock DTB/DTBO; списки модулей; `avb-info`; `mkbootimg-command`;
- `docs/UKE_FDT_DEVICE_LIST.md` — **379 compatible**, разбор по подсистемам и приоритетам;
- `docs/UKE_BOOTSTRAP_ROADMAP.md` — milestone-план (torch → simplefb → userspace → mainline).

**Статус:** simplefb-консоль («完美启动») и torch **подтверждены на железе**.
USB — нет; DRM, suspend, Wi-Fi, аудио, камеры — нет.

**Что взять (максимально переиспользуемо):**
1. Патч ядра `0001-uke-platform-and-usb-port.patch` — как основу USB/clock/SMMU.
2. `images/dtbo/Makefile` — готовую геометрию simplefb и правки stock DTBO.
3. Runtime DTS и `UKE_FDT_DEVICE_LIST.md` — карту железа и приоритеты.
4. Подход к initramfs и сборке boot-образов (адаптируем под pmOS initramfs).
5. Пиннутые сабмодули `lineage/` и `vendor/` — это нужные downstream-исходники
   (Xiaomi uke OSS, MiCode display/camera/wlan trees).

> Лицензия: патч — производная от Xiaomi-исходников (GPL-2.0), с сохранением copyright.
> При переносе сохранять атрибуцию.

---

## 3. MCC45TR/uke-linux — метапроект с лучшей документацией

**Где:** `github.com/MCC45TR/uke-linux` + 4 компонента:
`orangefox_device_xiaomi_uke`, `uke-project-aloha`, `senemos-uke-kernel-mainline`,
`uke-fedora-builder`.

**Цель:** Fedora Rawhide AArch64, recovery-first (OrangeFox) → UEFI (Project Aloha) →
mainline → Fedora, с двойной загрузкой и «OEM-качеством». Таргет — **POCO Pad X1 +
Xiaomi Pad 7**.

**База:** Linux **v7.2.8** (`9a66fdc0d7fd...`), ветка `senemos7/uke-7.2.8-bringup`.

**Статус:** физического устройства **нет**; загружаемого образа **нет**; Uke DTB
**нет**. Generic 7.2.8 собирается, но это не порт. UEFI-платформа не имеет таргета
для uke. Ценность — в подготовке и методологии, а не в результате.

**Что действительно хорошо:**
- `PLAN.md` — 100 шагов с приоритетами, зависимостями и критериями приёмки.
- `DEVICE-STATUS.md` — **143 способности** × (recovery/UEFI/Linux), с вариантами
  панелей/тача/памяти/регионов.
- `docs/research/DONORS.md` — список доноров подсистем с ограничениями.
- `reports/source-archive.md` — 50 архивов, проверка offline-restore.
- Анализ стоковой прошивки: 3 профиля (CN/Global/Turkey), раскладка разделов,
  AVB, модули, vermagic, DTB/DTBO.
- Строгая методология доказательств (U0–U3 / H0–H3), разделение source/build/
  emulation/third-party/own-device.

**Чего брать не нужно:** UEFI (Project Aloha), OrangeFox-recovery, Fedora-пакеты,
их 100-шаговый порядок как обязательный. Это другой путь, чем Nura + pmbootstrap.

**Что взять:**
- `PLAN.md` — как чек-лист (что вообще нужно не забыть).
- `DEVICE-STATUS.md` — матрицу железа и вариантов.
- `DONORS.md` и `source-archive.md` — готовый список исходников и их границы.
- Анализ прошивок и boot-раскладки — не переизобретать.
- Их требования к evidence-контракту — полезно перенять дисциплину.

---

## 4. Сводная таблица: что берём для нашего порта

| Слой | Источник | Что именно |
|---|---|---|
| SoC-ядро, DTSI, PMIC, драйверы | **palawan-mainline** | `palawan.dtsi`/`lamma.dtsi`, PMIC-инклюды, bindings/drivers |
| uke-специфика ядра | **ztsubaki** | патч USB/clock/SMMU/TLMM, геометрия simplefb |
| Board-DTS | пишем сами | `uke.dts` из palawan.dtsi + runtime FDT ztsubaki |
| Карта железа | **ztsubaki** + MCC45TR | `UKE_FDT_DEVICE_LIST.md`, `DEVICE-STATUS.md` |
| Boot-образы | **ztsubaki** + gts9wifi | boot image v4, init_boot, AVB hash footer |
| Firmware | сток uke | извлечение из прошивки (не QRD-репо palawan) |
| План/чек-лист | **MCC45TR** | `PLAN.md`, `DONORS.md` |
| Процесс/пакеты | **Nura pmaports** | `device-xiaomi-uke`, `linux-*`, `firmware-*` |

### Как это складывается

```
palawan-mainline   →  SoC-поддержка mainline (palawan/lamma dtsi, драйверы)
        +
ztsubaki патч      →  uke-специфика (USB, clocks, SMMU, simplefb, stock-DT overlay)
        +
свой uke.dts       →  чистая board-DTS на базе palawan.dtsi (долгосрочно)
        =
mainline-ядро для uke
        ↓
pmbootstrap + device-xiaomi-uke (Nura)  ←  чек-лист MCC45TR + референс gts9wifi
```

**Практический вывод:** начинать с комбинации palawan (база) + ztsubaki (патч и
stock-DT overlay) — это единственный путь, уже доказанный на железе. Параллельно
писать `uke.dts` на базе `palawan.dtsi`, чтобы уйти от стокового DTB. MCC45TR держать
как чек-лист, а не как план действий.

---

## 5. Источники

- palawan-mainline linux: `https://codeberg.org/palawan-mainline/linux`
- palawan-mainline u-boot (пусто): `https://codeberg.org/palawan-mainline/u-boot`
- palawan firmware (QRD): `https://codeberg.org/palawan-mainline/firmware-qualcomm-qrd8635`
- ztsubaki/uke-linux: `https://github.com/ztsubaki/uke-linux` (ветка `master`)
- MCC45TR/uke-linux: `https://github.com/MCC45TR/uke-linux`
- MCC45TR/uke-project-aloha: `https://github.com/MCC45TR/uke-project-aloha`
- MCC45TR/senemos-uke-kernel-mainline: `https://github.com/MCC45TR/senemos-uke-kernel-mainline`
