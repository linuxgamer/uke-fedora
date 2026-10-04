# Known Issues (uke)

Реестр открытых проблем. По мере решения — переносить в статус «fixed».

| # | Проблема | Статус |
|---|---|---|
| 1 | Панель O82: `mode.clock` и dual-DSI split (hdisplay 1600 vs 3200) не проверены | open |
| 2 | Панель: ESD IRQ (gpio168/169) не обрабатывается драйвером | open |
| 3 | Панель: вариант CSOT vs TM (panel-id) не выбирается | open |
| 4 | Тач: TDDI-синхронизация с панелью; протокол проверен только по коду | open |
| 5 | USB: WCD939x-роут и eUSB2 `param-override` не перенесены | open |
| 6 | Wi-Fi WCN6750: firmware в формате WPSS (`NON-HLOS.bin`), нужна упаковка под ath11k | open |
| 7 | Аудио (WCD939x/WSA/FS19xx) не настроено | open |
| 8 | Датчики/зарядка не портированы | open |
| 9 | **Подтверждено:** Xiaomi ABL не принимает gts9wifi-схему (свой vendor_boot/dtbo/vbmeta) → fastboot. Решение: ztsubaki (boot+init_boot) | fixed-by-design |
| 10 | Fedora rootfs ещё не грузился на железе | open |

## Fixed
- palawan `usb_dp_qmpphy` — пропущена `;` (patch 0001).
- `iris_platform_palawan.h` — лишнее `.num_comv` (patch 0002).
- KVER `+` (грязное git-дерево) — решено через `LOCALVERSION=-uke`.
