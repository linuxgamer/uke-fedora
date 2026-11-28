# SPDX-License-Identifier: GPL-3.0-only
"""Run a one-shot Uke Debug probe through Fedora's password-protected USB console."""

import base64
from getpass import getpass
from ipaddress import IPv4Address
import json
import re
import shlex
import sys
import time
import uuid
import zlib


LOGIN = rb"\blogin:[ \t]*\Z"
PASSWORD = rb"\bPassword:[ \t]*\Z"
SHELL = rb"(?:\blogin:|[#$])[ \t]*(?:\x1b\[\?2004h)?\Z"
G_SERIAL = (0x0525, 0xA4A7)

LAN_RECOVERY = b"""
import json
from pathlib import Path
import socket
import subprocess
import sys

peer = sys.argv[1]
try:
    route, = json.loads(subprocess.check_output(
        ["ip", "-j", "-4", "route", "get", peer], timeout=5,
        stderr=subprocess.STDOUT,
    ))
    interface = route.get("dev", "")
    if (not interface or route.get("gateway") or route.get("type", "unicast") != "unicast"
            or not (Path("/sys/class/net") / interface / "phy80211").exists()):
        raise ValueError("The PC address must be directly reachable over the tablet's Wi-Fi.")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.sendto(b"uke-debug-lan", (peer, 48178))
    print(json.dumps({"peer": peer, "interface": interface, "probe_sent": True}))
except (OSError, ValueError, subprocess.SubprocessError) as error:
    print(json.dumps({"error": str(error)}))
"""


def recover_lan(device, user, address):
    peer = IPv4Address(address)
    if peer.is_loopback or peer.is_multicast or peer.is_unspecified or str(peer) == "255.255.255.255":
        raise ValueError("Enter the PC's unicast Wi-Fi IPv4 address.")
    return json.loads(fetch_serial(device, user, str(peer), LAN_RECOVERY))


def detect_port():
    try:
        from serial.tools.list_ports import comports
    except ImportError as error:
        raise RuntimeError("USB serial capture requires pyserial on the PC.") from error
    ports = [port.device for port in comports() if (port.vid, port.pid) == G_SERIAL]
    if len(ports) != 1:
        raise RuntimeError("Connect one tablet with the USB console started, or pass its port explicitly.")
    return ports[0]


def expect(port, pattern, timeout):
    match_pattern = re.compile(pattern)
    deadline = time.monotonic() + timeout
    data = bytearray()
    while time.monotonic() < deadline:
        data.extend(port.read(port.in_waiting or 1))
        if len(data) > 2 * 1024 * 1024:
            raise RuntimeError("USB console output exceeded 2 MiB.")
        if match := match_pattern.search(data):
            return bytes(data[:match.start()]), match.group()
    raise RuntimeError("USB console did not respond in time.")


def fetch_serial(device, user, request, source):
    try:
        import serial
    except ImportError as error:
        raise RuntimeError("USB serial capture requires pyserial on the PC.") from error
    if not re.fullmatch(r"[a-zA-Z0-9_][a-zA-Z0-9_.-]*", user):
        raise ValueError("Enter a valid Fedora login name.")
    if not sys.stdin.isatty():
        raise RuntimeError("Run USB serial capture in an interactive terminal.")

    # Let the tester finish typing before starting Fedora's login timeout.
    password = getpass(f"Fedora password for {user} over USB: ")
    if "\r" in password or "\n" in password:
        raise ValueError("The USB login expects a single-line password.")

    token = uuid.uuid4().hex
    loader = ('import base64,zlib; data="".join(iter(input,".")); '
              'exec(compile(zlib.decompress(base64.b64decode(data)),"<uke-debug>","exec"))')
    command = (f"stty -echo; printf '\\n%s\\n' {token}-ready; "
               f"python3 -u -c {shlex.quote(loader)} {shlex.quote(request)}; "
               f"code=$?; stty echo; printf '\\n%s%d\\n' {token}-done- \"$code\"; exit")
    payload = base64.b64encode(zlib.compress(source))
    marker = token.encode("ascii")

    with serial.Serial(device, 115200, timeout=0.3, write_timeout=5) as port:
        port.write(b"\r")
        expect(port, LOGIN, 12)
        port.write(user.encode("ascii") + b"\r")
        expect(port, PASSWORD, 12)
        port.write(password.encode("utf-8") + b"\r")
        del password
        _, prompt = expect(port, SHELL, 20)
        if b"login:" in prompt:
            raise RuntimeError("Fedora rejected the USB login.")

        port.write(command.encode("ascii") + b"\r")
        expect(port, rb"\r?\n" + marker + rb"-ready\r?\n", 12)
        for start in range(0, len(payload), 512):
            port.write(payload[start:start + 512] + b"\r")
        port.write(b".\r")
        report, result = expect(port, rb"\r?\n" + marker + rb"-done-\d+\r?\n", 180)
        if not result.rstrip().endswith(b"-done-0"):
            raise RuntimeError("The Fedora diagnostic probe failed over USB.")
        return report.decode("utf-8", errors="replace").replace("\r\n", "\n").strip() + "\n"
