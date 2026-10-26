# Install Fedora 44 on Xiaomi Pad 7

This guide has been tested on **Xiaomi Pad 7**. The release builder produces separate
TTY, KDE, GNOME, Phosh and Plasma Mobile images. The boot image goes to **`boot_a`** and its root filesystem goes to
**`userdata`**. Slot B can be used for TWRP. Replacing
`userdata` erases the shared Android user data. The bootloader must be unlocked!

## 1. Prerequisites

You must run HyperOS **3.304 Global** and have unlocked bootloader, otherwise you may **brick** your tablet.
After unlocking, choose any available image you want, there are multiple variants:
- KDE - Best support
- GNOME - Should work well
- Phosh/Plasma mobile - experimantal, things may break.
- TTY - bare console, OTG keyboard needed.

## 2. Check the tablet in bootloader fastboot

Run the following commands yourself on a computer with reliable fastboot USB
communication.

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
is a physical partition. The boot partition must hold at least 100,663,296
bytes(~96MiB). The `userdata` partition must be at least `root_image_logical_bytes` from the manifest.

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
Do not touch `userdata` afterward: that would erase the
new Fedora system. If a command fails, **stop** and inspect the error
before changing slots or retrying.

## First boot and return to Android

KDE and Plasma Mobile show Plasma Setup on first boot. GNOME and Phosh use
GNOME Initial Setup. Create your own administrator account with the touchscreen;
no account or password is supplied with the image. These setup flows still need
on-device testing, especially the on-screen keyboard on the tablet.

The TTY image instead prompts on the console for a lowercase user name and a
password of at least eight characters. Without a physical keyboard, prepare
that account through ADB in TWRP before starting Fedora. The root account is
locked in every image.

If Fedora does not boot, keep the exact error or a photo of the screen and use
your working recovery route. Slot B retains the Android boot images, but
Android user data were replaced. Returning to Android requires restoring those
data or following the full OEM firmware recovery procedure; `fastboot
set_active b` by itself does not restore them. Avoid writing Android boot or
firmware partitions while diagnosing the Fedora pair.
