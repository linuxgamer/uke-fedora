# SPDX-License-Identifier: GPL-3.0-only
"""Verify img2simg output against the original raw image without decoding to disk."""

import hashlib
import struct


HEADER = struct.Struct("<I4H4I")
CHUNK = struct.Struct("<2H2I")
RAW, FILL, SKIP = 0xCAC1, 0xCAC2, 0xCAC3
BUFFER_BYTES = 1024 * 1024


def read_exact(stream, size):
    data = stream.read(size)
    if len(data) != size:
        raise ValueError("Truncated Android sparse image")
    return data


def verify_sparse(path, raw_size, raw_digest):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        magic, major, minor, header_size, chunk_size, block_size, blocks, chunks, checksum = (
            HEADER.unpack(read_exact(stream, HEADER.size))
        )
        if (magic != 0xED26FF3A or (major, minor) != (1, 0) or header_size != HEADER.size or
                chunk_size != CHUNK.size or checksum or block_size <= 0 or block_size % 4 or
                blocks * block_size != raw_size):
            raise ValueError("Unexpected img2simg header")

        remaining = raw_size
        for _ in range(chunks):
            kind, _, count, total_size = CHUNK.unpack(read_exact(stream, CHUNK.size))
            length = count * block_size
            payload_size = {RAW: length, FILL: 4, SKIP: 0}.get(kind)
            if (not 0 < length <= remaining or payload_size is None or
                    total_size != CHUNK.size + payload_size):
                raise ValueError("Invalid Android sparse chunk")
            remaining -= length
            if kind == RAW:
                while length:
                    data = read_exact(stream, min(length, BUFFER_BYTES))
                    digest.update(data)
                    length -= len(data)
            else:
                pattern = read_exact(stream, 4) if kind == FILL else b"\0" * 4
                data = pattern * (min(length, BUFFER_BYTES) // 4)
                while length:
                    size = min(length, len(data))
                    digest.update(data[:size])
                    length -= size

        if remaining or stream.read(1) or digest.hexdigest() != raw_digest:
            raise ValueError("Sparse image did not round-trip to the checked ext4 image")
