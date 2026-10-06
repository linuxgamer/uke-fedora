# Status and Known Issues

## Working

| Area | Status |
|---|---|
| Boot chain | Stock Xiaomi ABL with custom `boot`, `init_boot`, and stock-DT-derived `dtbo` |
| Kernel | Upstream Linux v6.12 plus ztsubaki `uke` patch set |
| Storage | UFS, ext4 rootfs, and Fedora boot to a login prompt |
| Console | simplefb and USB ACM serial console |
| Userspace | `switch_root` to Fedora systemd |

## Open Issues

| Area | Status |
|---|---|
| Display | O82 dual-DSI/DSC panel has not been validated on hardware |
| Touch | Novatek NT36532 port is compiled but untested |
| USB networking | RNDIS is under bring-up; ACM is currently the working debug transport |
| Wi-Fi/Bluetooth | WCN6750 firmware packaging and driver integration are incomplete |
| Audio | WCD939x/WSA/FS19xx machine support is not implemented |
| Sensors and charging | Not ported |
| Suspend, cameras, GPU userspace | Not validated |
| Systemd | Some services fail at boot; inspect with `systemctl --failed` and `journalctl -b -p warning` |
| Rootfs size | Limited to 3 GiB by ABL fastboot behavior; a Linux-side expansion path is needed |
| USB regulator warning | `vccq2-supply` is absent and assumed enabled |

## Confirmed Fixes

### Boot and Storage

- Xiaomi ABL rejects the earlier five-image bundle. The supported design modifies
  `boot`, `init_boot`, and stock-DT-derived `dtbo`; stock `vendor_boot` and
  `vbmeta` remain in place.
- UFS requires the v6.12 UFS/GDSC/SMMU/RPMh changes and DTBO fragments 134--137.
- UFS GDSC nodes must remain enabled with `regulator-always-on`; otherwise a power
  transition times out and drops the link.
- Optional NoC interconnect paths in `ufs-qcom` prevent an incomplete USB-only
  NoC provider from aborting UFS probe.

### Rootfs and Initramfs

- `rootfs/mk-internal-storage-fastboot.sh` creates a 3 GiB initialized raw ext4
  image. The partition must be zeroed before flashing because ABL skips zero blocks.
- The initramfs scans `/dev/sda*` for the root UUID because busybox `blkid -U` is
  unavailable.
- `/status.txt` and `dmesg -n 1` preserve useful early-boot status.
- USB ACM exposes an interactive shell on `/dev/ttyGS0`.
