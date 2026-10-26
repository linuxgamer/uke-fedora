# Install Fedora 44 on Xiaomi Pad 7

This guide has been tested on **Xiaomi Pad 7**. The release builder produces separate
TTY, KDE, GNOME, Phosh and Plasma Mobile images. The boot image goes to **`boot_a`** and its root filesystem goes to
**`userdata`**. Slot B can be used for TWRP. Replacing
`userdata` erases all Android user data. The bootloader must be unlocked!

## 1. Prerequisites

These images were built and tested against HyperOS **3.304 Global**. Confirm
that firmware baseline and unlock the bootloader before installing; other OEM
versions have not been validated for this release.
After unlocking, choose any available image you want, there are multiple variants:
- KDE - Best support
- GNOME - boots and works on the tested TM tablet.
- Phosh/Plasma Mobile - experimental.
- TTY - bare console; touch keyboard not yet tested on the tablet.

## 2. Check the tablet in fastboot

Run these commands yourself on a computer with reliable fastboot connection(USB 2.0).

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

`cd` into unarchived folder with Fedora images and run these commands:

```sh
fastboot set_active a
fastboot flash boot_a "fedora_boot.img"
fastboot flash userdata "userdata.img"
fastboot reboot
```

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
2. Make sure you flashed correct images
3. Try debugging from TWRP
4. To return to Android, restore your Android data backup and the matching OEM
   firmware. Switching to slot B alone cannot restore the overwritten `userdata`.
