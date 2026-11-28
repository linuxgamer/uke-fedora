# SPDX-License-Identifier: GPL-3.0-only
"""Read Android boot v4 images and write the port's kernel-only variant."""

from dataclasses import dataclass
import hashlib
import os
import shutil
import stat
import struct


PAGE = 4096
HEADER_SIZE = 1584
MAX_IMAGE = 512 * 1024**2
ROOT_ARG = b"senemos.root=userdata"
BOOT_ID_ARG = b"uke-fedora.boot_id="


@dataclass(frozen=True)
class BootHeader:
    kernel_bytes: int
    ramdisk_bytes: int
    signature_bytes: int
    os_version: int
    payload_end: int
    image_bytes: int
    avb_footer: bool
    command_line: bytes

    def check_userdata(self):
        selectors = [arg for arg in self.command_line.split() if arg.startswith(b"senemos.root=")]
        if selectors != [ROOT_ARG]:
            raise ValueError("Expected exactly one senemos.root=userdata boot argument")

    def check_boot_id(self, kernel_sha256):
        identifiers = [arg for arg in self.command_line.split() if arg.startswith(BOOT_ID_ARG)]
        if identifiers != [BOOT_ID_ARG + kernel_sha256.encode("ascii")]:
            raise ValueError("Boot image lacks the matching uke-fedora boot identity")


def aligned(size):
    return (size + PAGE - 1) // PAGE * PAGE


def image_size(stream):
    info = os.fstat(stream.fileno())
    if not stat.S_ISREG(info.st_mode) or not 64 <= info.st_size <= MAX_IMAGE:
        raise ValueError("Expected a bounded regular image file")
    return info.st_size


def read_header(stream):
    size = image_size(stream)
    block = stream.read(PAGE)
    if len(block) != PAGE or block[:8] != b"ANDROID!":
        raise ValueError("Expected an Android boot image")
    kernel, ramdisk, os_version, header_size, *reserved, version = struct.unpack_from("<9I", block, 8)
    command_line, terminator, _ = block[44:1580].partition(b"\0")
    if version != 4 or header_size != HEADER_SIZE or any(reserved) or not terminator:
        raise ValueError("Invalid Android boot v4 header")
    signature, = struct.unpack_from("<I", block, 1580)
    payload_end = PAGE + sum(aligned(length) for length in (kernel, ramdisk, signature))
    if not kernel or payload_end > size:
        raise ValueError("Boot payload extends beyond the image or has no kernel")
    stream.seek(-64, os.SEEK_END)
    footer = stream.read(4) == b"AVBf"
    return BootHeader(kernel, ramdisk, signature, os_version, payload_end, size, footer, command_line)


def inspect_boot(path):
    with path.open("rb") as stream:
        return read_header(stream)


def check_kernel(path, expected_sha256):
    with path.open("rb") as stream:
        header = read_header(stream)
        header.check_userdata()
        if header.ramdisk_bytes or header.signature_bytes:
            raise ValueError("Expected a kernel-only boot image")
        stream.seek(PAGE)
        digest = hashlib.sha256()
        remaining = header.kernel_bytes
        while remaining:
            chunk = stream.read(min(remaining, 1024**2))
            if not chunk:
                raise ValueError("Truncated boot kernel")
            digest.update(chunk)
            remaining -= len(chunk)
        if digest.hexdigest() != expected_sha256:
            raise ValueError("Boot image kernel differs from the staged kernel")
    return header


def write_userdata_boot(output, kernel, kernel_sha256, os_version, capacity):
    with kernel.open("rb") as source:
        size = image_size(source)
        arm64 = source.read(64)
        if len(arm64) != 64:
            raise ValueError("Truncated ARM64 Image header")
        declared_size, flags = struct.unpack_from("<QQ", arm64, 16)
        if arm64[56:60] != b"ARM\x64" or not size <= declared_size <= MAX_IMAGE or flags & 1:
            raise ValueError("Expected a little-endian raw ARM64 Image")
        end = PAGE + aligned(size)
        if end > capacity or capacity % PAGE:
            raise ValueError("Kernel does not fit the boot partition")
        header = bytearray(PAGE)
        header[:8] = b"ANDROID!"
        struct.pack_into("<9I", header, 8, size, 0, os_version, HEADER_SIZE, 0, 0, 0, 0, 4)
        command_line = b" ".join((ROOT_ARG, BOOT_ID_ARG + kernel_sha256.encode("ascii")))
        header[44:44 + len(command_line)] = command_line
        source.seek(0)
        with output.open("xb") as stream:
            stream.write(header)
            shutil.copyfileobj(source, stream, length=1024**2)
            if stream.tell() != PAGE + size:
                raise ValueError("Kernel size changed during assembly")
            stream.truncate(end)
    return end
