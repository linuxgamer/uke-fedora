# Focus Keyboard — full handoff (2026-11-18)

## Current state (last message)

- Device: Xiaomi Pad 7 (uke), Fedora 44, kernel **7.3.1-106**.
- Both `boot_a` and `boot_b` were flashed with the CI boot payload
  `fedora_boot.img` (sha256 `1e0ae857d43563fe950759b5fa1a66eb11d96a474465377e58d7a53f58cb933b`,
  100663296 bytes). The `misc` BCB is `slot_suffix=_a` (crc `0x8755b009`).
- The tablet booted the **new kernel** but its initramfs dropped to emergency
  because it cannot find `/dev/disk/by-partlabel/userdata`. The **old Fedora
  rootfs and `/home` are intact**; this is a rootfs pairing/label issue, not a
  keyboard failure.
- The paired new rootfs `userdata.img` (4160938104 bytes = 3.87 GiB) and
  `boot.img` (96 MiB) are on the phone:
  `/sdcard/Download/fedora-kb/`.
- The keyboard is **not yet proven typing on the new kernel**. On the old
  kernel the runtime overlay detected the MCU at `7-004c`
  (`compatible = nanosic,wn8030-uke`), the driver probe ran
  (`probe entered`, `power_on done`, `regmap ready`) and failed at the I2C
  transfer only because that kernel lacked the RPMH LDOB22/LDOB23 allow-list
  (`wait for supplier .../rpmh-regulator-ldob23/regulator-pmxr2230-l23`).
  The new kernel has that allow-list.

## Immediate recovery — keep the old rootfs (recommended)

In the emergency shell press Enter and run:

```sh
lsblk -o NAME,SIZE,LABEL,FSTYPE
blkid
```

Find the old Fedora partition (the large one). Then:

```sh
mkdir -p /sysroot
mount -o rw /dev/<old-root-partition> /sysroot
# Fedora btrfs usually needs: mount -o rw,subvol=root /dev/<part> /sysroot
mount --move /dev /sysroot/dev
mount --move /proc /sysroot/proc
mount --move /sys /sysroot/sys
mount --move /run /sysroot/run
exec switch_root /sysroot /usr/lib/systemd/systemd
```

This boots the **existing Linux on the new kernel**; no userdata flash.

## Test the keyboard

```sh
sudo dmesg | grep -iE 'nanosic|wn8030|i2c-7|a8c000'
ls /sys/bus/i2c/devices/
cat /proc/bus/input/devices | grep -i -A4 -E 'nanosic|focus|keyboard|touchpad'
ls /sys/class/leds/nanosic*
ls -l /dev/nanosic_auth
```

Expected: `i2c-7`/`7-004c`, `hid_nanosic_wn8030` bound, a keyboard input
device, `nanosic::kbd_backlight`/`micmute` LEDs. Type on the keyboard; if no
input, capture the `dmesg` output and continue debugging.

## Persist the old rootfs with the new kernel

Change only the boot image `cmdline` (not userdata):

```sh
abootimg -u boot.img -c "cmdline=... root=PARTLABEL=<old-root-label> ..."
fastboot flash boot_a boot.img
fastboot flash boot_b boot.img
```

Use the exact old cmdline/root discovered from `blkid`/the working old boot.
This keeps the old rootfs and the new kernel.

## Fallback — new rootfs (wipes /home)

Only if the old rootfs cannot be recovered:

```sh
fastboot flash userdata /path/to/kde-pair/userdata.img
fastboot reboot
```

The new rootfs includes the WN8030 module, firmware and modules-load. The
`userdata.img` on the phone is the extracted artifact image; its sha256 is
`aab4392daaea25e1734c36ca846f4cdb6164cb36c10ac7309e7d5c3e518ffa89`
(the artifact `SHA256SUMS` lists a different `af105...` for `userdata.img`;
the boot image matches `1e0ae857...`).

## MiTrustZone / MiAuth

The driver implements the stock MiAuth handshake: start, step-3 with the
MCU-advertised key-meta and a fresh challenge, step-5 token send. Without a
token daemon it deliberately skips step 5 instead of stalling the IRQ thread.
The real `devauth_token_get` needs Xiaomi's Android `midevauthd`/trustlet HAL
(`/dev/smcinvoke`); mainline exposes `/dev/tee0` (qcomtee 5.2.0) but not the
stock HAL. The HID path does not depend on the token; the 12 s wake keepalive
is the practical dropout fix.

## What is implemented in `main`

- Kernel `eae9b27` (and `378c41f`, `2e2a114`): mature WN8030 driver
  (keyboard + consumer + touchpad HID, LEDs, hinge/tablet-mode, uke variant,
  reset/boot/wake timing, wake keepalive, touchpad quirk, key-meta/auth).
- Umbrella `08cc97a`/`03e89db`/`d024997`: kernel pin, firmware, optional
  `nanosic-authd`, `modules-load.d`, CI hardening-contract fix.
- Build log from CI `ci-44209941663` confirms:
  `Nanosic WN8030 driver staged`, `CC/LD/INSTALL/SIGN hid-nanosic-wn8030.ko`.
- Installed on the current rootfs: `/lib/modules/7.3.1-106/extra/hid-nanosic-wn8030.ko`,
  `/usr/lib/firmware/nanosic/MCU_Upgrade.bin`, `/etc/modules-load.d/nanosic.conf`,
  `nanosic-authd`.

## Images / links

- Release: `https://github.com/saksham-991/uke-fedora/releases/tag/ci-44209941663`
- Artifact: `uke-bootable-images-44209941663` (7.8 GB; `gh run download`).
- `kde-pair/fedora_boot.img` sha256 `1e0ae857...cb933b` (96 MiB) — flashed to
  both slots; also on the phone.
- `kde-pair/userdata.img` 4160938104 bytes (3.87 GiB) — on the phone; only for
  the new-rootfs fallback.
- Current rootfs extras: module, firmware, `modules-load.d`, authd (see above).
- The `misc` backup and `set_active.py` are included in this handoff.

## Rollback

```sh
sudo dd if=misc-backup.bin of=/dev/disk/by-partlabel/misc
sudo python3 set_active.py a
```

The old rootfs is untouched; both boot slots are the new kernel. The old boot
image was overwritten, so booting the old kernel is not available unless the
old image is restored from a backup/release.

## Transcript

The complete visible session (user + assistant + tool calls/results) is in
[`CHAT-TRANSCRIPT.md`](CHAT-TRANSCRIPT.md). Internal reasoning/step events are
omitted; the sudo password and ADB serial are redacted. The raw session remains
in `~/.local/share/kilo/kilo.db` (session `ses_e149d5e45ffef2uE3Xli0VbFs4`).
