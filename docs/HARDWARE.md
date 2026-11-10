# Hardware bring-up status (developer view)

Status of each block on Xiaomi Pad 7 (`uke`, SM7675) for people working on the
port. This is not the user-facing table in `README.md`: it records evidence and
the technical blocker, not the marketing status.

Legend: **verified** — checked on the tablet; **reported** — owner report, no
measurement; **partial** — works with a known limitation; **broken** — does not
work; **untested** — never tried on hardware; **blocked** — needs a driver or
firmware bring-up before it can be tested.

| Block | Status | Evidence | Blocker / next step |
| --- | --- | --- | --- |
| KDE Plasma desktop | verified | r1, owner report | — |
| GNOME desktop | verified | r1, owner report | — |
| TTY / Phosh / Plasma Mobile | untested | — | built, never booted on the tablet |
| Display, TM panel | verified | native DPU/DSI, r1 | grey screen for ~2-3 s during handoff |
| Display, CSOT panel | untested | runtime variant selection exists | needs a CSOT tablet |
| Refresh rates | partial | 60/120 Hz observed | other OEM modes unverified; VRR disabled |
| Touch (NT36532) | verified | TM tablet | multitouch unreliable |
| GPU OpenGL | verified | `freedreno` renderer | — |
| GPU Vulkan | partial | experimental | not qualified |
| Video decode (H.264/HEVC) | broken | no `/dev/video*` | series active in kernel preparation and media config; boot overlay gated by `UKE_VIDEO_OVERLAY=1` (fail-soft); build/device test pending |
| CPU / DVFS | verified | all cores | — |
| Storage (UFS, growfs) | verified | rootfs grows to partition | — |
| Wi-Fi | verified | connects, transfers | — |
| Bluetooth | partial | controller works, GUI now ships | factory MAC is missing; `uke-bluetooth-address` fails, manual `btmgmt public-addr` needed |
| Audio playback | broken | no sound | no working codec/UCM path |
| Microphones | broken | — | — |
| Cameras | broken | — | no capture path |
| Stylus | broken | — | no pen input |
| Pogo keyboard | untested | issue #1 | needs a driver/ABL change |
| Sensors (IMU, compass, proximity, cover) | partial | varying support | per-sensor verification missing |
| USB-C OTG | partial | mouse via adapter | other accessories untested |
| USB CDC ACM | partial | manual on/off works | off by default |
| External display (DP/HDMI) | untested | — | — |
| Charging | partial | percentage and status | fast charge, limits, bypass unverified |
| Battery percentage | reported | KDE applet | — |
| Battery time estimate | broken | `energy_*` are zero | driver patch `0127-qcom-battmgr-report-energy-in-mah` on branch `fix/battmgr-energy-mah`; needs device test |
| Suspend / wake | partial | basic suspend | wake unreliable |
| Reboot | partial | works in some tests | — |
| Shutdown | partial | can hang or reboot | — |
| zram swap | fixed after r1 | `zram-generator`, `CONFIG_ZRAM=m` | verify on the next image |
| Boot reliability | uncertain | issue #8 | `boot_a` ends in fastboot after some use; cause unknown, see `private/issue-8-hypotheses.md` |

## Notes for bring-up work

- **Video** needs a new `videocc-cliffs` clock/power driver, Iris platform data
  for `qcom,cliffs-iris`, media config and the vendor-signed VPU firmware. The
  OEM DTB describes the block at `0x0aa00000` with the same layout as SM8550.
- **Firmware for video is not in the fastboot package.** Only names such as
  `vpu30_2v.mbn` appear in `super.img`; the files live on the `firmware`
  partition, which this package does not flash. Dump it from the tablet (TWRP or
  a rooted Android) or from a full OTA that includes the firmware partition.
- **Bluetooth** address: the factory MAC is not exposed; `btmgmt public-addr`
  works around it, but a proper fix belongs in the driver or ABL handoff.
- **Battery energy**: the charger reports capacity in mAh while the driver only
  exported `ENERGY_*` for mWh. Patch derived energy from charge × voltage.
- **Boot loop**: userspace does not write `boot_a`; the fastboot fallback is an
  ABL-side decision (slot or boot-attempt state) or repeated boot failures.

## Verification commands

```sh
# display and GPU
cat /sys/class/drm/card0/device/uevent
glxinfo -B 2>/dev/null | head

# video (after bring-up)
dmesg | grep -i iris
ls -l /dev/video*
v4l2-ctl --list-formats

# battery
upower --dump | grep -E 'energy|percentage'

# bluetooth
bluetoothctl list
journalctl -b -u uke-bluetooth-address

# zram
zramctl
swapon --show
```
