# SPDX-License-Identifier: GPL-3.0-only
"""Stage the pinned Senemos boot image, modules and matching audio data."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import struct
import subprocess
import tarfile
import tempfile


PIN = Path(__file__).resolve().parents[1] / "kernel/senemos-prebuilt.json"
BOOT_FILES = ("userdata.img", "manifest", "modules.sha256")
AUDIO_STAGE = "audio"


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def extract_payload(rpm, stage, release):
    modules = PurePosixPath(f"usr/lib/modules/{release}")
    boot = PurePosixPath(f"usr/lib/senemos/kernel-updates/{release}")
    audio_dirs = (
        PurePosixPath("usr/share/alsa/ucm2"),
        PurePosixPath("usr/share/wireplumber/wireplumber.conf.d"),
        PurePosixPath(f"usr/share/licenses/uke-kernel-audio-{release}"),
    )
    audio_layouts = {
        PurePosixPath(f"usr/share/senemos/uke/{release}/microphone-layout.json"),
        PurePosixPath("usr/share/senemos/uke/audio/microphone-layout.json"),
    }
    firmware = PurePosixPath(f"usr/lib/firmware/{release}/qcom")
    command = ["rpm2archive", "--nocompression", str(rpm)]
    with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
        with process.stdout, tarfile.open(fileobj=process.stdout, mode="r|") as archive:
            for member in archive:
                path = PurePosixPath(member.name)
                audio = False
                if path.is_relative_to(modules):
                    member.name = str(PurePosixPath("rootfs") / path)
                elif path.parent == boot and path.name in BOOT_FILES:
                    member.name = str(PurePosixPath("boot") / path.name)
                elif (any(path.is_relative_to(directory) for directory in audio_dirs)
                      or path in audio_layouts
                      or (path.is_relative_to(firmware) and path.name.endswith("-tplg.bin"))):
                    audio = True
                    member.name = str(PurePosixPath(AUDIO_STAGE) / path)
                else:
                    continue
                if ".." in path.parts or not (member.isfile() or member.isdir() or (audio and member.issym())):
                    raise ValueError(f"Unexpected archive member: {path}")
                archive.extract(member, path=stage, filter="data")
        if process.wait():
            raise ValueError("rpm2archive could not read the pinned RPM")


def verify_payload(stage, release):
    boot = stage / "boot"
    modules = stage / "rootfs/usr/lib/modules" / release
    manifest = dict(line.split("=", 1) for line in (boot / "manifest").read_text().splitlines())
    if manifest["kernel_release"] != release:
        raise ValueError("Boot manifest kernel release differs from pin")

    image = boot / "userdata.img"
    module_hashes = boot / "modules.sha256"
    if sha256(image) != manifest["userdata_image_sha256"]:
        raise ValueError("Userdata boot image checksum mismatch")
    if sha256(module_hashes) != manifest["modules_sha256"]:
        raise ValueError("Module manifest checksum mismatch")

    with image.open("rb") as stream:
        header = stream.read(4096)
        size = struct.unpack_from("<I", header, 8)[0]
        version = struct.unpack_from("<I", header, 40)[0]
        if header[:8] != b"ANDROID!" or version != 4 or not 0 < size <= image.stat().st_size - 4096:
            raise ValueError("Unexpected Android boot image header")
        kernel_hash = hashlib.sha256()
        remaining = size
        while remaining:
            chunk = stream.read(min(remaining, 1024 * 1024))
            if not chunk:
                raise ValueError("Truncated boot kernel")
            kernel_hash.update(chunk)
            remaining -= len(chunk)
    if kernel_hash.hexdigest() != manifest["userdata_kernel_sha256"]:
        raise ValueError("Embedded boot kernel checksum mismatch")
    if sha256(modules / "vmlinuz") != kernel_hash.hexdigest():
        raise ValueError("Installed kernel differs from embedded boot kernel")

    checked = set()
    for line in module_hashes.read_text().splitlines():
        digest, name = line.split("  ", 1)
        path = PurePosixPath(name)
        if not path.is_relative_to("kernel") or ".." in path.parts or name in checked:
            raise ValueError(f"Invalid module manifest path: {name}")
        if sha256(modules / name) != digest:
            raise ValueError(f"Module checksum mismatch: {name}")
        checked.add(name)
    present = {
        path.relative_to(modules).as_posix()
        for path in (modules / "kernel").rglob("*.ko*")
        if path.is_file()
    }
    if not checked or checked != present:
        raise ValueError("Staged module paths differ from the manifest")
    return len(checked)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rpm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    pin = json.loads(PIN.read_text())
    if args.output.exists() or args.output.is_symlink():
        parser.error(f"Output already exists: {args.output}")
    try:
        if args.rpm.name != pin["rpm"] or sha256(args.rpm) != pin["sha256"]:
            raise ValueError("RPM does not match the Senemos prebuilt pin")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=args.output.parent) as work:
            stage = Path(work) / "stage"
            stage.mkdir()
            extract_payload(args.rpm, stage, pin["release"])
            count = verify_payload(stage, pin["release"])
            stage.rename(args.output)
    except (OSError, ValueError, KeyError, struct.error, tarfile.TarError) as exc:
        parser.exit(1, f"Cannot stage Senemos: {exc}\n")
    print(f"Staged Senemos {pin['release']} and verified {count} modules in {args.output}")


if __name__ == "__main__":
    main()
