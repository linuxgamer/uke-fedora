# pmos/ — пакеты Nura (postmarketOS)

Локальные пакеты для порта `uke`. Соответствуют структуре pmaports
(`device/testing/...`). Собираются через `pmbootstrap`.

| Пакет | Содержимое |
|---|---|
| `device-xiaomi-uke/` | `deviceinfo`, `modules-initfs`, APKBUILD |
| `linux-postmarketos-qcom-sm7675/` | APKBUILD, `config-*`, `0001-uke-support.patch` (DTS + драйверы панели/тача + фиксы базы) |
| `firmware-xiaomi-uke/` | APKBUILD, `firmware.files`, `30-initramfs-firmware.files` (блобы — из стока) |

## Сборка

1. Сгенерировать firmware-тарбол:
   `etc/tools/make-firmware-tar.sh build/stock/rootfs pmos/firmware-xiaomi-uke`
2. Инициализировать `pmbootstrap` и указать локальный aports (каталог `pmos/`,
   содержащий пакеты):
   ```sh
   pmbootstrap init
   pmbootstrap --aports=pmos build linux-postmarketos-qcom-sm7675 --arch aarch64
   pmbootstrap build device-xiaomi-uke --arch aarch64
   pmbootstrap build firmware-xiaomi-uke --arch aarch64
   ```
3. Установка на устройство:
   ```sh
   pmbootstrap install
   pmbootstrap flasher flash_kernel   # boot.img (ядро + initramfs)
   pmbootstrap flasher flash_rootfs   # userdata
   ```

## Заметки

- Kernel-пакет клонирует `palawan-mainline` через git (Codeberg-архивы недоступны).
- `0001-uke-support.patch` — единый патч: фиксы базы (2 шт), board-DTS,
  драйвер панели O82, драйвер тача NT36532, правки Kconfig/Makefile/bindings.
- Точные значения `deviceinfo` (плотность, offset'ы) и firmware-раскладка
  уточняются на железе.
