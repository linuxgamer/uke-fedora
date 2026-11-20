#!/usr/bin/env python3
"""Validate that the build tree carries the product settings CI relies on.

This file used to patch them in with string replacement on every run.  That was
the wrong place: zram sizing, the VA-API driver and the Flatpak override are
product decisions, and a build that only gets them when CI rewrites the source
is a build that differs from a local one.  They now live in
the builder, and this script only checks that they are still there.

A silent no-op used to mean a broken image; here a missing marker is a failure,
so drift is loud.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (path, marker, what it is for)
MARKERS = [
    ("uke-fedora-builder/configs/images/uke-zram-generator.conf",
     "zram-size = min(ram * 3 / 4, 6144)",
     "6 GiB zram: KDE plus a browser on 8 GiB"),
    ("uke-fedora-builder/src/image/audit-rootfs.sh",
     "zram-size = min(ram * 3 / 4, 6144)",
     "the rootfs audit must agree with that sizing"),
    ("uke-fedora-builder/build-rootfs.sh",
     "uke-vaapi-v4l2-*.fc${release}.aarch64.rpm",
     "the VA-API V4L2 driver is installed with the hardware packages"),
    ("uke-fedora-builder/build-rootfs.sh",
     "var/lib/uke-vaapi/msm_drv_video.so",
     "Flatpak sandboxes get a copy of that driver"),
    ("uke-fedora-builder/configs/rootfs/var/lib/flatpak/overrides/global",
     "LIBVA_DRIVER_NAME=msm",
     "the override that points them at it"),
    ("uke-fedora-builder/src/image/build-kernel-rpms.sh",
     "uke-video",
     "the driver's component is part of every build"),
    ("uke-fedora-builder/build-images.sh",
     "uke-vaapi-v4l2-*.fc${release}.aarch64.rpm",
     "the pair build stages that RPM for the rootfs"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="accepted for symmetry; this never writes")
    parser.parse_args()

    missing = []
    for rel, marker, why in MARKERS:
        path = ROOT / rel
        try:
            text = path.read_text()
        except OSError as exc:
            missing.append(f"{rel}: cannot read ({exc})")
            continue
        if marker not in text:
            missing.append(f"{rel}: missing {marker!r} - {why}")

    if missing:
        for line in missing:
            print(line, file=sys.stderr)
        raise SystemExit("product settings have drifted from what CI expects")
    print(f"product settings present ({len(MARKERS)} markers)")


if __name__ == "__main__":
    main()
