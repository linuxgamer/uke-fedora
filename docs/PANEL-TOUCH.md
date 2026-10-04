# Панель и тач uke

## Панель O82 — сделано (черновик)

Драйвер: `kernel/drivers/panel-xiaomi-o82.c` (449 строк), каркас на базе
`panel-novatek-nt35950.c`. Binding: `kernel/drivers/xiaomi,o82.yaml`.

- **dual-DSI (bonded)**, 2× 1600×2136 = 3200×2136, DSI video mode.
- **DSC**: 10 bpc → 8 bpp, slice 800×24, 2 slices на линк, block-prediction.
- Режимы 120/144/90 Гц, reset gpio2, питание vddio/vsp/vsn.
- Init-последовательность (109 команд) сконвертирована из downstream MiCode
  (`uke-v-oss`) конвертером `tools/dsi-cmds.py`.
- В `uke.dts`: `&mdss_dsi0` + `&mdss_dsi1` (обе DSI уже есть в `palawan.dtsi`),
  панель на `dsi0` с `ports/port@0→dsi0`, `port@1→dsi1`; `display_panel_vsp/vsn`.

Статус: **компилируется** (`panel-xiaomi-o82.ko`), полная сборка ядра — 1642 модуля,
DTB собирается. На железе не проверялось.

Открытые вопросы:
- Точная частота `mode.clock` и разбиение dual-DSI (hdisplay 1600 vs 3200).
- ESD IRQ (gpio168/169) драйвером не обрабатывается.
- Выбор варианта панели CSOT vs TM (panel-id из DTB/стока).
- `mode_flags` (burst/non-burst) сверить с downstream.

## Тач Novatek NT36532 — план

Железо (из downstream/стока):
- Novatek **NT36532E**, TDDI (интегрирован с панелью O82), SPI.
- Downstream: `qupv3_se4_spi` → mainline `&spi4`; IRQ **gpio54**, `lcd_id` **gpio26**.
- Firmware: `odm/firmware/novatek_nt36532_o82_fw_{csot,tm}.bin`,
  `novatek_nt36532_o82_mp_{csot,tm}.bin`, `o82_nova_*_thp_config.ini`.
- Модули стока: `nt36532_touch.ko`, `xiaomi_touch.ko`.

Драйвер:
- В mainline **нет** драйвера NT36532.
- Downstream-исходник найден: `Xiaomi-Pad-7-Pro-Resources/android_kernel_xiaomi_sm8635-modules`
  → `qcom/opensource/touch-drivers/{nt36xxx,xiaomi}` (клон в `references/xiaomi-sm8635-modules`).
  Драйвер большой (4645 строк) и завязан на Android (`xiaomi_touch`, `metis`, DRM).
- Реализация: **`kernel/drivers/nt36532-uke.c`** — черновик mainline-порта:
  SPI mode 0, `novatek,NVT-ts`, reset/IRQ, `request_firmware`, input MT (10 пальцев).
- TDDI: тач и панель связаны; при порте учесть синхронизацию с драйвером панели.

Статус: **компилируется** (`nt36532-uke.ko`, 742 строки). Реализовано:
- SPI read/write по протоколу Novatek (маска 0x80/0x7F, dummy-байт, данные со смещением 2);
- регистровый доступ (`set_page`/`write_addr`), чтение fw info, reset-state, статуса;
- reset/boot MCU (`eng_reset`, `bootloader_reset`, `boot_ready`), **firmware download**
  (разбор bin-заголовка, запись SRAM по разделам, проверка checksum, retry);
- разбор пакета: 6 байт на палец, координаты `x=(b1<<4)|(b3>>4)`, `y=(b2<<4)|(b3&0xf)`,
  pressure, checksum 65 байт;
- report MT-B (10 слотов), BTN_TOUCH.
TODO: ESD/WDT-recovery, стилус (`pen-support`), MP-тест. Требует проверки на железе.
