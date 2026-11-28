# SPDX-License-Identifier: GPL-3.0-only
"""Build a Fedora tablet image pair on Linux or WSL2."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import uuid
import zipfile

from compose_console import DEFAULT_PROFILE, FEDORA_RELEASE, PACKAGE_LIST, PROFILE_LIST, PROFILES, compose_root, profile_name
from device_helpers import BINARIES, HARDWARE_SOURCE, HEXAGON_SOURCE, SPEAKER_SOURCE, UNITS, build_helpers
from package_console import (FIRMWARE_PIN, HELPERS_OVERLAY, OVERLAY, PROJECT,
                             build_pair, overlay_files, profile_overlays, read_firmware)
from stage_senemos import AUDIO_STAGE, PIN, extract_payload, sha256, verify_payload
from source_tree import source_revision
from tty_keyboard import BUFFYBOX_SOURCE, LVGL_SOURCE, SOURCE_SHA256, build_keyboard
from wrap_slot_a import BOOT_BYTES, STOCK_SHA256, wrap


BUILD = PROJECT / "build"
CACHE = BUILD / "cache"
WORK = BUILD / "work"
STAMP = ".build-key.json"


def build_key(*inputs, files=()):
    data = [inputs, [(str(path.name), sha256(path)) for path in files]]
    return hashlib.sha256(json.dumps(data, separators=(",", ":")).encode()).hexdigest()


def output_stats(directory, files):
    stats = {}
    for name in files:
        item = (directory / name).stat()
        # The staging overlay changes link counts and ctime on cached files.
        stats[name] = [item.st_ino, item.st_size, item.st_mtime_ns]
    return stats


def cached_stage(label, target, key, build, *, refresh=False, files=()):
    stamp = target / STAMP
    if target.is_symlink() or (target.exists() and not stamp.is_file()):
        raise ValueError(f"Move the unmanaged directory out of the build path: {target}")
    if not refresh and stamp.is_file():
        try:
            record = json.loads(stamp.read_text())
            if record["key"] == key and record["files"] == output_stats(target, files):
                print(f"Reusing {label}", flush=True)
                return record["generation"]
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            pass

    print(f"Building {label}", flush=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"{target.name}-", dir=WORK) as temporary:
        work = Path(temporary)
        result = build(work)
        record = {"key": key, "generation": uuid.uuid4().hex, "files": output_stats(result, files)}
        (result / STAMP).write_text(json.dumps(record) + "\n")
        previous = work / "previous"
        if target.exists():
            target.rename(previous)
        try:
            result.rename(target)
        except OSError:
            if previous.exists():
                previous.rename(target)
            raise
    return record["generation"]


def build_images(args):
    pin = json.loads(PIN.read_text())
    if args.senemos_rpm.name != pin["rpm"] or sha256(args.senemos_rpm) != pin["sha256"]:
        raise ValueError("RPM does not match the Senemos prebuilt pin")
    if args.stock_boot.stat().st_size != BOOT_BYTES or sha256(args.stock_boot) != STOCK_SHA256:
        raise ValueError("Stock image differs from the reviewed slot-A template")
    read_firmware(args.firmware_zip)

    release = pin["release"]
    profile = args.profile
    fedora = CACHE / f"fedora-{profile}"
    output = BUILD / "out" / profile
    senemos = CACHE / "senemos-stage"
    boot = CACHE / "slot-a"
    helpers = CACHE / "device-helpers"
    repo_dirs = ("/etc/yum.repos.d", "/etc/distro.repos.d", "/usr/share/dnf5/repos.d")
    repo_files = [Path("/etc/dnf/dnf.conf")]
    for directory in repo_dirs:
        repo_files.extend(sorted(Path(directory).glob("*.repo")))
    repository_key = build_key(args.fedora_release, files=[path for path in repo_files if path.is_file()])
    fedora_key = build_key(repository_key, profile, files=[BUILD / "compose_console.py", PACKAGE_LIST, PROFILE_LIST])
    kernel_key = build_key(files=[PIN, BUILD / "stage_senemos.py"])
    boot_key = build_key(kernel_key, STOCK_SHA256, files=[BUILD / "wrap_slot_a.py", BUILD / "android_boot.py"])
    helper_revisions = tuple(map(source_revision, (HARDWARE_SOURCE, HEXAGON_SOURCE)))
    helpers_key = build_key(repository_key, helper_revisions, files=[
        BUILD / "device_helpers.py", BUILD / "compose_console.py", BUILD / "source_tree.py",
        *sorted(path for path in SPEAKER_SOURCE.iterdir() if path.is_file()),
    ])

    def stage_senemos(work):
        result = work / "stage"
        extract_payload(args.senemos_rpm, result, release)
        verify_payload(result, release)
        return result

    def stage_boot(work):
        result = work / "stage"
        wrap(senemos, args.stock_boot, result / "boot.img")
        return result

    def stage_fedora(work):
        result = work / "stage"
        compose_root(result / "rootfs", args.fedora_release, CACHE / "dnf" / args.fedora_release,
                     args.refresh_fedora, profile=profile)
        return result

    def stage_pair(work):
        verify_payload(senemos, release)
        return build_pair(senemos, boot / "boot.img", args.firmware_zip, work, release,
                          args.fedora_release, base_root=fedora / "rootfs", profile=profile,
                          keyboard=keyboard, helpers=helpers)

    keyboard = None
    keyboard_key = None
    if profile == "tty":
        source = args.tty_keyboard_source
        if source is not None and sha256(source) != SOURCE_SHA256:
            raise ValueError("BuffyBox archive does not match the source pin")
        keyboard = CACHE / "buffyboard"
        keyboard_revisions = tuple(map(source_revision, (BUFFYBOX_SOURCE, LVGL_SOURCE))) if source is None else ()
        keyboard_key = build_key(repository_key, keyboard_revisions or SOURCE_SHA256, files=[
            BUILD / "tty_keyboard.py", BUILD / "compose_console.py", BUILD / "source_tree.py",
        ])
        cached_stage(
            "Buffyboard framebuffer keyboard", keyboard, keyboard_key,
            lambda work: build_keyboard(source, keyboard_revisions, work, args.fedora_release,
                                        CACHE / "dnf" / args.fedora_release),
            files=("usr/bin/buffyboard", "etc/buffyboard.conf"),
        )
    cached_stage("Senemos payload", senemos, kernel_key, stage_senemos,
                 files=("boot/manifest", f"rootfs/usr/lib/modules/{release}/vmlinuz",
                        f"{AUDIO_STAGE}/usr/share/senemos/uke/{release}/microphone-layout.json"))
    cached_stage("slot-A boot image", boot, boot_key, stage_boot, files=("boot.img",))
    helpers_generation = cached_stage(
        "Bluetooth, SSC and speaker helpers", helpers, helpers_key,
        lambda work: build_helpers(work, args.fedora_release, CACHE / "dnf" / args.fedora_release,
                                   helper_revisions),
        files=(*[f"usr/libexec/{name}" for name in BINARIES],
               *[f"usr/lib/systemd/system/{name}" for name in UNITS],
               "usr/share/licenses/uke-device-helpers/GPL-3.0"),
    )
    generation = cached_stage(f"Fedora {profile} root", fedora, fedora_key, stage_fedora,
                              refresh=args.refresh_fedora, files=("rootfs/etc/os-release", "rootfs/etc/shadow"))
    overlays = [*overlay_files(), *overlay_files(HELPERS_OVERLAY)]
    for source in profile_overlays(profile):
        overlays.extend(overlay_files(source))
    overlay = [(path.relative_to(OVERLAY).as_posix(), sha256(path)) for path in overlays]
    pair_key = build_key(
        generation, boot_key, helpers_generation, keyboard_key, sha256(args.firmware_zip), overlay,
        files=[FIRMWARE_PIN,
               BUILD / "package_console.py", BUILD / "ext4_metadata.py", BUILD / "android_sparse.py"],
    )
    cached_stage(
        f"{profile} images", output, pair_key, stage_pair,
        files=("boot.img", "userdata.img", "manifest.json", "SHA256SUMS"),
    )
    print(f"{profile} images: {output}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--senemos-rpm", required=True, type=Path)
    parser.add_argument("--stock-boot", required=True, type=Path)
    parser.add_argument("--firmware-zip", required=True, type=Path)
    parser.add_argument("--profile", type=profile_name, choices=PROFILES, default=DEFAULT_PROFILE)
    parser.add_argument("--tty-keyboard-source", type=Path,
                        help="use a local pinned BuffyBox archive for --profile tty")
    parser.add_argument("--fedora-release", default=FEDORA_RELEASE, help="default: %(default)s")
    parser.add_argument("--refresh-fedora", action="store_true", help="refresh repos and rebuild the Fedora root")
    args = parser.parse_args()
    if sys.platform != "linux" or os.geteuid() != 0:
        parser.error("Run as root on Linux or in a WSL2 Linux distro")
    if not args.fedora_release.isascii() or not args.fedora_release.isdecimal():
        parser.error("Fedora release must be a release number")

    import fcntl

    os.umask(0o022)
    try:
        WORK.mkdir(parents=True, exist_ok=True)
        with (WORK / ".build.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            build_images(args)
    except BlockingIOError:
        parser.exit(1, "Another build is using this checkout\n")
    except (OSError, ValueError, KeyError, struct.error, tarfile.TarError, zipfile.BadZipFile,
            subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Build failed: {exc}\n")


if __name__ == "__main__":
    main()
