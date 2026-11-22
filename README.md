<table>
<tr>
<td width="65%" valign="top">
<h1>Uke Linux</h1>
<p><strong>Fedora Rawhide for Xiaomi Pad 7 and POCO Pad X1</strong></p>
<p>A community Linux port for the Snapdragon 7+ Gen 3 (SM7675), running the standard Fedora KDE Plasma desktop.</p>
<p><strong>Experimental alpha</strong> · AArch64 · <code>uke</code></p>
</td>
<td width="35%" valign="top" align="center">
<br>
<img src="assets/images/uke-fedora-mockup.png" width="240" alt="Xiaomi Pad 7 mockup with Fedora KDE Plasma">
</td>
</tr>
<tr>
<td colspan="2" align="center">
<img src="assets/screenshots/KDE-Plasma/Fedora_Rawhide_X1_UKE_KDE_Plasma_Fastfetch_731.png" width="100%" alt="Fedora Rawhide with KDE Plasma on the Uke development installation, 17 October 2026">
</td>
</tr>
</table>

[Downloads](#downloads) · [Hardware support](#hardware-support) · [Build from source](#build-from-source) · [Documentation](#documentation) · [Report a problem](CONTRIBUTING.md)

> [!WARNING]
> This is experimental software, provided as is. Back up your data before installing. The singleboot image erases Android data, and charging protection is not fully verified. Use it at your own risk.

## Project status

**Last updated: 18 November 2026.**

Fedora Rawhide and KDE Plasma run on the tested **POCO Pad X1, 8 GB / 512 GB**. Display, touch, Wi-Fi, Bluetooth mouse and stereo audio, automatic rotation, automatic brightness, internal speakers, and microphones have all worked in device tests. Adaptive sync / VRR works across the 30–144 Hz range. HDMI output and monitor audio work through tested Juo JH925 dock.

Four-speaker playback was verified at gain 223 (OSS 243). Higher gain with verified speaker protection, 45 W charging, camera capture, reliable suspend and hibernation remain under development. See the [changelog](CHANGELOG.md) for earlier development updates.

[Linux 7.3.5-2-unstable](https://copr.fedorainfracloud.org/coprs/mcc45tr/uke-linux-unstable/build/11351293/) is the latest development kernel confirmed running through the stock Android bootloader.

## Distribution roadmap

**Fedora Rawhide is the only active distribution port yet.** Development uses
the `Fedora` branch. Ubuntu and Arch Linux editions are planned, with image,
installer, and device testing still pending.

Past TEST and EL2/KVM work is retained in Git history for future reference,
without replacing the currently reviewed Fedora submodule pins. See the
[distribution roadmap and consolidated branch notes](DISTRIBUTIONS.md).

## Downloads

New Fedora Rawhide singleboot ZIP will be available soon. Once it is available, connect the tablet to your computer in Fastboot mode and run the following command from the directory containing the ZIP.

```sh
fastboot update ./fedora*.zip
```

## Hardware support

These results cover Fedora Rawhide AArch64 development builds tested from **14 October to 18 November 2026** on the **POCO Pad X1, 8 GB / 512 GB**. Some features were tested on earlier kernels and still need retesting on Linux 7.3.5. Hardware qualification on the Xiaomi Pad 7 and other memory and storage variants remains open.

🟢 Working in the listed tests · 🟡 Partial · 🔴 Not working · ⚪ Not verified · ⏸️ Disabled

<details>
<summary><strong>Boot, CPU and storage</strong></summary>

| Feature | Status | Notes |
| --- | --- | --- |
| Fedora boot | 🟢 Working | Linux 7.3.5-2-unstable boots through the stock Android bootloader. The earlier prolonged gray screen was fixed in 7.3.4 tests. The Uke Plymouth theme appears during Linux startup, with a brief interruption around the display handoff. |
| CPU and power profiles | 🟢 Working | All eight cores and three frequency policies work. Sustained loads need more testing. |
| RAM | 🟢 Working | Linux reports 7.21 GiB; sustained stress testing remains incomplete. |
| UFS storage and EXT4 | 🟢 Working | Basic read/write tests, scaling, and WriteBooster work. |
| UFS MCQ and inline encryption | 🟡 Partial | MCQ starts and a bounded direct read passes. A read-only inline encryption test exercised the hardware key path. Encrypted writes, hardware-backed key release, and concurrent queues still need testing. |
| Memory bandwidth and cache monitoring | 🟡 Partial | CPU/DDR monitors and eight cache counters respond. Counter units, scaling, and MEMLAT policy need more work. |
| Reboot | 🟢 Working | Normal reboot returns to Fedora. The tested updater can retain a working boot slot while staging a signed kernel update. |
| Shutdown | 🟢 Working | The Uke Plymouth theme appears during the shutdown phase of a reboot. |
| Reboot to Fastboot | 🟢 Working | Bootloader entry works. Fastboot was used to select and boot the retained Linux slot after a failed kernel trial. |
| Reboot to recovery | 🔴 Not working | A recovery reboot returned to Fedora in the recorded test. |
| UEFI, EL2 and KVM | ⚪ Not verified | Separate experimental work; not used for the Fedora results above. |

</details>

<details>
<summary><strong>Display, graphics and input</strong></summary>

| Feature | Status | Notes |
| --- | --- | --- |
| Internal display | 🟢 Working | Native display output at 3200×2136. |
| Fixed refresh rates | 🟢 Working | 30, 48, 50, 60, 90, 120, and 144 Hz. |
| Manual brightness | 🟢 Working | Backlight adjustment works. |
| Screen off/on | 🟢 Working | The display turns off and back on normally. |
| Color depth | 🟡 Partial | Active 10-bit framebuffer and DSC link; output depth cannot be selected. |
| Touchscreen | 🟢 Working | Finger and multi-touch input work on the configured installation. Recent development tests still recorded touch packet errors. Gestures and suspend/resume need more testing. |
| Adaptive sync / VRR | 🟢 Working | Works across the tested 30–144 Hz range on the internal display. |
| KDE Plasma / Wayland | 🟢 Working | KDE Plasma and desktop applications run reliably in a Wayland session. |
| Adreno 732 / OpenGL | 🟢 Working | Hardware-accelerated OpenGL ES works through Freedreno. |
| Vulkan / OpenCL | 🟡 Partial | Some transfer and compute tests pass; Vulkan image tests still fail. |
| Browser graphics / WebGPU | 🟡 Partial | GL works; operation with the GPU sandbox is unverified. Chrome has no WebGPU adapter. |
| Power and volume buttons | 🟢 Working | Normal input works; waking from suspend is unverified. |
| Stylus | 🟡 Partial | Pen input works, but pressure sensitivity and tilt are not supported yet. |
| USB mouse | 🟢 Working | Tested with a receiver through the powered Juo dock. |
| USB and pogo keyboards | ⚪ Not verified | The system detected a USB keyboard. Typing and pogo touchpad tests remain open. |
| KDE Plasma on-screen keyboard | 🟢 Working | The standard KDE Plasma on-screen keyboard works. |

</details>

<details>
<summary><strong>Networking, USB and external displays</strong></summary>

| Feature | Status | Notes |
| --- | --- | --- |
| Wi-Fi | 🟢 Working | Automatic connection, SSH, and file transfers work. |
| Bluetooth | 🟢 Working | Mouse pairing, reconnection, and LDAC stereo playback tested. Microphone modes remain unverified. |
| KDE Connect discovery | 🟢 Working | Device discovery works; pairing and transfers need testing. |
| USB-C roles and accessory power | 🟡 Partial | Device mode and dock peripherals work; role changes, power delivery, and reconnects need testing. |
| USB SuperSpeed | 🟡 Partial | Devices connect at 5 Gbit/s; storage throughput is unverified. |
| USB serial and network gadgets | 🟢 Working | Manual CDC ACM and ECM/SSH setup works. Both are off by default. |
| USB hubs | 🟢 Working | USB 2/3 devices detected through the tested Juo dock. |
| USB-C video output | 🟢 Working | HDMI through Juo works at 2560×1440: 60 Hz RGB10 and 75 Hz RGB8. These modes were tested separately. |
| External HDR | 🟢 Working | KDE Plasma outputs HDR to a compatible external display, including at 1440p60. |
| MST and four-lane DisplayPort | 🟢 Working | External DisplayPort output works at 3840×2160 at 60 Hz. |
| External DSC/FEC | 🟢 Working | Display Stream Compression and Forward Error Correction work on the external display connection. |
| Monitor brightness over DDC/CI | 🔴 Not working | Queries fail and brightness commands have no visible effect through either Juo HDMI socket. |
| USB Ethernet | 🟢 Working | RTL8153 connects at 1 Gbit/s. Receive drops and sustained throughput still need investigation. |
| NFC tag interface | 🟡 Partial | The POCO-specific tag driver registers and a bounded I2C read passes. External RF transfer remains unverified; this is not reader support. |
| Infrared transmitter | ⚪ Not verified | The transmitter registers; optical output and receiver response remain untested. |

</details>

<details>
<summary><strong>Sensors and desktop integration</strong></summary>

| Feature | Status | Notes |
| --- | --- | --- |
| Screen rotation | 🟢 Working | Manual and automatic rotation work, with matching touch coordinates in all four orientations. |
| Automatic brightness | 🟢 Working | Responds to front and rear light sensors. |
| Front proximity sensor | 🟢 Working | Near/far detection works. |
| Gyroscope and compass | 🟡 Partial | Gyroscope readings are available, but motion response is unverified. Compass accuracy tests fail. |
| Magnetic cover detection | 🟢 Working | Cover events work; automatic screen blanking is unverified. |
| Ambient color temperature | ⚪ Not verified | No calibrated color-temperature reading. |
| Light flicker sensing | 🟡 Partial | Seven raw channels are readable; units and response to controlled lighting remain unverified. |
| SAR / body proximity | ⏸️ Disabled | No usable sensor response. |

</details>

<details>
<summary><strong>Audio, cameras and video</strong></summary>

| Feature | Status | Notes |
| --- | --- | --- |
| Internal speakers | 🟢 Working | All four speakers passed separate low-level playback tests at gain 223. Channel rotation worked in earlier tests. Calibrated feedback, limiter behavior, and higher gain remain unverified. |
| Microphones | 🟢 Working | Internal microphone recording works. |
| Bluetooth and HDMI audio | 🟢 Working | Stereo playback tested with Space Q45 headphones and a monitor through Juo HUB. |
| USB audio | 🟢 Working | USB audio playback and recording work. |
| Front and rear cameras | 🔴 Not working | Capture for both cameras is in development. Read-only access to the front camera calibration EEPROM works. |
| Native hardware video | 🟢 Working | Native hardware-accelerated video decoding and encoding work. |
| VA-API and browser video | 🟡 Partial | Seven H.264, HEVC, and VP9 modes passed short decode tests. A five-minute Chrome 4K60 run averaged 59.93 compositor submissions per second and reported 41 dropped frames. HDR, display frame pacing, and longer playback still need testing. |

</details>

<details>
<summary><strong>Battery, power and platform services</strong></summary>

| Feature | Status | Notes |
| --- | --- | --- |
| Battery and temperature readings | 🟢 Working | Charge, voltage, current, power, and temperature readings are available; KDE shows battery status. Energy estimates and calibration remain incomplete. |
| USB charging / Power Delivery | 🟡 Partial | Charging through a powered dock works, and the tablet detected a directly connected USB-PD adapter. The negotiated power profile and 45 W charging remain unverified. |
| Charge limits | 🟢 Working | Charging follows the configured stop and restart thresholds. |
| Charging protection | ⚪ Not verified | Battery, charger, and USB-C temperature readings are available. Electrical cutoff, moisture detection, and fault response still need physical verification. |
| Battery bypass | ⚪ Not verified | Low net battery current is observed under dock power; this does not establish direct power or battery isolation. |
| Offline charging | 🔴 Not working | Connecting power while the tablet is off automatically boots Fedora. |
| Suspend-to-idle | 🟡 Partial | One RTC wake cycle passed. Display, touch, repeated resume, and sleep power use need testing. |
| Deep suspend and input wake | ⚪ Not verified | Deep sleep, power-button wake, and USB input wake have not been tested. |
| Hibernation | 🔴 Not working | The development installation uses partition-backed swap. Hibernation remains unavailable under kernel integrity lockdown. |
| USB cable wake | 🔴 Not working | Required wake interrupts are missing. |
| Thermal protection | 🟢 Working | Thermal management monitors temperatures and applies CPU and GPU limits. |
| RGB notification LED | 🟢 Working | Basic colors tested; notification behavior and extended use need testing. |
| Flashlight | ⚪ Not verified | Control code exists; physical output has not been confirmed. |
| Clock | 🟡 Partial | Saved time and NTP work; hardware startup time is incorrect. |
| PMIC, DSP and platform services | 🟡 Partial | WPSS and ADSP run. CDSP compute, PMIC access warnings, and restart recovery still need work. |
| CoreSight tracing | ⏸️ Disabled | Disabled after earlier resets. |

</details>

## Build from source

```sh
git clone --branch Fedora --recurse-submodules https://github.com/MCC45TR/uke-linux.git
cd uke-linux
./ukelinux.sh
```

To update an existing workspace from this repository:

```sh
git pull --ff-only --recurse-submodules
git submodule update --init --recursive
```

The components track the branches declared in `.gitmodules` (`main`, or `R12.0`
for OrangeFox). The hourly workspace workflow updates their recorded revisions
after validation. To follow the component branch tips immediately, run
`git submodule update --init --remote --checkout`. Keep local component changes
committed or stashed before updating. Git submodules always record a commit in
the parent; branch tracking and the refresh workflow advance that record.

For a kernel-only build:

```sh
./ukelinux.sh --build kernel
```

The menu includes desktop, filesystem, boot-layout, and package-channel options. Build output is saved to `out/` in the directory where the command is run. See the [public build guide](https://github.com/MCC45TR/uke-fedora-builder/blob/main/docs/PUBLIC-BUILD.md) for supported hosts, requirements, and installation instructions. The [pinned release recipe](https://github.com/MCC45TR/uke-fedora-builder/blob/b0fd2380b07dbaaf37403c057b74796faf8f5ed3/docs/PUBLIC-BUILD.md) describes the earlier 26 October KDE EXT4 image.

### Manual GitHub image builds

Open [EXT4 singleboot image and release](https://github.com/MCC45TR/uke-linux/actions/workflows/image-release.yml)
and select **Run workflow** on `Fedora`. Choose KDE Plasma, GNOME, Cutefish
or Plasma Mobile, a login shell, and an initial 16 GiB or 8 GiB filesystem
(16 GiB is the default). The workflow selects the unstable channel;
`latest` resolves the current unstable kernel once for that run;
an exact `7.3.x-N.fc46` tuple can also be supplied.

The native ARM64 workflow composes and validates the image from signed
packages. The [Cutefish workflow](https://github.com/MCC45TR/uke-linux/actions/workflows/cutefish-image.yml)
first checks source contracts and host capacity; `compose` produces test artifacts
without publishing. Cutefish requires physical first-account and login acceptance
before a release. Plasma Mobile follows the original Fedora November 14 compose
mobile groups, with Uke's signed unstable kernel and existing account setup.
Optional publication creates an image-only pre-release; manifests
and build receipts are retained in Actions for 90 days. Host validation
does not establish physical tablet boot, first-account setup, charging or
recovery acceptance.

### Updates

After the first Fedora boot, update from the configured signed repositories:

```sh
sudo dnf update --refresh
```

Keep the kernel, modules, device trees, and boot profile matched. The current
development updater automatically stages a matching boot image to the inactive
slot and preserves the previous working slot. For R4, follow the [release instructions for kernel updates](https://github.com/MCC45TR/uke-linux/releases/tag/fedora-rawhide-uke-senemos-021126-r4#after-installation).
Wait for the updater to report that staging is complete before rebooting, then
confirm the running version with `uname -r`.

## Documentation

| Topic | Link |
| --- | --- |
| Builds and installation | [Public build guide](https://github.com/MCC45TR/uke-fedora-builder/blob/main/docs/PUBLIC-BUILD.md) · [Manual installation and rollback](https://github.com/MCC45TR/uke-fedora-builder/blob/main/docs/PUBLIC-BUILD.md#output-and-manual-installation) |
| Development updates | [Changelog](CHANGELOG.md) |
| Distribution roadmap and archived branches | [DISTRIBUTIONS.md](DISTRIBUTIONS.md) |
| Screenshots | [Fedora KDE gallery](assets/screenshots/README.md) |
| Contributions and bug reports | [Contributing guide](CONTRIBUTING.md) · [Open an issue](https://github.com/MCC45TR/uke-linux/issues/new?template=bug_report.yml) |
| Security reports | [Security policy](SECURITY.md) |

<details>
<summary>Maintainer notes — access required</summary>

[Development plan](https://github.com/MCC45TR/uke-linux-docs/blob/main/PLAN.md) · [Engineering records](https://github.com/MCC45TR/uke-linux-docs/blob/main/docs/README.md)

</details>

## Project repositories

| Component | Repository |
| --- | --- |
| Kernel and device trees | [senemos-uke-kernel-mainline](https://github.com/MCC45TR/senemos-uke-kernel-mainline) |
| Hardware integration and packages | [uke-linux-hardware-support](https://github.com/MCC45TR/uke-linux-hardware-support/tree/main) |
| Image builder | [uke-fedora-builder](https://github.com/MCC45TR/uke-fedora-builder/tree/main) |
| Image distribution | [uke-linux-images](https://github.com/MCC45TR/uke-linux-images/tree/main) |
| Desktop environment packaging | [uke-desktop-environment-support](https://github.com/MCC45TR/uke-desktop-environment-support/tree/main) |
| OrangeFox Recovery | [orangefox_device_xiaomi_uke](https://github.com/MCC45TR/orangefox_device_xiaomi_uke/tree/R12.0) |
| Experimental UEFI | [uke-project-aloha](https://github.com/MCC45TR/uke-project-aloha/tree/main) |

These links follow development branches. The submodules track the branches in `.gitmodules`; the workspace refresh workflow advances their recorded revisions after validation.

## Thanks

Thanks to [RealDexxo](https://github.com/RealDexxo) for work on speaker support and improvements to the build scripts.

## License

Original files are covered by the [MIT License](LICENSE). Components retain their own licenses and attribution.

Uke Linux is an independent community project, unaffiliated with Fedora, Xiaomi, POCO, or Qualcomm.
