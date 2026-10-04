# AGENTS.md

Порт **Fedora** (mainline Linux) на **Xiaomi Pad 7** (`uke`, SoC **SM7675**).
Загрузка через стоковую Android boot-цепочку (ABL). Пайплайн зеркалит
[gts9wifi-fedora](https://github.com/nacht20-de/gts9wifi-fedora) — держать
раскладку и процессы такими же.

## Раскладка
| Путь | Что |
|---|---|
| `kernel/` | `files/` (DTS, драйверы, `config-mainline.aarch64` + `config-uke.fragment`), `patches/`, `prepare.sh`, `build.sh`, `kernel.spec` |
| `boot/` | `build-bundle.sh` (Android boot-image v4), `build-initramfs.sh`, cmdline/bootconfig, dracut |
| `rootfs/` | `build-rootfs.sh`, `mk-internal-storage.sh` (TWRP), `mk-sd-card.sh`, overlay |
| `tools/` | mkbootimg, avbtool, make-twrp-zip, извлечение стока, конвертеры |
| `docs/` | BUILD, Known-Issues, Hardware-Notes, PORT-KIT, Device-Controls, research |
| `.github/workflows/` | CI: kernel, rootfs, boot-bundle, full-set |
| `references/`, `attic/` | клоны доноров и архив (не коммитятся) |

## Сборка
```sh
kernel/build.sh                 # vmlinuz.efi + DTB + модули (KVER 7.2.0-rc2-uke)
boot/build-initramfs.sh         # dracut в arm64-контейнере
boot/build-bundle.sh --vmlinuz build/uke-build/arch/arm64/boot/vmlinuz.efi \
    --dtb build/uke-build/arch/arm64/boot/dts/qcom/sm7675-xiaomi-uke.dtb \
    --initramfs build/initramfs.img \
    --cmdline boot/cmdline.txt --bootconfig boot/bootconfig.txt --out build/fedora-boot
docker run --rm --network host -v "$PWD:/work" -w /work \
    quay.io/fedora/fedora:44 ./rootfs/build-rootfs.sh
```

## Правила
- **НИКОГДА не выполнять `fastboot`** — прошивкой занимается только пользователь.
- **Не коммитить**: `build/`, `references/`, `attic/`, `rootfs/firmware.tar.gz`,
  бэкапы, `*.img/*.dtb/*.ko`. Firmware-блобы в репозиторий не попадают.
- Ядро — форк `palawan-mainline` (`palawan/v7.2-rc2`); патчи — `kernel/patches/series`.
- `vmlinuz.efi` (EFI zboot) → `extract-zboot-payload.py` → сжатый kernel для ABL.
- Держать стиль/структуру как gts9wifi; device-специфику — своя.
- Обновлять `docs/Known-Issues.md` при находках.

## Ключевые значения
- `KVER=7.2.0-rc2-uke`; `LOCALVERSION=-uke`.
- root UUID: `19364720-0ee1-4715-b30a-51a47d4a814c` (совпадает в `boot/cmdline.txt`,
  `rootfs/build-rootfs.sh`, `rootfs/mk-internal-storage.sh`).
- Разделы: `boot`/`vendor_boot` 96 МиБ, `init_boot` 8 МиБ, `dtbo` 24 МиБ, `vbmeta` 128 КиБ.
- Device: `uke`, model `2410CRP4CG`; UFS `1d84000.ufshc`.
- Хост-требования: `docker` + `qemu-user-static-binfmt`, `clang`/`llvm`/`lld`, `bc`,
  `dtc`, `pahole`, `flex`, `bison`, `lz4`, `cpio`, `python3`.
