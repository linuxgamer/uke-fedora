# Release checklist

How the Fedora images for Xiaomi Pad 7 are built, checked and published.
This replaces the old private notes; keep it short and keep it current.

## 1. Build

```sh
./ukelinux.sh --cross-kernel --profiles kde,gnome --output build/<name>
```

A build is only usable when `status.json` says `complete` and
`audit-report.txt` beside the images reports no failures. The audit checks image
hashes, critical rootfs files, package install errors and the rebuilt udev
database. Read the log for skipped or reused stages before trusting a cache hit.

## 2. Package

Use the release packager instead of hand-picking files from a pair directory.
It compresses with `tar --zstd`, so the level comes from the environment:

```sh
ZSTD_CLEVEL=12 ZSTD_NBTHREADS=4 \
  ./uke-fedora-builder/tools/package-release.sh --tag <tag> --output build/release-<tag> \
    --twrp <twrp_recovery_ab.tar.zst> build/<name>/*-pair
```

Level 12 shrinks a 1.72 GB tar of the 7.3.1 source tree to 198 MB in 12 s;
level 19 takes 178 s for 170 MB. The CI workflow uses 12 because the packaging
step cost 9m07s at 19 and splitting absorbs the larger archive. `ZSTD_NBTHREADS=0`
means one thread, not all of them.

Each archive contains exactly the shipped files and a checksum file:

```
fedora_boot.img  userdata.img  manifest.json  SHA256SUMS
```

The inner `SHA256SUMS` lists only the three shipped files (the checksum file
itself is not listed) and `sha256sum -c` must pass after extraction. Never copy
the build-internal pair checksums: they name `Image`, `boot.config` and other
files that are not in the archive.

The packager writes an outer `SHA256SUMS` covering the archives and the TWRP
asset, and prints the result. Turn that directory into release assets, because
GitHub rejects any single asset of 2 GiB or more:

```sh
./tools/split-release-assets.sh --input build/release-<tag> --output build/publish-<tag>
```

The splitter moves the archives, breaks anything above 1900 MiB into
`<name>.part-00`, `<name>.part-01`, ... and checks that the parts join back to
the original bytes before deleting the whole file. It writes its own
`SHA256SUMS` (over the emitted assets) and a `README.txt` whose text is also
used as the release notes. Publish the contents of `build/publish-<tag>`:

- `fedora-44-uke-<tag>-kde.tar.zst` or its `.part-NN` pieces
- `fedora-44-uke-<tag>-gnome.tar.zst` or its `.part-NN` pieces
- `fedora-44-uke-<tag>-tty.tar.zst` if a TTY image is released
- `twrp_recovery_ab.tar.zst`
- `SHA256SUMS` and `README.txt`

A split archive is reassembled with `cat <name>.part-* > <name>`, then checked
against the digest printed in `README.txt`; `sha256sum -c SHA256SUMS` only
covers the parts as downloaded. The `.github/workflows/build.yml` and
`publish-release.yml` workflows run the same commands, so a hand-made release
and a CI release have identical layouts.

Mark the GitHub release as a pre-release while the image is still alpha. The
release notes must say so in the first line; do not present an alpha image as a
daily-driver release.

## 3. Device smoke test

Test each profile separately on a TM-panel tablet and record the result next to
the tag. Do not publish an image as tested until this list is done.

| Check | Notes |
| --- | --- |
| First boot reaches the setup wizard, then the desktop | Note how long the grey screen lasts |
| Touch-only account creation, keyboard and login | |
| Wi-Fi connects; Bluetooth can be enabled | |
| Touch selects the real TM/CSOT panel; gestures work after screen off/on | |
| Battery level appears; `upower` and power profile report data | |
| Renderer reports the GPU, not `llvmpipe` | |
| Brightness 5 → 10% and 95 → 100% without flicker | |
| Refresh-rate modes switch and return to 60 Hz | |
| Clock survives an offline reboot | |
| Screen off/on, reboot, clean shutdown | |
| USB ACM on/off and an OTG mouse | |

Write down failures with the exact behaviour, the panel type and the kernel
version. A successful build is not evidence that an image boots.

## 4. After the release

- Keep the previous release assets available for rollback.
- Do not change the boot/root contract inside a patch release.
- Update the hardware table in `README.md` when a device result changes.
