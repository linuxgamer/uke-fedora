# Port Kit (uke)

Инвентарь извлечения из стока. См. `docs/STOCK-DTB.md`, `docs/STOCK-SUPER.md`.

- Стоковая прошивка: `uke_global_images_OS3.0.303.0.WOZMIXM_16.0`.
- Извлечение: `tools/extract-stock.sh`, `tools/make-firmware-tar.sh`.
- DTB/DTBO: 4 базовых SoC-DTB + DTBO-overlay (board-специфика uke).
- `super.img`: `vendor`, `odm`, `*_dlkm` (EROFS).
- Разделы (4096 Б): boot/vendor_boot 96 МиБ, init_boot 8 МиБ, dtbo 24 МиБ,
  vbmeta 128 КиБ, super 10752 МиБ, persist 32 МиБ.
- Клон донора тача: `Xiaomi-Pad-7-Pro-Resources/android_kernel_xiaomi_sm8635-modules`.
