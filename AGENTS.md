# AGENTS.md

Порт **Fedora** (mainline Linux) на **Xiaomi Pad 7** (`uke`, SoC **SM7675**).
Загрузка через стоковую Android boot-цепочку (ABL). Пайплайн зеркалит
[gts9wifi-fedora](https://github.com/nacht20-de/gts9wifi-fedora) — держать
раскладку и процессы такими же.

## Ветки ядра
- **Рабочая (основная): ztsubaki 6.12** (`build/ztsubaki/`) — upstream v6.12 +
  патч `references/ztsubaki-uke-linux/patches/uke/` (GCC/TCSR/RPMh/GDSC/SMMU/USB/UFS).
  **Fedora грузится до login.** Схема загрузки: `boot`+`init_boot` (стоковые
  `vendor_boot`/`dtbo`/`vbmeta` не трогаем).
- **Palawan 7.2** (`kernel/`, `build/linux-uke/`, KVER `7.2.0-rc2-uke`) — наш
  mainline-форк со своим DTS/драйверами; **запаркован** (не грузится). Держать как
  референс для переноса device-специфики (панель `panel-xiaomi-o82.c`, тач
  `nt36532-uke.c`, `sm7675-xiaomi-uke.dts`) на 6.12.

## Раскладка
| Путь | Что |
|---|---|
| `kernel/` | palawan 7.2: `files/` (DTS, драйверы, config), `patches/`, `prepare.sh`, `build.sh`, `kernel.spec` (запарковано) |
| `boot/` | `build-initramfs-usb.sh` (рабочий initramfs), `build-bundle-ztsubaki.sh`, `build-bundle.sh`, `build-initramfs.sh`, cmdline/bootconfig, dracut |
| `rootfs/` | `build-rootfs.sh`, `mk-internal-storage-fastboot.sh` (рабочий), `mk-internal-storage.sh` (TWRP), `mk-sd-card.sh`, overlay |
| `tools/` | mkbootimg, avbtool, make-twrp-zip, извлечение стока, конвертеры |
| `docs/` | BUILD, Known-Issues, Hardware-Notes, PORT-KIT, Device-Controls, research |
| `.github/workflows/` | CI: kernel, rootfs, boot-bundle, full-set |
| `references/`, `attic/` | клоны доноров и архив (не коммитятся) |

## Сборка (рабочая: ztsubaki 6.12)
```sh
make -C build/ztsubaki/linux O="$PWD/build/ztsubaki/out" ARCH=arm64 LLVM=1 Image.gz
make -C build/ztsubaki/linux O="$PWD/build/ztsubaki/out" ARCH=arm64 LLVM=1 modules
boot/build-initramfs-usb.sh     # busybox-initramfs + USB ACM + /status.txt
# boot.img / dtbo.img / init_boot.img — см. docs/BUILD.md §3a
rootfs/mk-internal-storage-fastboot.sh 3   # raw rootfs 3 ГБ (лимит ABL ~4 ГБ)
# ПЕРЕД fastboot flash userdata — занулить раздел (ABL пропускает нули): см. BUILD §4a
```
Palawan 7.2 (архив): `kernel/build.sh` → `vmlinuz.efi` + DTB + модули.

## Правила
- **НИКОГДА не выполнять `fastboot`** — прошивкой занимается только пользователь.
- **Не коммитить**: `build/`, `references/`, `attic/`, `rootfs/firmware.tar.gz`,
  бэкапы, `*.img/*.dtb/*.ko`. Firmware-блобы в репозиторий не попадают.
- Рабочее ядро — ztsubaki 6.12 (`build/ztsubaki`); palawan 7.2 (`kernel/`) — референс.
- Держать стиль/структуру как gts9wifi; device-специфику — своя.
- Обновлять `docs/Known-Issues.md` при находках.

## Ключевые значения
- Рабочий KVER — `6.12.0-dirty` (ztsubaki); palawan — `7.2.0-rc2-uke`, `LOCALVERSION=-uke`.
- root UUID: `19364720-0ee1-4715-b30a-51a47d4a814c` (метка `uke_root`).
- Разделы: `boot`/`vendor_boot` 96 МиБ, `init_boot` 8 МиБ, `dtbo` 24 МиБ, `vbmeta` 128 КиБ.
- Device: `uke`, model `2410CRP4CG`; UFS `1d84000.ufshc`; `userdata` = `/dev/block/sda32`.
- Хост-требования: `docker` + `qemu-user-static-binfmt`, `clang`/`llvm`/`lld`, `bc`,
  `dtc`, `pahole`, `flex`, `bison`, `lz4`, `cpio`, `python3`.
