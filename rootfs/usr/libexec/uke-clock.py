# SPDX-License-Identifier: GPL-3.0-only
"""Restore UTC from a synchronized sample and the Uke PMIC counter."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


RTC_CLASS = Path("/sys/class/rtc")
ANCHOR = Path("/var/lib/uke-clock/anchor.json")
SECOND_NS = 1_000_000_000
COUNTER_MAX = (1 << 32) - 1


def read_counter():
    devices = [rtc for rtc in RTC_CLASS.glob("rtc[0-9]*")
               if (rtc / "device/of_node/qcom,rtc-counter-only").is_file()]
    if len(devices) != 1:
        raise ValueError("expected exactly one counter-only RTC")
    rtc = devices[0]
    counter = int((rtc / "since_epoch").read_text())
    if not 0 <= counter <= COUNTER_MAX:
        raise ValueError("RTC counter outside its 32-bit range")
    return counter


def save():
    synchronized = subprocess.check_output(
        ["/usr/bin/timedatectl", "show", "--property=NTPSynchronized", "--value"],
        text=True, timeout=4,
    ).strip()
    if synchronized != "yes":
        return

    counter = read_counter()
    utc_ns = time.time_ns()
    with tempfile.NamedTemporaryFile(mode="w", dir=ANCHOR.parent, delete=False) as stream:
        pending = Path(stream.name)
        try:
            json.dump({"counter": counter, "utc_ns": utc_ns}, stream)
            stream.flush()
            os.fsync(stream.fileno())
            pending.replace(ANCHOR)
            directory = os.open(ANCHOR.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            pending.unlink(missing_ok=True)


def estimate(anchor, counter):
    if (not isinstance(anchor, dict) or type(anchor.get("counter")) is not int
            or type(anchor.get("utc_ns")) is not int or anchor["utc_ns"] <= 0
            or not 0 <= anchor["counter"] <= COUNTER_MAX):
        raise ValueError("invalid clock anchor")
    elapsed = counter - anchor["counter"]
    if elapsed < 0:
        raise ValueError("RTC counter reset or wrapped since the last synchronized sample")
    return anchor["utc_ns"] + elapsed * SECOND_NS


def restore():
    try:
        anchor = json.loads(ANCHOR.read_text())
    except FileNotFoundError:
        return
    utc_ns = estimate(anchor, read_counter())
    if utc_ns > time.time_ns():
        time.clock_settime_ns(time.CLOCK_REALTIME, utc_ns)
        print("Restored UTC from the synchronized clock sample and PMIC counter.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("restore", "save"))
    args = parser.parse_args()
    try:
        (restore if args.action == "restore" else save)()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Uke clock {args.action} skipped: {error}", flush=True)


if __name__ == "__main__":
    main()
