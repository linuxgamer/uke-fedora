# Hardware Notes

Sources: [stock-dtb.md](stock-dtb.md) and [stock-super.md](stock-super.md).

| Component | Details |
|---|---|
| SoC | Qualcomm SM7675 (`lamma` / `cliffs7`), Adreno 732, GMU 735 |
| Display | O82 3200x2136 dual DSI with DSC; reset GPIO 2; VSP/VSN GPIO 74/75 |
| Touchscreen | Novatek NT36532E TDDI on SPI `se4`; IRQ GPIO 54 |
| Backlight | Two KTZ8866 controllers at I2C address `0x11` |
| Storage | UFS host `1d84000.ufshc`; 4096-byte sectors |
| USB | DWC3, WCD939x USB route, PM7550BA eUSB2 repeater |
| Wireless | WCN6750; firmware originates in `NON-HLOS.bin` |
| Audio | WCD937x/WCD939x, WSA883x/884x, FS19xx amplifiers |
| Modem | Not populated; downstream disables `mpss_mem` |

The O82 panel and NT36532 touchscreen are board-specific work still missing from
the supported v6.12 boot path. See
[the archived panel and touchscreen notes](../references/archive/palawan-7.2/PANEL-TOUCH.md)
for the Palawan implementation record.
