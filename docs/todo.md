# Uke Port TODO

This is the implementation queue for the supported Fedora / Linux v6.12 port.
Hardware support is reported in [hardware-notes.md](hardware-notes.md); this
document defines the work and the evidence required to close it.

## Completed Baseline

- [x] Boot through stock Xiaomi ABL with custom `boot`, `init_boot`, and
  stock-derived `dtbo`; leave stock `vendor_boot` and `vbmeta` in place.
- [x] Bring up RPMh, GDSC, SMMU, UFS, and an ext4 Fedora rootfs.
- [x] Boot Fedora 44 to a login prompt with a USB ACM serial console.
- [x] Track the Uke kernel delta, config, module list, and reproducible full
  source archive under `kernel/`.
- [x] Restrict the fastboot rootfs image to the ABL-safe 3 GiB size.

## Boot and Release Reliability

- [ ] Test the current RNDIS/ECM gadget on hardware from a clean boot.
  Success: host obtains a `usb0` interface and can reach `172.16.42.1` while
  the ACM shell remains usable.
- [ ] Test the complete release bundle against a matching stock `dtbo.img`.
  Success: `boot/build-dtbo.sh`, bundle creation, and archive checksums complete
  from a clean build directory.
- [ ] Add a Linux-side rootfs expansion procedure after first boot.
  Success: a 3 GiB flashed image can safely grow to the `userdata` partition
  without relying on ABL to flash a larger image.
- [ ] Record a repeatable on-device smoke-test log for every release.
  Success: boot, UFS, root UUID, serial console, and `systemctl --failed` output
  are captured with the release tag.

## Display and Input

- [ ] Port the O82 dual-DSI/DSC panel driver and binding from the archived work
  to Linux v6.12 conventions.
  Success: DRM detects the panel and exposes a stable 3200x2136 mode.
- [ ] Validate panel power sequencing, reset GPIO 2, VSP/VSN, and ESD GPIOs.
  Success: repeated cold boots and display blank/unblank cycles work without
  panel damage or DSI timeouts.
- [ ] Add KTZ8866 backlight support for both controllers.
  Success: brightness is controllable through the standard backlight interface.
- [ ] Port and validate the NT36532E SPI touchscreen driver and firmware flow.
  Success: ten-finger MT-B input works with both CSOT and TM panel variants.
- [ ] Implement touchscreen ESD/WDT recovery, pen support if present, and MP
  testing.
  Success: touch recovers after repeated suspend, display reset, and stress use.

## Wireless and USB

- [ ] Extract and package WCN6750 firmware from stock `NON-HLOS.bin` without
  committing blobs to this repository.
  Success: documented external firmware package provides the files expected by
  the upstream driver.
- [ ] Integrate WCN6750 Wi-Fi with the upstream ath11k/CNSS path and board data.
  Success: scan, WPA connection, DHCP, and sustained traffic pass on hardware.
- [ ] Integrate Bluetooth firmware and transport.
  Success: adapter initializes, scans, pairs, and transfers audio or data.
- [ ] Determine and validate USB-C host/OTG and external-display behavior.
  Success: supported roles and limitations are documented from device tests.

## Graphics, Audio, and Camera

- [ ] Bring up Adreno 732/GMU 735 with the required firmware and mainline DRM.
  Success: DRM render node and Mesa acceleration work without GPU resets.
- [ ] Port the WCD939x/WCD937x, WSA883x/884x, and FS19xx audio machine path.
  Success: ALSA exposes expected cards and playback/recording work.
- [ ] Inventory camera sensors and port their DT, drivers, firmware, and
  userspace integration.
  Success: at least one camera streams reliably using a standard Linux stack.

## Power and Peripherals

- [ ] Port battery gauge, charger, USB power role, and thermal descriptions.
  Success: battery percentage, charging state, thermal zones, and safe charging
  behavior are visible in Linux.
- [ ] Enable and validate suspend/resume after storage, display, and power paths
  are stable.
  Success: repeated suspend/resume preserves UFS, display, touch, and USB.
- [ ] Inventory and port sensors, hall switches, NFC, and keyboard accessory
  support as applicable.
  Success: each discovered device is either functional or explicitly documented
  as unsupported in the hardware matrix.

## Documentation and Maintenance

- [ ] Keep [hardware-notes.md](hardware-notes.md) current after every hardware
  result, including negative test results.
- [ ] Update [known-issues.md](known-issues.md) when boot or hardware status
  changes, as required by `AGENTS.md`.
- [ ] Publish `linux-6.12-uke-source.tar.zst` with every binary release.
- [ ] Keep proprietary firmware out of Git; commit only extraction tooling,
  package manifests, hashes, and documentation.
