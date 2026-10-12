# Hardware and current limits

The target is the **Xiaomi Pad 7**, device codename **uke**, with Qualcomm
SM7675. Similar Qualcomm tablets are useful references, not interchangeable
targets. Stock Android data, display configuration and memory layout must match
this device.

## What we can say today

The current candidate uses Linux **7.2.9-senemos-uke** and a Fedora Rawhide console
rootfs. The build machine checked its kernel ABI, all 1,146 matching modules,
boot image layout, rootfs contents and installation utilities.

Those checks do **not** establish working tablet hardware.

| Area | Current candidate status |
| --- | --- |
| Physical installation and boot | Not accepted on the tablet yet. |
| Internal storage | Kernel and rootguard path included; physical installation/boot still needs testing. |
| USB development console | Included and build-checked; physical USB access still needs testing. |
| Display and touch | Do not assume they work. Older display experiments are not accepted in this candidate. |
| Wi-Fi, Bluetooth and audio | Not established for this candidate. |
| Battery readings, charging and suspend | Not established for this candidate. |
| Desktop environments | Optional package choices, not tested tablet desktops. |

A controller appearing in a device tree, a loaded module, and a functioning
device are three different things. Likewise, a list of Android sensor
descriptors is not a count of physical sensor chips.

## Firmware and storage

The owner reported stock **OS3.0.303.0.WOZMIXM**, an unlocked bootloader and TWRP
on B. The saved boot A matches the known OS3.0.303 boot-template hash. Boot-chain
readbacks were checked against the device when captured.

The saved device tree came from **TWRP B**, not a normal Android A boot.
The Linux handoff uses the tree selected by the bootloader at each actual boot.
That normal-A handoff is still a physical acceptance item.

The candidate uses the existing **userdata** partition; no new GPT partition is
needed. The intended write is boot **A** only, plus owner-approved formatting of
userdata. B's boot chain, recovery, vendor_boot, init_boot, dtbo, vbmeta and early
firmware are not Linux flashing targets.

Read [installation and rollback](uke-fedora-builder/docs/USERDATA-INSTALL.md)
for the exact sequence and data-loss warning.

## How to report a hardware test

Record the exact image hashes, kernel release, firmware version, active slot
and what you actually observed. Keep private identifiers in private reports.
Do not turn an old boot result into acceptance of a newly built image.
