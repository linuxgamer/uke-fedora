# Разбор `super.img` и firmware

Прошивка: `uke_global_images_OS3.0.303.0.WOZMIXM_16.0`.
Артефакты (не коммитятся): `build/stock/super.raw.img`, `build/stock/parts/`, `build/stock/rootfs/`.
Инструменты: `lpunpack`, `dump.erofs`, `fsck.erofs` (собраны в `build/tools/erofs-utils`).

## Логические разделы (lpdump, A/B; активен `_a`)

| Раздел | Размер | ФС |
|---|---:|---|
| `odm_a` | ~1.11 GiB | EROFS |
| `product_a` | ~3.4 GiB | EROFS |
| `system_a` | ~0.67 GiB | EROFS |
| `system_ext_a` | ~0.61 GiB | EROFS |
| `vendor_a` | ~1.14 GiB | EROFS |
| `vendor_dlkm_a` | ~30 MiB | EROFS |
| `system_dlkm_a` | ~15 MiB | EROFS |
| `mi_ext_a` | — | EROFS |

## Модули (для справки; **не** загружаемы в mainline)

- `vendor_dlkm/lib/modules/modules.load` — **391** модуль; `system_dlkm/.../modules.load` — 60.
- ⚠️ vermagic vendor-модулей: **`6.1.68-android14-11`**, а ядро в `boot` — **6.1.138**. ABI не совпадает
  даже внутри стока; в mainline тем более неприменимо.
- Полезны как указатель на драйверы:

| Подсистема | Модули |
|---|---|
| WLAN | `qca_cld3_qca6750.ko`, `cnss2.ko`, `icnss2.ko`, `wlan_firmware_service.ko`, `cnss_nl.ko` |
| Тач | `nt36532_touch.ko`, `xiaomi_touch.ko` |
| Аудио | `wcd939x_dlkm.ko`, `wcd937x_dlkm.ko`, `wcd938x_dlkm.ko`, `aw882xx_dlkm.ko`, `fs19xx_dlkm.ko` |
| Дисплей/GPU | `msm_drm.ko`, `msm_kgsl.ko` |
| Прочее | `xiaomi_hall.ko`, `wcd_usbss_i2c.ko`, `panel_event_notifier.ko`, `dwc3-msm.ko` |

## `vendor/etc/fstab.qcom` (ключевое)

- `system`/`product`/`system_ext`/`vendor`/`vendor_dlkm`/`system_dlkm`/`odm`/`mi_ext` — **EROFS**, ro.
- `metadata` — f2fs; `persist` — ext4; `userdata` — **f2fs**, FBE `aes-256-xts`, `sysfs_path=/sys/.../1d84000.ufshc`.
- Отдельные физические разделы: `modem` (vfat, монтируется в `/vendor/firmware_mnt`), `dsp` (ext4),
  `bluetooth` (vfat), `qmcs`, `spunvm`.

## Firmware (что и где)

| Расположение | Содержимое | Для чего в mainline |
|---|---|---|
| `vendor/firmware/` (7.6 МБ) | `gen71100_gmu.bin`, `gen71100_sqe.fw`, `gen71100_zap` (в odm), `CAMERA_ICP.elf` | GPU (GMU/zap), camera |
| `odm/firmware/` (36 МБ) | `novatek_nt36532_o82_fw_{csot,tm}.bin`, `novatek_nt36532_o82_mp_*.bin`, `o82_nova_*_thp_config.ini`, `fs19xx.fsm`, `gen71100_zap.mbn`, `CAMERA_ICP.b*`, `evass*`, `vpu20_*` | **тач NT36532** (CSOT/TM), аудио (Foursemi), GPU zap, camera, video |
| `NON-HLOS.bin` (modem, FAT) | `image/qca6750/`: `wpss.b*`, `bd_o82.elf`, `bdwlan.b01`, `Data.msc`; `image/kiwi/`: `amss.bin`, `amss20.bin`, `bd_*.elf`; `image/`: `adsp.b*`, `cdspr.jsn` | **WLAN WCN6750** (WPSS/amss/bdwlan), ADSP/CDSP |
| `dspso.bin` | DSP-образ | CDSP |
| `BTFM.bin` | BT/FM | Bluetooth |
| `vendor/firmware/wlan/qca_cld/qca6750/` | симлинки: `WCNSS_qcom_cfg.ini -> /vendor/etc/wifi/...`, `wlan_mac.bin -> /mnt/vendor/persist/wlan/` | конфиг/калибровка WLAN |

**Вывод по WLAN:** прошивка WCN6750 лежит в разделе `modem` (`NON-HLOS.bin`): `wpss.*`, `amss.bin`,
`bdwlan.b01`, `bd_o82.elf`. Для mainline `ath11k` обычно нужны `amss.bin`/`m3.bin`/`board-2.bin`/`regdb.bin`
в `firmware-name` — придётся конвертировать/переупаковать. Это самый тяжёлый пункт (в вики Nura Wi-Fi ❌).

**Вывод по тачу:** в `odm/firmware` есть готовые образы `novatek_nt36532_o82_fw_csot.bin` и `_tm.bin`
плюс `mp` и конфиги — то, что грузит драйвер Novatek. Упрощает порт тача.

## Для `firmware-xiaomi-uke`

Кандидаты в пакет (лицензионно-чувствительно, только списки):
- GPU: `gen71100_gmu.bin`, `gen71100_zap.mbn`, `gen71100_sqe.fw`, `gen70900_*`.
- Тач: `novatek_nt36532_o82_fw_{csot,tm}.bin`, `novatek_nt36532_o82_mp_{csot,tm}.bin`, `o82_nova_*_thp_config.ini`.
- Аудио: `fs19xx.fsm`, WCD/WSA образы (в `NON-HLOS`/`dspso`).
- WLAN/BT: `amss.bin`, `bdwlan.b01`, `bd_o82.elf`, `wpss.*`, `BTFM.bin` (после конвертации в формат ath11k).
- Camera/video: `CAMERA_ICP.*`, `evass*`, `vpu20_*`.

Пути-источники: `build/stock/rootfs/vendor/firmware`, `.../odm/firmware`,
`NON-HLOS.bin` (`mdir -i NON-HLOS.bin ::/image/qca6750/`).
