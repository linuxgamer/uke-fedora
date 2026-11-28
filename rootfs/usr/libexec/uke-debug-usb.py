# SPDX-License-Identifier: GPL-3.0-only
"""Open or close an authenticated USB console for the current Fedora boot."""

import argparse
import os
from pathlib import Path
import subprocess


GETTY = "serial-getty@ttyGS0.service"
MODULE = Path("/sys/module/g_serial")


def start():
    already_loaded = MODULE.is_dir()
    subprocess.run(["/usr/sbin/modprobe", "g_serial"], check=True)
    try:
        subprocess.run(["/usr/bin/systemctl", "start", GETTY], check=True)
    except subprocess.CalledProcessError:
        if not already_loaded:
            subprocess.run(["/usr/sbin/modprobe", "-r", "g_serial"], check=False)
        raise
    print("USB console ready. Connect a data cable and run Uke Debug on the PC.")


def stop():
    subprocess.run(["/usr/bin/systemctl", "stop", GETTY], check=True)
    if MODULE.is_dir():
        subprocess.run(["/usr/sbin/modprobe", "-r", "g_serial"], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "stop"), nargs="?", default="start")
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Run this script with sudo")
    try:
        (start if args.action == "start" else stop)()
    except (OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"USB console setup failed: {error}\n")


if __name__ == "__main__":
    main()
