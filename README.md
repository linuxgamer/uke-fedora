# Uke Fedora

Fedora Linux port made mainly for the **Xiaomi Pad 7**, based on [MCC45TR's port](https://github.com/MCC45TR/uke-linux). It may not work on POCO Pad X1.

This port is **work in progress**. Differences are: Fedora 44, `/userdata` install, more DEs, build optimisations, extra QoL stuff.

> [!WARNING]
> This is not ready for daily use. Installing to `userdata` overwrites Android user data. Back up any data you have!

## Hardware support

Comes from [upstream hardware tests](https://github.com/MCC45TR/uke-linux#hardware-support) on POCO Pad X1.

| Component | Status | Notes |
| --- | --- | --- |
| Fedora KDE desktop | 🟡 Partial | Boots into KDE and runs applications, but some desktop issues remain. |
| Other desktops | ⚪ Not verified | Only KDE images have been tested. |
| TTY touch keyboard | ⚪ Not verified | An experimental framebuffer keyboard is packaged for TTY images; touch-only first boot still needs a tablet test. |
| Display | 🟢 Working | Native 3200 × 2136 resolution and adjustable brightness. |
| Refresh rate | 🟡 Partial | Fixed 30–144 Hz modes work; adaptive refresh (VRR) is disabled. |
| Touchscreen | 🟡 Partial | Works for normal use; multitouch reliability still needs work. |
| Graphics (GPU) | 🟡 Partial | Desktop OpenGL works, Vulkan and some graphics features remain experimental. |
| CPU and storage | 🟢 Working | All CPU cores are available, internal storage works. |
| Wi-Fi | 🟢 Working | Connects to networks and supports normal data transfers. |
| Bluetooth | 🟢 Working | Tested with a mouse and wireless headphones, including audio playback. |
| Auto-rotation | 🟢 Working | Screen and touch orientation follow tablet rotation. |
| Other sensors | 🟡 Partial | Motion, compass, proximity and cover detection have varying levels of support. |
| USB-C accessories | 🟡 Partial | A powered hub and mouse work, other accessories need more testing. |
| External display | 🔴 Not working | Video output over USB-C/HDMI/DP has not been tested. |
| Charging | 🟡 Partial | Charging and battery percentage are detected; fast charging, charge limits and bypass may not work. |
| Sleep and wake | 🟡 Partial | Basic suspend testing exists, but wake is unreliable. |
| Reboot and shutdown | 🟡 Partial | Reboot works in some tests; shutdown can hang or restart the tablet. |
| Built-in speakers and microphones | 🔴 Not working | No functional playback or recording yet. |
| Cameras | 🔴 Not working | Neither camera has a verified working capture. |
| Stylus | 🔴 Not working | Pen input, pressure and tilt are unavailable. |
| Magnetic keyboard |🔴 Not working| Pogo keyboard and touchpad support have not been tested. |

🟢 Working · 🟡 Partial · 🔴 Not working · ⚪ Not verified

<details>
<summary><strong>Detailed hardware tables for developers</strong></summary>

Detailed reference copied from [upstream at this commit](https://github.com/MCC45TR/uke-linux/blob/ed63fda9a7f2903611e71b1c99972a10baf09ec2/README.md#hardware-support).

**Test scope:** POCO Pad X1, 8 GB / 512 GB; Fedora Rawhide AArch64; stock Android
bootloader; development kernel `7.2.11-6`. Reviewed **20 October 2026**. These results do not come from downloadable Alpha 1 images.

Each row separates the observed result from remaining validation. Status applies
only to the function and test scope stated in that row.

- 🟢 **Working:** the listed function was used successfully on the tested tablet;
  the stated limits still apply.
- 🟡 **Partial:** some functions work, with incomplete integration or validation.
- 🔴 **Broken:** the function is not currently operational in this Linux stack;
  this does not imply a physical hardware defect.
- ⚪ **Not tested / not qualified:** the needed functional or calibration result is unavailable.
- ⏸️ **Disabled:** kept off while a known fault is investigated.

### Boot, CPU and storage

| Feature | Status | Observed result | Remaining validation / limits |
|---|---|---|---|
| Fedora boot | 🟢 **Working** | KDE starts with display and touch on Linux 7.2.11-6. | Complete published images. |
| CPU — Snapdragon 7+ Gen 3 (SM7675) | 🟢 **Working** | All eight cores online. | Sustained heavy loads. |
| CPU frequency policies | 🟢 **Working** | All three CPU policies respond to power-profile changes. | Sustained performance and energy use. |
| RAM | 🟡 **Partial** | Linux reports 7.21 GiB; memory stress stops at the 65 °C guard. | Complete sustained memory test. |
| UFS storage | 🟢 **Working** | 256 MiB write/readback passes; bounded direct read about 1.7 GB/s. | Bounded workloads only. |
| UFS scaling / WriteBooster | 🟢 **Working** | Gear scaling, WriteBooster and runtime idle states respond to load. | MCQ and inline encryption disabled. |
| Memory-pressure telemetry | 🟢 **Working** | CPU, memory and I/O pressure counters available. | Effective OOM policy. |
| UFS I/O scheduler | 🟢 **Working** | mq-deadline retained across two boots without the earlier switch errors. | Two-boot sample. |
| Linux partition / EXT4 | 🟢 **Working** | Fedora boots from the dedicated EXT4 linux partition. | Power-loss recovery. |
| Bootloader entry | 🟢 **Working** | FASTBOOT screen visible. | USB detection assessed separately. |
| Fastboot USB connection | 🟡 **Partial** | Earlier sessions functional; current PC connection not detected. | Restore and repeat USB enumeration. |
| Normal reboot — kernel 6 | 🟢 **Working** | Tested normal reboots return to KDE. | Shutdown assessed separately. |
| Shutdown / poweroff | 🟡 **Partial** | USB-powered shutdown can restart the tablet; intermittent shutdown hang. | Reliable shutdown with and without USB. |
| Reboot to recovery | ⚪ **Not tested** | No validated entry from the current Fedora kernel. | Physical recovery-entry test. |
| Hardware information / Fastfetch | 🟢 **Working** | All-module capture completes. | Some hardware fields unavailable. |
| Project Aloha / UEFI boot | ⚪ **Not tested** | Fedora test path uses the stock Android bootloader. | Separate UEFI development and device validation. |

### Display, graphics and input

| Feature | Status | Observed result | Remaining validation / limits |
|---|---|---|---|
| Tablet screen / local TTY | 🟢 **Working** | KDE and local console at 3200×2136. | Internal display only. |
| Manual backlight brightness | 🟢 **Working** | Smooth manual adjustment. | Optical calibration. |
| Screen-off backlight / DPMS | 🟡 **Partial** | Scanout returns after off/on; one DPU frame-done timeout in ten cycles. | Resolve timeout and repeat transitions. |
| Native DPU / DSI / DSC display | 🟢 **Working** | Native KDE scanout on the internal screen. | Display lifecycle tests. |
| Refresh-rate switching | 🟢 **Working** | Fixed 30/48/50/60/90/120/144 Hz modes functional. | VRR assessed separately. |
| Adaptive sync / dynamic refresh | ⏸️ **Disabled — input regression** | Multitouch/display faults and touch watchdogs with VRR. | Disabled; no supported physical 1 Hz path. |
| Display color depth | 🟡 **Partial** | Active 10-bit framebuffer and DSC link. | Selectable 8/12/16-bit output not implemented. |
| Firmware DRM fallback | 🟡 **Partial** | Earlier firmware-framebuffer operation recorded. | Current fallback behavior. |
| Original Fedora KDE / Wayland | 🟡 **Partial** | Desktop and applications operational. | Clipboard-related shutdown deadlock. |
| Desktop scrolling | 🟡 **Partial** | Settings-list scrolling stutters. | Content-frame pacing; display Hz alone is insufficient. |
| Manual display rotation | 🟢 **Working** | Rotation with matching touch coordinates. | — |
| GPU — Adreno 732 | 🟡 **Partial** | Desktop OpenGL operational. | OpenGL ES failures and lifecycle coverage. |
| KDE GPU statistics | 🟡 **Partial** | KSystemStats exposes idle usage and frequency. | Active-load accuracy and GUI presentation. |
| Xwayland / OpenGL | 🟢 **Working — desktop OpenGL** | 27 output checks per backend plus bounded workloads pass. | Desktop OpenGL only. |
| Vulkan / Turnip | 🟡 **Partial** | 9,000-frame cube completes; vulkaninfo display-extension query fails. | Resolve query failure and broaden validation. |
| Touchscreen — Novatek NT36532 | 🟡 **Partial** | Normal-use touch operational. | Ten-contact/VRR faults and continuous-contact reliability. |
| Stylus / pen | 🔴 **Broken** | No pen input, pressure or tilt. | Functional pen implementation and tests. |
| Power / volume buttons | 🟢 **Working** | Buttons respond during normal Fedora use. | Wake from real suspend. |
| Power-button screen toggle | 🟡 **Partial** | Display-only policy configured. | Physical toggle test. |
| USB receiver mouse | 🟢 **Working** | Mouse input through powered Juo dock on 7.2.10-27. | Tested dock/kernel only. |
| USB keyboard | ⚪ **Not tested** | No physical input result. | Keyboard input test. |
| Pogo keyboard / touchpad | 🔴 **Broken** | No keyboard available. | Native transport, authentication and hardware tests. |

### Networking and USB

| Feature | Status | Observed result | Remaining validation / limits |
|---|---|---|---|
| Wi-Fi — WCN6750 | 🟢 **Working** | Automatic connection, SSH and file transfers; factory WLAN address retained across restarts. | — |
| Signed network updates | 🟢 **Working** | Signed Fedora/COPR packages install over Wi-Fi. | Kernel updates require matching boot/modules. |
| Bluetooth | 🟢 **Working — mouse and audio** | Mouse pairing/reconnection and Space Q45 LDAC playback functional. | Broader device coverage. |
| NFC | ⚪ **Not tested** | No exposed controller. | Confirm fitted hardware. |
| USB overall | 🟡 **Partial** | Device mode and dock mouse operational. | Role changes and combined dock workloads. |
| Manual CDC ACM management | 🟢 **Working — manual** | Manual on/off control; default off. | Current-cable reconnect and suspend. |
| USB ECM / SSH | 🟢 **Working — manual** | Earlier SSH and verified 16 MiB transfers pass. | Default off; earlier-test scope. |
| USB host / accessory power (VBUS) | 🟡 **Partial** | Dock devices enumerate. | Accessory power budget and earlier ESP32 power failure. |
| USB-C switch / role control | 🟡 **Partial** | PC sink/device and dock host/sink states reported. | Broader role switching. |
| USB reconnect / driver lifecycle | 🟡 **Partial** | Software reconnect functional in earlier tests. | Physical reconnect and driver-reload recovery. |
| USB SuperSpeed | 🟡 **Partial** | Hub and RTL8153 enumeration at 5 Gbit/s. | Storage throughput. |
| DisplayPort / USB-C video output | 🟡 **Partial** | No successful tablet HDMI output. | Powered test requires charging-protection qualification. |
| External-monitor DDC/CI brightness | 🟡 **Partial** | PowerDevil/ddcutil initializes. | Actual monitor brightness control. |
| USB hubs | 🟢 **Working — tested dock** | Juo USB 2/3 enumeration and powered-dock mouse input functional. | Storage and Ethernet assessed separately. |
| USB Ethernet | 🟡 **Partial** | RTL8153 and firmware detected. | Cable carrier and real traffic. |

### Sensors and desktop integration

Sensor startup uses native readiness dependencies. Factory calibration remains
on read-only persist; runtime registry writes use RAM. Some endpoints still
lack a validated physical mapping.

| Feature | Status | Observed result | Remaining validation / limits |
|---|---|---|---|
| SSC sensor startup | 🟢 **Working** | Automatic motion, light and proximity service startup. | DSP restart recovery. |
| Accelerometer — LSM6DSO | 🟢 **Working — rotation** | Four physical orientations with matching touch alignment. | Rotation only. |
| Gyroscope — LSM6DSO | 🟡 **Partial** | Readable XYZ angular rates. | Physical motion response and drift. |
| Magnetometer / compass — QMC630x family | 🟡 **Partial** | Heading responds to movement; absolute-heading comparison fails. | Absolute-heading accuracy. |
| Front light sensor — STK3BCx family | 🟢 **Working — ambient light** | Front illumination changes lux and KDE brightness. | Ambient light only. |
| Rear light sensor — SIP1328 | 🟢 **Working — ambient light** | Rear illumination changes brightness with the front dark. | Ambient light only. |
| Ambient color temperature | ⚪ **Not qualified** | No valid startup color sample. | Calibrated Kelvin conversion. |
| Front proximity sensor — STK3BCx family | 🟢 **Working — near/far** | Cover/release sequence reports far → near → far. | Near/far response only. |
| SAR / body proximity — SX937x family | ⏸️ **Disabled** | No usable endpoint or physical response. | Endpoint mapping and physical validation. |
| Automatic rotation / sensor fusion | 🟢 **Working — four poses** | KDE and touch alignment follow all four orientations. | Four poses. |
| Automatic brightness | 🟢 **Working** | Brightness follows front/rear illumination changes. | Long-run and sunlight behavior. |
| Magnetic cover / lid detection | 🟢 **Working — switch events** | Front cover and rear fold generate expected switch events. | Cover-triggered blanking. |
| Temperature telemetry | 🟢 **Working** | Standard interfaces and KDE expose PMIC/thermal readings. | Absolute calibration and protection effectiveness. |

### Audio, cameras and media

| Feature | Status | Observed result | Remaining validation / limits |
|---|---|---|---|
| Internal speakers | 🔴 **Broken** | No usable ALSA playback route. | Protected speaker playback. |
| Microphones | 🔴 **Broken** | No usable ALSA recording route. | Functional recording route and capture. |
| Bluetooth audio / LDAC | 🟢 **Working — stereo playback** | Clear stereo LDAC playback reported on Space Q45. | Microphone/HFP and suspend. |
| USB audio | ⚪ **Not tested** | No playback/recording test result. | Physical playback and capture. |
| Front camera | 🔴 **Broken** | No capture device or verified frame. | Functional capture pipeline. |
| Rear camera | 🔴 **Broken** | No capture pipeline or verified frame. | Functional capture pipeline. |
| Hardware video decoding / encoding | e⚪ **Not tested** | No usable codec device or verified workload. | Hardware decode/encode workloads. |

### Power, thermal management and platform services

| Feature | Status | Observed result | Remaining validation / limits |
|---|---|---|---|
| Battery percentage / voltage / temperature | 🟢 **Working — readings** | Readings available after normal boot. | Independent accuracy checks. |
| Battery current / net power | 🟢 **Working — readings** | Signed current, net battery power and charge counter available. | Protection effectiveness assessed separately. |
| Charging from computer USB | 🟡 **Partial** | USB input detected; system load can exceed the supply. | Sustained net charging under the tested load. |
| USB Power Delivery / fast charging | 🟡 **Partial — powered dock** | Battery charging through the powered dock observed. | Negotiated protocols and protection. |
| Charge limits / charge stop | 🟡 **Partial — effect unverified** | 70/80 setting retained. | Physical cutoff and restart hysteresis. |
| Battery bypass / direct system supply | ⚪ **Not qualified** | No verified bypass or battery isolation. | Physical power-path qualification. |
| Native device management | 🟡 **Partial** | Status, sensor reports and inventory functional. | Swap-partition preference and advanced controls. |
| Battery runtime estimates | 🟡 **Partial — software checks** | Model checks pass. | Qualified device forecasts unavailable. |
| Offline charging | 🔴 **Broken — charger-mode entry** | USB-triggered starts return to KDE without the charging screen. | Charger-mode entry and physical screen operation. |
| Plasma battery indicator | 🟢 **Working** | Battery icon and readings visible in KDE. | Readings only; protection separate. |
| Desktop power profiles | 🟢 **Working** | All three profiles selectable without an error. | Sustained energy and thermal behavior. |
| Thermal protection / throttling | 🟡 **Partial** | Emulated events lower CPU/GPU limits. | Actual heat response and protective shutdown. |
| Display-only soft sleep | 🟡 **Partial** | Scanout returns after off/on; one DPU timeout recorded. | Resolve timeout and repeat cycles. |
| Suspend-to-idle / s2idle | 🟡 **Partial — RTC wake tested** | One successful RTC-wake cycle. | Display, touch, power-key wake, repetition and sleep energy. |
| Deep suspend | ⚪ **Not tested** | No physical sleep/resume result. | Suspend and resume tests. |
| Power-key IRQ wake | ⚪ **Not tested** | No physical suspend-wake result. | Power-key wake from real suspend. |
| USB cable wake | 🔴 **Broken** | Required USB wake interrupts missing from the device tree. | Wake interrupt integration and physical test. |
| USB keyboard / mouse wake | ⚪ **Not tested** | No physical input-wake result. | Input wake from real suspend. |
| RTC / persistent clock | 🟡 **Partial** | Saved-time restoration and NTP functional; hardware startup time incorrect. | Hardware clock correctness. |
| Watchdog | 🟡 **Partial** | Driver starts. | Recovery behavior. |
| PMIC / regulators | 🟡 **Partial** | Essential storage/USB resources operational. | Remaining PMIC probe failures. |
| DMA / IOMMU resources | 🟡 **Partial** | Essential device paths operational. | Broader clients and lifecycle coverage. |
| Interconnect / platform power control | 🟡 **Partial** | Basic operation functional. | Provider errors and measured power/performance. |
| DSPs — ADSP / CDSP / QSH | 🟡 **Partial** | Charger and sensor services start. | Audio, other workloads and restart recovery. |
| FastRPC sensor transport | 🟢 **Working** | ADSP contexts serve sensor registry requests. | General DSP compute and restart recovery. |
| CoreSight tracing | ⏸️ **Disabled** | Autoload blocked after earlier resets. | Cause and recovery investigation. |

The current boot handoff is **EL1**. EL2/KVM work remains on a separate
experimental branch, and Project Aloha/UEFI is not the boot path used for the
reported Fedora tests.

</details>

## Downloads and building

Go to [releases](https://github.com/linuxgamer/uke-fedora/releases) and download any desktop you want. Then look at [installation guide](INSTALL.md).

To build separate Fedora 44 images on an x86_64 PC, use
`./uke-fedora-builder/build-fedora44-images.sh --cross-kernel --output build/<DESIRED FOLDER>`.
By default all desktop variants are built, add `--profiles <ANY DE YOU WANT>,<DE 2>` to select DEs.
`--cross-kernel` speeds up the kernel compilation by running Clang natively
on the x86 PC, other packages and rootfs still use AArch64 containers. On an ARM64
host, omit the flag. See the [Fedora 44 build guide](uke-fedora-builder/docs/FEDORA44-BUILD-CACHE.md) for cache, resume and rebuild options.

## Source

This repository brings together the following components as submodules:

| Component | Repository |
| --- | --- |
| Kernel and device trees | [senemos-uke-kernel](senemos-uke-kernel/) |
| Hardware support and packages | [uke-linux-hardware-support](uke-linux-hardware-support/) |
| Fedora image builder | [uke-fedora-builder](uke-fedora-builder/) |

To clone with the submodules:

```sh
git clone --recurse-submodules https://github.com/linuxgamer/uke-fedora.git
```

## License

Original files are licensed under [MIT](LICENSE). Submodules and other components retain their respective licenses. Including proprietary blobs is legal.
