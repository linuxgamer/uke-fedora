# Project instructions

Keep this fork simple and easy to sync with upstream. The root repository coordinates three pinned component submodules: `uke-mainline-linux`, `uke-fedora-rootfs`, and `uke-hardware`. Make focused changes in the repository that owns the code; do not treat directories inside `uke-hardware` as separate repositories or rewrite components. Ask before changes that would make upstream merges harder.

Keep reports, references, and LLM working notes under ignored `/private`, not in tracked project files. Keep public documentation concise, understandable and human-readable.

Do not install host packages, flash devices, or push changes without explicit authorization. Plan Linux for slot A; preserve slot B as the Android rollback, subject to device verification. Treat `/userdata` as destructive to Android user data: verify the target and recovery path before proposing storage or boot changes.

Distinguish source edits, successful builds, offline checks, and actual device tests. Never present an untested image or a planned Fedora release change as validated hardware behavior.
