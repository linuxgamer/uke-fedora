#!/usr/bin/env bash
# Извлечь и разобрать стоковую прошивку uke (только чтение).
# Использование: tools/extract-stock.sh <каталог_прошивки>
# Пример: tools/extract-stock.sh ~/Загрузки/uke_global_images_OS3.0.303.0.WOZMIXM_16.0
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FW="${1:?usage: extract-stock.sh <firmware_dir>}"
IMG="${FW}/images"
OUT="${ROOT}/build/stock/extracted"
DTC="${ROOT}/build/tools/dtc/dtc"

for f in boot.img init_boot.img vendor_boot.img dtbo.img vbmeta.img; do
	[[ -f "${IMG}/${f}" ]] || {
		echo "нет ${IMG}/${f}" >&2
		exit 1
	}
done

mkdir -p "${OUT}"

echo "== boot =="
unpack_bootimg --boot_img "${IMG}/boot.img" --out "${OUT}/boot" | head -12

echo "== init_boot =="
unpack_bootimg --boot_img "${IMG}/init_boot.img" --out "${OUT}/init_boot" | head -10

echo "== vendor_boot =="
unpack_bootimg --boot_img "${IMG}/vendor_boot.img" --out "${OUT}/vendor_boot" | head -12

echo "== dtbo =="
mkdir -p "${OUT}/dtbo"
mkdtboimg dump "${IMG}/dtbo.img" -b "${OUT}/dtbo/dtbo"

echo "== vbmeta =="
avbtool info_image --image "${IMG}/vbmeta.img" | head -20

# DTC: собрать из первоисточника, если нет
if [[ ! -x "${DTC}" ]]; then
	echo "== сборка dtc =="
	mkdir -p "$(dirname "${DTC}")"
	git clone --depth 1 https://github.com/dgibson/dtc "$(dirname "${DTC}")"
	make -C "$(dirname "${DTC}")" -j"$(nproc)"
fi

# vendor_boot DTB: склеенные DTB -> разбить и декомпилировать
echo "== split + decompile vendor_boot DTB =="
python3 - "$OUT/vendor_boot/dtb" "$OUT/vendor_boot/dtb-parts" <<'PY'
import struct, os, sys
src, outdir = sys.argv[1], sys.argv[2]
data = open(src, "rb").read()
os.makedirs(outdir, exist_ok=True)
i = n = 0
while True:
    j = data.find(b"\xd0\x0d\xfe\xed", i)
    if j < 0:
        break
    total = struct.unpack(">I", data[j+4:j+8])[0]
    open(f"{outdir}/dtb.{n}", "wb").write(data[j:j+total])
    print(f"dtb.{n}: offset={j} size={total}")
    n += 1
    i = j + max(total, 4)
PY

for f in "${OUT}"/vendor_boot/dtb-parts/dtb.*; do
	[[ "${f}" == *.dts ]] && continue
	"${DTC}" -I dtb -O dts "${f}" >"${f}.dts"
	echo "decompiled ${f} -> ${f}.dts"
done
"${DTC}" -I dtb -O dts "${OUT}/dtbo/dtbo.0" >"${OUT}/dtbo/dtbo.0.dts"
echo "decompiled ${OUT}/dtbo/dtbo.0 -> dtbo.0.dts"

echo
echo "Готово: ${OUT}"
echo "Панель/тач/USB: см. ${OUT}/dtbo/dtbo.0.dts"
