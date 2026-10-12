# Hardware status

Recorded maintainer results for the existing development profiles. The planned
userdata profile is not yet implemented or validated; it inherits none of these
results automatically. [Workspace](README.md).

## Hardware support

**Last reviewed: 2026-10-11 — Fedora Rawhide AArch64, Linux `7.2.9-senemos-uke`.**
These results come from the owner's POCO Pad X1, 8 GB / 512 GB, using the stock
Android bootloader. Linux displays the requested name **Xiaomi Pad 7**. Other
models and firmware versions need their own tests. The current boot candidate is
`pair-0242a33799d12541`; earlier successful USB transfers are identified in the
linked reports.

| Status | What it means |
|---|---|
| 🟢 **Working** | The function described in the row was used successfully on the tablet. |
| 🟡 **Partial** | Some functionality works; the row explains the limitation. |
| 🔴 **Broken** | The function is unavailable or fails in this Linux build. This does not mean the hardware is defective. |
| ⚪ **Not tested** | We have no physical functional result for this feature. |
| ⏸️ **Disabled** | Deliberately kept off while a known problem is investigated. |

### Boot, processor and storage

| Feature | Status | What you can expect today |
|---|---|---|
| Fedora boot | 🟡 **Partial** | Two RAM boots reached the real Fedora filesystem and USB SSH. Repeated cold boots and automatic slot-B startup still need testing. |
| CPU — Snapdragon 7+ Gen 3 (SM7675) | 🟢 **Working** | All eight cores are online and run native Linux commands. Heavy workloads have not been tested. |
| CPU frequency control | 🟡 **Partial** | Three frequency policies are exposed, up to about 2.80 GHz. Voltage changes and throttling need validation. |
| RAM | 🟡 **Partial** | Linux uses about 7.21 GiB of the installed 8 GB. Memory stress and suspend retention are untested. |
| UFS storage | 🟢 **Working** | Fedora reads and writes its real internal-storage root filesystem. Long transfers, power-loss recovery and resume are untested. |
| Linux partition / EXT4 | 🟢 **Working** | The existing 64 GiB partition is fully usable. Root is selected by GPT partition name `linux`, not by UUID. |
| `reboot bootloader` | 🟢 **Working** | One command returned the tablet to bootloader fastboot, confirmed on the tablet and computer. Repeat testing remains open. |
| Normal reboot, recovery command and poweroff | ⚪ **Not tested** | These routes have not been qualified on the current candidate. |
| Project Aloha / UEFI boot | ⚪ **Not tested** | The current Fedora session uses the stock Android bootloader. The Uke UEFI port is still in development. |

### Screen and input

| Feature | Status | What you can expect today |
|---|---|---|
| Tablet screen / local TTY | 🟢 **Working** | A real command prompt is visible at 3200×2136 using the framebuffer left by the bootloader. |
| Backlight | 🟡 **Partial** | The screen stays lit, but Linux cannot adjust brightness or control blanking yet. |
| Native panel control / refresh switching | 🔴 **Broken** | The native Linux display path is not usable. The current image relies on the bootloader's fixed display setup. |
| GPU — Adreno 732 | 🔴 **Broken** | No usable DRM/render device or hardware acceleration. Showing the GPU name in Fastfetch does not enable graphics. |
| Touchscreen | 🔴 **Broken** | No usable touch input device in Fedora. |
| Stylus / pen | 🔴 **Broken** | No usable pen input, pressure or tilt interface in Fedora. |
| Power / volume buttons | 🟡 **Partial** | Input drivers register; physical key events and navigation have not been verified. |
| USB keyboard / mouse | ⚪ **Not tested** | Tablet host mode is not ready; no successful physical input test. |
| Pogo keyboard / touchpad | ⚪ **Not tested** | Attachment, key events and touchpad input still need testing. |

### Networking and USB

| Feature | Status | What you can expect today |
|---|---|---|
| Wi-Fi — WCN6750 | 🔴 **Broken** | No Wi-Fi interface appears. Firmware, wireless processor startup and board resources still need integration. |
| Bluetooth | 🔴 **Broken** | No Bluetooth controller appears; scanning and pairing are unavailable. |
| USB overall | 🟡 **Partial** | Device mode works with a computer. Host power, accessories and role switching are not ready. |
| USB CDC ACM / serial shell | 🟢 **Working** | The computer can exchange native shell commands and logs with the tablet. |
| USB ECM / SSH | 🟢 **Working** | SSH over the USB cable works. A previous matched profile also passed a byte-identical 16 MiB round trip and software gadget reconnect. |
| USB host / accessory power (VBUS) | 🔴 **Broken** | The owner's ESP32-S3 received no power from the tablet. Host accessories are not usable through this path yet. |
| USB-C switch / role control | 🔴 **Broken** | The switch driver fails while acquiring its reset GPIO. Automatic host/device switching is not qualified. |
| Physical USB unplug / replug | ⚪ **Not tested** | Software reconnect passed; a physical cable-disconnect test is still needed. |
| USB SuperSpeed | ⚪ **Not tested** | No validated USB 3 accessory transfer. |
| DisplayPort / USB-C video output | ⚪ **Not tested** | No external-monitor or adapter test has passed. |
| USB Ethernet adapters / hubs | ⚪ **Not tested** | Accessory networking and hub operation still need physical tests. |

### Sensors

Sensor names below come from the earlier stock Android inventory and OEM
configuration. Exact populated variants still need confirmation. Fedora currently
exposes no usable motion, light or SAR sensor interface.

| Feature | Status | What you can expect today |
|---|---|---|
| Accelerometer — LSM6DSO family | 🔴 **Broken** | No acceleration samples in Fedora. |
| Gyroscope — LSM6DSO family | 🔴 **Broken** | No angular-rate samples in Fedora. |
| Magnetometer / compass — QMC630x family | 🔴 **Broken** | No magnetic-field samples or working compass. |
| Front light sensor — STK3BCx family | 🔴 **Broken** | No usable front ambient-light readings. |
| Rear light sensor — SIP1328 | 🔴 **Broken** | No usable rear light or flicker readings. |
| Front proximity sensor — STK3BCx family | 🔴 **Broken** | No usable proximity events. |
| SAR / body proximity — SX937x family | 🔴 **Broken** | No usable capacitive proximity readings. |
| Automatic rotation / sensor fusion | 🔴 **Broken** | Motion data and fused orientation are unavailable. |
| Automatic brightness | 🔴 **Broken** | Both ambient-light input and Linux brightness control are missing. |
| Hall / cover detection | ⚪ **Not tested** | No controlled cover-open/close event test. |
| Temperature sensors | 🟡 **Partial** | 36 thermal channels are readable. Their accuracy and protective actions have not been validated. |

### Audio and media

| Feature | Status | What you can expect today |
|---|---|---|
| Internal speakers | 🔴 **Broken** | No usable ALSA sound card or playback route. |
| Microphones | 🔴 **Broken** | No usable ALSA recording route. |
| USB / Bluetooth audio | ⚪ **Not tested** | No physical playback or recording test; Bluetooth itself is unavailable. |
| Front camera | ⚪ **Not tested** | No validated camera capture pipeline or captured frame. |
| Rear camera | ⚪ **Not tested** | No validated camera capture pipeline or captured frame. |
| Hardware video decoding / encoding | ⚪ **Not tested** | No validated hardware codec workload. |

### Power, time and platform services

| Feature | Status | What you can expect today |
|---|---|---|
| Battery percentage / voltage / current / temperature | 🔴 **Broken** | Linux exposes no battery telemetry. Charge state and battery temperature cannot be monitored. |
| Charging / USB Power Delivery | ⚪ **Not tested** | Charging behavior and negotiated power are not validated; battery readings are missing. |
| Thermal protection / throttling | ⚪ **Not tested** | Readable temperatures do not establish working throttling or shutdown protection. |
| Suspend / resume | ⚪ **Not tested** | No physical sleep/wake test. |
| RTC / persistent clock | 🟡 **Partial** | The RTC driver binds, but startup time is wrong. System time was corrected from the computer; persistence and NTP are untested. |
| Watchdog | 🟡 **Partial** | The Gunyah watchdog driver binds. Recovery behavior has not been tested. |
| PMIC / regulators | 🟡 **Partial** | Enough resources work for storage and USB. Other PMIC probes still report errors. |
| DMA / IOMMU resources | 🟡 **Partial** | Reviewed storage, USB and related bus paths are usable. GPU and wireless resources still need work. |
| Interconnect / platform power control | 🟡 **Partial** | Basic root and USB operations work, but provider errors remain; performance and power behavior are unverified. |
| DSPs — ADSP / CDSP / QSH | 🔴 **Broken** | No usable remote-processor interface for audio, sensor or DSP services. |
| CoreSight tracing | ⏸️ **Disabled** | Autoload is blocked after earlier resets. The exact failure still needs investigation. |

The next priority is **Wi-Fi**, followed by native graphics and an original
Fedora KDE image. Battery telemetry is a prerequisite for stress, charging and
power-management experiments. KDE applications will come from Fedora's packages.

The tables describe the recorded development profiles, not a finished tablet
release. Stock slot A and the existing root were preserved; the new `boot_b`
image was written and verified, but unattended slot-B startup is still untested.
Build, RPM and virtual-machine checks are tracked separately from physical results.

The private [hardware report](https://github.com/MCC45TR/uke-linux-docs/blob/main/docs/testing/FEDORA-HARDWARE-AUDIT-2026-10-11.md)
and [sensor report](https://github.com/MCC45TR/uke-linux-docs/blob/main/docs/testing/FEDORA-SENSOR-AUDIT-2026-10-11.md)
contain the detailed evidence and test limits. Access is required. Historical
sensor descriptors are not a count of physical chips or proof of Linux support.
