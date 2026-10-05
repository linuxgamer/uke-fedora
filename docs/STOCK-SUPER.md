# Stock `super.img` and Firmware Analysis

Source firmware: `uke_global_images_OS3.0.303.0.WOZMIXM_16.0`. Extracted images
under `build/stock/` are local artifacts and must not be committed.

## Logical Partitions

| Partition | Approximate size | Filesystem |
|---|---:|---|
| `odm_a` | 1.11 GiB | EROFS |
| `product_a` | 3.4 GiB | EROFS |
| `system_a` | 0.67 GiB | EROFS |
| `system_ext_a` | 0.61 GiB | EROFS |
| `vendor_a` | 1.14 GiB | EROFS |
| `vendor_dlkm_a` | 30 MiB | EROFS |
| `system_dlkm_a` | 15 MiB | EROFS |
| `mi_ext_a` | variable | EROFS |

Stock Android modules are references only. They have vermagic
`6.1.68-android14-11` and cannot be loaded by the stock 6.1.138 kernel, much less
by mainline Linux.

## Useful Driver and Firmware Clues

| Area | Stock artifacts | Porting value |
|---|---|---|
| WLAN | `qca_cld3_qca6750.ko`, `cnss2.ko`, `icnss2.ko` | Identifies WCN6750 integration |
| Touch | `nt36532_touch.ko`, `xiaomi_touch.ko` | Protocol and firmware reference |
| Audio | WCD939x/WCD937x, AW882xx, FS19xx modules | Machine-driver and amplifier reference |
| Display/GPU | `msm_drm.ko`, `msm_kgsl.ko` | Downstream implementation reference |
| USB | `wcd_usbss_i2c.ko`, `dwc3-msm.ko` | USB routing and controller reference |

## Firmware Locations

| Location | Contents | Mainline relevance |
|---|---|---|
| `vendor/firmware/` | GMU, SQE, zap, camera files | GPU and camera |
| `odm/firmware/` | NT36532 CSOT/TM images, FS19xx, GPU zap | Touch, audio, GPU |
| `NON-HLOS.bin` | WCN6750 WPSS/AMSS/board files, ADSP/CDSP | WLAN, audio DSP, Bluetooth |
| `dspso.bin` | DSP image | CDSP |
| `BTFM.bin` | Bluetooth/FM firmware | Bluetooth |

WCN6750 firmware is stored in the modem partition's `NON-HLOS.bin`. It needs
conversion or repackaging for `ath11k`; this remains a major blocker. The OEM
NT36532 CSOT and TM firmware images in `odm/firmware/` are available as a basis
for the future touchscreen port.

Do not commit proprietary firmware blobs. Keep extraction scripts and file lists
in the repository instead.
