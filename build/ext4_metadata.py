# SPDX-License-Identifier: GPL-3.0-only
"""Apply and verify offline ext4 metadata with debugfs and libselinux."""

from contextlib import contextmanager
import ctypes as c
import errno
import os
import re
import stat
import subprocess


CAPABILITY = "security.capability"
CONTEXT = "security.selinux"
FILE_TYPES = {
    stat.S_IFREG: "regular",
    stat.S_IFDIR: "directory",
    stat.S_IFLNK: "symlink",
    stat.S_IFCHR: "character special",
    stat.S_IFBLK: "block special",
    stat.S_IFIFO: "FIFO",
    stat.S_IFSOCK: "socket",
}


@contextmanager
def file_contexts(path):
    class SelinuxOption(c.Structure):
        _fields_ = [("type", c.c_int), ("value", c.c_char_p)]

    # SELABEL_CTX_FILE = 0 and SELABEL_OPT_PATH = 3 in libselinux's public API.
    lib = c.CDLL("libselinux.so.1", use_errno=True)
    lib.selabel_open.argtypes = [c.c_uint, c.POINTER(SelinuxOption), c.c_uint]
    lib.selabel_open.restype = c.c_void_p
    lib.selabel_lookup_raw.argtypes = [c.c_void_p, c.POINTER(c.c_void_p), c.c_char_p, c.c_int]
    lib.selabel_lookup_raw.restype = c.c_int
    lib.selabel_close.argtypes = lib.freecon.argtypes = [c.c_void_p]
    lib.selabel_close.restype = lib.freecon.restype = None
    option = SelinuxOption(3, os.fsencode(path))
    handle = lib.selabel_open(0, c.byref(option), 1)
    if not handle:
        raise ValueError(f"Cannot load SELinux file contexts from {path}: {os.strerror(c.get_errno())}")

    def lookup(name, mode):
        result = c.c_void_p()
        if lib.selabel_lookup_raw(handle, c.byref(result), os.fsencode(name), mode):
            error = c.get_errno()
            if error == errno.ENOENT:  # Also covers explicit <<none>> entries.
                return None
            raise OSError(error, os.strerror(error), name)
        try:
            return c.string_at(result) + b"\0"
        finally:
            lib.freecon(result)

    try:
        yield lookup
    finally:
        lib.selabel_close(handle)


def image_name(path, root):
    name = "/" + path.relative_to(root).as_posix() if path != root else "/"
    if "\r" in name or "\n" in name:
        raise ValueError(f"Path cannot be represented in a debugfs command: {name!r}")
    return name


def source_capability(path):
    try:
        return os.getxattr(path, CAPABILITY, follow_symlinks=False)
    except OSError as exc:
        if exc.errno not in (errno.ENODATA, errno.ENOTSUP):
            raise
        return None


def ext4_time(nanoseconds):
    seconds, fraction = divmod(nanoseconds, 10**9)
    low = (seconds + 2**31) % 2**32 - 2**31
    epoch = (seconds - low) // 2**32
    if not 0 <= epoch <= 3:
        raise ValueError("Staged file timestamp is outside the ext4 range")
    return low, fraction * 4 + epoch


def run_debugfs(image, work, commands, *, write=False):
    batch = work / "debugfs-commands"
    batch.write_bytes(os.fsencode("\n".join(commands) + "\n"))
    args = ["debugfs", "-w"] if write else ["debugfs"]
    result = subprocess.run(
        [*args, "-f", batch.name, image.absolute()], cwd=work, check=True, capture_output=True,
        env={**os.environ, "LC_ALL": "C", "TZ": "UTC"},
    )
    # Batch command failures can leave debugfs with exit status zero.
    errors = os.fsdecode(result.stderr).splitlines()
    if errors and errors[0].startswith("debugfs "):
        errors.pop(0)
    if errors:
        raise ValueError("debugfs failed: " + "\n".join(errors[:5]))
    output = re.split(r"^debugfs: ", os.fsdecode(result.stdout), flags=re.M)[1:]
    if [part.partition("\n")[0] for part in output] != commands:
        raise ValueError("Incomplete debugfs batch output")
    return [part.partition("\n")[2] for part in output]


def verify_inode(name, details, source, mtime, capability):
    if source is None:  # mkfs generated lost+found.
        return
    mode = re.search(r"^Inode: +\d+ +Type: (.+?) +Mode: +([0-7]+) ", details, re.M)
    owner = re.search(r"^User: +(\d+) +Group: +(\d+) ", details, re.M)
    if (not mode or not owner or mode[1] != FILE_TYPES[stat.S_IFMT(source.st_mode)] or
            int(mode[2], 8) != stat.S_IMODE(source.st_mode) or
            (int(owner[1]), int(owner[2])) != (source.st_uid, source.st_gid)):
        raise ValueError(f"Ext4 type, ownership or mode differs at {name}")
    timestamp = re.search(r"^ *mtime: 0x([0-9a-f]+):([0-9a-f]+)", details, re.M)
    low, extra = mtime
    if not timestamp or (int(timestamp[1], 16), int(timestamp[2], 16)) != (low % 2**32, extra):
        raise ValueError(f"Ext4 mtime differs at {name}")
    if capability is None and f"\n  {CAPABILITY} (" in details:
        raise ValueError(f"Unexpected ext4 file capability at {name}")


def apply_and_verify(image, root, contexts, work):
    if not stat.S_ISREG(image.lstat().st_mode) or not stat.S_ISDIR(root.lstat().st_mode):
        raise ValueError("Expected a regular ext4 image file and a staged root directory")
    writes, reads, entries = [], [], []
    context_files = {}
    with file_contexts(contexts) as lookup:
        for path in (root, *root.rglob("*")):
            source = path.lstat()
            name = image_name(path, root)
            entries.append((name, source, lookup(name, source.st_mode)))
        if not any(name == "/lost+found" for name, _, _ in entries):
            entries.append(("/lost+found", None, lookup("/lost+found", stat.S_IFDIR)))

    checks = []
    for name, source, context in entries:
        escaped = name.replace('"', '""')
        target = f'"{escaped}"'
        if context is not None:
            if context not in context_files:
                value = f"context-{len(context_files)}"
                (work / value).write_bytes(context)
                context_files[context] = value
            writes.append(f"ea_set -f {context_files[context]} {target} {CONTEXT}")
        mtime = capability = None
        if source is not None:
            low, extra = mtime = ext4_time(source.st_mtime_ns)
            writes.extend((f"set_inode_field {target} mtime @{low % 2**32}",
                           f"set_inode_field {target} mtime_extra {extra}"))
            capability = source_capability(root / name.lstrip("/"))
        reads.append(f"stat {target}")
        attributes = [(key, value) for key, value in ((CONTEXT, context), (CAPABILITY, capability))
                      if value is not None]
        reads.extend(f"ea_get -x {target} {key}" for key, _ in attributes)
        checks.append((name, source, mtime, capability, attributes))

    run_debugfs(image, work, writes, write=True)
    results = iter(run_debugfs(image, work, reads))
    for name, source, mtime, capability, attributes in checks:
        verify_inode(name, next(results), source, mtime, capability)
        for key, expected in attributes:
            prefix = f"{key} ({len(expected)}) ="
            value = next(results).strip()
            if not value.startswith(prefix) or bytes.fromhex(value[len(prefix):]) != expected:
                raise ValueError(f"Ext4 {key} differs at {name}")
    print(f"Verified metadata for {len(checks)} ext4 paths")
