#!/usr/bin/env python3
"""Check that arm64 KVM host support and the guest tooling are in the tree.

Like prepare-ci-fallback.py, this used to patch the sources on the runner.
CONFIG_VHOST_NET, CONFIG_VSOCKETS and the QEMU/libvirt packages are product
settings: a locally built image should boot guests too, so they belong in the
builder and kernel config, not in a CI-only rewrite.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

MARKERS = [
    ("senemos-uke-kernel/packaging/native/native.config", "CONFIG_VHOST_NET=y",
     "vhost networking for guest traffic"),
    ("senemos-uke-kernel/packaging/native/native.config", "CONFIG_VSOCKETS=y",
     "vsock, the host/guest channel libvirt uses"),
    ("senemos-uke-kernel/packaging/native/native.config", "CONFIG_VIRTIO_VSOCKETS=y",
     "the virtio transport for it"),
    ("uke-fedora-builder/build-rootfs.sh", "qemu-system-aarch64",
     "the guest tooling in the KDE image"),
    ("uke-fedora-builder/build-rootfs.sh", "virt-install",
     "libvirt's installer front end"),
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
        raise SystemExit("KVM settings have drifted from what CI expects")
    print(f"KVM settings present ({len(MARKERS)} markers)")


if __name__ == "__main__":
    main()
