# SPDX-License-Identifier: GPL-3.0-only
"""Build the Uke Bluetooth, SSC and speaker userspace helpers."""

from pathlib import Path
import shutil
import subprocess

from compose_console import install_root
from source_tree import export_source
from stage_senemos import PIN


SOURCE_ROOT = PIN.parents[1] / "rootfs/device-helpers"
HARDWARE_SOURCE = SOURCE_ROOT / "hardware-support"
HEXAGON_SOURCE = SOURCE_ROOT / "hexagonrpc"
SPEAKER_SOURCE = SOURCE_ROOT / "speaker-runtime"
PATCHES = (
    "0001-select-sequence-type.patch",
    "0002-verbose-native-u64.patch",
    "0003-map-oem-odm-sensor-config.patch",
    "0004-reject-mapped-symlinks.patch",
    "0005-reject-incomplete-shell-images.patch",
    "0006-notify-listener-readiness.patch",
)
BINARIES = ("uke-bluetooth-address", "uke-hexagonrpcd", "uke-ssc-cache", "uke-speaker-runtime")
UNITS = ("uke-bluetooth-address.service", "uke-ssc-cache.service",
         "uke-ssc-root.service", "uke-ssc-sensors.service")


def build_helpers(work, fedora_release, rpm_cache, revisions):
    builder, result = work / "builder", work / "helpers"
    bluetooth = "components/uke-desktop-integration"
    sensors = "components/uke-sensors"
    cpp = {
        "bluetooth-address.cpp": f"{bluetooth}/src/bluetooth-address.cpp",
        "ssc-cache.cpp": f"{sensors}/src/ssc-cache.cpp",
    }
    unit_paths = {name: f"{sensors}/packaging/systemd/{name}" for name in UNITS[1:]}
    unit_paths[UNITS[0]] = f"{bluetooth}/packaging/{UNITS[0]}"
    patch_paths = {name: f"{sensors}/patches/hexagonrpc/{name}" for name in PATCHES}
    hardware = work / "hardware"
    export_source(HARDWARE_SOURCE, revisions[0], hardware, work,
                  *cpp.values(), *unit_paths.values(), *patch_paths.values())

    binaries = result / "usr/libexec"
    units = result / "usr/lib/systemd/system"
    licenses = result / "usr/share/licenses/uke-device-helpers"
    for directory in (binaries, units, licenses):
        directory.mkdir(parents=True)
    for name, path in unit_paths.items():
        shutil.copyfile(hardware / path, units / name)

    install_root(builder, fedora_release, ("gcc", "gcc-c++", "patch", "systemd-devel", "bluez-libs-devel",
                                         "alsa-lib-devel", "openssl-devel"), rpm_cache)
    sources = builder / "src"
    hexagon = sources / "hexagonrpc"
    export_source(HEXAGON_SOURCE, revisions[1], hexagon, work)
    shutil.copyfile(hexagon / "COPYING", licenses / "GPL-3.0")
    speaker = sources / SPEAKER_SOURCE.name
    shutil.copytree(SPEAKER_SOURCE, speaker)
    shutil.copyfile(speaker / "GPL-2.0", licenses / "speaker-runtime-GPL-2.0")
    shutil.copyfile(speaker / "LICENSE", licenses / "speaker-runtime-MIT")
    for name, path in cpp.items():
        shutil.copyfile(hardware / path, sources / name)
    for name, path in patch_paths.items():
        shutil.copyfile(hardware / path, sources / name)
        subprocess.run(["chroot", builder, "patch", "--batch", "--forward",
                        "-d", f"/src/{hexagon.name}", "-p1", "-i", f"/src/{name}"], check=True)

    compiler = ["-O2", "-Wall", "-Wextra", "-Werror"]
    for source, binary in (("bluetooth-address.cpp", BINARIES[0]), ("ssc-cache.cpp", BINARIES[2])):
        subprocess.run(["chroot", builder, "g++", "-std=c++20", *compiler, f"/src/{source}",
                        "-o", f"/{binary}"], check=True)
    sources_c = [f"/{path.relative_to(builder)}" for folder in ("libhexagonrpc", "hexagonrpcd")
                 for path in sorted((hexagon / folder).rglob("*.c"))]
    subprocess.run(["chroot", builder, "gcc", "-std=gnu11", *compiler, "-Wno-unused-parameter",
                    "-I", f"/src/{hexagon.name}/include", *sources_c, "-lsystemd",
                    "-o", f"/{BINARIES[1]}"], check=True)
    subprocess.run(["chroot", builder, "g++", "-std=c++20", *compiler,
                    f"/src/{speaker.name}/uke-speaker-runtime.cpp", "-lasound", "-lcrypto",
                    "-o", "/uke-speaker-runtime"], check=True)
    for name in BINARIES:
        shutil.copy2(builder / name, binaries / name)
    return result
