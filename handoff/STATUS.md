# Focus Keyboard bring-up status (2026-11-18)

## 2026-11-18 update: active-slot image

The first reboot landed on the old kernel because the ABL followed the active
slot `a`, not the BCB.  The verified CI payload has now also been written to
`boot_a` and the BCB was set back to `_a`:

- `boot_a` sha256 `1e0ae857d43563fe950759b5fa1a66eb11d96a474465377e58d7a53f58cb933b`
- `boot_b` has the same image as a fallback
- `misc` BCB `slot_suffix=_a`, crc `0x8755b009`

Reboot again.  Both slots now contain the new kernel, so the next boot must be
the CI kernel regardless of which slot the ABL picks.

## Boot slot is ready

The CI image built successfully (`ci-44209941663`) and the KDE boot payload
was verified and flashed to the inactive slot:

- `kde-pair/fedora_boot.img`
  sha256 `1e0ae857d43563fe950759b5fa1a66eb11d96a474465377e58d7a53f58cb933b`
  (100663296 bytes, exactly the boot_b size)
- `boot_b` -> that image (100663296 bytes written)
- `misc` BCB -> `slot_suffix=_b`, magic `BCB`, version 1, nb_slot 2,
  crc `0x34c19dca`

**Reboot when you are back.** The ABL should boot slot b with the new kernel.

Backup / rollback:

```sh
sudo dd if=/home/saksham/misc-backup.bin of=/dev/disk/by-partlabel/misc
sudo python3 /home/saksham/focus-keyboard/set_active.py a
```

## What the new boot contains

`build.log` from the CI artifact confirms:

```
Nanosic WN8030 driver staged
CC [M] drivers/hid/hid-nanosic-wn8030.o
LD [M] drivers/hid/hid-nanosic-wn8030.ko
INSTALL .../lib/modules/7.3.1-106/kernel/drivers/hid/hid-nanosic-wn8030.ko
SIGN    .../hid-nanosic-wn8030.ko
```

The boot image is the branch kernel with the RPMH LDOB22/LDOB23 allow-list, the
display/keyboard DTBO, and the vendor/uke display stack.  The current rootfs
also has:

- `/lib/modules/7.3.1-106/extra/hid-nanosic-wn8030.ko`
- `/usr/lib/firmware/nanosic/MCU_Upgrade.bin`
- `/etc/modules-load.d/nanosic.conf` -> `hid-nanosic-wn8030`
- `/usr/local/sbin/nanosic-authd` + `nanosic-authd.service` (optional)

On this boot the runtime overlay already proved the bus and MCU:
`i2c-7` + `7-004c` with `compatible = nanosic,wn8030-uke`.  The only failure on
the old kernel was the missing RPMH rail supplier (the dynamic-debug trace was
`wait for supplier .../rpmh-regulator-ldob23/regulator-pmxr2230-l23`).  The new
kernel has that allow-list, so the probe can power the rails and load the MCU
firmware.

## Full new rootfs (optional)

The artifact also has `kde-pair/userdata.img` (4160938104 bytes) and
`tty-pair/userdata.img`.  Flashing `userdata` replaces the current Fedora
rootfs; the boot-only update above preserves your data and is what is installed.

## MiTrustZone

The driver implements the stock MiAuth start / step-3 handshake, reads the
MCU's key-meta candidates and picks the correct one, sends a fresh challenge,
and does not stall the IRQ thread when no token provider is running.  The HID
path does not depend on the token.  A real `devauth_token_get` still requires
Xiaomi's `midevauthd` trustlet path (Android `/dev/smcinvoke`); mainline exposes
`/dev/tee0` (qcomtee 5.2.0) but not the stock HAL.  The new driver also restarts
the 12 s wake keepalive across suspend/resume, which is the practical fix for
the "stops after a while" behaviour.

## Live-system note

The touchscreen NT36532 was recovered after the QUP1 experiments (`input48`).
Do not unbind `geni_i2c` on a live QUP1; it shares GPI streams with the
touchscreen SPI.
