#!/usr/bin/env python3
# Equivalent of `fastboot set_active b` for the Android BCB in misc.
# Back up misc first: sudo dd if=/dev/disk/by-partlabel/misc of=misc-backup.bin
import struct
import sys
import zlib

MISC = "/dev/disk/by-partlabel/misc"
BCB_OFFSET = 2048
BCB_SIZE = 32


def crc32_le(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def make_control(slot: str) -> bytes:
    if slot not in ("a", "b"):
        raise SystemExit("slot must be a or b")
    ctl = bytearray(BCB_SIZE)
    suffix = ("_" + slot).encode()
    ctl[0:4] = suffix.ljust(4, b"\0")
    ctl[4:8] = b"BCB\0"
    ctl[8] = 1          # version low
    ctl[9] = 0          # version high
    ctl[10] = 2         # nb_slot
    ctl[11] = 0         # recovery_tries_remaining
    ctl[12] = 0         # merge_status
    ctl[13:21] = b"\0" * 8
    ctl[28:32] = struct.pack("<I", crc32_le(bytes(ctl[:28])))
    return bytes(ctl)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} a|b")
    data = make_control(sys.argv[1])
    with open(MISC, "r+b") as f:
        f.seek(BCB_OFFSET)
        f.write(data)
        f.flush()
    print(f"misc BCB slot_suffix=_{sys.argv[1]} crc=0x{struct.unpack('<I', data[28:32])[0]:08x}")


if __name__ == "__main__":
    main()
