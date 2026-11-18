#!/usr/bin/env python3
"""Add Flatpak, Discover backends, Flathub and VA-API sandbox support.

The builder submodule is pinned to linuxgamer/uke-fedora-builder, so this
overlay patches its build-rootfs.sh on the CI runner before the image is built.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILDER = ROOT / "uke-fedora-builder/build-rootfs.sh"
FLATPAK_OVERRIDE = ROOT / "configs/flatpak/global"


def main():
    text = BUILDER.read_text()

    def replace_once(old, new):
        nonlocal text
        count = text.count(old)
        if count != 1:
            raise SystemExit(
                f"build-rootfs.sh: expected one match, found {count}: {old[:80]!r}"
            )
        text = text.replace(old, new, 1)

    replace_once(
        "common=(NetworkManager-wifi bluez dbus-daemon mesa-dri-drivers pipewire wireplumber upower",
        "common=(NetworkManager-wifi bluez dbus-daemon mesa-dri-drivers pipewire wireplumber "
        "flatpak flatpak-session-helper PackageKit upower",
    )

    old_discover = "powerdevil firefox kate plasma-discover ark kcalc); display=sddm ;;"
    new_discover = (
        "powerdevil firefox kate plasma-discover plasma-discover-flatpak "
        "plasma-discover-packagekit ark kcalc); display=sddm ;;"
    )
    count = text.count(old_discover)
    if count != 2:
        raise SystemExit(
            f"build-rootfs.sh: expected two Discover desktop matches, found {count}"
        )
    text = text.replace(old_discover, new_discover)

    anchor = "            if [[ $profile != tty ]]; then\n"
    if text.count(anchor) != 1:
        raise SystemExit(
            f"build-rootfs.sh: expected one post-install anchor, found {text.count(anchor)}"
        )
    integration = """            test -f "$root/usr/lib64/dri/v4l2_drv_video.so" || die 'uke-vaapi-v4l2 driver missing'
            install -d -m0755 "$root/var/lib/uke-vaapi"
            install -m0644 "$root/usr/lib64/dri/v4l2_drv_video.so" "$root/var/lib/uke-vaapi/v4l2_drv_video.so"
            ln -sfn v4l2_drv_video.so "$root/var/lib/uke-vaapi/msm_drv_video.so"
            install -Dm0644 "$here/../configs/flatpak/global" "$root/var/lib/flatpak/overrides/global"
            chroot "$root" flatpak remote-add --system --if-not-exists flathub \\
                https://flathub.org/repo/flathub.flatpakrepo || die 'Failed to add Flathub remote'
"""
    text = text.replace(anchor, integration + anchor, 1)

    if not FLATPAK_OVERRIDE.is_file():
        raise SystemExit(f"missing {FLATPAK_OVERRIDE.relative_to(ROOT)}")

    BUILDER.write_text(text)
    print("Flatpak/Discover integration applied to build-rootfs.sh")


if __name__ == "__main__":
    main()
