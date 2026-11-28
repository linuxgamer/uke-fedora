# SPDX-License-Identifier: GPL-3.0-only
"""Acknowledge the slot-A image that supplied this boot's device tree arguments."""

from pathlib import Path
import re
import stat
import subprocess
import sys


DEVICE_TREE = Path("/sys/firmware/devicetree/base")
PARTITIONS = Path("/dev/disk/by-partlabel")
# Accept the pre-preview marker on tablets that still have the earlier boot image.
BOOT_ID_ARGS = (b"uke-fedora.boot_id=", b"ukelinux.boot_id=")
SLOT_ARG = b"androidboot.slot_suffix="
BOOTCTL_FALLBACK_MESSAGES = {
    "Couldn't find cmdline arg: 'slot_suffix'",
    "get_current_or_active_slot: Unable to read boot slot property",
}


def block_device(path):
    info = path.stat()
    if not stat.S_ISBLK(info.st_mode):
        raise ValueError(f"{path} is not a block device")
    return info.st_rdev


def boot_header(path):
    with path.open("rb") as stream:
        header = stream.read(4096)
    if len(header) != 4096:
        raise ValueError(f"Cannot read the boot header of {path}")
    return header


def verify_boot_identity(cmdline, handoff, slot_property, boot_a, boot_b):
    if [arg for arg in cmdline.split() if arg.startswith(b"root=")] != [b"root=PARTLABEL=userdata"]:
        raise ValueError("This boot does not select userdata")
    for args in (cmdline.split(), handoff.split()):
        slots = [arg for arg in args if arg.startswith(SLOT_ARG)]
        if slots not in ([], [SLOT_ARG + b"_a"]):
            raise ValueError("Boot arguments disagree with slot A")
    if slot_property not in (None, b"_a\0"):
        raise ValueError("Device tree slot disagrees with slot A")

    identifiers = [arg for arg in handoff.split() if arg.startswith(BOOT_ID_ARGS)]
    if len(identifiers) != 1:
        raise ValueError("Bootloader handoff lacks a unique uke-fedora boot identity")
    digest = identifiers[0].partition(b"=")[2]
    if not re.fullmatch(rb"[0-9a-f]{64}", digest):
        raise ValueError("The uke-fedora boot identity is malformed")
    arguments = boot_a[44:1580].split(b"\0", 1)[0].split()
    if (boot_a[:8] != b"ANDROID!" or boot_a[40:44] != b"\x04\0\0\0" or
            [arg for arg in arguments if arg.startswith(BOOT_ID_ARGS)] != identifiers or
            b"senemos.root=userdata" not in arguments or
            any(prefix + digest in boot_b for prefix in BOOT_ID_ARGS)):
        raise ValueError("The running uke-fedora image cannot be attributed uniquely to boot_a")


def bootctl(*args):
    result = subprocess.run(["/usr/bin/qbootctl", *args], capture_output=True, text=True,
                            encoding="utf-8", env={"LC_ALL": "C"}, check=True)
    errors = set(result.stderr.splitlines()) - BOOTCTL_FALLBACK_MESSAGES - {""}
    if errors:
        raise ValueError("; ".join(sorted(errors)))
    return result.stdout.strip()


def acknowledge():
    if b"xiaomi,uke" not in (DEVICE_TREE / "compatible").read_bytes().split(b"\0"):
        raise ValueError("Expected a Xiaomi Uke tablet")
    if block_device(PARTITIONS / "userdata") != Path("/").stat().st_dev:
        raise ValueError("The running root filesystem is not on userdata")
    boot_a, boot_b = PARTITIONS / "boot_a", PARTITIONS / "boot_b"
    if block_device(boot_a) == block_device(boot_b):
        raise ValueError("Boot partitions refer to the same block device")
    slot = DEVICE_TREE / "firmware/android/slot_suffix"
    verify_boot_identity(Path("/proc/cmdline").read_bytes(),
                         (DEVICE_TREE / "chosen/bootargs").read_bytes().removesuffix(b"\0"),
                         slot.read_bytes() if slot.exists() else None,
                         boot_header(boot_a), boot_header(boot_b))

    if bootctl("-a") != "Active slot: _a" or bootctl("-b", "a") != "SLOT _a: is marked bootable":
        raise ValueError("Slot A must be active and bootable")
    status = bootctl("-n", "a")
    if status == "SLOT _a: is marked successful":
        return
    if status != "SLOT _a: is not marked successful":
        raise ValueError(f"Unexpected slot status: {status}")
    bootctl("-m", "a")
    if bootctl("-n", "a") != "SLOT _a: is marked successful":
        raise ValueError("Slot A success flag did not verify")
    print("Slot A boot marked successful")


if __name__ == "__main__":
    try:
        acknowledge()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Slot A acknowledgement failed: {exc}", file=sys.stderr)
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            print(exc.stderr.rstrip(), file=sys.stderr)
        sys.exit(1)
