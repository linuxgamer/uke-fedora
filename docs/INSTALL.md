# Install Fedora 44 on Xiaomi Pad 7

This is an experimental manual installation for **Xiaomi Pad 7 (`uke`)** with
Xiaomi OS3.0.304.0.WOZMIXM firmware. The release builder produces separate
TTY, KDE, GNOME, Phosh and Plasma Mobile images. Tablet boot and hardware
operation of a newly built image still need physical testing.

The Linux boot image goes to **`boot_a`** and its root filesystem goes to
**`userdata`**. Confirm that slot B still has a working Android boot path;
the commands below leave its boot images in place. Replacing
`userdata` erases the shared Android user data; selecting slot B later cannot
restore those data. Keep a data backup, the original boot images and the full
OEM firmware before starting. The bootloader must be unlocked.

## 1. Build a profile

Clone the workspace with submodules. From its root, build the profile you want.
On an x86_64 PC, `--cross-kernel` speeds up kernel compilation:

```sh
git clone --recurse-submodules https://github.com/linuxgamer/uke-fedora.git
cd uke-fedora
./uke-fedora-builder/build-fedora44-images.sh --cross-kernel \
  --profiles kde --output build/fedora44-images
```

Replace `kde` with `gnome`, `tty`, `phosh` or `plasma-mobile`. On an ARM64 host,
omit `--cross-kernel`. Phosh and Plasma Mobile are experimental profiles. The
builder verifies its bundled OS3.0.304.0 OEM inputs and does not access the
tablet. If a build was interrupted, repeat the same command with `--resume`.
Wait for the script to report completed image pairs.

## 2. Check the image pair

Set `PAIR` to the directory for your chosen profile. For GNOME, use
`gnome-pair`; for TTY, use `tty-pair`.

```sh
PAIR=build/fedora44-images/kde-pair
(cd "$PAIR" && sha256sum -c SHA256SUMS)
jq '{device, release, profile, kernel_release, boot_partition, root_partition, root_image_logical_bytes, boot_tested, hardware_tested}' "$PAIR/manifest.json"
```

Every checksum must pass. The manifest must say `uke`, Fedora release `44`,
the selected profile, `boot_a` and `userdata`. Its `boot_tested` and
`hardware_tested` values describe this build's test status; do not read `false`
as a boot failure. Use `fedora_boot.img` and `userdata.img` from the **same**
`*-pair` directory. `userdata.img` is an Android sparse ext4 image. Do not
flash `userdata.raw.img` or a file from `*-rootfs`.

## 3. Check the tablet in bootloader fastboot

Run the following commands yourself on a computer with reliable fastboot USB
communication. This repository does not run fastboot for you.

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

Continue only if the connected product is `uke`, the bootloader is unlocked,
this is bootloader fastboot (`is-userspace: no`), `boot_a` exists and `userdata`
is a physical partition. The boot partition must hold at least 100,663,296
bytes. The `userdata` partition must be at least `root_image_logical_bytes` from the
manifest. A missing or unclear answer needs checking before any write. Preserve
slot B's boot partitions; neither `boot_b` nor Android early firmware is an
installation target. The commands are described in the
[Android fastboot reference](https://source.android.com/docs/core/architecture/bootloader/fastbootd).

## 4. Flash the checked pair

These commands overwrite `boot_a` and **all existing userdata**. Run them only
after the checks above and your backup are complete:

```sh
fastboot flash boot_a "$PAIR/fedora_boot.img"
fastboot flash userdata "$PAIR/userdata.img"
fastboot set_active a
fastboot reboot
```

Do not run `fastboot -w` or format `userdata` afterward: that would erase the
new Fedora root filesystem. If a command fails, stop and inspect the error
before changing slots or retrying.

## First boot and return to Android

On first boot, the tablet should show a Fedora console prompt to create a local
administrator account. Choose a lowercase user name and a password of at least
eight characters. The graphical login starts after account creation for desktop
profiles. TTY stays at a console. The image ships with no user password or
password hash, and the root account is locked.

If Fedora does not boot, keep the exact error or a photo of the screen and use
your working recovery route. Slot B retains the Android boot images, but
Android user data were replaced. Returning to Android requires restoring those
data or following the full OEM firmware recovery procedure; `fastboot
set_active b` by itself does not restore them. Avoid writing Android boot or
firmware partitions while diagnosing the Fedora pair.
