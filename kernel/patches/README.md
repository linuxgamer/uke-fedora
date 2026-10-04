# kernel/patches/

Серия патчей поверх базы `palawan-mainline`. Патчи применяются к **копии** дерева
в `build/`, база `build/src/linux-palawan` не модифицируется.

`series` — по одному пути на строку, в порядке применения.

## Текущая серия

1. `0001-arm64-dts-palawan-fix-usb-dp-phy-compatible.patch` — фикс синтаксиса базы:
   у `usb_dp_qmpphy` пропущена `;` в `compatible`, без него DTB не компилируется.
2. `0002-media-iris-fix-palawan-inst-caps.patch` — фикс базы: лишнее поле `.num_comv`
   в `iris_platform_palawan.h` (нет в `struct platform_inst_caps`), без него
   `VIDEO_QCOM_IRIS` не компилируется.

Board-DTS и правки `Makefile`/`qcom.yaml` добавляет `kernel/scripts/prepare-tree.sh`
(копирует `kernel/dts/*.dts` в дерево). Драйверные патчи (панель O82, тач, USB handoff)
появятся здесь по мере порта.
