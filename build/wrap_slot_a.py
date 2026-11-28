# SPDX-License-Identifier: GPL-3.0-only
"""Wrap a staged Senemos kernel using the verified uke-fedora slot-A recipe."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from android_boot import check_kernel, inspect_boot, write_userdata_boot
from stage_senemos import PIN, sha256, verify_payload


# Slot-A template used by uke-fedora-builder at 366247338e60f57954f39a95767b57f3e8a8d59a.
STOCK_SHA256 = "1eaf4858a7c70bee9b663b485f3192b164738bbdae3edbb986a5419621c8ef30"
BOOT_BYTES = 100_663_296


def block_coresight(kernel, output, expected_sha256):
    # Senemos forces its built-in command line. Replace its three copies
    # in place and use padding to keep every other byte at the same offset.
    before = b"quiet loglevel=1 rd.systemd.show_status=no"
    after = b"loglevel=1 module_blacklist=coresight"
    data = kernel.read_bytes()
    if data.count(before) != 3:
        raise ValueError("Unexpected Senemos built-in command lines")
    patched = data.replace(before, after.ljust(len(before)))
    if hashlib.sha256(patched).hexdigest() != expected_sha256:
        raise ValueError("CoreSight-blocked kernel differs from the reviewed boot payload")
    output.write_bytes(patched)


def avb_info(image):
    details = subprocess.check_output(["avbtool", "info_image", "--image", str(image)], text=True)
    rollback = re.search(r"^Rollback Index:\s*(\d+)\s*$", details, re.M)
    properties = dict(re.findall(r"^\s*Prop: ([A-Za-z0-9_.-]+) -> '(.*)'$", details, re.M))
    if rollback is None or "com.android.build.boot.os_version" not in properties:
        raise ValueError("Boot image lacks the expected AVB metadata")
    return rollback[1], properties


def wrap(stage, stock, output):
    pin = json.loads(PIN.read_text())
    release = pin["release"]
    verify_payload(stage, release)
    source = stage / "boot/userdata.img"
    kernel = stage / "rootfs/usr/lib/modules" / release / "vmlinuz"
    if stock.stat().st_size != BOOT_BYTES or sha256(stock) != STOCK_SHA256:
        raise ValueError("Stock image differs from the reviewed slot-A template")
    stock_header = inspect_boot(stock)
    if stock_header.ramdisk_bytes or stock_header.signature_bytes or not stock_header.avb_footer:
        raise ValueError("Unexpected Android boot header in slot-A template")
    rollback, properties = avb_info(stock)
    inspect_boot(source).check_userdata()
    kernel_digest = pin["boot_kernel_sha256"]

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        wrapped = Path(tmp) / "boot.img"
        boot_kernel = Path(tmp) / "vmlinuz"
        block_coresight(kernel, boot_kernel, kernel_digest)
        payload_end = write_userdata_boot(wrapped, boot_kernel, kernel_digest, stock_header.os_version, BOOT_BYTES)
        footer = [
            "avbtool", "add_hash_footer", "--image", wrapped,
            "--partition_name", "boot", "--partition_size", str(BOOT_BYTES),
            "--algorithm", "NONE", "--salt", STOCK_SHA256, "--rollback_index", rollback,
        ]
        for key, value in properties.items():
            footer.extend(("--prop", f"{key}:{value}"))
        subprocess.run(footer, check=True)
        subprocess.run(["avbtool", "verify_image", "--image", wrapped], check=True)
        result_header = check_kernel(wrapped, kernel_digest)
        result_header.check_boot_id(kernel_digest)
        if (result_header.image_bytes != BOOT_BYTES or
                not result_header.avb_footer or
                result_header.payload_end != payload_end or
                result_header.os_version != stock_header.os_version or
                avb_info(wrapped) != (rollback, properties)):
            raise ValueError("Wrapped boot image does not match the slot-A layout")
        output.hardlink_to(wrapped)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("senemos_stage", type=Path)
    parser.add_argument("stock_boot", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error(f"Output already exists: {args.output}")
    try:
        wrap(args.senemos_stage, args.stock_boot, args.output)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Cannot wrap slot-A boot image: {exc}\n")
    print(f"Verified slot-A boot image: {args.output}")
    print(f"SHA-256: {sha256(args.output)}")


if __name__ == "__main__":
    main()
