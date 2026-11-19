#!/usr/bin/env python3
"""Answer Nanosic WN8030 offline-auth requests from /dev/nanosic_auth.

The kernel driver forwards the MCU step-3 challenge as a 36-byte request
(uid[16] + keyMeta[4] + challenge[16]) and blocks up to 5 s for a 16-byte
step-5 token.  keyMeta comes from the MCU in the 0x31 report; the token provider
signs all three, so passing a hardcoded value would ask the wrong key.
This daemon supplies that token. Token sources, in order:

  1. NANOSIC_TOKEN_FILE /etc/nanosic/auth-token (32 hex chars)
  2. tokenhelper (Android vendor HAL) if NANOSIC_TOKEN_HELPER exists
  3. a zero token in offline mode (driver key-meta 00000002)

Without any daemon the driver times out and input still flows.
"""

import binascii
import os
import signal
import subprocess
import sys
import time

DEV = os.environ.get("NANOSIC_AUTH_DEV", "/dev/nanosic_auth")
TOKEN_FILE = os.environ.get("NANOSIC_TOKEN_FILE", "/etc/nanosic/auth-token")
HELPER = os.environ.get("NANOSIC_TOKEN_HELPER", "/usr/libexec/nanosic/tokenhelper")
# Used only when the driver does not supply one; the MCU normally does.
KEYMETA_DEFAULT = os.environ.get("NANOSIC_KEYMETA", "00000002")
ZERO_TOKEN = bytes(16)
running = True


def log(msg):
    print(f"nanosic-authd: {msg}", flush=True)


def token_from_file():
    try:
        raw = open(TOKEN_FILE, "r", encoding="ascii").read().strip()
        tok = binascii.unhexlify(raw)
        return tok if len(tok) == 16 else None
    except OSError:
        return None


def token_from_helper(uid, key_meta, challenge):
    if not os.access(HELPER, os.X_OK):
        return None
    try:
        out = subprocess.run(
            [HELPER, "token", "1", uid.hex(), key_meta.hex(), challenge.hex()],
            capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        log(f"tokenhelper failed: {exc}")
        return None
    if out.returncode != 0:
        log(f"tokenhelper rc={out.returncode}: {out.stderr.strip()}")
        return None
    try:
        tok = binascii.unhexlify(out.stdout.strip())
    except (ValueError, binascii.Error):
        return None
    return tok if len(tok) == 16 else None


def token_for(uid, key_meta, challenge):
    tok = token_from_file()
    if tok:
        return tok
    tok = token_from_helper(uid, key_meta, challenge)
    if tok:
        return tok
    return ZERO_TOKEN


def stop(_signum, _frame):
    global running
    running = False


def serve(fd):
    while running:
        try:
            req = os.read(fd, 36)
        except OSError as exc:
            log(f"read: {exc}")
            return
        if len(req) != 36:
            log(f"short request ({len(req)} bytes), expected 36")
            return
        uid, key_meta, challenge = req[:16], req[16:20], req[20:]
        if key_meta == bytes(4):
            key_meta = binascii.unhexlify(KEYMETA_DEFAULT)
        tok = token_for(uid, key_meta, challenge)
        try:
            os.write(fd, tok)
        except OSError as exc:
            log(f"write: {exc}")
            return
        log(f"token sent uid={uid.hex()} keymeta={key_meta.hex()} "
            f"challenge={challenge.hex()} token={tok.hex()}")


def main():
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    if token_from_file():
        log(f"static token from {TOKEN_FILE}")
    elif os.access(HELPER, os.X_OK):
        log(f"tokenhelper backend {HELPER} keymeta={KEYMETA_DEFAULT}")
    else:
        log("no tokenhelper/static token: using offline zero token")
    while running:
        try:
            fd = os.open(DEV, os.O_RDWR)
        except OSError:
            time.sleep(2)
            continue
        log(f"opened {DEV}")
        try:
            serve(fd)
        finally:
            os.close(fd)
            log("closed device")
        time.sleep(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
