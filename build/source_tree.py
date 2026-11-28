# SPDX-License-Identifier: GPL-3.0-only
"""Export committed source from local submodules into build scratch space."""

import subprocess
import tarfile


def source_revision(checkout):
    if not (checkout / ".git").exists():
        raise ValueError(f"Submodule is missing at {checkout}. Run git submodule update --init --recursive.")
    return subprocess.check_output(["git", "-C", checkout, "rev-parse", "HEAD"], text=True).strip()


def export_source(checkout, revision, target, work, *paths):
    target.mkdir(parents=True, exist_ok=True)
    archive = work / f"{target.name}.tar"
    subprocess.run(["git", "-C", checkout, "archive", "--format=tar", "--output", archive,
                    revision, "--", *paths], check=True)
    with tarfile.open(archive) as stream:
        stream.extractall(target, filter="data")
    archive.unlink()
