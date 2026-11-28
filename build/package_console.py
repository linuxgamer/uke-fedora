# SPDX-License-Identifier: GPL-3.0-only
"""Package a staged Fedora root and its matching slot-A boot image."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from android_boot import check_kernel
from android_sparse import verify_sparse
from compose_console import DESKTOP, FEDORA_RELEASE, PROFILES
from device_helpers import BINARIES
from ext4_metadata import apply_and_verify
from stage_senemos import AUDIO_STAGE, PIN, sha256, verify_payload
from wrap_slot_a import BOOT_BYTES


PROJECT = PIN.parents[1]
FIRMWARE_PIN = PROJECT / "build/inputs/console-firmware.json"
OVERLAY = PROJECT / "rootfs"
HELPERS_OVERLAY = OVERLAY / "device-helpers"


def root_bytes(profile):
    return PROFILES[profile].get("image_gib", DESKTOP["image_gib"]) * 1024**3


def run(*command):
    subprocess.run(command, check=True)


def read_firmware(firmware):
    pin = json.loads(FIRMWARE_PIN.read_text())
    required = pin["files"]
    expected = required | pin.get("optional_files", {})
    files = {}
    with zipfile.ZipFile(firmware) as archive:
        entries = archive.namelist()
        names = set(entries)
        if len(entries) != len(names) or required.keys() - names or names - expected.keys():
            raise ValueError("Firmware ZIP must contain each required entry once and only pinned optional entries.")
        for name in entries:
            metadata = expected[name]
            if archive.getinfo(name).file_size != metadata["bytes"]:
                raise ValueError(f"Firmware size mismatch: {name}")
            data = archive.read(name)
            if hashlib.sha256(data).hexdigest() != metadata["sha256"]:
                raise ValueError(f"Firmware checksum mismatch: {name}")
            destination = metadata.get("install_path", f"usr/lib/firmware/{name}")
            if (not destination.startswith(("usr/lib/firmware/", "usr/share/uke-sensors/")) or
                    ".." in Path(destination).parts or destination in files):
                raise ValueError(f"Invalid firmware install path: {destination}")
            files[destination] = data
    return files


def overlay_files(source=OVERLAY):
    files = []
    for relative in ("etc", "usr/share", "usr/local/share", "usr/libexec"):
        directory = source / relative
        for path in sorted(directory.rglob("*")):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise ValueError(f"Expected a regular configuration file or directory: {path}")
            if path.is_file():
                files.append(path)
    return files


def profile_overlays(profile):
    manager = PROFILES[profile].get("manager")
    if manager == "plasmalogin":
        return (OVERLAY / "plasma-common", OVERLAY / profile)
    if profile == "phosh-gnome":
        return (OVERLAY / "gdm-common", OVERLAY / "gnome", OVERLAY / profile)
    if manager == "gdm":
        return (OVERLAY / "gdm-common", OVERLAY / profile)
    return (OVERLAY / profile,)


def overlay_destination(root, relative):
    destination = root / relative
    if not destination.parent.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Configuration path escapes the staged root: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.unlink(missing_ok=True)
    return destination


def install_overlay(root, source, files, *, executables=()):
    for path in files:
        destination = overlay_destination(root, path.relative_to(source))
        if path.is_symlink():
            destination.symlink_to(path.readlink())
        else:
            shutil.copyfile(path, destination)
            destination.chmod(0o755 if path.relative_to(source) in executables else 0o644)


def prepare_root(root, firmware, work, profile, keyboard, helpers):
    if not (root / "usr/lib64/security/pam_systemd.so").is_file():
        raise ValueError("Fedora systemd PAM session module is missing")
    if PROFILES[profile].get("manager") == "plasmalogin":
        if not (root / "usr/bin/dbus-run-session").is_file():
            raise ValueError("Plasma first-run setup requires dbus-run-session")
        if not (root / "usr/lib64/libGLESv2.so.2").is_file():
            raise ValueError("KWin requires libGLESv2.so.2 at runtime")
    alternate_session = {"kde": "plasma", "phosh-gnome": "gnome"}.get(profile)
    if alternate_session:
        sessions = root / "usr/share/wayland-sessions"
        for name in (PROFILES[profile]["session"], alternate_session):
            if not (sessions / f"{name}.desktop").is_file():
                raise ValueError(f"The {profile} image requires the {name} Wayland session")
    shadow = (root / "etc/shadow").read_text().splitlines()
    if not any(row.startswith("root:!unprovisioned:") for row in shadow):
        raise ValueError("The staged root account is not in Fedora's unprovisioned state")
    # In the cached build the staging tree shares file inodes with the base.
    machine_id = root / "etc/machine-id"
    replacement = work / "machine-id"
    replacement.write_text("uninitialized\n")
    if machine_id.exists():
        source = machine_id.stat()
        os.chown(replacement, source.st_uid, source.st_gid)
        shutil.copystat(machine_id, replacement)
    replacement.replace(machine_id)
    install_overlay(root, OVERLAY, overlay_files())
    if not all((root / "usr/bin" / name).is_file() for name in ("python3", "qbootctl")):
        raise ValueError("Slot A acknowledgement requires Fedora Python and qbootctl")
    vendor_service = root / "etc/systemd/system/qbootctl.service"
    if not vendor_service.is_symlink() or vendor_service.readlink() != Path("/dev/null"):
        raise ValueError("The generic qbootctl service must be masked")
    run("systemctl", f"--root={root}", "enable", "uke-slot-success.service", "chronyd.service",
        "uke-clock-restore.service", "uke-clock-save.timer")
    for source in profile_overlays(profile):
        install_overlay(root, source, overlay_files(source))
    if PROFILES[profile].get("manager") == "gdm":
        schemas = root / "usr/share/glib-2.0/schemas"
        # The staged tree is hard-linked to the cached Fedora base.
        (schemas / "gschemas.compiled").unlink(missing_ok=True)
        run("chroot", root, "/usr/bin/glib-compile-schemas", "--strict", "/usr/share/glib-2.0/schemas")
    if profile == "tty" and keyboard is not None:
        binary = Path("usr/bin/buffyboard")
        install_overlay(root, keyboard, (path for path in sorted(keyboard.rglob("*")) if path.is_file()),
                        executables=(binary,))
        run("chroot", root, f"/{binary}", "--version")
        run("systemctl", f"--root={root}", "enable", "uke-console-input.service")
    if helpers is not None:
        executables = tuple(Path("usr/libexec") / name for name in BINARIES)
        files = (path for path in sorted((helpers / "usr").rglob("*")) if path.is_file())
        install_overlay(root, helpers, files, executables=executables)
        install_overlay(root, HELPERS_OVERLAY, overlay_files(HELPERS_OVERLAY))
        run("systemctl", f"--root={root}", "enable", "uke-bluetooth-address.service")
        for path in executables:
            run("chroot", root, "/lib/ld-linux-aarch64.so.1", "--list", f"/{path}")
    for name, data in firmware.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)


def build_pair(stage, slot_a_boot, firmware_zip, work, release, fedora_release,
               *, base_root=None, profile="tty", keyboard=None, helpers=None):
    pair = work / "pair"
    pair.mkdir()
    boot = pair / "boot.img"
    run("cp", "--reflink=auto", "--sparse=always", slot_a_boot, boot)
    if boot.stat().st_size != BOOT_BYTES:
        raise ValueError("Unexpected slot-A boot image size")
    run("avbtool", "verify_image", "--image", boot)
    modules = Path("usr/lib/modules") / release
    kernel_digest = json.loads(PIN.read_text())["boot_kernel_sha256"]
    boot_header = check_kernel(boot, kernel_digest)
    boot_header.check_boot_id(kernel_digest)
    if not boot_header.avb_footer:
        raise ValueError("Slot-A boot image lacks its AVB footer")

    root = work / "rootfs"
    if base_root is None:
        run("cp", "-a", "--reflink=auto", stage / "rootfs", root)
    else:
        run("cp", "-al", base_root, root)
        module_target = root / modules
        module_target.parent.mkdir(parents=True, exist_ok=True)
        if module_target.exists() or module_target.is_symlink():
            raise ValueError(f"Fedora base already contains {modules}")
        run("cp", "-al", stage / "rootfs" / modules, module_target)
    root.chmod(0o755)
    audio = stage / AUDIO_STAGE
    install_overlay(root, audio, (path for path in sorted(audio.rglob("*")) if not path.is_dir()))
    prepare_root(root, read_firmware(firmware_zip), work, profile, keyboard, helpers)
    size = root_bytes(profile)
    raw = work / "userdata.raw.img"
    with raw.open("xb") as stream:
        stream.truncate(size)
    # The Senemos initramfs root guard requires this label on userdata.
    run("mkfs.ext4", "-q", "-F", "-b", "4096", "-L", "UKE_LINUX", "-m", "0",
        "-E", "lazy_itable_init=0,lazy_journal_init=0", "-d", root, raw)
    contexts = root / "etc/selinux/targeted/contexts/files/file_contexts"
    apply_and_verify(raw, root, contexts, work)
    run("e2fsck", "-fn", raw)

    userdata = pair / "userdata.img"
    run("img2simg", raw, userdata)
    raw_digest = sha256(raw)
    raw.unlink()
    verify_sparse(userdata, size, raw_digest)

    images = {"boot_a": boot, "userdata": userdata}
    manifest = {
        "target": "uke", "fedora_release": fedora_release, "profile": profile, "arch": "aarch64",
        "kernel_release": release, "userdata_logical_bytes": size,
        "firmware_zip_sha256": sha256(firmware_zip),
        "images": {partition: {"filename": path.name, "bytes": path.stat().st_size,
                               "sha256": sha256(path)} for partition, path in images.items()},
    }
    (pair / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (pair / "SHA256SUMS").write_text("".join(
        f"{item['sha256']}  {item['filename']}\n" for item in manifest["images"].values()
    ))
    return pair


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=Path)
    parser.add_argument("slot_a_boot", type=Path)
    parser.add_argument("firmware_zip", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fedora-release", default=FEDORA_RELEASE)
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Run as root to preserve root filesystem ownership")
    if args.output.exists() or args.output.is_symlink():
        parser.error(f"Output already exists: {args.output}")
    release = json.loads(PIN.read_text())["release"]
    try:
        verify_payload(args.stage, release)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=args.output.parent) as work:
            pair = build_pair(args.stage, args.slot_a_boot, args.firmware_zip, Path(work), release,
                              args.fedora_release)
            pair.rename(args.output)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Cannot package console images: {exc}\n")
    print(f"Verified Fedora {args.fedora_release} console image pair in {args.output}")


if __name__ == "__main__":
    main()
