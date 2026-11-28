# SPDX-License-Identifier: GPL-3.0-only
"""Build the TTY framebuffer keyboard from pinned BuffyBox and LVGL sources."""

from contextlib import ExitStack
from pathlib import Path
import os
import shutil
import subprocess
import tarfile

from compose_console import install_root
from source_tree import export_source
from stage_senemos import PIN, sha256


SOURCE_SHA256 = "e33d332ae6638652b95417dbf570fbe681d984593d2af22e127c06f3d7262327"
BUFFYBOX_SOURCE = PIN.parents[1] / "rootfs/tty/buffybox"
LVGL_SOURCE = BUFFYBOX_SOURCE / "lvgl"
BUILD_PACKAGES = ("gcc", "meson", "ninja-build", "pkgconf", "inih-devel",
                  "libinput-devel", "systemd-devel", "libxkbcommon-devel")


def build_keyboard(source, revisions, work, fedora_release, rpm_cache):
    builder = work / "builder"
    upstream = builder / "src/buffybox-3.6.0"
    install_root(builder, fedora_release, BUILD_PACKAGES, rpm_cache)
    if source is None:
        export_source(BUFFYBOX_SOURCE, revisions[0], upstream, work)
        export_source(LVGL_SOURCE, revisions[1], upstream / "lvgl", work)
    else:
        if sha256(source) != SOURCE_SHA256:
            raise ValueError("BuffyBox archive does not match the source pin")
        with tarfile.open(source, "r:xz") as archive:
            archive.extractall(builder / "src", filter="data")

    def run(*command):
        subprocess.run(["chroot", builder, "/usr/bin/env", "-i", "PATH=/usr/bin:/usr/sbin",
                        "PKG_CONFIG=/usr/bin/pkgconf", "LC_ALL=C", *command], check=True)

    with ExitStack() as mounts:
        for name in ("proc", "dev"):
            mount = builder / name
            mount.mkdir(exist_ok=True)
            subprocess.run(["mount", "--bind", f"/{name}", mount], check=True)
            mounts.callback(subprocess.run, ["umount", mount], check=True)
        run("meson", "setup", "/build", "/src/buffybox-3.6.0", "--prefix=/usr",
            "--libdir=lib64", "-Dlvgl_backends=framebuffer", "-Dman=false", "-Dsystemd=false")
        run("meson", "compile", "-C", "/build", "-j", str(min(os.cpu_count() or 1, 8)),
            "buffyboard/buffyboard")
        run("meson", "install", "-C", "/build", "--no-rebuild", "--tags=buffyboard",
            "--destdir=/image")
        run("/image/usr/bin/buffyboard", "--version")

    image = builder / "image"
    result = work / "keyboard"
    result.mkdir()
    for relative in ("usr/bin/buffyboard", "etc/buffyboard.conf"):
        path = Path(relative)
        (result / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image / path, result / path)
    licenses = result / "usr/share/licenses/buffyboard"
    licenses.mkdir(parents=True)
    for relative, name in (("COPYING", "COPYING"), ("lvgl/LICENCE.txt", "LVGL-LICENCE.txt"),
                           ("shared/fonts/README.md", "fonts-README.md"),
                           ("shared/cursor/README.md", "cursor-README.md")):
        shutil.copyfile(upstream / relative, licenses / name)
    return result
