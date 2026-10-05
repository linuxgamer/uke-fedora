# `kernel/` (Archived Palawan 7.2 Work)

This directory contains the parked Palawan 7.2 mainline fork, including draft
`uke` DTS, panel, and touchscreen work. It is a reference only: it does not boot
on the device. The supported path is ztsubaki-based Linux v6.12 in
`build/ztsubaki/`.

`prepare.sh` creates a disposable build tree from `palawan-mainline/linux`; the
base checkout is not modified. Keep device-specific work here available for a
future forward-port to v6.12.
