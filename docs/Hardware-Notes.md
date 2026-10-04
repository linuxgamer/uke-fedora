# Hardware Notes (uke)

Заметки по подсистемам. Источники: `docs/STOCK-DTB.md`, `docs/STOCK-SUPER.md`.

- **SoC**: SM7675 (lamma/cliffs7), семейство pineapple. Adreno 732, GMU 735.
- **Панель**: O82, dual DSI + DSC, 3200×2136, reset gpio2, vsp/vsn gpio74/75.
- **Тач**: Novatek NT36532E (TDDI), SPI `se4`, IRQ gpio54.
- **Подсветка**: 2× KTZ8866 @0x11 (i2c0/i2c12).
- **USB**: dwc3 + WCD939x, eUSB2 repeater `pm7550ba`.
- **UFS**: `1d84000.ufshc`, 4096-байтные сектора.
- **Wi-Fi/BT**: WCN6750; firmware в `NON-HLOS.bin`.
- **Модема нет** (downstream отключает `mpss_mem`).
