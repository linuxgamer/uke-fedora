# boot/

Упаковка ядра и initramfs в загрузочные образы Android boot image v4.

- `cmdline.txt` — kernel cmdline.
- `bootconfig.txt` — vendor_boot bootconfig.
- `scripts/` — `mkbootimg`/`avbtool`-обёртки, упаковка `boot.img`/`init_boot.img`, флеш и откат.

Схема (как у ztsubaki/gts9wifi): ядро → `boot`, initramfs → `init_boot`,
`vendor_boot`/`dtbo` не трогаем на раннем этапе.
