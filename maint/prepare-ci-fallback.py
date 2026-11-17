#!/usr/bin/env python3
"""Fallback overlay: 6 GiB zram and the native Iris video path.

Applied only when the base build fails. Every replacement is asserted.
"""
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

    # 6 GiB zram: enough for KDE + browser on 8 GiB while keeping headroom.
    replace_once("uke-fedora-builder/configs/images/uke-zram-generator.conf",
                 "zram-size = min(ram / 2, 4096)", "zram-size = min(ram * 3 / 4, 6144)", writes)
    replace_once("uke-fedora-builder/src/image/audit-rootfs.sh",
                 "grep -Fxq 'zram-size = min(ram / 2, 4096)'",
                 "grep -Fxq 'zram-size = min(ram * 3 / 4, 6144)'", writes)

    # Native Iris video: instantiate the DT node and install its VPU firmware.
    replace_once(
        "uke-fedora-builder/build-rootfs.sh",
        "if [[ $copr == 1 ]]; then\n",
        'sudo install -Dm644 "$here/../uke-linux-hardware-support/xiaomi-uke-firmware/payload/oem-os3.0.304.0/firmware/qcom/vpu/vpu30_2v.mbn" '
        '"$output/root/usr/lib/firmware/qcom/uke/vpu30_2v.mbn"\n'
        "if [[ $copr == 1 ]]; then\n",
        writes)

    # The VA-API stage is an extra build stage beyond the stock count.
    replace_once(
        "uke-fedora-builder/build-images.sh",
        "build_total=$((12 + 2 * ${#build_profiles[@]}))",
        "build_total=$((13 + 2 * ${#build_profiles[@]}))",
        writes)

    # Build and install the stateful Iris VA-API backend so browsers actually
    # pick the hardware decoder instead of software decoding.
    replace_once(
        "uke-fedora-builder/build-images.sh",
        "make -C uke-linux-hardware-support/xiaomi-uke-firmware image-data-srpm\n",
        "make -C uke-linux-hardware-support/xiaomi-uke-firmware image-data-srpm\n"
        "make -C uke-linux-hardware-support/uke-video srpm\n",
        writes)
    replace_once(
        "uke-fedora-builder/build-images.sh",
        "  uke-linux-hardware-support/uke-boot/build/srpm/rpmbuild\n",
        "  uke-linux-hardware-support/uke-boot/build/srpm/rpmbuild\n"
        "  uke-linux-hardware-support/uke-video/build/srpm\n",
        writes)
    replace_once(
        "uke-fedora-builder/build-images.sh",
        "        */uke-boot/*) component=boot-integration;;\n",
        "        */uke-boot/*) component=boot-integration;;\n"
        "        */uke-video/*) component=vaapi;;\n",
        writes)
    replace_once(
        "uke-fedora-builder/build-images.sh",
        'cp "$workspace"/uke-linux-hardware-support/xiaomi-uke-firmware/build/fedora${release}-image-data/rpmbuild/RPMS/noarch/uke-fedora${release}-oem-data-3.0.304.0-2.fc${release}.noarch.rpm "$hardware_rpms/"\n',
        'cp "$workspace"/uke-linux-hardware-support/xiaomi-uke-firmware/build/fedora${release}-image-data/rpmbuild/RPMS/noarch/uke-fedora${release}-oem-data-3.0.304.0-2.fc${release}.noarch.rpm "$hardware_rpms/"\n'
        'cp "$workspace"/uke-linux-hardware-support/uke-video/build/srpm/RPMS/aarch64/uke-vaapi-v4l2-1.0.0-*.fc${release}.aarch64.rpm "$hardware_rpms/"\n',
        writes)
    replace_once(
        "uke-fedora-builder/build-rootfs.sh",
        "/core-rpm/uke-core-meta.rpm /hardware-rpms/uke-fedora*-oem-data-*.rpm\n",
        "/core-rpm/uke-core-meta.rpm /hardware-rpms/uke-fedora*-oem-data-*.rpm /hardware-rpms/uke-vaapi-v4l2-*.rpm\n",
        writes)

    print("fallback overlay applied" if writes else "fallback overlay patterns validated")


if __name__ == "__main__":
    main()
