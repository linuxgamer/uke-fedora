# Build cache and disk use

## Rebuilds and disk use

Fedora 45 AArch64 is the bring-up target. Set `--fedora-release` to change the Fedora repository release used for composition. Profiles share the DNF downloads, staged Senemos payload, slot-A boot image, and compiled Bluetooth and SSC helpers. Each profile has its own cached Fedora base and image pair. TTY caches the compiled keyboard separately. Use `--refresh-fedora` to check for updated Fedora packages and recompose the selected root.

The builder keeps the latest completed result for each stage and replaces it after a successful rebuild. Copy the output pair elsewhere if you want to keep it across rebuilds. Temporary work under `build/work/` is cleaned up on success or a handled failure. Linux hard links avoid duplicating the cached root and kernel files during image staging. Sparse verification hashes the decoded bytes as a stream. While the builder is idle, remove generated entries under `build/cache/` to reclaim space.

See the [bring-up plan](../BRINGUP.md) for Senemos source compilation and tablet testing.
