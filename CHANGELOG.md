# Development changes

## 1 November 2026

This update combines the maintainer's latest hardware confirmation with
repository and release changes. Development-system results remain separate
from acceptance of the downloadable images.

- **Microphones and VRR:** microphones now work, and adaptive sync / VRR
  works across the full 30–144 Hz range, as confirmed by the maintainer.
  This supersedes the earlier microphone and VRR status below; it does not
  qualify Bluetooth microphone modes, USB recording, or every release image.
- **Four desktop images:** the experimental
  [Senemos 011126 r1 release](https://github.com/MCC45TR/uke-linux/releases/tag/fedora-rawhide-uke-senemos-011126-r1)
  provides KDE Plasma, GNOME, Cutefish and NextKDE images with Linux
  7.3.1-115 and one shared boot image. Boot and initial setup remain
  unverified on physical tablets for these exact images.
- **Image delivery:** desktop builds reuse a common Fedora core. The
  publication workflow checks compatibility before appending another
  desktop to the same release; Cutefish can be built separately without
  rebuilding the other editions. Public releases contain the image files,
  while manifests and build receipts are retained in Actions.
- **Unified builder:** the workspace now tracks the builder's `main`
  branch. Distribution selection defaults to Fedora; Ubuntu and Arch
  choices stop explicitly before host preparation because their native
  image backends are not implemented. This source change does not establish
  additional distribution support or alter the published images.
- **Documentation and gallery:** hardware status now reflects the
  microphone and VRR confirmation, and screenshots are organized by
  desktop environment.

## 29 October 2026

Environment: POCO Pad X1, 8 GB / 512 GB, Fedora Rawhide AArch64 and original
Fedora KDE. This update reviews recorded development tests; no new tablet test
was run for the documentation. The published 26 October image is unchanged
and remains untested on a tablet.

- Signed Linux 7.3.0-48 boots with matching modules. Earlier hardware results
  keep their original test scope; the latest boot does not repeat every test.
- HDMI through Juo JH925 has visible 1440p60 RGB10 and 1440p75 RGB8 results.
  KDE HDR output is visible at 60 Hz, but color accuracy and browser HDR remain
  unverified; 75 Hz HDR is rejected. DSC/FEC still produces a black image and
  receiver errors. Release 48 recovers visible uncompressed output automatically.
  DDC/CI fails through both dock HDMI sockets.
- The original KMix provides four internal-speaker level sliders. Playback and
  screen-based channel rotation work; independent acoustic channel isolation
  and suspend/resume still need testing. Microphones and camera capture remain
  unfinished.
- UFS MCQ starts and passes a bounded direct read; encrypted I/O is unverified.
  CPU/DDR bandwidth monitors and eight cache counters respond. NFC tag I2C
  transport, infrared registration and raw flicker readings are available;
  RF, optical, calibration and lifecycle checks remain separate.
- Seven VA decode modes pass bounded tests. Native 4K pixel and throughput
  controls do not establish original Chrome 4K60 playback, which still fails
  sustained performance. Serial decode waits and video downclocking are
  reproduced; the cached-surface experiment alone does not resolve throughput.
- Battery/PD observation, threshold validation and original KDE/UPower fixes
  pass source, host and emulation checks. Combined signed delivery, installed
  desktop behavior, physical cutoff/restart, bypass, calibration and charging
  protection remain open. No new charging protocol is declared working.

## 26 October 2026

Environment: POCO Pad X1, 8 GB / 512 GB, Fedora Rawhide AArch64 and original
Fedora KDE. Development-installation results are separate from exported images.

- Linux 7.3 is the current development series. Signed `7.3.0-15`, COPR
  11207395, passed the recorded normal boot, boot readback and boot-health
  checks. Hardware observations from older kernels retain their original scope.
- HDMI output works on Linux 7.3, confirmed in device use on 26 October.
  The exact mode and precision were not remeasured. HDR, DDC/CI and experimental
  DSC/FEC remain separate acceptance items; DSC/FEC stays disabled by default.
- Earlier Juo trials also confirm native/Chromium monitor sound and basic
  Gigabit Ethernet connectivity. Later RX drops, reconnect and cover behavior
  remain open. The signed RGB cohort passes one visible ten-second color test.
- On Linux 7.3.0-15, seven VA decode modes each produce 30 exact-reference
  320x240 frames: H.264 Baseline/Main/High, HEVC Main/Main10 and VP9 Profile0/2.
  Independent ten-bit references retain non-eight-bit samples. The native FFmpeg
  High/B-frame path still fails despite exiting zero. Basic H.264 Main encoding
  produces 30 independently decoded frames with correct SPS timing; missing
  color metadata, rate control, larger modes and endurance remain open.
  Browser hardware video and sandbox/GL coexistence remain unqualified.
- The signed KDE Connect desktop policy enabled discovery of POCO F5 on
  24 October. Pairing, transfers and the separate laptop route issue remain open.
- The README now covers current display/input, graphics, browser/video,
  networking, USB, sensors, audio/camera, charging and lifecycle results at
  function level. It includes recent changes, update instructions, source
  checkpoints and live release availability rather than treating package or
  capability enumeration as physical support.
- Native identity/probe, kernel, recovery and Project Aloha source checkpoints
  are published on separate development branches. Source/host checks do not
  create a new device acceptance result.
- The KDE EXT4 singleboot testing image is replaced with signed Linux 7.3.0-16
  and Control 1.15.0-2. Host content/metadata, SELinux, both sparse decoders,
  Zstandard and independent root checks pass. The generic export omits the
  device-local touch reference; local provisioning and tablet acceptance remain
  open. The release carries only matched `boot.img` and `system.img.zst`.

## 20 October 2026

- **Functional status:** the tables separate tested functions from broader
  unfinished work, including boot versus shutdown and dock mouse versus
  keyboard input. Existing observations support 40 Working rows, previously 20;
  combined rows are split where needed. Descriptions are shortened and a stable
  release checklist is added. No new tablet trial is run; charging, VRR/input,
  sleep, HDMI and release-image limitations remain open.
- **Offline charging entry:** on POCO Pad X1 with Linux 7.2.11-6 and native
  screen 9, both 19 October powered-shutdown and cold USB trials return to KDE
  without a charger signal. The hardware table now records failing entry;
  physical screen/key/unplug operation remains untested. Exact Android and
  boot-infrastructure comparisons separate shutdown notification from charging
  mode selection. Stock flag readback is blocked by missing fastboot USB
  enumeration. No bootloader setting, slot or boot image is changed. See the
  [device and source record](https://github.com/MCC45TR/uke-linux-docs/blob/main/docs/testing/UKE-OFFLINE-CHARGING-2026-10-20.md).

## 19 October 2026

Environment: POCO Pad X1, 8 GB / 512 GB, Fedora Rawhide AArch64, original KDE
and Linux 7.2.11-5/6. Development-system results remain separate from the older
public Alpha 1 images and physical acceptance after the latest reboot.

- **Power arithmetic and test pacing:** signed Control/tests 19 (COPR 11173912)
  and observer/offline screen 9 (11173924) install through DNF on kernel 6.
  Exact-source/signature/payload checks, RPM/hash verification and native
  diagnostic self-tests pass. Runtime power is weighted by elapsed sample time;
  absolute test deadlines avoid adding rendering time to every frame period.
  The offline screen suppresses charge duration without healthy positive net
  battery power. Controls/profiles remain unqualified, with charge helper 7
  and its disabled workers retained. No kernel or firmware change is made.
  A 43-second VRR run with the earlier test observes cadence following actual
  submissions and about 30 Hz idle, but two touch watchdogs recur. VRR remains
  off at a 144 Hz base; the corrected visual repeat awaits an unlocked session.
  The reviewed O82 stack has no qualified physical 1 Hz path. See the
  [equations, device observations and remaining gates](https://github.com/MCC45TR/uke-linux-docs/blob/main/docs/testing/UKE-POWER-VRR-OPTIMIZATION-2026-10-19.md).
- **Touch reliability follow-up:** a live release-10 stall reaches a 6 GiB
  memory peak in recursive contact assignment. Release 11 bounds the workspace;
  release 12 restores OEM charger-noise policy, bounds configuration reads and
  wraps tracking IDs without active collisions. Signed COPR 11173813 installs
  exactly touchscreen 12 through DNF on kernel 6. RPM verification, firmware
  policy readback and unchanged-state event deduplication pass. Input publishes
  in 410 ms; a bounded resource observation retains approximately 11 MiB RSS,
  eleven descriptors and no restart. Host ASan/LSan checks and 18800 private
  replay operations pass; they do not establish zero leaks for all lifecycles.
  The physical release-12 trial, pen and wake features remain unqualified.
- **Lifetime boundary follow-up:** source 13 also saturates palm history and
  contact age through the same boundary-tested helper. COPR 11173836 and source
  contracts pass; signed exact-source/payload checks and DNF installation of
  only touchscreen 13 pass on kernel 6. Input publishes in 437 ms and firmware
  power-policy readback succeeds. Thirty one-second samples retain 9516 KiB
  RSS, eleven descriptors, zero swap and no restart/watchdog after 32 unchanged-
  state power events. This is not a controlled RAM improvement. Physical touch,
  pen and lifecycle qualification remain pending.
- **VRR regression:** ten-finger input on release 11 causes transient upper-
  display corruption and oscillating contacts with Always VRR. Never at the
  same 60 Hz base removes the reported symptom. VRR remains disabled, reopening
  earlier continuity acceptance. Firmware watchdog causes and complete panel/
  THP synchronization remain unresolved.
- **Current delivery correction:** kernel 6 returns to KDE after a normal
  restart, with user-confirmed display/touch. Uke Control 18 and integration 14
  are installed and verified. A persistent original KSystemStats client reads
  finite idle GPU usage and 255 MHz; active load and GUI presentation remain
  pending. Kernel 7/8 package fixtures fail after compilation; corrected kernel
  9 COPR 11173706 succeeds and passes signed source/Image/module/initramfs audits,
  but is not installed during the same-kernel touch control. These observations
  supersede the earlier unavailable-access and package-only limits below.

- **Memory accounting:** the desktop/lock-screen baseline reports 2.36 GiB
  used and 4.85 GiB available, with unused swap. Plasma PSS is about 224 MiB,
  KWin 112 MiB and the keyboard 80 MiB. MSM reports about 1.10 GiB resident
  graphics buffers; shared process/display buffers must not be counted twice.
  No leak or measured reduction is established. A reversible THP madvise trial
  awaits the same-state post-reboot comparison; no packaged default is added.
- **Original KDE GPU sensors:** the existing Linux GPU provider enumerates
  PCI devices and misses platform Adreno. A native C++ SystemStats extension
  supplies activity/frequency sensors and a standard Adreno GPU page without
  rebuilding KDE or weakening compositor proc protection. Signed integration
  13 from COPR 11171580 passes exact-source, AArch64, hardening, Python-free and
  two native test checks. Signed kernel 7.2.11-6 from COPR 11171564 passes exact
  source, matched Image/module and native initramfs checks. Its completed-engine
  counter is independent of governor polling. Neither candidate is installed;
  original GUI output, idle/load behavior and power profiles remain pending.
- **Diagnostic robustness:** application 16 corrects a reproduced report abort
  when disk inventory or device status fails. Earlier logs and their receipt are
  retained, with separate private metadata errors. Read-only process/cgroup,
  short CPU/memory samples, boot-chain, fstab and THP context are added. Four
  failure/success fixtures, full native/SDK checks and actual contained report
  generation pass. COPR 11171675 succeeds; signatures, exact sources, native
  hardening and Python-free payload/dependency checks pass before installation.
  It adds no daemon or startup workload; tablet execution and
  a measured resource improvement remain pending while access is unavailable.
- **Root mount policy:** a verified live fstab update adds noatime and
  errors=remount-ro to the PARTLABEL-selected ext4 root. Journaling, barriers,
  normal commit timing, read-only persist and periodic trim remain. Boot package
  21 and both builder root producers plus the composition assertion match.
  COPR 11171579, exact-source/signature checks and builder CI pass; existing
  administrator fstabs are not overwritten by packaging.
- **Latest restart limitation:** the ordinary 10:36:53 UTC restart on the
  existing kernel 5 has not returned to authenticated SSH after the live mount
  and THP trial. No kernel or GPU plugin was installed for this restart.
  Physical state and shutdown/startup logs are needed to distinguish the cause;
  no new startup, RAM-saving or error-free-log result is claimed.
- **Native management 15:** signed COPR 11170610 installs through DNF after
  exact source, signature, native hardening and Python-free payload checks.
  Swap discovery uses GPT metadata while retaining filesystem-label searches,
  ambiguity refusal and actual partition/signature validation. An on-device
  comparison measures 0.53–0.63 s against 1.01–1.10 s for the old discovery path.
  Real lock contention refuses inventory refresh without changing either
  snapshot. Three helper restarts take 0.64–0.86 s; this is separate from boot
  concurrency and full startup time. Half-RAM swap and disabled charging workers
  are preserved. No package-channel transition is performed.
- **PC USB and idle resources:** the confirmed direct computer connection
  reports 5 V / 500 mA SDP. A 60.40-second observation averages 1.82 W input,
  approximately -0.02 W battery-side power and 1.14% aggregate CPU. Cached power
  samples are not integrated energy. About 5.1 GiB of RAM is available, swap is
  unused and no direct reclaim or compaction stalls are observed. Active desktop
  scrolling and battery energy remain separate measurements.
- **Pressure accounting:** signed kernel 5 from COPR 11170586 exposes procfs
  and cgroup CPU/memory/I/O PSI. Original systemd-oomd starts; its policy has
  no monitored cgroups, so effective OOM protection is not qualified. The native
  private report captures all pressure files and ten command groups without
  uploading raw logs. No custom memory policy is introduced.
- **Normal startup:** two kernel-5 boots report 8.053 and 6.743 seconds in
  systemd, versus the initial 8.372 seconds on kernel 4. The latest helper
  takes 1.043 seconds and 0.300 CPU-seconds. Bootloader and physical first frame
  are excluded; concurrent work and original Fedora updates prevent isolated
  attribution. A separate 60.36-second screen-off sample reports 0.358%
  aggregate CPU with no memory-pressure/reclaim stalls and unused swap.
- **Idle services:** unused software RAID units are disabled, with matching
  vendor defaults in integration 11. Original fwupd retains on-demand access
  and active-operation inhibitors but now exits after its normal five-minute
  idle timeout. About 55 MiB previously remained allocated; battery-life gain
  is unmeasured. Authentication, sensors, thermal management, fstrim, SELinux
  and ordinary firmware-update access remain enabled.
- **UFS checks:** UFS 4.0 identification, two-lane rate B, dynamic gear and
  WriteBooster, clock gating and runtime suspension are observed. A bounded
  native 256 MiB CRC32C file test and short QD1/QD32 reads complete without
  error. A separate read-only 1 GiB sample reaches about 1.7 GB/s. MCQ, inline
  encryption, temperature notification, maximum gear, endurance and power-loss
  behavior remain unqualified.
- **Consistent UFS scheduling:** signed integration 12 from COPR 11170835
  skips Fedora's generic BFQ assignment only for Qualcomm UFS. Before the
  change, concurrent shared-tag LUN switches produce EBUSY and mixed schedulers.
  After two normal boots, all six LUNs retain mq-deadline without those errors.
  External disks retain Fedora's rule, administrator configuration is preserved
  and installation performs no live scheduler transition. Later startup reports
  are 7.440 and 7.172 seconds; no performance gain is attributed to this rule.
- **VRR preference and clock check:** KDE Always is restored through the
  original kscreen-doctor and retained after reboot on kernel 5. Twelve seconds
  of DRM intervals average 29.973 Hz idle with the 144-Hz upper mode selected;
  this is not optical panel timing. Existing boot-integration 20 restores saved
  drift-file time through original chronyd before normal NTP synchronization.
  The hardware RTC still reports an old epoch. No additional clock daemon,
  VRR enforcement service or RTC write is added.
- **Final quiet sample:** with integration 12 and DPMS off, 60.37 seconds
  report 0.322% aggregate CPU, approximately 4.88 GiB available RAM, unused
  swap and no memory-pressure/reclaim stalls. Seven cached power samples
  average 1.818 W input and +0.023 W battery-side power at 52%, Good and 24 °C.
  This is near balance in that state, not battery-life or active-scrolling
  qualification.
- **Remaining scheduler observation:** the repeated post-policy file test
  passes integrity and read jobs, but emits one deadline-replenishment warning
  during QD32 reads. Upstream resets the late deadline/budget; the affected
  entity and relation to UI stutter are not established. No scheduler warning
  is suppressed and no speculative real-time or governor setting is applied.

Charge cutoff, bypass, powered HDMI, active scrolling, physical screen/input
after the new boot and exported-image qualification remain open.

## 18 October 2026

Environment: POCO Pad X1, 8 GB / 512 GB, Fedora Rawhide AArch64, original KDE
Plasma and stock Android bootloader. These results concern the development
installation. The public Alpha 1 images retain their older kernel and have not
been accepted as complete exported images on this tablet.

### Installed and observed

- **Kernel 7.2.11-4:** signed COPR 11169288 passes the complete kernel build,
  battery/audio fixtures and package audit. DNF installs the matching tuple;
  Android A and earlier tested images/modules are preserved. Normal reboot
  returns to SSH with original KDE processes and active touch/sensor services.
  s2idle remains the startup selection. Physical display/touch confirmation
  after this reboot is pending.
- **Kernel 7.2.11-2:** signed COPR 11168745 installs through DNF. Boot B is
  written and read back, Android A is unchanged and earlier tested image/modules
  are retained. A normal reboot reaches KDE; physical display and touch pass.
- **VRR preference and observation:** KDE Always persists through that reboot.
  An eight-second DRM/DPU capture measures about 30 Hz idle while the configured
  upper mode remains 144 Hz. The user accepts the development VRR/touch profile;
  optical cadence and complete receiver/endurance qualification remain separate.
- **Native management:** signed COPR 11168593 installs uke-control 11 and its
  separate development diagnostics. Signed COPR 11169204 upgrades runtime and
  charging helper to 7. Exact source/signature/native payload and DNF verification
  pass; charge workers stay disabled. The 3690 MiB half-RAM
  swap survives reboot. Existing swap-partition preference remains untested.
- **Charging configuration:** an explicit input-off operation enables the
  existing firmware 70/80 band. Readback survives normal reboots through
  7.2.11-2, without service replay. A later powered observation reaches reported
  80% with positive battery current; physical charge stop remains unqualified.
  On 7.2.11-4, one separate input-off target request receives an opaque 16-byte
  reply and verified unchanged settings. Actuator effect remains unknown;
  no automatic retry, charge worker or bypass is enabled.
- **Minimal charging interface:** signed runtime cohort 7 retains the separate
  native offline screen. Its normal-boot guard refuses drawing over KDE; the
  desktop and touch service remain uninterrupted. The interface includes a large
  battery, percentage, firmware time-to-full, signed battery-side power and
  temperature. Missing time data remains unknown. Actual charger boot is untested.
- **USB dock:** the powered Juo dock on kernel 27 enumerates its hubs, receiver
  and RTL8153; mouse movement passes evdev and physical confirmation. Kernel 28
  enables compressed firmware loading; ethtool reports rtl8153b-2 v2 04/27/23.
  SuperSpeed enumeration is distinct from throughput or Ethernet traffic.
  Kernel 7.2.11-2 corrects the WCD AUX status address/mask. Its powered HDMI
  validation remains behind the charging gate.
- **Manual CDC:** CDC defaults off. Explicit one-shot management uses
  `uke-control set cdc on/off`; it has no persistent gadget service. Development
  SSH uses infrastructure Wi-Fi.
- **External brightness preparation:** original Fedora ddcutil is installed.
  Adaptive-display 9 initializes original PowerDevil/libddcutil after reboot
  while excluding internal GENI buses. Physical DDC/CI brightness remains open.
- **Bluetooth audio:** soundcore Space Q45 stereo playback is reported clear;
  PipeWire confirms an active A2DP/LDAC transport. HFP, latency and lifecycle
  qualification remain separate.
- **Power and sensors:** three desktop CPU/GPU profiles switch successfully;
  the current profile is balanced. Native sensor readiness and original KDE
  interfaces are retained. These observations do not close jank, energy,
  thermal, color-temperature or complete sensor-accuracy work.
- **Fastfetch:** signed COPR 11169224 installs 2.68.1-2. A non-x86 guard removes
  the legacy PC BIOS memory scan that caused root SIGBUS. The all-module root
  capture completes at exit 0 without a device-permission workaround. Missing
  cache geometry and unavailable hardware remain explicit.
- **Native management:** signed COPR 11169315 installs uke-control 14 and its
  development diagnostics through DNF. Package verification and three bounded
  sensor snapshots pass on Linux 7.2.11-2. Cached values, unknown acquisition
  age and stale front-color data remain visible. Channel transitions and
  physical sensor accuracy remain untested; no repository policy is changed.
- **Scrolling measurements:** a physical original Settings-list trial records
  approximately 143.9 Hz DPU timing and application CPU use approaching one full
  core. GPU frequency responds to load. Content frame rate and the reported
  stutter remain unresolved; no KDE application is forked or replaced.
- **Suspend policy:** signed COPR 11169255 installs adaptive-display 10. Standard
  systemd selects s2idle at startup and each suspend request; logind reports
  suspend available after deliberate removal of earlier laboratory masks. A
  device-test PM phase and one real approximately 26-second s2idle cycle return
  with zero failure counters. The recorded wake IRQ maps to the RTC alarm;
  Wi-Fi reconnects about nine seconds after resume. Physical display/input,
  power-key wake, repeated cycles and sleep power remain separate gates.

### Remaining work

Installed kernel 7.2.11-4/sourceac1ed7e adds the fixed input-off application
probe for the already enabled 70/80 band and reviewed AudioReach response and
readiness changes. Fresh ordered 79-patch/native preparation, actual battery
and audio fixtures and complete AArch64 translation units pass. Full
[COPR 11169288](https://copr.fedorainfracloud.org/coprs/build/11169288/) succeeds
and its matching bundle is installed. The prior -3 full kernel compiles, but its package
check fails because compiler-rt is missing; -4 declares that build dependency.
Audio stays disabled, with no admitted speaker,
microphone, DAI or amplifier path. Opaque charging receipt/readback cannot prove
actuator effect or battery bypass. Actual offline charging remains untested.

Qualify charge-stop behavior, reboot-persistent protection and any actual
bypass/system-power path before resuming powered HDMI tests. HDMI output,
Ethernet traffic, storage throughput and external brightness still need physical
tests. The internal display uses the OEM 10-bpc RGB/DSC path; selectable 8/12/16-bpc
modes are not implemented. White-flash behavior, stability and energy efficiency
remain open. S2idle is now enabled at the user's request; actual sleep/resume
and energy validation remain open. Display-only blanking is a separate action.

Source, host tests, signed packages and physical observations are reported
separately in the [hardware support table](README.md#hardware-support).
