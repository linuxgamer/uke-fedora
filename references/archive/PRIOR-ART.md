# Prior Art and Sources

## ztsubaki/uke-linux

[ztsubaki/uke-linux](https://github.com/ztsubaki/uke-linux) is the foundation of
the working path. It combines upstream Linux v6.12 with a platform patch and a
stock-DT transformation workflow. Its key contribution is proving that Xiaomi ABL
boots a mainline kernel from `boot` with a small initramfs in `init_boot` while
the stock `vendor_boot`, `dtbo`, and `vbmeta` remain in place.

This repository extends that work with the UFS, GDSC, RPMh, SMMU, and Fedora
rootfs changes required to reach a login prompt.

## gts9wifi-fedora

[gts9wifi-fedora](https://github.com/nacht20-de/gts9wifi-fedora) is the layout and
process reference for this Fedora port: host-side image construction, a small
early initramfs, and an internal-UFS rootfs. Its device-specific code is not
reused.

## palawan-mainline

[palawan-mainline/linux](https://codeberg.org/palawan-mainline/linux) provides a
more complete SM7675/SM8635 SoC base and informed the archived Palawan 7.2 work
in `kernel/`. That tree has draft `uke` panel, touchscreen, and board-DTS code,
but it does not currently boot on this device. It is retained as a technical
reference for porting those board-specific pieces to v6.12.

## Other References

- [MCC45TR/uke-linux](https://github.com/MCC45TR/uke-linux): useful planning and
  hardware-inventory reference; not a proven boot path.
- Xiaomi downstream device trees and modules: source of board wiring, panel,
  touchscreen, and firmware details.
