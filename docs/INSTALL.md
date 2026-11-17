# Install Fedora 44 on Xiaomi Pad 7

This guide has been tested on **Xiaomi Pad 7**. TTY, KDE, GNOME, Phosh and Plasma Mobile images are available for install. The boot image goes to **`boot_a`** and its root filesystem goes to
**`userdata`**. Slot B can be used for TWRP. Replacing
`userdata` erases all Android user data. The bootloader must be unlocked!

## 1. Prerequisites

These images were built and tested with HyperOS **3.304 Global**. Ensure you have this version and unlock the bootloader before installing, other OEM
versions have not been validated for this release.
### Unlocking the bootloader

1. In HyperOS, enable Developer options, then `OEM unlocking` and USB debugging.
2. Apply for bootloader unlock in Xiaomi community app.
3. Use Xiaomi's Mi Unlock tool on a Windows host with the same Mi account as the
   tablet. Xiaomi may enforce a waiting period (often 168 hours) before the
   unlock is allowed; plan for it.
4. Unlocking wipes all user data and may affect the warranty. Back up first.
5. Never re-lock the bootloader while a non-stock `boot` or `vendor_boot` image
   is flashed.
6. Do not flash firmware from an older ROM: anti-rollback can brick the tablet.

Official unlock request: <https://en.miui.com/unlock/>

After unlocking, choose any available image you want, there are multiple variants:
- KDE - Best support
- GNOME - boots and works.
- Phosh/Plasma Mobile - not tested.
- TTY - bare console; touch keyboard not yet tested on the tablet.

## 2. Check the tablet in fastboot

Run these commands yourself on a computer with a reliable fastboot connection (USB 2.0).

```sh
fastboot devices
fastboot getvar product
fastboot getvar unlocked
fastboot getvar is-userspace
fastboot getvar current-slot
fastboot getvar partition-size:boot_a
fastboot getvar partition-size:userdata
fastboot getvar is-logical:userdata
```

Continue only if the connected product is `uke`, the bootloader is `unlocked`,
this is bootloader fastboot (`is-userspace: no`), `boot_a` exists and `userdata`
is a physical partition. The boot partition should hold at least 100,663,296
bytes (~96 MiB). The `userdata` partition must be at least as large as
`root_image_logical_bytes` in the downloaded pair's `manifest.json`; this
checks the image against the actual tablet without assuming a storage size.

## 3. Flash it!

It is also recommended to install TWRP in case your system breaks:

```sh
fastboot flash recovery_ab "twrp_recovery_ab.img"
```

`cd` into the extracted folder with Fedora images and use bootloader fastboot:

```sh
fastboot flash userdata "userdata.img"
fastboot flash boot_a "fedora_boot.img"
fastboot set_active a
fastboot reboot
```

If flashing `userdata` fails, **do not reboot into Fedora**. Check the exact
error, the fastboot version and the USB connection before retrying. The
reported need for `fastbootd` in
[issue #5](https://github.com/linuxgamer/uke-fedora/issues/5) was later traced
to a broken `termux-fastboot` installation; the reporter confirmed the commands
above work from bootloader fastboot.

These commands overwrite `boot_a` and **all existing userdata!**
Do not touch `userdata` afterward, that would erase the
new Fedora system. If a command fails, **stop** and inspect the error
before changing slots or retrying.

## First boot and return to Android

All images will launch setup wizards. Create your own account, the images include no preset password.

If Fedora does not boot:
1. Keep the exact error or a photo of the screen and make a bug report.
2. Make sure you flashed the correct `fedora_boot.img` and `userdata.img` from
   the same build.
3. Try debugging from TWRP: extract `twrp_recovery_ab.tar.zst` from the release,
   boot it with `fastboot --set-active=b` and `fastboot reboot recovery and inspect the partitions`. To boot back into Fedora run `fastboot --set-active=a` and `fastboot reboot`

### Return to Android

Switching to slot B alone cannot restore `userdata`; that partition now holds
Fedora. Keep a matching stock fastboot ROM and your data backup before flashing.

1. Download the stock ROM for your region and the TWRP archive from the release.
2. Back up anything still readable: boot into TWRP and copy the internal storage
   or the partitions you need to a USB drive.
3. Return to bootloader fastboot, then run the stock `flash_all.sh` (or MiFlash)
   from the matching ROM. It erases `userdata` and restores `boot`, `vendor_boot`
   and the stock system.
4. Do not flash firmware from an older ROM: anti-rollback can brick the tablet.
5. Never re-lock the bootloader while a non-stock `boot` or `vendor_boot` is
   flashed.

## Emergency rootfs expansion (ext4)

If the root filesystem does not expand to fill the `userdata` partition on first boot, the ext4 superblock may have an error flag set that blocks online resizing. Symptoms:

- `df -h /` shows ~8 GiB used of a larger partition (e.g. 105 GiB `userdata`)
- `dmesg -T | grep ext4` shows:
  ```
  EXT4-fs warning: There are errors in the filesystem, so online resizing is not allowed
  ```

### Fix without USB / without rebooting the tablet

1. Ensure `sysrq` is enabled (default on these images):
   ```sh
   cat /proc/sys/kernel/sysrq
   # should print 1 or higher
   ```

2. Trigger an emergency remount-read-only via the SysRq `u` key:
   ```sh
   sudo sh -c 'echo u > /proc/sysrq-trigger'
   ```
   The root filesystem will be remounted read-only. This clears the in‑memory ext4 error flag.

3. Run the ext4 repair (it will prompt; answer `y`):
   ```sh
   sudo e2fsck -fy /dev/disk/by-partlabel/userdata
   ```

4. The filesystem is now clean and mounted read‑only. Remount it read‑write and grow it:
   ```sh
   sudo mount -o remount,rw /
   sudo resize2fs /dev/disk/by-partlabel/userdata
   ```

5. Verify:
   ```sh
   df -h /
   # should now show the full partition size (e.g. 105 GiB)
   ```

**Why this works**: The ext4 kernel driver sets an in‑memory `EXT4_ERROR_FS` flag when it detects metadata checksum mismatches. Online resize refuses to run while that flag is set. The SysRq `u` (emergency remount‑ro) forces the filesystem to flush and remount read‑only, which clears the flag. `e2fsck` fixes the on‑disk metadata (bitmap checksums, free counts). After remounting read‑write, the flag stays clear and `resize2fs` succeeds.

> **Note**: This procedure modifies the live root filesystem. It worked on a Xiaomi Pad 7 (SM7675) running the Fedora 44 `userdata` image. If `e2fsck` reports unrecoverable corruption, flash a fresh image instead.

