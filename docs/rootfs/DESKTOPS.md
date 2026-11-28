# Desktop and console defaults

### Plasma rotation

New Plasma and Plasma Mobile sessions enable automatic rotation for the built-in `DSI-1` panel. The default uses KWin's output configuration format from the upstream Uke integration and applies rotation regardless of KWin's tablet-mode status. An existing user display configuration takes precedence. [Upstream Uke display defaults](https://github.com/MCC45TR/uke-linux-hardware-support/blob/0a27cd293fc6ce5758aab631be83c3bfe16277ff/components/uke-desktop-integration/packaging/kwinoutputconfig.json)

### Desktop defaults

Plasma and Plasma Mobile share the same KWin, PowerDevil, and Screen Locking defaults. The built-in `DSI-1` panel uses 250% scaling. The power button and lid closure request display blanking, inactivity requests suspend, and automatic locking defaults to **Never** with lock after waking from sleep off. Users can change these defaults in System Settings. [KWin output configuration](https://github.com/KDE/kwin/blob/v6.8.3/src/outputconfigurationstore.cpp) | [PowerDevil settings](https://github.com/KDE/powerdevil/blob/v6.8.3/PowerDevilProfileSettings.kcfg) | [Screen Locking page](https://github.com/KDE/kscreenlocker/blob/v6.8.3/kcm/ui/main.qml)

Both Plasma profiles include Discover with Fedora's PackageKit backend for RPM software. The combined image labels the touch-oriented app **Plasma Mobile Settings** and keeps **System Settings** for the full KDE settings interface. [Fedora Discover package](https://packages.fedoraproject.org/pkgs/plasma-discover/plasma-discover/) | [Fedora PackageKit backend](https://packages.fedoraproject.org/pkgs/plasma-discover/plasma-discover-packagekit/)

GNOME and Phosh use Fedora's GSettings schemas to enable idle suspend on battery and AC, allow automatic rotation, and disable idle locking. The GNOME session in either image enables the built-in on-screen keyboard and requests about 267% scaling for `DSI-1`, the closest scale to 250% that Mutter 51 supports at 3200×2136. Phosh uses its existing Stevia keyboard provider and Phoc requests 250% on `DSI-1`. Phosh 0.57 locks the session before system suspend in the shell. Power and lid actions follow each desktop's stock handling. Verify these settings on the tablet before qualifying the profiles. [GNOME on-screen keyboard](https://github.com/GNOME/gnome-shell/blob/51.1/js/ui/keyboard.js) | [Mutter supported scales](https://github.com/GNOME/mutter/blob/51.1/src/backends/meta-monitor.c) | [Phosh suspend and screen locking](https://github.com/PhoshMobi/phosh/blob/v0.57.0/src/screen-saver-manager.c)

### Plasma graphics

Senemos exposes Adreno rendering and display scanout as separate DRM devices. The compositor launcher lists the Adreno render node first and the display controller second for Plasma Login and signed-in Plasma sessions. This lets KWin select the GPU for rendering and keeps the display controller available for modesetting. The launcher checks the device nodes and respects an explicit KWin device selection. [KWin render-device selection](https://github.com/KDE/kwin/blob/v6.8.3/src/compositor.cpp)

### Native hardware video

The pinned Senemos package includes the Qualcomm Iris driver. When the firmware ZIP includes the pinned VPU blob, the rootfs supplies it at `/usr/lib/firmware/qcom/uke/vpu30_2v.mbn`. Check the kernel journal for `qcom-iris`, then validate native V4L2 decode and encode with real workloads. [Upstream video test matrix](https://github.com/MCC45TR/uke-linux-hardware-support/blob/0a27cd293fc6ce5758aab631be83c3bfe16277ff/components/uke-video/docs/TEST-MATRIX.md)

### TTY framebuffer keyboard

The builder reads the [BuffyBox submodule](../../rootfs/tty/buffybox) at `d0f52495f7f3afa8839eef4b19f43f4ca1243107` and its nested LVGL submodule at `85aa60d18b3d5e5588d7b247abf90198f07c8a63`. It builds the framebuffer backend with Fedora build dependencies and caches the resulting keyboard. These revisions come from the fork's keyboard recipe. [Fork source lock](https://github.com/linuxgamer/uke-linux-hardware-support/blob/847a00492f91285d84dfe2ab5c85d6260b53aee9/uke-console-input/source-lock.json)

To use the local `buffybox-3.6.0-with-lvgl.tar.xz` source bundle, pass its path with `--tty-keyboard-source`. The accepted archive SHA-256 is `e33d332ae6638652b95417dbf570fbe681d984593d2af22e127c06f3d7262327`.

The TTY service uses the Senemos NT36532 touch device, `/dev/fb0` and `uinput`. Senemos 7.3.5-47 enables `CONFIG_FB`, `CONFIG_FB_DEVICE`, and `CONFIG_DRM_FBDEV_EMULATION`. On the Xiaomi Pad 7 the running kernel exposes `/dev/fb0` through MSM DRM. Keep a USB keyboard available for the first tablet test.
