#!/usr/bin/env python3
"""Check that the pinned component trees still carry what the build needs.

This used to rewrite the submodule sources on the runner, because the
submodules pointed at upstream repositories the fork could not push to.  They
now point at this fork, so anything the build depends on belongs in the
repository, not in a patch applied at build time: a CI image that only gets a
setting when the workflow rewrites the source is a different image from a local
build, and a source change silently turning the rewrite into a no-op failed the
run long after the real work had finished.

Two things remain here, and both are genuinely about the checkout rather than
the code: the kernel spec release has to match the builder's package lock, and
a handful of settings must still be present after a submodule bump.
"""
import argparse
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def assert_marker(rel, marker):
    """Fail when a setting the build depends on is not in the source.

    Used for behaviour that used to be patched in on the runner and now lives
    in the pinned tree.  Keeping the assertion here means a submodule bump that
    silently drops it fails the run instead of shipping a different image.
    """
    path = ROOT / rel
    text = path.read_text()
    if marker not in text:
        raise SystemExit(f"{rel}: missing expected setting: {marker[:70]!r}")


def sync_kernel_release(builder, kernel, writes):
    """Copy the kernel spec release into the builder's package lock.

    build-rootfs.sh resolves the kernel RPM by the NEVRA pinned in
    configs/package-lock.json, so a lock that lags the spec fails the rootfs
    stage after the whole kernel has been compiled.
    """
    spec = ROOT / kernel / "packaging/senemos-uke-linux-kernel-mainline.spec"
    match = re.search(r"^%global senemos_build_release ([0-9]+)$",
                      spec.read_text(), re.MULTILINE)
    if match is None:
        raise SystemExit(f"{spec.name}: no senemos_build_release line")
    release = match.group(1)
    lock = ROOT / builder / "configs/package-lock.json"
    text = lock.read_text()
    updated, count = re.subn(r'("kernel_release":\s*")[0-9]+(")',
                             rf"\g<1>{release}\g<2>", text)
    if count != 1:
        raise SystemExit(f"{lock.name}: expected one kernel_release, found {count}")
    if writes and updated != text:
        lock.write_text(updated)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate patterns without writing")
    args = parser.parse_args()
    writes = not args.check

    builder = "uke-fedora-builder"
    kernel = "senemos-uke-kernel"
    hardware = "uke-linux-hardware-support"

    # Keep the builder pointed at the kernel release the spec actually builds.
    sync_kernel_release(builder, kernel, writes)

    # The OEM firmware count and the OEM data RPM's place in the primary
    # transaction used to be patched here.  Both are product behaviour now, so
    # assert them instead of rewriting the source on the runner.
    for rel, marker in (
        (f"{builder}/src/image/verify-oem-rpm.sh", "[[ $count == 75 ]]"),
        (f"{builder}/src/image/audit-rootfs.sh", "firmware_count == 75"),
        (f"{builder}/build-rootfs.sh", "uke-fedora${release}-oem-data-3.0.304.0-2.fc${release}.noarch.rpm"),
    ):
        assert_marker(rel, marker)

    # The KDE image keeps the stock SDDM and Plasma first-run setup: no
    # pre-created account, root stays locked, and first-boot-policy keeps
    # its Requires= ordering. The earlier GDM overlay created the demo
    # account in src/public/desktop-setup.sh, which only the public COPR
    # stage sources; build-rootfs.sh never ran it, so the CI image shipped
    # no password-capable account at all.
    print("CI preflight: component settings present" if writes
          else "CI preflight: component settings present (no writes made)")


if __name__ == "__main__":
    main()
