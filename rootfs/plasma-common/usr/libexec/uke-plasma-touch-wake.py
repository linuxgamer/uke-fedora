# SPDX-License-Identifier: GPL-3.0-only
"""Forward Uke display input to the active Plasma session or greeter."""

import ctypes
import fcntl
import logging
import os
from pathlib import Path
import pwd
import struct
import subprocess
import sys


EV_KEY = 1
EV_ABS = 3
EV_SW = 5
KEY_WAKEUP = 143
SW_LID = 0
EVIOCSMASK = 0x40104593
EVENT = struct.Struct("@llHHi")


def set_event_mask(device, event_type, code=None):
    # The kernel takes a bitmap sized in native unsigned longs.
    word_bits = ctypes.sizeof(ctypes.c_ulong) * 8
    word, bit = divmod(code or 0, word_bits)
    mask = (ctypes.c_ulong * (word + 1))()
    if code is not None:
        mask[word] = 1 << bit
    request = struct.pack("=IIQ", event_type, ctypes.sizeof(mask), ctypes.addressof(mask))
    fcntl.ioctl(device, EVIOCSMASK, request)


def set_active_display(power, *, greeter_only):
    session = subprocess.check_output(
        ["/usr/bin/loginctl", "show-seat", "seat0", "-p", "ActiveSession", "--value"],
        text=True, timeout=4,
    ).strip()
    if not session:
        return

    details = subprocess.check_output(
        ["/usr/bin/loginctl", "show-session", session,
         "-p", "User", "-p", "Active", "-p", "Type", "-p", "Class", "-p", "Desktop"],
        text=True, timeout=4,
    )
    properties = dict(line.split("=", 1) for line in details.splitlines())
    if properties.get("Active") != "yes" or properties.get("Type") != "wayland":
        return
    uid = properties.get("User", "")
    if not uid.isdecimal() or int(uid) == 0:
        return
    account = pwd.getpwuid(int(uid))
    is_greeter = properties.get("Class") == "greeter" and account.pw_name == "plasmalogin"
    is_plasma = (properties.get("Class") == "user"
                 and properties.get("Desktop", "").lower() in {"kde", "plasma", "plasma-mobile"})
    if not (is_greeter or (is_plasma and not greeter_only)):
        return
    runtime = Path(f"/run/user/{account.pw_uid}")
    env = {"HOME": account.pw_dir, "XDG_RUNTIME_DIR": str(runtime),
           "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime}/bus", "QT_QPA_PLATFORM": "wayland"}
    credentials = {"user": account.pw_uid, "group": account.pw_gid,
                   "extra_groups": os.getgrouplist(account.pw_name, account.pw_gid)}
    settings = subprocess.check_output(
        ["/usr/bin/systemctl", "--user", "show-environment"],
        env=env, text=True, timeout=4, **credentials,
    )
    display = next((line.partition("=")[2] for line in settings.splitlines()
                    if line.startswith("WAYLAND_DISPLAY=")), "")
    if not display and is_greeter:
        # Plasma Login uses KWin's default socket in its own runtime directory.
        display = "wayland-0"
    if not display.startswith("wayland-") or not display[8:].isdecimal():
        return

    subprocess.run(
        ["/usr/bin/kscreen-doctor", "--dpms", power],
        env=dict(env, WAYLAND_DISPLAY=display), check=True, timeout=5, **credentials,
    )


def main():
    source = sys.argv[1]
    if source not in {"touchscreen", "lid"}:
        raise ValueError(f"Unsupported Uke display input: {source}")
    lid = source == "lid"
    with open(f"/dev/input/uke-{source}", "rb", buffering=0) as device:
        # Read only the switch or wake key on this file descriptor.
        set_event_mask(device, EV_KEY, None if lid else KEY_WAKEUP)
        set_event_mask(device, EV_ABS)
        set_event_mask(device, EV_SW, SW_LID if lid else None)
        while data := device.read(EVENT.size):
            _, _, event_type, code, value = EVENT.unpack(data)
            power = None
            if lid and (event_type, code) == (EV_SW, SW_LID) and value in (0, 1):
                power = "off" if value else "on"
            elif not lid and (event_type, code, value) == (EV_KEY, KEY_WAKEUP, 1):
                power = "on"
            if power:
                try:
                    set_active_display(power, greeter_only=lid)
                except (KeyError, OSError, subprocess.SubprocessError) as error:
                    logging.warning("Could not turn the Plasma display %s: %s", power, error)


if __name__ == "__main__":
    main()
