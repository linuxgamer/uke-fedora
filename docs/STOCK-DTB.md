# Разбор стоковой прошивки uke

Прошивка: `uke_global_images_OS3.0.303.0.WOZMIXM_16.0` (Global).
Артефакты (не коммитятся): `build/stock/extracted/`. Воспроизведение: `tools/extract-stock.sh`.

## Образы

| Образ | Размер | Содержимое |
|---|---:|---|
| `boot.img` | 100663296 | только ядро 35 432 960 Б, header v4, без ramdisk |
| `init_boot.img` | 8388608 | ramdisk 2 309 001 Б, без ядра |
| `vendor_boot.img` | 100663296 | vendor ramdisk 34 052 447 Б + DTB 1 885 913 Б + bootconfig |
| `dtbo.img` | 20971520 | 1 entry, 591 943 Б (board overlay uke) |
| `vbmeta.img` | 8192 | SHA256_RSA2048; chain `boot`/`recovery`/`vbmeta_system` |

`vendor_boot` cmdline: `video=vfb:640x400,bpp=32,memsize=3072000 swinfo.fingerprint=uke:14/OS3.0.303.0.WOZMIXM:user mtdoops.fingerprint=...`
Fingerprint: `Xiaomi/uke_global/uke:14/UKQ1.240624.001/OS3.0.303.0.WOZMIXM:user/release-keys`.

## Разделы (из `rawprogram*.xml`, сектор 4096 Б)

| LUN | Раздел | Размер |
|---|---|---:|
| 4 | `boot_a` / `boot_b` | 96 MiB |
| 4 | `vendor_boot_a` / `_b` | 96 MiB |
| 4 | `init_boot_a` / `_b` | 8 MiB |
| 4 | `dtbo_a` / `_b` | 24 MiB |
| 4 | `recovery_a` / `_b` | 100 MiB |
| 4 | `vbmeta_a` / `_b` | 32 сект. |
| 0 | `misc` | 4 MiB |
| 0 | `metadata` | 64 MiB |
| 0 | `super` (dynamic) | 10752 MiB |
| 0 | `userdata` | до конца LUN0 |
| 5 | `persist` | 32 MiB |

A/B: слот `a` (по данным ztsubaki — единственный подтверждённо рабочий).

## Базовые DTB (4 штуки в vendor_boot)

`vendor_boot` несёт **4 склеенных DTB** — это SoC-варианты, не board:

| # | model | msm-id | SoC |
|---|---|---|---|
| dtb.0 | Cliffs SoC | 0x266 | SM8635 |
| dtb.1 | **Cliffs 7 SoC** | **0x278** | **SM7675 (uke)** |
| dtb.2 | Cliffs7P SoC | 0x283 | — |
| dtb.3 | CliffsP SoC | 0x282 | — |

Board-специфика uke — в **DTBO** (`dtbo.img`), overlay поверх базы.

## DTBO (uke overlay)

```
model = "Qualcomm Technologies, Inc. Uke based on SM8635"
compatible = "qcom,cliffs-mtp", "qcom,cliffs", "qcom,mtp"
qcom,msm-id = <0x282 0x10000 0x278 0x10000 0x283 0x10000 0x266 0x10000>
qcom,board-id = <0x08 0x00>
xiaomi,miboard-id = <0x0b 0x00>
```

## Железо uke (из DTBO)

| Узел | Данные |
|---|---|
| **Панель O82** | dual DSI + DSC, video mode, TDDI, 30 bpp; варианты panel-id `0x004F3832 0x5042020B` и `0x004F3832 0x5036020A` |
| Панель: reset | `gpio2`; reset-seq `<0 10 1 3 0 3 1 15>` |
| Панель: ESD IRQ | `gpio168` + `gpio169` (второй DSI) |
| Панель: питание | `vddil8b`=L8B(1.9 В), `vsp`=gpio74(5.8 В), `vsn`=gpio75(5.8 В) |
| Панель: режимы | 30/48/50/60/90/120/144 Гц; топология `<2 2 2>` |
| **Тач** | Novatek `NVT-ts-spi` на `qupv3_se4_spi`; IRQ `gpio54`, lcd_id `gpio26` |
| **Подсветка** | 2× KTZ8866 @0x11 на `qupv3_se0_i2c` и `qupv3_se12_i2c` (compatible `ktz,ktz8866` → mainline `kinetic,ktz8866`) |
| **USB** | `usb0`/dwc3 + WCD939x (`wcd_usbss`, `wcd939x-codec`); eUSB2 repeater `pm7550ba` |
| **Аудио** | WCD939x/WCD937x codec, WSA883x/884x, 4× `fs19xx_smartpa` @0x34-0x37 |
| **Кнопка** | volume-up на `pmxr2230_gpios 6` |
| **NFC** | `fm19511` на `qupv3_se12_i2c` @0x57, IRQ gpio170 |
| **Hall** | `gpio99` (lid) + `gpio100` (table) |
| **Wi-Fi/BT** | WCN6750; enable `gpio135` |
| **Клавиатура** | Nanosic 803 @0x4c на `qupv3_se3_i2c` (не поддерживаем) |
| **Батарея** | `battery_charger` (Xiaomi charge profile) |

## Замечания для порта

- Панель **TDDI** — тач интегрирован с дисплеем (novatek ссылается на panel).
- Модема нет (downstream отключает `mpss_mem`/`modem_pas`).
- Панель и драйвер тача в mainline отсутствуют — основная работа.
- Compatible-имена downstream (`qcom,cliffs-*`, `ktz,ktz8866`) нужно мапить на mainline (`qcom,palawan-*`/`qcom,lamma-*`, `kinetic,ktz8866`).
