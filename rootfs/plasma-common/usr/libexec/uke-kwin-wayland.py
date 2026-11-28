# SPDX-License-Identifier: GPL-3.0-only
"""Prefer the Adreno render node when Senemos splits rendering and scanout."""

import os
from pathlib import Path
import sys


DRM = Path("/dev/dri/by-path")
RENDER = DRM / "platform-3d00000.qcom_kgsl-3d0-render"
DISPLAY = DRM / "platform-ae01000.display-controller-card"


def main():
    arguments = sys.argv[1:]
    kwin = "/usr/bin/kwin_wayland_wrapper"
    if arguments[:1] == ["--greeter"]:
        kwin = "/usr/bin/kwin_wayland"
        arguments = arguments[1:]
    environment = os.environ.copy()
    if ("KWIN_DRM_DEVICES" not in environment and "KWIN_RENDER_NODES" not in environment
            and RENDER.is_char_device() and DISPLAY.is_char_device()
            and os.access(RENDER, os.R_OK | os.W_OK)):
        # KWin selects the first usable rendering device and keeps the KMS node for displays.
        environment["KWIN_DRM_DEVICES"] = f"{RENDER}:{DISPLAY}"
    os.execve(kwin, [kwin, *arguments], environment)


if __name__ == "__main__":
    main()
