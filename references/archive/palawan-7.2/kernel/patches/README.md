# `kernel/patches/` (Archived Palawan 7.2 Work)

This ordered series is applied to a disposable `build/` copy of
`palawan-mainline`; the base checkout at `build/src/linux-palawan` remains clean.
`series` contains one patch path per line in application order.

Current patches fix an invalid USB DP PHY compatible property and a stale Iris
`.num_comv` initializer. `kernel/prepare.sh` also copies the draft board DTS and
adds its Makefile and binding entries. This is not the supported boot path.
