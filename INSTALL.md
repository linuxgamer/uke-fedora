# Install Fedora 44 on Xiaomi Pad 7

This guide has been tested on **Xiaomi Pad 7**. The release builder produces separate
TTY, KDE, GNOME, Phosh and Plasma Mobile images. The boot image goes to **`boot_a`** and its root filesystem goes to
**`userdata`**. Slot B can be used for TWRP. Replacing
`userdata` erases all Android user data. The bootloader must be unlocked!

## 1. Prerequisites

These images were built and tested against HyperOS **3.304 Global**. Confirm
that firmware baseline and unlock the bootloader before installing; other OEM
versions have not been validated for this release.
### Unlocking the bootloader

1. In HyperOS, enable Developer options, then `OEM unlocking` and USB debugging.
2. Use Xiaomi's Mi Unlock tool on a Windows host with the same Mi account as the
   tablet. Xiaomi may enforce a waiting period (often 168 hours) before the
   unlock is allowed; plan for it.
3. Unlocking wipes all user data and may affect the warranty. Back up first.
4. Never re-lock the bootloader while a non-stock `boot` or `vendor_boot` image
   is flashed.
5. Do not flash firmware from an older ROM: anti-rollback can brick the tablet.

Official unlock request: <https://en.miui.com/unlock/>

After unlocking, choose any available image you want, there are multiple variants:
- KDE - Best support
- GNOME - boots and works on the tested TM tablet.
- Phosh/Plasma Mobile - experimental.
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

KDE uses Plasma Setup; its touch-only setup and login have been tested. GNOME
has also been tested on the TM tablet. Plasma Mobile, Phosh and TTY first boot
still need on-device testing. Create your own account; the images include no
preset password.

If Fedora does not boot:
1. Keep the exact error or a photo of the screen and make a bug report.
2. Make sure you flashed the correct `fedora_boot.img` and `userdata.img` from
   the same build.
3. Try debugging from TWRP: extract `twrp_recovery_ab.tar.zst` from the release,
   boot it with `fastboot boot twrp_recovery_ab.img` and inspect the partitions.

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
