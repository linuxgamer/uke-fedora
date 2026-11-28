# SPDX-License-Identifier: GPL-3.0-only
"""Compose the Fedora AArch64 console root and stage its Senemos boot reference."""

import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib

from stage_senemos import AUDIO_STAGE, PIN, verify_payload


FEDORA_RELEASE = "45"
PACKAGE_LIST = PIN.parents[1] / "rootfs/packages.txt"
PROFILE_LIST = PACKAGE_LIST.with_name("profiles.toml")
with PROFILE_LIST.open("rb") as source:
    PROFILE_CONFIG = tomllib.load(source)
PROFILES = PROFILE_CONFIG["profiles"]
DESKTOP = PROFILE_CONFIG["desktop"]
DEFAULT_PROFILE = "plasma"
PROFILE_ALIASES = {"plasma-mobile": "kde", "phosh": "phosh-gnome"}


def profile_name(name):
    return PROFILE_ALIASES.get(name, name)


def profile_packages(profile):
    packages = [line.split("#", 1)[0].strip() for line in PACKAGE_LIST.read_text().splitlines()]
    packages = [name for name in packages if name]
    if "manager" in PROFILES[profile]:
        packages.extend(DESKTOP["packages"])
    packages.extend(PROFILES[profile]["packages"])
    if not packages or any(not re.fullmatch(r"[A-Za-z0-9][\w.+-]*", name, re.ASCII) for name in packages):
        raise ValueError(f"Expected one Fedora package name per line in {PACKAGE_LIST}")
    return list(dict.fromkeys(packages))


def install_packages(root, fedora_release, packages, rpm_cache=None, refresh=False):
    command = [
        "dnf5", "--forcearch=aarch64", f"--releasever={fedora_release}",
        "--use-host-config", f"--installroot={root}", "--assumeyes",
        "--disable-repo=*", "--enable-repo=fedora", "--enable-repo=updates",
        "--setopt=install_weak_deps=False",
    ]
    if rpm_cache is not None:
        command.extend((f"--setopt=cachedir={rpm_cache}", "--setopt=keepcache=True"))
    if refresh:
        command.append("--refresh")
    command.extend(("install", *packages))
    scriptlet_failed = False
    with subprocess.Popen(
        command, env={**os.environ, "LC_ALL": "C"}, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True,
    ) as process:
        for line in process.stdout:
            print(line, end="", flush=True)
            if re.search(r"scriptlet.*(?:failed|failure|error)|error.*scriptlet", line, re.I):
                scriptlet_failed = True
        if process.wait() or scriptlet_failed:
            raise ValueError("Fedora package transaction or RPM scriptlet failed")


def verify_root(root):
    query = subprocess.check_output(
        ["rpm", "--root", str(root), "-qa", "--qf", "%{NAME}\t%{ARCH}\n"], text=True,
    )
    packages = (line.split("\t", 1) for line in query.splitlines())
    architectures = {arch for name, arch in packages if name != "gpg-pubkey"}
    if "aarch64" not in architectures or architectures - {"aarch64", "noarch"}:
        raise ValueError(f"Unexpected rootfs architectures: {sorted(architectures)}")
    subprocess.run(["chroot", str(root), "/usr/bin/true"], check=True)
    subprocess.run(["systemd-hwdb", f"--root={root}", "update"], check=True)
    if not (root / "etc/udev/hwdb.bin").stat().st_size:
        raise ValueError("Fedora hardware database is empty")
    if not list((root / "etc/selinux/targeted/policy").glob("policy.*")):
        raise ValueError("Fedora SELinux binary policy is missing")


def configure_profile(root, profile):
    systemctl = ["systemctl", f"--root={root}"]
    settings = PROFILES[profile]
    services = ["NetworkManager.service", "bluetooth.service"]
    if "manager" not in settings:
        subprocess.run([*systemctl, "set-default", "multi-user.target"], check=True)
        subprocess.run([*systemctl, "enable", "getty@tty1.service", *services], check=True)
        return

    manager, session = settings["manager"], settings["session"]
    if not (root / f"usr/share/wayland-sessions/{session}.desktop").is_file():
        raise ValueError(f"Missing {session} Wayland session")
    subprocess.run([*systemctl, "disable", "getty@tty1.service"], check=True)
    subprocess.run([*systemctl, "mask", "systemd-firstboot.service"], check=True)
    subprocess.run([*systemctl, "set-default", "graphical.target"], check=True)
    services.append(f"{manager}.service")
    if manager == "plasmalogin":
        config = root / "etc/xdg/plasmasetuprc"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text("[Accounts]\nUserGroups=wheel\n")
        if not (root / "usr/libexec/plasma-setup-bootutil").is_file():
            raise ValueError("Plasma first-run setup is missing")
        services.append("plasma-setup.service")
    else:
        if not (root / "usr/share/gnome-session/sessions/gnome-initial-setup.session").is_file():
            raise ValueError("GNOME first-run setup is missing")
        (root / "etc/gdm/custom.conf").write_text(
            f"[daemon]\nInitialSetupEnable=true\nFallbackSession={session}\n"
        )
    subprocess.run([*systemctl, "enable", *services], check=True)


def install_root(root, fedora_release, packages, rpm_cache=None, refresh=False):
    os.unshare(os.CLONE_NEWNS)
    subprocess.run(["mount", "--make-rprivate", "/"], check=True)
    root.mkdir(parents=True)
    with ExitStack() as mounts:
        for name in ("proc", "sys"):
            target = root / name
            target.mkdir()
            subprocess.run(["mount", "-o", "bind,ro", f"/{name}", str(target)], check=True)
            mounts.callback(subprocess.run, ["umount", str(target)], check=True)
        install_packages(root, fedora_release, packages, rpm_cache, refresh)


def compose_root(root, fedora_release, rpm_cache=None, refresh=False, *, profile="tty"):
    install_root(root, fedora_release, profile_packages(profile), rpm_cache, refresh)
    subprocess.run(["systemctl", f"--root={root}", "mask", "qbootctl.service"], check=True)
    verify_root(root)
    configure_profile(root, profile)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("senemos_stage", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fedora-release", default=FEDORA_RELEASE)
    parser.add_argument("--profile", type=profile_name, choices=PROFILES, default="tty")
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Run as root in the Linux build environment")
    if args.output.exists() or args.output.is_symlink():
        parser.error(f"Output already exists: {args.output}")
    release = json.loads(PIN.read_text())["release"]
    try:
        verify_payload(args.senemos_stage, release)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=args.output.parent) as work:
            stage = Path(work) / "console"
            compose_root(stage / "rootfs", args.fedora_release, profile=args.profile)
            modules = Path("rootfs/usr/lib/modules") / release
            shutil.copytree(args.senemos_stage / modules, stage / modules)
            shutil.copytree(args.senemos_stage / "boot", stage / "boot")
            audio = args.senemos_stage / AUDIO_STAGE
            if audio.is_dir():
                shutil.copytree(audio, stage / AUDIO_STAGE, symlinks=True)
            count = verify_payload(stage, release)
            stage.rename(args.output)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Cannot compose console root: {exc}\n")
    print(f"Staged Fedora {args.fedora_release} AArch64 console root and {count} modules in {args.output}")


if __name__ == "__main__":
    main()
