# Stock Boot Image and Device Tree Analysis

Source firmware: `uke_global_images_OS3.0.303.0.WOZMIXM_16.0` (Global).
Generated artifacts live under `build/stock/extracted/` and are not committed.
Reproduce the extraction with `tools/extract-stock.sh`.

## Boot Images

| Image | Partition size | Contents |
|---|---:|---|
| `boot.img` | 96 MiB | 35,432,960-byte kernel, boot header v4, no ramdisk |
| `init_boot.img` | 8 MiB | 2,309,001-byte LZ4 ramdisk, no kernel |
| `vendor_boot.img` | 96 MiB | 34,052,447-byte vendor ramdisk, 1,885,913-byte DTB area, bootconfig |
| `dtbo.img` | 20 MiB | One 591,943-byte board overlay |
| `vbmeta.img` | 8 KiB | SHA256_RSA2048 chain for boot/recovery/vbmeta_system |

## Partitions

Partition table data comes from `rawprogram*.xml`; sector size is 4096 bytes.

| LUN | Partition | Size |
|---|---|---:|
| 4 | `boot_a` / `boot_b` | 96 MiB |
| 4 | `vendor_boot_a` / `_b` | 96 MiB |
| 4 | `init_boot_a` / `_b` | 8 MiB |
| 4 | `dtbo_a` / `_b` | 24 MiB |
| 4 | `recovery_a` / `_b` | 100 MiB |
| 4 | `vbmeta_a` / `_b` | 32 sectors |
| 0 | `misc` | 4 MiB |
| 0 | `metadata` | 64 MiB |
| 0 | `super` | 10,752 MiB |
| 0 | `userdata` | Remaining LUN 0 space |
| 5 | `persist` | 32 MiB |

The working Linux setup uses slot `a`. Preserve the stock boot images as a
recovery baseline.

## Device Tree

`vendor_boot` contains four concatenated SoC DTBs. `dtb.1`, labelled **Cliffs 7
SoC** with MSM ID `0x278`, is the SM7675 base used by `uke`. Board-specific nodes
are provided by the single DTBO overlay:

```text
model = "Qualcomm Technologies, Inc. Uke based on SM8635"
compatible = "qcom,cliffs-mtp", "qcom,cliffs", "qcom,mtp"
qcom,board-id = <0x08 0x00>
xiaomi,miboard-id = <0x0b 0x00>
```

## Board Hardware Found in DTBO

| Device | Details |
|---|---|
| O82 panel | Dual DSI + DSC, 30--144 Hz; panel IDs for CSOT and TM variants |
| Panel power | Reset GPIO 2, ESD GPIO 168/169, 1.9 V L8B, VSP/VSN GPIO 74/75 |
| Touchscreen | Novatek `NVT-ts-spi` on `qupv3_se4_spi`; IRQ GPIO 54, LCD ID GPIO 26 |
| Backlight | Two KTZ8866 devices at `0x11` on `qupv3_se0_i2c` and `qupv3_se12_i2c` |
| USB | DWC3, WCD939x USB route, PM7550BA eUSB2 repeater |
| Audio | WCD939x/WCD937x, WSA883x/884x, four FS19xx amplifiers |
| Wireless | WCN6750, enable GPIO 135 |
| Other | NFC FM19511, keyboard controller, hall sensors, Xiaomi battery charger |

The panel and touch controller do not have mainline implementations. Downstream
compatible names such as `qcom,cliffs-*` must be mapped to the applicable upstream
or port-specific bindings.
