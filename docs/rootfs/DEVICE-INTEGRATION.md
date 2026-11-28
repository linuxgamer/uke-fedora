# Device integration

## Image hardware requirements

Aim for roughly the features demonstrated in upstream device tests. Use stock Fedora components where they cover the feature and keep the remaining Uke integration in this project. Use the upstream package sources to identify firmware requests, configuration and runtime helpers. A feature belongs in the candidate once its required pieces are present. Record actual support after the hardware session. [Upstream hardware results](https://github.com/MCC45TR/uke-linux#hardware-support) · [Upstream hardware integration](https://github.com/MCC45TR/uke-linux-hardware-support)

| Feature | What the candidate needs |
| --- | --- |
| Desktop and graphics | Start the first tablet test with the stock Fedora Plasma profile. All four graphical profiles use stock Fedora Mesa, the Senemos MSM graphics driver and the pinned GPU firmware. |
| Touch and input | Senemos `7.3.5-47` embeds native display overlays for Tianma and CSOT that bind the OEM Novatek node to its NT36532 module. The local firmware ZIP supplies both panel-specific files checked against the digests in that module. Use this kernel input path for the first candidate and verify panel selection and multitouch on hardware. |
| Wi-Fi, Bluetooth and USB-C | The pinned kernel has WCN6750 Wi-Fi and Bluetooth drivers and USB-C support. The local ZIP supplies WPSS, the referenced global Wi-Fi board and regulatory data, and the Bluetooth MS12 firmware and NVM. Check controller address setup and dock functions on the tablet. |
| Audio | The pinned Senemos RPM supplies the Qualcomm audio topology, ALSA profiles for speaker and DisplayPort playback and microphone capture, and WirePlumber rules. The local ZIP supplies the OEM ADSP, its split DTB firmware, and the FS19xx preset. The image uses stock Fedora ALSA, PipeWire, and WirePlumber. Playback and capture on the tablet remain part of the first desktop session. |
| Sensors and power | Senemos ships SSC IIO and Qualcomm battery drivers. Use the staged ADSP with the SSC driver, then check that stock SensorProxy can use the resulting sensor channels and that UPower can read the battery. Keep calibration and identifiers local to each tablet. |

Each image stages 150 checksum-pinned OEM files, including 70 for SSC. The WPSS, ADSP and ADSP DTB bundles contain all external load segments declared in their headers.

The slot-A wrapper keeps the stock Android bootloader path. Senemos adapts the bootloader-selected device tree before Linux probes devices. The NT36532 binding comes from the embedded panel overlays. Both overlays target the OEM Novatek node referenced by the stock `dtbo.img`, and the same kernel payload is used in our wrapped `boot.img`. [Senemos boot adaptation](https://github.com/MCC45TR/senemos-uke-kernel-mainline/blob/38c2f657506822a73a5bc6e7626e08d6c16ecaec/kernel/overlay/arch/arm64/kernel/uke-abl.c) · [Panel binding source](https://github.com/MCC45TR/senemos-uke-kernel-mainline/blob/38c2f657506822a73a5bc6e7626e08d6c16ecaec/kernel/overlay/arch/arm64/boot/dts/qcom/sm7675-uke-thp.dtsi)

Camera capture, hibernation, and charging or speaker modes that still need upstream qualification can follow later. Include the boot and rootfs images together for host verification before the first tablet session. [Upstream hardware results](https://github.com/MCC45TR/uke-linux#hardware-support)

### Audio checks for the first tablet session

After desktop login, use `wpctl status --name` to identify the output and microphone node names. Start playback at a low volume.

1. Play the same short WAV with `pw-play --target OUTPUT_NODE sample.wav` through the internal speakers, then through a DisplayPort audio device and paired Bluetooth headphones. Record the result for each route.
2. Record a short sample from the internal microphones with `pw-record --target MIC_NODE --rate 48000 --channels 4 --channel-map AUX0,AUX1,AUX2,AUX3 uke-mic.wav`. Stop with Ctrl+C and check for a signal on each channel.
3. If a route fails, save `wpctl status` and `pw-dump` alongside the tablet model, panel variant and kernel release. [PipeWire playback and capture tools](https://docs.pipewire.org/page_man_pw-cat_1.html)

## Hardware-support package audit

Use Senemos for drivers and select stock Fedora software directly. Carry forward the device-specific files and behavior needed for feature parity. The audit compared the two hardware-support revisions pinned by the reference ports. [Upstream pin](https://github.com/MCC45TR/uke-linux-hardware-support/tree/0a27cd293fc6ce5758aab631be83c3bfe16277ff) · [`uke-fedora` pin](https://github.com/linuxgamer/uke-linux-hardware-support/tree/847a00492f91285d84dfe2ab5c85d6260b53aee9)

| Legacy packages or area | Rewrite plan |
| --- | --- |
| Core and desktop metapackages, compatibility builds, and repository wrappers | Use the project package list with stock Fedora Plasma, Mesa, BlueZ, PipeWire, NetworkManager, UPower, and other distribution packages. Diagnose any remaining compatibility gap against the selected Fedora build. |
| `uke-touchscreen`, OEM data and firmware RPMs | Use the pinned Senemos NT36532 driver and the local firmware ZIP. Keep per-device calibration and addresses out of the generic bundle. Confirm the kernel touch path on both panel variants. |
| `uke-displayport-audio` and `uke-speaker-firmware` | Supply the Uke ALSA UCM profiles for the active card and the OEM FS19xx preset through the image and firmware ZIP. Fedora 45's checked `alsa-ucm` RPM has no Uke/SM7675 profiles. The pinned amplifier module explicitly requests `qcom/uke/audio/fs19xx.fsm`. Qualify speaker, microphone and DisplayPort routes on hardware. |
| Wi-Fi and Bluetooth factory setup | The image includes stock NetworkManager, stock BlueZ, and the upstream Bluetooth factory-address helper. |
| SSC, SensorProxy, adaptive display and power packages | The image includes the DSP filesystem service alongside Fedora SensorProxy and UPower. Qualify sensor selection and charging behavior on the tablet. |
| Boot integration, install profiles and kernel updater | Carry forward the slot-A/`userdata` configuration, filesystem growth, and matched boot-image and module updates with recovery. The legacy packages provide device behavior beyond installing kernel files. |
| TTY input | Build the fork's pinned BuffyBox source and bind the keyboard to Senemos touch input. Check first-boot password entry and VT switching during the first tablet test. |
| Uke Control, NFC/IR, themes, recovery and diagnostics | Review these against the replacement criteria. NFC/IR uses Senemos drivers and may still need a udev rule or userspace tool. Choose desktop settings, debug tools and optional apps based on the features we keep. |

The builder takes the audio data and license directly from the pinned Senemos core RPM. This includes the UCM lookup links for both tablet names, the release-specific microphone rules and topology, and the microphone channel layout. The FS19xx preset was extracted from stock `/odm/firmware/fs19xx.fsm` and matched the upstream spec's SHA-256. [Kernel pin](../../kernel/senemos-prebuilt.json) · [Senemos audio policy](https://github.com/MCC45TR/senemos-uke-kernel-mainline/tree/3689b8c48c3f029743a29774a17b84dac7134f6c/src/audio/desktop) · [Speaker preset](https://github.com/MCC45TR/uke-linux-hardware-support/blob/0a27cd293fc6ce5758aab631be83c3bfe16277ff/components/xiaomi-uke-firmware/packaging/speaker-firmware/uke-speaker-firmware.spec)

When the Uke sound card appears, the speaker provisioning service reads the generic Forte data from the firmware bundle and the tablet's calibration from `/mnt/vendor/persist/audio`. The mount is read-only and the helper keeps the per-device calibration in memory. Senemos admits the protected speaker graph after provisioning. Check the state with `sudo /usr/libexec/uke-speaker-runtime --status`. The helper comes from the upstream `uke-speaker-runtime-0.4-3.src.rpm` with SHA-256 `22f97cc686e6746cb035865fbf9ba6e7161d3ba00034f8dc7742dd942db286c4`. It includes the idempotent loading behavior from the pinned `uke-control` integration. [Upstream source archive](https://github.com/MCC45TR/uke-linux-hardware-support/releases/tag/copr-consolidation-archive-20261101) · [Upstream provisioning behavior](https://github.com/MCC45TR/uke-linux-hardware-support/blob/0a27cd293fc6ce5758aab631be83c3bfe16277ff/components/uke-control/docs/SPEAKER-RUNTIME-CONSOLIDATION.md)

### Bluetooth factory address

The builder takes the Bluetooth helper, SSC cache helper, service units, and HexagonRPC patches from the [hardware-support submodule](../../rootfs/device-helpers/hardware-support) at `0a27cd293fc6ce5758aab631be83c3bfe16277ff`. The [HexagonRPC submodule](../../rootfs/device-helpers/hexagonrpc) is pinned to `510c87e5c89026ee2bd2034776fc4d15994f353d`. The local mount unit disables ext4 journal replay on `persist`.

The pinned `qca/msnv12.bin` contains the generic Qualcomm address. The Bluetooth helper runs for the onboard controller and reads `persist/bluetooth/.bt_nv.bin` from the physical partition mounted read-only. It supplies the address through the BlueZ management API when the controller requests it and checks the address on an already configured controller. Keep that file per-device. Compare the controller address from `btmgmt info` with the factory address locally during bring-up. [Upstream Bluetooth integration](https://github.com/MCC45TR/uke-linux-hardware-support/blob/0a27cd293fc6ce5758aab631be83c3bfe16277ff/components/uke-desktop-integration/docs/BLUETOOTH.md)

### SSC sensors

Senemos `7.3.5-47` ships `uke-ssc.ko`. After SSC discovery and metadata validation, it publishes acceleration and illuminance through standard IIO channels. Fedora 45's SensorProxy rules recognize those channels and start the proxy when they appear. Keep stock SensorProxy and check orientation and front/rear light selection with `monitor-sensor` on the tablet. If IIO devices are missing, check the driver's `ssc_client_connected`, `ssc_ready_sensors`, `ssc_registered_sensors`, and `ssc_last_error_stage` attributes to locate the failure. [Senemos IIO driver](https://github.com/MCC45TR/senemos-uke-kernel-mainline/blob/38c2f657506822a73a5bc6e7626e08d6c16ecaec/kernel/overlay/drivers/iio/common/uke-ssc/uke-ssc-iio.c) · [SSC diagnostics](https://github.com/MCC45TR/senemos-uke-kernel-mainline/blob/38c2f657506822a73a5bc6e7626e08d6c16ecaec/kernel/overlay/Documentation/ABI/testing/sysfs-driver-uke-ssc)

The FastRPC device starts the filesystem service. The service prepares a disposable registry in RAM using model-specific OEM data and calibration from read-only `persist`. Its inputs are 68 ODM sensor files including `json.lst`, the vendor `sns_reg.conf`, and the DSP `sns_tppe.so`. The pinned Global OS3.0.304.0 list refers to two absent AK7323 JSON files. The build preserves the original list. Upstream reported native IIO readings with the filesystem service running. Qualify the result on the tablet with stock SensorProxy. [Upstream filesystem service report](https://github.com/MCC45TR/uke-linux-hardware-support/blob/0a27cd293fc6ce5758aab631be83c3bfe16277ff/components/uke-sensors/docs/SSC-SERVICE-DECOUPLING.md) · [OEM input provenance](https://github.com/linuxgamer/uke-linux-hardware-support/blob/847a00492f91285d84dfe2ab5c85d6260b53aee9/xiaomi-uke-firmware/manifests/oem-runtime-source.json)
