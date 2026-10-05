#!/usr/bin/env python3
"""Convert Qualcomm downstream DSI commands to C for a mainline panel driver.

Packet format: <type> <last> <vc> <ack> <wait> <len_hi> <len_lo> <payload...>
  type 0x05/0x15/0x39 -> DCS write; wait (ms) -> mipi_dsi_msleep.

Usage:
  tools/dsi-cmds.py <file.dtsi> [property] [--after MARKER]

  tools/dsi-cmds.py dsi-panel-o82-42-...dtsi qcom,mdss-dsi-on-command --after timing@120
"""
import re
import sys


def extract(text, prop, after=None):
    start = 0
    if after:
        i = text.find(after)
        if i < 0:
            raise SystemExit(f"marker not found: {after}")
        start = i
    m = re.search(re.escape(prop) + r"\s*=\s*\[", text[start:])
    if not m:
        raise SystemExit(f"property not found: {prop}")
    body = text[start + m.end():]
    end = body.find("];")
    return body[:end]


def parse(body):
    packets = []
    for line in body.splitlines():
        line = line.split("//")[0].strip()
        if not line:
            continue
        toks = re.findall(r"\b[0-9A-Fa-f]{2}\b", line)
        if not toks:
            continue
        packets.append([int(t, 16) for t in toks])
    return packets


def emit(packets, ctx="dsi_ctx"):
    out = []
    for p in packets:
        if len(p) < 7:
            out.append(f"\t/* skipping short packet: {' '.join(f'{b:02x}' for b in p)} */")
            continue
        typ, wait, ln = p[0], p[4], (p[5] << 8) | p[6]
        payload = p[7:7 + ln]
        if typ in (0x05, 0x15, 0x39):
            args = ", ".join(f"0x{b:02x}" for b in payload)
            out.append(f"\tmipi_dsi_dcs_write_seq_multi(&{ctx}, {args});")
        elif typ == 0x06:
            out.append(f"\t/* read: {' '.join(f'{b:02x}' for b in payload)} */")
        else:
            out.append(f"\t/* TODO type 0x{typ:02x}: {' '.join(f'{b:02x}' for b in payload)} */")
        if wait:
            out.append(f"\tmipi_dsi_msleep(&{ctx}, {wait});")
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--after=")]
    after = None
    for a in sys.argv[1:]:
        if a.startswith("--after="):
            after = a.split("=", 1)[1]
    path = args[0]
    prop = args[1] if len(args) > 1 else "qcom,mdss-dsi-on-command"
    text = open(path, encoding="utf-8").read()
    body = extract(text, prop, after)
    for line in emit(parse(body)):
        print(line)


if __name__ == "__main__":
    main()
