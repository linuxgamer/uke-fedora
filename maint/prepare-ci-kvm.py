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

    # QEMU/libvirt/OVMF for running ARM64 guests. The tree overlay may already
    # have added the Discover Flatpak backends to this line, so accept both.
    kvm_packages = ("                              qemu-system-aarch64 qemu-img libvirt "
                    "virt-install edk2-aarch64); display=sddm ;;")
    variants = (
        ("                              powerdevil firefox kate plasma-discover ark kcalc); display=sddm ;;",
         "                              powerdevil firefox kate plasma-discover ark kcalc\n" + kvm_packages),
        ("                              powerdevil firefox kate plasma-discover plasma-discover-flatpak "
         "plasma-discover-packagekit ark kcalc); display=sddm ;;",
         "                              powerdevil firefox kate plasma-discover plasma-discover-flatpak "
         "plasma-discover-packagekit ark kcalc\n" + kvm_packages),
    )
    path = ROOT / f"{builder}/build-rootfs.sh"
    text = path.read_text()
    for old_line, new_line in variants:
        if text.count(old_line) == 1:
            if writes:
                path.write_text(text.replace(old_line, new_line, 1))
            break
    else:
        if "qemu-system-aarch64" not in text:
            raise SystemExit(f"{builder}/build-rootfs.sh: KVM package line not found")
        print("overlay: KVM packages already present")

    print("kvm overlay applied" if writes else "kvm overlay patterns validated")


if __name__ == "__main__":
    main()
