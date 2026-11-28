# Build inputs

- Supply the Senemos core RPM specified in `kernel/senemos-prebuilt.json`. See the [dependency inventory](DEPENDENCIES.md) for the bring-up artifact's origin.
- Use the reviewed stock `boot.img` from OS3.0.304.0.WOZMIXM. The wrapper verifies its SHA-256.
- Supply the files pinned in `build/inputs/console-firmware.json` as ZIP entries. The bundle covers the GPU, both NT36532 panel variants, WCN6750 Wi-Fi and Bluetooth, the ADSP, the FS19xx speaker preset, the Forte speaker ACDB data, and the Global OS3.0.304.0 SSC inputs. The Forte file comes from `/odm/etc/acdbdata/Forte/Forte_acdb_cal.acdb` in the same stock ROM. Keep local inputs and blob-bearing outputs private during bring-up.

For an Iris video test image, add the matching OEM `vpu30_2v.mbn` from OS3.0.304.0.WOZMIXM to the ZIP at `qcom/uke/vpu30_2v.mbn`. Its size and SHA-256 are pinned in `build/inputs/console-firmware.json`. The existing ZIP still builds an image without VPU firmware. [Legacy firmware packaging](https://github.com/linuxgamer/uke-linux-hardware-support/commit/2b14d5bffd) | [Hardware video checks](../rootfs/DESKTOPS.md#native-hardware-video)

For a Focus Keyboard test image, add the O81 `MCU_Upgrade.bin` from the keyboard PR's pinned kernel at ZIP entry `qcom/uke/nanosic/MCU_Upgrade.bin`. The builder verifies its size and SHA-256 and stages the bytes unchanged for the pinned Senemos Nanosic driver. The firmware stays local. [Keyboard PR](https://github.com/linuxgamer/uke-fedora/pull/26) | [Pinned firmware revision](https://github.com/linuxgamer/senemos-uke-kernel-mainline/commit/4a37b10832fac85abbb2e7e14b29c7322d164363)

The builder compiles the hardware-support and HexagonRPC sources from the local submodules and the pinned speaker helper for Fedora AArch64. The built image uses the tablet's factory partition for sensor and speaker calibration and its Bluetooth address.

Use `--profile kde` for the KDE preview image or `--profile phosh-gnome` for the Phosh and GNOME preview image. The older names `plasma-mobile` and `phosh` resolve to the same respective profiles and output folders. The default `plasma` profile builds desktop Plasma alone, and `--profile gnome` builds GNOME alone. `--profile tty` builds Buffyboard from the BuffyBox and nested LVGL submodules. See the [TTY source options](../rootfs/DESKTOPS.md#tty-framebuffer-keyboard).

The builder writes `boot.img`, `userdata.img`, `manifest.json`, and `SHA256SUMS` under `build/out/<profile>/`. Every profile uses the same slot-A boot image and `userdata` root selector. The Android sparse `userdata.img` contains an ext4 filesystem labeled `UKE_LINUX` as required by the Senemos initramfs, sized at 4 GiB for graphical profiles or 2 GiB for TTY. Systemd grows it to fill the partition.
