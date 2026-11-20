# State

Updated: 2026-11-21 (image assets moved into `configs/rootfs` and the keyboard
became a package, so the rootfs no longer depends on host-side copies; nothing
built yet). Verify with commands before relying on it; update this file at the
end of every session.
Long history and decisions live in the private notes; this file records only
facts.

## Upstream and forks

Upstream: `MCC45TR/uke-linux`, branch `Fedora`, pin `5786c9c` (2026-11-06),
recorded in [`upstream.lock`](../upstream.lock). Model: vendored fork with three
rebased component forks; patches are exported for review only. See
[UPSTREAM.md](UPSTREAM.md).

| Component | Branch | Head | State |
| --- | --- | --- | --- |
| umbrella | `main` | this handoff commit | docs; Flatpak VA-API override; kernel and hardware gitlinks moved |
| `senemos-uke-kernel` | `main` | `5c87b0f` (gitlink and worktree) | release `7.3.1-107`; video series active; native `%prep` fixed; WN8030 keyboard boots from the initramfs and keeps scanning keys (`mi_auth=0`); RPMH regulator driver registers again; keyboard bus admitted by the ABL scope pass |
| `uke-fedora-builder` | `main` | `3662473` (gitlink) | apps, ru locale, COPR repo; internal source cache renamed to `source-cache/` |
| `uke-linux-hardware-support` | `main` | `00c9420` (gitlink and worktree) | firmware payload with uke-firmware provides; libssc fetched from Codeberg again |

Verify with `git submodule status` and `git ls-tree HEAD -- <component>`; compare
the worktree head with the recorded gitlink before moving a pointer.

## No kernel A/B in the shipped image (2026-11-20)

`build-rootfs.sh` refuses seven packages by name before the image is accepted
(`build-rootfs.sh:263`): `senemos-uke-linux-kernel-mainline`, its `-boot`
subpackage, `uke-kernel-update`, `uke-charge-control`, `uke-offline-charge`,
`uke-boot-recovery` and `uke-cdc-debug`.

`uke-userdata-accept.service`, `uke-userdata-fallback.service` and both update
profiles live in the `uke-kernel-update` subpackage
(`uke-boot/packaging/uke-boot-integration.spec:330-339`), so the image carries
none of them: no binary, no units, no `/etc/senemos/*-update.conf`. The kernel
reaches the tablet one way only - rebuild and flash `boot_a`. Nothing stages
itself and no rollback slot is in use. The userdata A/B design in
`uke-boot/docs/USERDATA-AB.md` is an asset for a later profile, not a capability
of this release.

`uke-install-profile` is absent for the same reason: it is the `linux` root
profile's detector and unit masker (`install-profile.cpp:236-239`), nothing in
the Fedora 44 path requires it, and `uke-core-meta-1.0.4-1.fc44` does not list
it. A move to a dedicated `linux` root partition has to add it back, or the
userdata-only units stay enabled on a root they no longer describe.

## Rootfs packages now come from comps groups (2026-11-21)

`build-rootfs.sh` no longer carries a hand-written package list for the base and
desktop layers. The base transaction installs `@core` and
`@networkmanager-submodules`; the desktops install `@kde-desktop`,
`@gnome-desktop`, `@phosh-desktop` or `@kde-mobile`, and the shared layer adds
`@multimedia`. That closes the gaps the hand-written lists had accumulated:
`procps-ng`, `iputils`, `iproute`, `man-db`, `dnf5-plugins`, `plymouth`,
`firewalld`, `alsa-ucm`, `pipewire-pulseaudio` and a Wi-Fi backend in the TTY
image, which previously had none because only the desktop branch named
`NetworkManager-wifi`.

Measured closures (aarch64, empty installroot, `install_weak_deps=False`),
against the hand-written sets they replace: TTY 158 → 288, KDE 1020 → 1398,
GNOME 655 → 1114, phosh 648 → 886, plasma-mobile 936. The growth is the group
defaults: akonadi and samba for KDE, gnome-boxes and rygel for GNOME. No image
has been built with the new sets yet.

Three facts that the groups forced:

- `systemd-pam` is still not in the `@core` closure with weak dependencies off.
  It stays explicit, because `authselect` below rewrites the PAM stack and
  `audit-rootfs.sh` checks `/usr/lib64/security/pam_systemd.so`.
- Both KDE groups prefer `plasma-login-manager`, and `kde-settings-plasmalogin`
  hard-requires it, so the SDDM profiles exclude all three
  (`kde-settings-plasmalogin`, `plasma-login-manager`, `kcm-plasmalogin`) and
  name `sddm`, `sddm-breeze` and `sddm-wayland-plasma` explicitly. Excluding
  `plasma-login-manager` alone fails the transaction. `sddm-breeze` is what
  carries the `01-breeze-fedora` theme that `audit-rootfs.sh:87` requires.
- `@kde-desktop` installs `fedora-release-kde-desktop`, which replaces the
  release identity and changes `VARIANT_ID` in `/etc/os-release` - and with it
  the `osrel` entry the boot image carries. That is accepted deliberately, not
  an accident. GNOME keeps the basic identity because its group names no
  release package.

Other deliberate replacements: GNOME's terminal is `ptyxis` now, not
`gnome-terminal`, and `firefox`, `kate`, `kcalc`, `powerdevil`,
`plasma-keyboard` and the KDE VM stack stay named because no group carries
them. `@phosh-desktop` is a phone shell with no `gdm`, no
`gnome-initial-setup` and no `gnome-control-center`, so the gdm path keeps
those three explicit.

What still differs from `src/image/install-userdata-device-packages.sh`:
`--setopt=tsflags=nodocs`, `%_install_langs`, signature checking
(`localpkg_gpgcheck=False` here, `True` there) and the closing `dnf check`
pass. Tracked as B31.

## Image assets have one home (2026-11-21)

`build-rootfs.sh` used to copy seven keyboard files and four desktop assets
into `$output/root` from the host, after the container had exited and after the
expensive dnf work. That stage needed `sudo` while everything else ran
rootless, wrote a second ownership source into a tree the container otherwise
owned, and none of it was covered by `BUILD-INPUTS.sha256`, so `--resume`
reused a rootfs built from the old bytes after an asset had been edited.

There are now two places and no third:

- `configs/rootfs/` mirrors the target paths and is copied inside the container
  by an `apply_overlay` stage in `build-rootfs.sh`. `configs/rootfs-copr/` is
  applied only when `UKE_COPR` is not 0, and that variable is now passed into
  the container, where it is actually read.
- The keyboard firmware, three helpers and three units are one noarch package,
  `uke-keyboard-support`, built from `configs/nanosic` by
  `packaging/uke-keyboard-support.spec`; `build-images.sh` builds it into
  `hardware-rpms` before the rootfs step. The helpers moved from
  `/usr/local/sbin` to `/usr/bin` (SELinux type `usr_t` to `bin_t`), the module
  load entry from `/etc/modules-load.d` to `/usr/lib/modules-load.d`, and
  `nanosic-authd` is still installed with its unit still not enabled.

Both trees and the package inputs feed `BUILD-INPUTS.sha256`. `audit-rootfs.sh`
walks the overlay trees and requires each file to exist, stay a regular file,
keep mode 0644 and match its source byte for byte; ownership is asserted inside
the container instead, because a rootless build maps container root to the
invoking user, so the host tree is user-owned by design. The audit also checks
the keyboard package layout, an empty `machine-id`, no SSH host keys and no
`random-seed`. The keyboard RPM's digest lands in `HARDWARE-RPMS.sha256`, so the
image now records which firmware it carries instead of leaving that to the
working tree; the package is built reproducibly (changelog epoch, fixed build
host, pinned mtimes), so that digest changes only when its inputs do and
`--resume` keeps reusing the rootfs.

Builder commits `c18e08c..0320d3e` (overlay, package, ownership check where the
container mapping makes it observable, reproducible package, audit path fix). No
image has been built with any of them yet; B32 tracks the first build.

## First boot and working keyboard (2026-11-19)

The tablet boots to a root shell from CI run `44359576130` (kernel
`7.3.1-107`, `boot_a` flashed, existing `userdata` kept) and the Pogo keyboard
works: `a8c000.i2c` probes, `5-004c` exists as an i2c client, the WN8030 driver
loads its MCU firmware, and `systemd-backlight@leds:nanosic::kbd_backlight`
starts.

Three defects had to be fixed, and two of them had nothing to do with the
keyboard itself.

**The RPMH regulator driver never registered.** `patches/7.3.0/0002` declares its
new-file hunk as `@@ -0,0 +1,2124 @@` but carries 2126 added lines. `git apply`
honours the declared count and silently dropped the last two:

```c
arch_initcall(rpmh_regulator_init);
module_exit(rpmh_regulator_exit);
```

`drivers/regulator/qcom-rpmh-regulator-uke.c` then compiled to a `.o` holding
only modinfo - three symbols, 1400 bytes - with `of_match_table`, `probe` and the
whole RPMH voter path discarded. No DT node matching `qcom,rpmh-vrm-regulator`,
`qcom,rpmh-arc-regulator` or `qcom,rpmh-xob-regulator` ever bound, so every
`rpmh-regulator-*` supplier stayed in EPROBE_DEFER. That left `1d84000.ufshc`
and `1d80000.ufsphy_mem` unbound, no block partition appeared and
`uke-root-guard` fell into `emergency.target`. Fixed by correcting the hunk
count to `+1,2126`; the compiler now emits 92 symbols including
`rpmh_regulator_match_table` (kernel `a0eeaba`, manifest re-pin `8453c90`).

**The ABL scope pass disabled the keyboard bus.** `uke_scope_qup_buses()`
disables every child of the QUP nodes that its admitted list does not name, and
the `qupv3_0` entry held only `i2c@a80000`, `spi@a90000` and `spi@a84000`. The
keyboard sits on `i2c@a8c000` (QUP0 SE3), which the keyboard overlay enables a
few lines earlier:

```
988   fdt_overlay_apply(output, keyboard_overlay);   -> i2c@a8c000 = okay
1044  uke_scope_qup_buses(output);                   -> i2c@a8c000 = disabled
```

So the overlay's own enable was undone before OF scanned the tree. No platform
device was created, `geni_i2c` had nothing to bind, no i2c client existed for
`nanosic@4c`, and `dmesg` carried no nanosic line at all - not even a firmware
error. Fixed by adding `i2c@a8c000` to the `qupv3_0` entry and widening the
table from `[][4]` to `[][5]` to keep room for the NULL terminator (kernel
`291d2d5`).

**The shipped MCU firmware was the wrong device's.** `configs/nanosic/MCU_Upgrade.bin`
parses as pid `0x1294`, version `XM_P81_V206-0828`, 83,436 bytes - the P81 image
used by the Xiaomi Pad 6S Pro 12.4. This tablet is O81/uke (`2410CRP4CC`), and
the OEM `nanosic_driver.ko` for it is built around pid `0x1260`, which is what
the stock ROM's `odm/firmware/MCU_Upgrade.bin` declares (`XM_O81_V207-0822`,
82,740 bytes). Replaced with the O81 blob (umbrella `c1b1d45`).

The firmware is now also built into the Image rather than only being installed
into the rootfs: `CONFIG_EXTRA_FIRMWARE="nanosic/MCU_Upgrade.bin"` with the
relative `CONFIG_EXTRA_FIRMWARE_DIR="firmware"`. The firmware loader consults
built-in firmware before any filesystem path, so the keyboard comes up in the
initramfs and does not depend on the rootfs carrying the file. Verified on a
clean 7.3.1 tree: the Image holds the whole 82,740-byte blob, its `0x7FC0`
`NANO IC` header and the `XM_O81_V207-0822` version string (kernel `4a37b10`).

`tests/abl-dt-contract.sh` already asserted that `i2c@a8c000` ends up `okay`,
but nothing invokes that script, so the regression stayed invisible. Wiring it
into the preparation path is tracked in the backlog.

On-device state after the fix:

```
/sys/bus/platform/devices/a8c000.i2c                     present
/sys/bus/i2c/devices/5-004c                              present
systemd-backlight@leds:nanosic::kbd_backlight            starts
devicetree/.../i2c@a8c000/status                         okay
```

`/sys/class/regulator/*/name` shows `pmxr2230_l22` and `pmxr2230_l23`, the
`dvdd`/`vddio` rail pair the overlay names as L22B/L23B, and `pm_v8_s8_level`,
`pmxr2230_l4`, `pmxr2230_l12`, `pmxr2230_l17` - every supplier the earlier boot
photo showed deferred.

Flashing this build needs `boot_a` only: the fix is all `=y` code and keeps the
`7.3.1-107` release, so the module vermagic is unchanged and the existing
`userdata` stays valid.

## The keyboard stops scanning keys after a few minutes (2026-11-19)

The Pogo keyboard works from boot and then goes silent: nothing reaches
`/dev/input/event*`, the Caps Lock LED stops responding to the `leds` class,
but the MCU keeps talking. `/proc/interrupts` on GPIO 116 climbs while keys are
pressed (436 counts in 13 s) and falls back to a slow accelerometer trickle
when idle, so the MCU is alive, the I2C controller works, and the driver keeps
receiving frames.

Four suspects were ruled out on the device rather than by reading code:

- **No stuck task.** `ps` shows no `D` state process, `sysrq-w` prints an empty
  blocked-task list and `systemd-udevd` sits in `do_epoll_wait` with one task, so
  no mutex is held across a dead I2C transfer.
- **No hall-sensor gating.** `nanosic_wn8030_hall_ids` requires the handler's
  `swbit` bitmap - `SW_LID | SW_TABLET_MODE`, i.e. `0x3` - to be a subset of the
  device's. The two `xiaomi_hall` children expose only `0x2` and only `0x1`, so
  `input_match_device_id()`'s `bitmap_subset(id->swbit, dev->swbit, SW_MAX)`
  never matches and `hall_connect` is never called. `lid_closed` and
  `tablet_mode` stay zero, and `input_enabled` stays at the value `probe` set.
- **Not a stuck `suspended` flag.** `suspend` always sets it, so `resume` always
  takes the branch that clears it.
- **Not the MCU refusing to answer.** The GPIO interrupt count keeps rising
  under key presses.

What is left is the MiAuth handshake. The driver answers it itself: on `0x24`
it sends `MIAUTH`, on `0x31` it sends `key_meta` plus a challenge, and on `0x32`
it waits for a token from `/dev/nanosic_auth`. There is no token source on
Linux. The OEM userspace gets one from
`odm/bin/hw/vendor.xiaomi.hardware.keyboardnanoapp_aidl-service`, which needs the
vendor key and a Binder environment; `nanosic-authd` can only answer with
sixteen zero bytes. The journal shows the MCU challenging about once a minute
for as long as the tablet runs, always with uid
`0007000100000000001a51d87f8cd7fa` and a challenge whose first four bytes are
random while `49490001` and `0411121327760132` stay fixed:

```
04:50:56 token sent uid=0007... challenge=04212aa9 49490001 04111213 27760132 token=0000...
04:51:56 token sent uid=0007... challenge=5ad15a69 49490001 04111213 27760132 token=0000...
04:52:57 token sent uid=0007... challenge=e0010a29 49490001 04111213 27760132 token=0000...
```

The OEM `nanosic_driver.ko` contains no MiAuth path at all - no `MIAUTH`
string, none of the `38/31`, `38/32` or `38/33` command prefixes, and no
`token`/`challenge` text - so on Android the kernel driver is not a participant
in the handshake the way this driver assumed.

Fixed by leaving the handshake alone unless `mi_auth=1` is passed on load
(kernel `5c87b0f`). Stopping `nanosic-authd` alone is not enough: the driver
still sends `MIAUTH` and `s3t1`, the MCU still waits for a token, and the
keyboard only lasts longer. The daemon is now installed but not enabled
(umbrella `4dedb5c`, gitlink `e385460`).

The two paths that were dropping input silently now log: a frame failing the
`0x57` header check, and any change of `input_enabled`.

Because `CONFIG_HID_NANOSIC_WN8030=m`, the driver lives in
`/usr/lib/modules/7.3.1-107/kernel/drivers/hid/hid-nanosic-wn8030.ko.zst` inside
`userdata`, not in the boot image. Any fix in this driver that keeps the release
at `7.3.1-107` can be tried without reflashing: build the `.ko` against the
cross tree, copy it over and `insmod` it. Reflashing `userdata` is what wipes
the installed system, so a same-release module swap is the cheap experiment.

## Pogo keyboard on `main` (2026-11-18)

`main` is `origin/main` (`2d22cc0`) plus two commits. The first moves only the
kernel gitlink, from `57d7fbb3` to `3163e55`, which is `saksham-991`'s kernel
`main` (`2e2a114`, 32 commits on `57d7fbb3`) plus one commit of ours.

The kernel side is the fork's mature WN8030 HID driver (`src/hid/hid-nanosic-wn8030.c`):
keyboard, consumer and touchpad HID reports, LED class devices for the mic-mute
and keyboard backlight, the `/dev/nanosic_hinge` tablet-mode interface with its
UAPI header, the `nanosic,wn8030-uke` variant and the auth token handshake. The
driver loads `nanosic/MCU_Upgrade.bin` at probe time and fails without it, so
the umbrella carries the 83,436-byte `configs/nanosic/MCU_Upgrade.bin` and the
CI overlay installs it to `/usr/lib/firmware/nanosic/`.

Our commit on top keeps the keyboard out of the optional display overlay: the
fragments moved from `src/input/sm7675-uke-focus-keyboard.dtsi`, which the O82
display overlay included, into a standalone `src/input/sm7675-uke-focus-keyboard.dtso`
applied by `uke-abl.c` as a fourth overlay after the USB one. The fragments
target the OEM nodes by path instead of the `qupv3_se3_i2c` label; only
`tlmm`, `gpi_dma0`, `L22B` and `L23B` are needed from `__symbols__`, and all
four are present on the device. The bus runs at 400 kHz, the IRQ is pin 116 on
the rising edge, reset is 127, status 128, sleep 98, `vddio` is L23B and
`dvdd` L22B.

`make check-pins` passes, the overlay compiles with `dtc`, applies to a
synthetic base carrying those four symbols, and the CI overlay anchors match
the new pin. The kernel was not compiled, the image was not built and nothing
was tested on the tablet.

The kernel submodule URL now points at the `Dustymind` fork of the kernel
repository, because `3163e55` exists only there once it is pushed.
`actions/checkout` fetches submodules recursively, so a run started before that
push fails at checkout with `not our ref` rather than during the build.

## Fork sync `saksham-991/uke-fedora` (2026-11-18)

Merge commit `241563b` brings the six upstream umbrella commits
(`817c38b..08cc97a`) into `main`; the kernel gitlink moves to `deccf8a`, the
merge of our `ba3156d` with the upstream `378c41f` (reset pulse: 2 ms, boot
50 ms, wake 20 ms) and `eae9b27` (restart the 12 s keepalive after resume).

Upstream additions kept: the `MCU_Upgrade.bin` install (identical blob), the
`nanosic-authd` script and unit, and `modules-load.d/nanosic.conf` which loads
`hid-nanosic-wn8030` at boot. Both `replace_or_skip` conversions around the
module-signing policy are kept; they now hit the already-applied marker in the
pinned tree and only the integrity-lockdown rewrite runs.

Our side kept: the zh_CN locale block, the `authselect` PAM assertion, and the
removal of the GDM and pre-created-account overlay, so KDE still ships stock
SDDM with the Plasma first-run setup.

`nanosic-authd.service` is also enabled now: upstream installs the unit and
`[Install] WantedBy=multi-user.target` but never enables it, and the image has
no preset pass for a file installed outside rpm. The overlay writes the
`multi-user.target.wants` symlink itself, which is what `systemctl enable`
would create, so no host tooling is involved. The unit is a plain system
service: root, no session bus, no graphical target, no login, so it answers
`/dev/nanosic_auth` from early boot and on the `tty` profile as well, where the
same rootfs block runs.

Tested off-device against a pty standing in for the char device: a 32-byte
request is answered with the 16-byte zero token, with a 32-hex
`/etc/nanosic/auth-token` it is answered with that token, and with no device
present the daemon stays up retrying every 2 s. The driver drops auth requests
without stalling the IRQ thread when the device is not open, so the keyboard
keeps working whether the daemon runs or not. Two caveats: the daemon holds a
single open, and its SIGTERM handler cannot break the blocking read, so
`systemctl stop` waits for the stop timeout before SIGKILL.

The kernel spec now says release `107`, so this head no longer collides with
`ci-44209941663`. The builder used to pin the kernel NEVRA separately in
`configs/package-lock.json`; `maint/prepare-ci-tree.py` now copies the release
out of the spec into that lock, because `build-rootfs.sh` resolves the kernel
RPM by that NEVRA and a lagging lock fails the rootfs stage only after the
whole kernel has compiled. The changelog entry records the four changes in
this release: the standalone keyboard overlay, the native ABL patch re-anchor,
and the two upstream Nanosic fixes.

The release number is mirrored a second time inside the kernel tree:
`manifests/llcc-source-candidate-20261020.json` carries a `kernel_release` field
and `make validate` compares it with the ABI that `rpmspec` reports for the
spec. Bumping only the spec broke that assertion, and CI run `44248952150`
failed there after 1m25s with `make validate` error 1, before the first of the
17 stages. `fadf7f8` moves the manifest to `7.3.1-107`; any future bump has to
touch both places.

## CI rootfs overlay: locale, login and PAM (2026-11-18)

`maint/prepare-ci-tree.py` now ships Simplified Chinese and the stock login
stack:

- `glibc-langpack-zh` and `langpacks-zh_CN` replace `glibc-langpack-ru` and
  `langpacks-ru`; `/etc/locale.conf` is `zh_CN.UTF-8` and
  `google-noto-sans-cjk-fonts` is installed. Fedora has no `noto-fonts-cjk`
  package: the Noto CJK family is split, and the sans face is the one the
  desktop needs.
- The GDM overlay is gone. KDE keeps its own `sddm.service` with
  `plasma-setup.service`, so the first user comes from the Plasma first-run
  setup, exactly as upstream. No account, password or SSH credential is
  shipped, `root` stays locked and `first-boot-policy` keeps its
  `Requires=uke-root-capacity.service uke-swap-ready.service` ordering.

Password authentication in the previous image could not work as intended:

1. The demo `uke:fedora` account was created only in
   `src/public/desktop-setup.sh`, and only `src/public/stage.sh` sources that
   file; `build-rootfs.sh` does not. The account the overlay promised therefore
   never reached the image. The remaining account path was the
   `plasma-setup.service` wizard, which runs `Before=display-manager.service`,
   and `build-rootfs.sh` still refuses to finish unless `root` stays locked, so
   there was no fallback account.
2. That wizard sets the password through `chpasswd`, and every password prompt
   reads `/etc/pam.d/system-auth` and `/etc/pam.d/password-auth`. Both are ghost
   files owned by `authselect-libs`: only its posttrans creates them, and that
   posttrans hides its own errors. Nothing in the builder verified them, so a
   failed `authselect select` would leave a desktop that starts but rejects every
   password. The overlay now runs
   `authselect select local with-silent-lastlog --force --nobackup` before the
   rootfs is finalized and stops the build if either file is missing.

The overlay patterns were validated with `--check` against builder `3662473`,
kernel `3163e55` and hardware `cf48c20`; nothing was built or installed.

## Release assets: compression and splitting (2026-11-18)

Run `44192935337` built all 17 stages in 52m58s and failed only in `Publish
release`: GitHub rejects a single release asset of 2 GiB or more, the KDE
archive is about 2.4 GiB, `gh release create` returned HTTP 422 and rolled the
whole release back. The artifact was complete (7.54 GiB).

- The packaging step now runs with `ZSTD_CLEVEL=12` and `ZSTD_NBTHREADS=4`, which
  the `tar --zstd` child honours. Level 19 cost 9m07s of the 40m45s job on the
  4.4 GiB rootfs; on the 1.72 GB sample tar level 12 wrote 198 MB in 12 s and
  level 19 wrote 170 MB in 178 s, so the larger archive is left to the splitter.
  `ZSTD_NBTHREADS=0` means one thread, not all. `--long=27` would need a patch
  to `package-release.sh` in the builder; it is not used.
- `tools/split-release-assets.sh` turns a packaging directory into release
  assets: archives of 1900 MiB or more become `<name>.part-NN`, the parts are
  proven to reassemble to the original digest, and it writes `SHA256SUMS` over
  the emitted files plus a `README.txt` that doubles as the release notes. It
  consumes the input archives, because the arm64 runner has no room for a second
  copy.
- Both workflows publish the split layout: `build.yml` via `build/publish-<tag>`,
  `publish-release.yml` by downloading the artifact and splitting it, or copying
  it unchanged when the run already shipped parts. The publish step is
  `continue-on-error` and the job summary reports the release outcome separately
  from the build result.
- The artifact path moved to `build/publish-*`, so a failed release still leaves
  downloadable assets.

Checked with a 3 GiB archive: two parts, matching reassembly digest, `sha256sum
-c` clean, and the parts branch copies untouched. No build, no publish.

## libssc source moved off Codeberg, then back (2026-11-19)

The Debian mirror switch below was a workaround for a Codeberg DNS outage. That
outage cleared, so `uke-sensors/Makefile` fetches
`https://codeberg.org/DylanVanAssche/libssc/archive/v0.4.4.tar.gz` again. The
pinned sha256 (`716d6bd6...621587`) is unchanged, so the built package stays
byte-identical, and the URL was re-checked: Codeberg answers 200 and the
downloaded archive hashes to the pin.

## libssc source moved off Codeberg (2026-11-18)

Run `44253183775` failed at `Prepare source RPMs` with `make: *** [Makefile:14:
srpm] Error 6`; the log shows `curl: (6) Could not resolve host:
codeberg.org` retried three times. `uke-sensors` fetched libssc 0.4.4 from there
and nothing else in the image build depends on that host, so one DNS failure
blocks every image.

Hardware `cd43287` points the same fetch at the Debian pool:

```
https://deb.debian.org/debian/pool/main/libs/libssc/libssc_0.4.4.orig.tar.gz
155242 B, sha256 716d6bd6…, unpacks to libssc/
```

The bytes are identical, so `hash=` in the Makefile is unchanged and the
`%autosetup -n libssc` name still matches. Verified end to end with an empty
`source-cache/libssc`: the fetch, the digest check and `rpmbuild -bs` all pass,
and the SRPM payload digests match a build from the Codeberg copy. `make
validate` and `uke-sensors/tests/source-contract.sh` pass. No image build.

`packaging/ubuntu/upstreams.tsv` still names the Codeberg URL: that is the
separate Ubuntu source route, and `packaging/ubuntu/tests/main-data-recipes.sh`
asserts the URL inside the generated copyright file.

## CI wall-clock reductions (2026-11-18)

Run `44243678354` took 40m45s: 28m17s in `Build baseline image` and 9m07s in
`Package release archives`. Three changes target the seconds and the reliability,
not the stages:

- `ZSTD_CLEVEL` 19 → 12. The step is a pure compression pass and level 12 keeps
  most of the saving; `tools/split-release-assets.sh` absorbs the larger archive
  by emitting another part.
- The cache paths dropped `~/.cache/ccache` and `~/.cache/docker`: the builder
  exports `CCACHE_DIR=/build-cache/ccache`, and rootful Docker keeps images in
  `/var/lib/docker`, so both entries restored and saved nothing. They were
  replaced by the per-component `source-cache` trees, which are the actual
  network dependency: `uke-sensors` fetches libssc from codeberg.org, and run
  `44253183775` failed at `make srpm` with `curl: (6) Could not resolve host:
  codeberg.org`.
- The tool image is rebuilt on every run (`ensure-build-image.sh` inspects the
  daemon store, which starts empty), costing about 70 s. It is left alone here:
  it needs a `docker save`/`load` pair and the image tag embeds the recipe hash.

Not changed: `--parallel 1` (the builder serialises tty before desktops and
there are only two profiles), `UKE_JOBS=$(nproc)` (already four on the runner),
and the kernel RPM re-use path (`kernel-rpm-cache.sh` needs the multi-GB
`rpmbuild` tree in the cache; that is a builder change).

## Baseline CI image build success (2026-11-14)

- Workflow run 43519285547 succeeded in 12m33s on GitHub Actions ARM64 runner (`ubuntu-24.04-arm`).
- Generated and uploaded artifact `uke-bootable-images-43519285547` (1.09 GB) containing `fedora_boot.img` and `userdata.img`.
- Key fixes applied:
  - Enabled Docker runtime for `build-rootfs.sh` (`UKE_CONTAINER=docker`).
  - Added `--nocheck` to `rpmbuild -ba` to skip heavy test suites during image composition.
  - Added `Provides: uke-firmware` and `xiaomi-uke-firmware` to `uke-oem-data.spec` (`1d20cc3`).
  - Wired `uke-fedora*-oem-data-*.rpm` into the primary DNF install transaction.
  - Set `UKE_COPR=0` and resolved host file permission on image repository paths.

## Kernel preparation fix and build unblocking (2026-11-11, later)

- Root-caused the kernel COPR `%prep` failure from the public COPR builder log
  (no API token needed): `packaging/native/prepare.sh` invoked
  `src/video/prepare-source.sh` twice. The first call applied
  `patches/video/*.patch`, whose `0012` creates
  `include/linux/qcom-uke-video.h`; the second call met the bare
  `[[ ! -e ... ]]` re-entry guard and exited 1 without output, which is why the
  log ended after the DP ELD receipt. Fixed in kernel `4ed80615`; a failing
  preparation step now names its line and command through an ERR trap, and
  `tests/native-prepare-steps-contract.sh` rejects a duplicated source step.
- Kernel `e942f625` makes ten sanitizer contracts inherit the builder's
  `ASAN_OPTIONS` (`${ASAN_OPTIONS:-detect_leaks=1}`). They forced
  `detect_leaks=1`, which LeakSanitizer cannot do under qemu-user aarch64, so
  the kernel `%prep` also failed on x86_64 hosts and CI runners that emulate
  aarch64.
- Builder `9b83d79` defines `cache_dir=/build-cache` inside the SRPM container
  heredoc. The "skip unchanged kernel SRPM" change used the host variable there,
  so every image build stopped at stage 0 with "cache_dir: unbound variable".
- Local evidence: `./ukelinux.sh --profiles tty --cross-kernel --output
  build/video13-check` logged `UKE_BUILD_STAGE source_prepare elapsed_s=1090`,
  so the kernel `%prep` passes. The run was stopped before the cross-compile,
  RPM packaging and rootfs stages; no image, RPM or on-device result exists yet.

## Last session (2026-11-11, documentation and agent-rules pass)

- Published the contributor rules as [AGENTS.md](../AGENTS.md) (removed from
  `.gitignore`) and added [docs/DEVELOPING.md](DEVELOPING.md): environment,
  checks, submodule flow, contribution targets, troubleshooting.
- Added `tools/check-dev-env.sh` (clone shape and host tools) and
  `tools/check-docs.sh` (relative links in published docs).
- Added `.github/PULL_REQUEST_TEMPLATE.md` and a developer-guide contact link in
  the issue template config.
- Fixed developer docs: CONTRIBUTING now has a code-contribution section and no
  longer claims the release image is untested on a tablet; UPSTREAM no longer
  claims `SECURITY.md` is vendored, records the real CI situation and the
  missing evidence paths; README links into submodules (404 on GitHub) replaced
  with repository URLs and dev/user entry points separated.
- Updated the three component `AGENTS.md`: removed links to the dropped
  `referances/` and `uke-linux-docs/` trees, retired the OrangeFox and missing
  ACCESSORY paths, added the real checks with host prerequisites and the
  umbrella gitlink/PR flow (component commits `0a0a2631`, `0a48226` and `88ffc06`).
  Also moved `INSTALL.md` to `docs/INSTALL.md`, fixed every link and restored the
  Fedora 44 and CSOT wording in README (`531d154`).
- Findings recorded in the backlog: builder CI parity runner (B12), kernel
  check prerequisites (B13, partly covered by `tools/check-dev-env.sh`), docs
  and link CI (B14), stale component `AGENTS.md` evidence paths (B15), the
  user-facing release/docs refresh (B16, release polish B9 reopened), newcomer
  labels (B17), the security reporting channel (B18) and tooling nits (B19).
- Split the private journal: decisions and host quirks stay in `private/NOTES.md`,
  owner-only actions moved to `private/TODO.md`; public work remains here and in
  the backlog.
- Component source-contracts CI passed for the AGENTS commits (`0a48226`,
  `88ffc06`) and the cleanup commits (`facd4e1`, `8d95e01`); the kernel
  workflow runs on pull requests only.
- Renamed the remaining internal builder and hardware-support caches from
  `referances/` to `source-cache/`, including the staging loop, pinned source
  inputs, component/family caches, manifests' local evidence paths and the
  nested AGENTS policy (builder `3662473`, hardware `847a004`). The unsupported
  Ubuntu packaging route keeps its external source-layout names.
- Removed the trees that kept reappearing: the kernel `referances/` cache and
  OEM evidence, the kernel and builder `reports/`, and the hardware-support
  top-level `docs/`. The kernel SRPM cache moved to the ignored
  `source-cache/releases/`; the Makefile and two native object checks now use
  it (all entry points: kernel `96ee63a6`), and scrubbed the last
  `referances/` path strings from the research/source-plan manifests (kernel
  `57d7fbb3`). Added `tools/check-forbidden-paths.sh` and documented the policy
  in AGENTS/UPSTREAM/DEVELOPING; component commits `2d6ed7b8`/`96ee63a6`/
  `57d7fbb3`, `e9d0cca`, `604b443`/`bd04ec9`.
- Rewrote all three component `AGENTS.md` from the umbrella template and
  removed October documents: 26 kernel, 3 builder and 18 hardware-support
  files created in October 2026 or earlier that were unreferenced and not
  maintained in November (component commits `8d968d14`, `facd4e1`, `8d95e01`).
  README/AGENTS/BUILDING/SECURITY, November-maintained and referenced documents
  remain; removed files are recoverable from git history.

## Previous session (2026-11-11, earlier)

- Added the first version of the root `AGENTS.md`, `docs/STATE.md` and
  `docs/BACKLOG.md`; rewrote the private notes as a decision/host journal.
- Created the COPR project and published eight userland packages. The kernel
  `%prep` failure was later root-caused from the public builder log and fixed
  in `e942f625`; the COPR upload is still pending.
- The image CI run 43008866968 was cancelled; the extended workflow has not run.
- No image has been built after the broad native archive fix (`30dfa729`).

## Working now

- Kernel video bring-up is source-complete: the candidate series applies on
  7.3.1, all contracts pass, Iris/VIDEOCC/interconnect objects compile, and the
  OEM `vpu30_2v.mbn` firmware is packaged.
- COPR project <https://copr.fedorainfracloud.org/coprs/linuxgamer/uke-fedora/>
  has `uke-boot-integration`, `uke-console-input`, `uke-core-meta`,
  `uke-battery-observer`, `uke-touchscreen`, `libssc`, `iio-sensor-proxy` and
  `uke-ssc-fileservice`.
- Images get an optional COPR repo (`UKE_COPR=0` disables it), excluding kernel
  and OEM packages.
- Desktop profiles install Firefox, a text editor, the store, an archive manager
  and a calculator, plus `zh_CN.UTF-8` and Noto Sans CJK.
- Release packaging splits archives above 1900 MiB into parts, so the GitHub
  2 GiB asset limit no longer aborts publishing; issue templates exist and
  screenshots are in the README.
- Build speed: kernel SRPM reuse, locked status file, `--parallel N`, CI caches.
- The tablet boots from CI run `44359576130` to a root shell, and the Pogo
  keyboard works. See "First boot and working keyboard" above.
- RPMH regulator suppliers register, so UFS, PHY and the keyboard rails bind
  instead of deferring.
- Flatpak apps can reach the host V4L2 VA-API driver through a global override;
  see `.github/workflows/build.yml` and `configs/rootfs/var/lib/flatpak/overrides/global`.

## Blockers
- **Ext4 rootfs expansion blocked by error flag** (fixed 2026-11-17). The ext4 superblock error flag prevented online resize. Fixed on‑device via `echo u > /proc/sysrq-trigger` (emergency remount‑ro), `e2fsck -fy`, `resize2fs`. Documented in [INSTALL.md](INSTALL.md#emergency-rootfs-expansion-ext4).

- **Kernel COPR build needs a rebuild.** The `%prep` failure is fixed and the
  native preparation passes locally, but the fixed SRPM has not been uploaded;
  that needs the rotated token (B2).
- **Image CI run `43008866968` was cancelled.** The extended workflow (cache,
  `--parallel`, release packaging) has not run successfully yet.
- **No image has been built after the broad native archive fix** (`30dfa729`).
  The blockers found on that path are fixed (kernel `4ed80615`/`e942f625`,
  builder `9b83d79`) and the local cheap stage passes the kernel `%prep`, but no
  full run has completed.
- **COPR API credentials need rotation**; do not repeat the value in public.
- OEM firmware and sensor blobs stay out of public repositories; see
  [COPR.md](COPR.md).
- The removed upstream evidence trees are documented in
  [DEVELOPING.md](DEVELOPING.md#missing-evidence-paths); do not recreate them.

## Next action

The boot and keyboard milestone is reached, so the open work is now the remaining
hardware and the guards that should have caught the defects above.

The ABL regression guard is the cheapest one: `tests/abl-dt-contract.sh` already
asserts the `i2c@a8c000` outcome, but no script runs it, which is why the scope
pass could disable the keyboard bus unnoticed. Wire it into
`prepare-abl-source.sh` or `make validate` next.

After that, rotate the COPR token (B2), upload the fixed kernel SRPM and confirm
a green COPR build (B1). All of these are in the backlog.

Two hardware defects found while chasing the keyboard are still open and are
independent of it:

- **USB host re-enumeration fails after a role switch.** `xhci-hcd` is removed
  and re-registered about three seconds later, and every device plugged into the
  port then fails with `device descriptor read/64, error -71` and
  `unable to enumerate USB device`. The `usb-profile` is `typec-v1`, so the port
  is dual-role and the switch leaves the PHY in a state that cannot enumerate.
- **The touchscreen rejects most frames.** `nt36532-uke-touch spi1.0` logs
  `Touch matrix packet rejected: -74` (EBADMSG) hundreds of times per second
  while the panel still tracks touches, so `nvt_uke_decode()` rejects most
  frames but enough succeed to keep the pointer usable.
