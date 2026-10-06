# Xiaomi Pad 7 (`xiaomi-uke`) Hardware Support

This page follows the hardware-support matrix format used by postmarketOS device
pages. It records observed support in the supported Fedora 44 / mainline Linux
v6.12 boot path, not Android or the archived Palawan 7.2 tree.

| Property | Value |
|---|---|
| Manufacturer | Xiaomi |
| Model | Pad 7 (`2410CRP4CG`) |
| Codename | `uke` |
| SoC | Qualcomm SM7675 (`lamma` / `cliffs7`) |
| Architecture | arm64 |
| Kernel | Upstream Linux v6.12 with the tracked Uke patch series |
| Boot path | Stock Xiaomi ABL, custom `boot`, `init_boot`, and stock-derived `dtbo` |

## Status Legend

| Status | Meaning |
|---|---|
| Works | Confirmed on the target device in the supported boot path. |
| Partially works | Useful functionality works, with an important limitation. |
| Does not work | Required driver, firmware, or board integration is absent. |
| Not tested | No hardware validation result yet. |
| Not applicable | Hardware is absent from this Wi-Fi-only tablet. |

## Hardware Support

| Category | Feature | Status | Notes |
|---|---|---|---|
| Main | Boot to Fedora login | Works | Boots through stock ABL from UFS into Fedora 44 systemd. |
| Main | UFS storage | Works | `1d84000.ufshc`, ext4 rootfs, and `userdata` on `/dev/block/sda32`. |
| Main | USB ACM console | Works | Device exposes `/dev/ttyGS0`; host uses `/dev/ttyACM0`. |
| Main | USB networking | Not tested | RNDIS and ECM modules are in the initramfs; ACM remains the supported debug transport. |
| Main | DRM display | Does not work | The boot console is simplefb only; the O82 DSI panel has not been brought up. |
| Main | Backlight | Does not work | Two KTZ8866 controllers need board integration with the display path. |
| Main | Touchscreen | Does not work | Novatek NT36532E support from the archived tree needs a v6.12 port and device testing. |
| Main | Battery and charging | Not tested | Xiaomi battery/charger board support has not been ported. |
| Main | Suspend and resume | Not tested | Do not treat suspend as supported. |
| Multimedia | GPU acceleration | Does not work | Adreno 732/GMU 735 firmware and Mesa userspace have not been validated. |
| Multimedia | Audio | Does not work | WCD939x/WCD937x, WSA883x/884x, and FS19xx machine support is absent. |
| Multimedia | Cameras | Does not work | Camera DT, drivers, firmware, and userspace are not ported. |
| Connectivity | Wi-Fi | Does not work | WCN6750 firmware extraction/packaging and ath11k board integration are incomplete. |
| Connectivity | Bluetooth | Does not work | BTFM firmware and controller integration are incomplete. |
| Connectivity | Cellular modem | Not applicable | No modem is populated; downstream disables `mpss_mem`. |
| Connectivity | NFC | Not tested | Stock DTBO identifies an FM19511 controller; no Linux integration exists. |
| Misc | Sensors | Does not work | Accelerometer, gyroscope, hall sensors, and related board descriptions are not ported. |
| Misc | Keyboard accessory | Not tested | Stock DTBO identifies a keyboard controller; it has not been investigated. |
| Misc | External display | Not tested | No Type-C display path has been validated. |

## Hardware Inventory

| Area | Board details |
|---|---|
| Display | O82 bonded dual-DSI panel with DSC, 3200x2136, 30--144 Hz; reset GPIO 2; ESD GPIOs 168/169; VSP/VSN GPIOs 74/75. |
| Touch | Novatek NT36532E TDDI on `qupv3_se4_spi`; IRQ GPIO 54; LCD-ID GPIO 26. |
| Backlight | Two KTZ8866 controllers at I2C address `0x11` on `qupv3_se0_i2c` and `qupv3_se12_i2c`. |
| Storage | UFS host `1d84000.ufshc`; 4096-byte sectors. |
| USB | DWC3, WCD939x USB route, and PM7550BA eUSB2 repeater. |
| Wireless | WCN6750, enable GPIO 135; firmware is sourced from `NON-HLOS.bin`. |
| Audio | WCD939x/WCD937x codecs, WSA883x/884x speakers, and four FS19xx amplifiers. |

## Sources and Scope

- [Stock DTB and DTBO analysis](stock-dtb.md) is the source for board devices,
  GPIOs, and buses.
- [Stock super and firmware analysis](stock-super.md) identifies downstream
  drivers and firmware locations. Proprietary firmware is not tracked here.
- [Known issues](known-issues.md) records boot-specific constraints and confirmed
  fixes.
- The [archived panel and touchscreen notes](../references/archive/palawan-7.2/PANEL-TOUCH.md)
  document an unvalidated 7.2-era implementation. They are reference material,
  not evidence of v6.12 support.
