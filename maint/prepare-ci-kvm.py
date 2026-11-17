#!/usr/bin/env python3
"""Enable KVM host support, vhost networking and QEMU/libvirt in the image."""
import argparse
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def replace_once(rel, old, new, writes):
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{rel}: expected one match, found {count}: {old[:70]!r}")
    if writes:
        path.write_text(text.replace(old, new, 1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    writes = not args.check

    kernel = "senemos-uke-kernel"
    builder = "uke-fedora-builder"

    # arm64 KVM host is CONFIG_KVM; add vhost networking and vsock.
    replace_once(f"{kernel}/packaging/native/native.config",
                 "# CONFIG_VHOST_NET is not set", "CONFIG_VHOST_NET=y", writes)
    replace_once(f"{kernel}/packaging/native/native.config",
                 "# CONFIG_VSOCKETS is not set",
                 "CONFIG_VSOCKETS=y\nCONFIG_VSOCKETS_DIAG=y\nCONFIG_VIRTIO_VSOCKETS=y", writes)

    # QEMU/libvirt/OVMF for running ARM64 guests.
    replace_once(f"{builder}/build-rootfs.sh",
                 "                              powerdevil firefox kate plasma-discover ark kcalc gdm); display=sddm ;;",
                 "                              powerdevil firefox kate plasma-discover ark kcalc gdm\n"
                 "                              qemu-system-aarch64 qemu-img libvirt virt-install edk2-aarch64); display=sddm ;;",
                 writes)

    print("kvm overlay applied" if writes else "kvm overlay patterns validated")


if __name__ == "__main__":
    main()
