# Panel and Touchscreen Notes (Archived Palawan Work)

This document describes code in the parked Palawan 7.2 tree. It compiles but has
not been validated on hardware and is not part of the working v6.12 Fedora path.

## O82 Panel

`kernel/files/panel-xiaomi-o82.c` is a draft panel driver based on
`panel-novatek-nt35950.c`, with binding `kernel/files/xiaomi,o82.yaml`.

- Bonded dual DSI: two 1600x2136 links for a 3200x2136 panel.
- DSC: 10 bpc to 8 bpp, 800x24 slices, two slices per link, block prediction.
- 90, 120, and 144 Hz modes; reset GPIO 2; `vddio`, `vsp`, and `vsn` supplies.
- The 109-command initialization sequence was converted from Xiaomi downstream
  MiCode sources with `tools/dsi-cmds.py`.

Open questions: exact pixel clock and split geometry, ESD IRQ handling on GPIO
168/169, CSOT versus TM panel selection, and burst-mode flags.

## Novatek NT36532 Touchscreen

`kernel/files/nt36532-uke.c` is a draft mainline-oriented driver for the
NT36532E TDDI controller. It uses SPI mode 0, `request_firmware`, and Linux input
multi-touch reporting for ten contacts.

Implemented pieces include protocol read/write, firmware metadata and reset state,
firmware download with checksum retry, and MT-B contact reports. The driver still
needs hardware validation, ESD/WDT recovery, pen support, and MP testing.

The panel and touch controller are coupled by the TDDI design; a production port
must validate their power-up and synchronization sequence together.
