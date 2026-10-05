# Bring-up Notes: Palawan 7.2 and ztsubaki v6.12

> [!NOTE]
> This is historical reference material. The supported and booting path is
> ztsubaki-based Linux v6.12. The Palawan 7.2 work is parked.

The Palawan tree already contains broad SoC-level support for SM7675/SM8635:
clocks, pinctrl, RPMh, PMIC support, UFS, DWC3, SMMU, GPU, DSI, and interconnects.
It does not contain an `uke` board DTS or validated board peripherals.

The ztsubaki v6.12 path instead uses stock device-tree data transformed through
DTBO fragments. Its platform patch set supplies the handoff behavior needed to
boot from Xiaomi ABL: GCC/TCSR state retention, RPMh and GDSC access, SMMU setup,
eUSB2/DWC3 gadget support, and UFS enablement.

The parked Palawan tree remains useful as a source for future board-specific work:

- `sm7675-xiaomi-uke.dts` draft board description.
- O82 dual-DSI/DSC panel driver.
- Novatek NT36532 touchscreen driver.
- KTZ8866 backlight, WCD939x routing, and other device integration.

Do not use `kernel/build.sh` output for flashing. Keep device-specific work there
as a reference for a future forward-port to the working v6.12 tree.
