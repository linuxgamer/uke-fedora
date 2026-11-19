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
| Touch (NT36532) | verified | TM tablet, 10-point multitouch | the CSOT variant is untested |
| GPU OpenGL | verified | `freedreno` renderer | — |
| GPU Vulkan | partial | experimental | not qualified |
| Video decode (H.264/HEVC) | broken | no `/dev/video*` | Two independent blockers. No V4L2 device: the DT overlay asks for `qcom,sm7675-videocc`, and the 21-patch video series does add that compatible to `videocc-sm8550.c`, but the boot overlay stays behind `UKE_VIDEO_OVERLAY` (0 by default, 1 in CI) and nothing has confirmed the clock controller or the VPU firmware loading on hardware. Separately, Fedora's own ffmpeg build disables the `h264` decoder and ships only `libopenh264`, whose PrefetchPic rejects streams above a few reference frames, so some files do not decode even in software |
| CPU / DVFS | verified | all cores | — |
| Storage (UFS, growfs) | verified | rootfs grows to partition | — |
| Wi-Fi | verified | connects, transfers | — |
| Bluetooth | partial | controller works, keyboard/mouse/headphones pair | factory MAC is not exposed, so the address is random after each boot unless `btmgmt public-addr` sets one |
| Audio playback | verified | speaker-test on the four amplifiers | ACP discards a UCM profile when any mapping fails to open. The speaker verb carried `HDMI1` on `hw:0,0`, which returns EINVAL on this kernel, so the whole HiFi profile went away and the card offered only `off` and `pro-audio` - no sink, dummy output. With the device removed the profile is accepted and UCM's EnableSequence enables the amplifiers. `hw:0,0` itself is still broken and is the remaining kernel bug here |
| Microphones | verified | four-channel capture | routed through the same HiFi profile |
| Cameras | broken | — | no capture path |
| Stylus | broken | — | no pen input |
| Pogo keyboard | partial | keys and Caps Lock, then the MCU stops scanning | The MCU asks for an MiAuth token on its own timer (observed as `0x24` with `p[6]=0x64`, once a minute, at 829 s and 889 s in one session) and stops reporting keys when the window closes. The token is signed by the Android devauth TA over RPMB, which Linux cannot reach, and answering with a zero token is worse than silence because the MCU then treats the session as failed. Workaround: pulse the reset line, about 70 ms with the supplies untouched, driven by an idle-aware helper - each pulse costs the Caps Lock state and any keystroke it lands in the middle of. The MCU firmware (`odm/firmware/MCU_Upgrade.bin`, `NANO IC` header, plain byte-sum, no signature) carries no recognisable ARM or Thumb instruction stream - no `bx lr`, no Thumb NOP, and fewer BL prefixes than random data - so the image is packed or encrypted and the gate cannot be removed from that side without the bootloader's key |
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
| Boot reliability | verified | issue #8 closed | the report was a reporter tablet fault, not the port; keep watching for a recurrence |

## Notes for bring-up work

- **Video** has its clock and Iris patches: the 21-patch series adds a
  `qcom,sm7675-videocc` compatible to `videocc-sm8550.c` (`CONFIG_SM_VIDEOCC_8550=m`
  is already on) plus Iris platform data for the SM7675 VPU. The blocker is not
  the driver but the fact that nobody has confirmed any of it on hardware: the
  boot overlay is gated by `UKE_VIDEO_OVERLAY`, which is 0 for a local build and
  1 only in CI, so a stock image never carries it.
- **The VPU firmware does ship.** `odm/firmware/vpu30_2v.mbn` is a real
  2.3 MB ELF (Tensilica Xtensa) and `uke-oem-data` installs it to
  `/usr/lib/firmware/qcom/vpu/`; an earlier note here said it was only reachable
  from the `firmware` partition and that was wrong.
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
