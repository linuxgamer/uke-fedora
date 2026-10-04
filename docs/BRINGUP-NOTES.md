# Bring-up заметки: palawan 7.2 vs ztsubaki

Дата: 2026-10-03. База: `palawan-mainline/linux`, ветка `palawan/v7.2-rc2`,
commit `0d9f7fdf7` (Linux 7.2.0-rc2). Локально: `build/src/linux-palawan`.

## Главный вывод

**palawan 7.2 уже содержит почти всю платформенную поддержку SoC.** Патчи ztsubaki
писаны против **v6.12**, где этого не было, и называет всё `cliffs`/`uke`; в palawan
то же самое называется `palawan`. Поэтому **большую часть платформенных патчей
ztsubaki переносить не нужно** — на 7.2 это уже есть.

## Что уже есть в palawan 7.2

| Подсистема | Файлы / compatible |
|---|---|
| Clocks | `clk/qcom/gcc-palawan.c`, `camcc-palawan.c`, `gpucc-palawan.c`; `CLK_PALAWAN_*` |
| Pinctrl | `pinctrl-palawan.c`, `pinctrl-palawan-lpass-lpi.c`; `PINCTRL_PALAWAN` |
| Interconnect | `interconnect/qcom/palawan.c`; `INTERCONNECT_QCOM_PALAWAN` |
| RPMh/SMEM | `QCOM_RPMH`, `QCOM_SMEM`, `QCOM_SMEM_STATE` (общие) |
| SPMI/PMIC | PMIC-инклюды: `pm7550`, `pm7550ba`, `pm8550`, `pm8550ve/vs`, `pmk8550`, `pmr735a`, `pm8010` |
| UFS | `ufs-qcom.c`: `qcom,palawan-ufshc`; PHY `qcom,palawan-qmp-ufs-phy` |
| USB | `usb_1: usb@a600000` → `qcom,palawan-dwc3`, `qcom,snps-dwc3`; PHY `qcom,palawan-snps-eusb2-phy`; repeater `qcom,pm8550b-eusb2-repeater` |
| SMMU | `qcom,palawan-smmu-500`, `adreno-smmu` |
| GPU | `qcom,adreno-43030b00` (Adreno 732), GMU `qcom,adreno-gmu-735.0` |
| Display | DPU-каталог `dpu_10_1_palawan.h`; DSI |
| Video | iris `iris_platform_palawan.h` |
| IPA, IPCC, GENI, GPI, smp2p | есть в `palawan.dtsi` |
| LED flash | `LEDS_QCOM_FLASH` → `qcom,spmi-flash-led` |
| eUSB2 PHY | `drivers/phy/phy-snps-eusb2.c` → `qcom,sm8550-snps-eusb2-phy` (fallback palawan) |
| eUSB2 repeater | `PHY_QCOM_EUSB2_REPEATER` → `qcom,pm8550b-eusb2-repeater` |

Платы в дереве: только `palawan-qrd.dts`, `lamma-qrd.dts`. **`uke` нет.**

## Что реально нужно от ztsubaki (не платформа)

1. **uke board-DTS** — основная работа; пишем на базе `palawan.dtsi` (у ztsubaki это
   `stock DTB + overlay`, у нас будет чистый `uke.dts`).
2. **simplefb** — геометрия ABL-фреймбуфера: `0xe3940000`, 3200×2136, stride 12800,
   `a8r8g8b8`, `no-map` для 43 МиБ splash-region, `stdout-path`.
3. **torch** — `qcom,pm8350c-flash-led`/`qcom,spmi-flash-led`, `led-sources 1 4`.
4. **USB handoff quirks** — если palawan-драйверы не сохраняют состояние от ABL
   (GCC clock hold, SMMU SMR/S2CR/context bank, GDSC последовательность). Проверить
   на железе; возможно, часть уже учтена.
5. **WCD939x USB2 route** — при необходимости; upstream есть
   `drivers/usb/typec/mux/wcd939x-usbss.c`.

## Соответствие имён cliffs → palawan

| ztsubaki (cliffs/uke) | palawan |
|---|---|
| `PINCTRL_CLIFFS` | `PINCTRL_PALAWAN` |
| `SM_GCC_CLIFFS` | `CLK_PALAWAN_GCC` |
| `INTERCONNECT_QCOM_CLIFFS_USB` | `INTERCONNECT_QCOM_PALAWAN` |
| `QCOM_RPMH_UKE` / `REGULATOR_QCOM_RPMH_UKE` | общий `QCOM_RPMH` |
| `QCOM_GDSC_REGULATOR_UKE` | общий `QCOM_GDSC` |
| `USB_PHY_QCOM_UKE` (phy-msm-snps-eusb2) | `PHY_SNPS_EUSB2` |
| `USB_REPEATER_QCOM_UKE` | `PHY_QCOM_EUSB2_REPEATER` |
| `USB_WCD939X_UKE` | upstream `wcd939x-usbss` (typec mux) |
| `qcom,sm7675-*` compatible | `qcom,palawan-*` / `qcom,sm8550-*` fallback |

## Пробелы для uke (что предстоит сделать)

- **Board DTS** `sm7675-xiaomi-uke.dts` (память, панель, тач, LED, USB role, PMIC).
- **Панель** O82 (dual DSI, DSC) + драйвер панели.
- **Тачскрин** Novatek NT36532.
- **Backlight** KTZ8866 ×2.
- **Wi-Fi/BT** WCN6750 (ath11k + firmware + DTS-узел; в вики Nura — ❌).
- **Audio** WCD937x/939x + WSA + FS16xx, ASoC + UCM.
- **Датчики** IMU/ALS/магнитометр, charging/fuel gauge.
- **DWC3 QCOM glue** — проверить, что generic `qcom,snps-dwc3` достаточно для palawan.

## Что дальше (фаза 0)

- [x] Клонировать palawan, ztsubaki, MCC45TR.
- [x] Gap-анализ платформы.
- [x] Черновик `kernel/config/uke.fragment`.
- [x] Downstream uke DTS: `references/downstream-uke/`.
- [x] Черновик `kernel/dts/sm7675-xiaomi-uke.dts` (на базе `lamma-qrd.dts`).
- [x] Из downstream уточнены: панель O82 (reset gpio2, vsp/vsn gpio74/75, L8B 1.9В),
      подсветка 2x KTZ8866 @0x11 (i2c0/i2c12), тач NT36532 IRQ gpio54, отсутствие модема.
- [x] Разбор стоковой прошивки: `docs/STOCK-DTB.md`, `tools/extract-stock.sh`.
- [x] DTS добавлен в `Makefile` + binding `xiaomi,uke` (`kernel/scripts/prepare-tree.sh`).
- [x] **DTB компилируется без ошибок** (`kernel/scripts/build-dtb.sh`, cpp+dtc).
- [x] Найден и исправлен баг базы: `palawan.dtsi` — пропущена `;` в `compatible`
      у `usb_dp_qmpphy` (патч `kernel/patches/0001-...`).
- [x] Найден и исправлен баг базы: `iris_platform_palawan.h` — лишнее поле `.num_comv`
      (патч `kernel/patches/0002-...`).
- [x] **Baseline-ядро собрано** (`kernel/scripts/build-kernel.sh`): `Image` 50.5 МБ,
      `7.2.0-rc2`, **1641** модуль, DTB. См. раздел ниже.
- [ ] Порт панели O82 + `mdss_dsi1` (dual DSI) — панели в mainline нет.
- [ ] Порт/адаптация драйвера тача Novatek NT36532.
- [ ] Собрать pmOS-пакет ядра и initramfs.

## Baseline-сборка ядра

Инструменты (хост): `clang` + `ld.lld` + пакет **`llvm`** (`llvm-nm`/`objcopy`/`readelf`),
`bc`, `pahole`, `flex`, `bison`. Сборка: `LLVM=1 ARCH=arm64`.

```sh
kernel/scripts/prepare-tree.sh    # worktree + патчи + DTS + Makefile/qcom.yaml
kernel/scripts/build-kernel.sh    # defconfig + uke.fragment + Image + DTB + modules
```

Результат: `build/uke-build/arch/arm64/boot/Image` (50.5 МБ),
`.../dts/qcom/sm7675-xiaomi-uke.dtb`, 1641 `.ko` (в т.ч. `ath11k.ko` для WCN6750,
`msm.ko`). Версия: `7.2.0-rc2-g0d9f7fdf720a`.

### Баги базы palawan 7.2-rc2 (исправлены патчами)

1. `palawan.dtsi`: у `usb_dp_qmpphy` пропущена `;` в `compatible` — DTB не собирался.
2. `iris_platform_palawan.h`: `.num_comv` отсутствует в `struct platform_inst_caps`
   (поле убрали при рефакторинге) — `VIDEO_QCOM_IRIS` не компилировался.
