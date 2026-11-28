# Remaining feature parity

## Remaining feature parity

| Area | Remaining work |
| --- | --- |
| Desktop profiles | Qualify Plasma Mobile and Phosh first, then GNOME, which the old fork tested on hardware. Verify TTY first login and touchscreen typing separately. |
| Video and apps | Package the VA-API backend as an optional component and test longer Firefox playback, additional codecs, and higher resolutions. Plasma includes Discover for Fedora RPMs. Qualify VLC, Flatpak, and Flathub separately if they are offered. |
| Input and display | Verify multitouch and rotation alignment in all orientations, internal VRR, and both panel variants. Test basic stylus input. Have the Focus Keyboard PR author test typing, touchpad, LEDs, backlight, and resume with the pinned driver. Defer low-end brightness testing until after replacement. |
| Graphics | Qualify Vulkan image and transfer workloads, OpenCL compute, and browser GL. Track WebGPU separately because the upstream results are partial. |
| Docks and audio | Verify USB host mode and SuperSpeed, hub peripherals, USB audio, Bluetooth stereo and reconnection, USB Ethernet, and external displays and audio. Qualify external HDR, link modes, and compression with compatible gear. |
| Sensors and power | Check proximity, LED controls, charger and dock suspend/resume, real charge thresholds, thermal behavior, and battery status once its test kernel is available. Measure charger input separately. Qualify POCO NFC tag behavior and infrared where suitable hardware is available. |
| Connectivity and maintenance | Qualify SSH and LAN transfers across networks. Check KDE Connect discovery where offered. Validate optional USB networking alongside CDC ACM. Track MTP and ADB as separate opt-in additions. Qualify signed kernel updates and rollback before offering automatic updates. |

Camera capture, offline charging, and hibernation are listed as non-working upstream. Keep those outside the first rewrite release. Use the [hardware checklist](extra/README.md) for per-feature evidence. [Legacy hardware table](https://github.com/linuxgamer/uke-fedora#hardware-support) · [Upstream hardware table](https://github.com/MCC45TR/uke-linux#hardware-support) · [Video and Flatpak PR](https://github.com/linuxgamer/uke-fedora/pull/23) · [Focus Keyboard PR](https://github.com/linuxgamer/uke-fedora/pull/26)
