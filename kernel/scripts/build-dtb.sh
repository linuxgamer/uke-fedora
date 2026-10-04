#!/usr/bin/env bash
# Собрать только board-DTB для uke (без кросс-тулчейна): cpp + dtc.
# Требует подготовленного дерева: kernel/scripts/prepare-tree.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TREE="${ROOT}/build/linux-uke"
DTS_NAME="sm7675-xiaomi-uke"
DTC="${ROOT}/build/tools/dtc/dtc"
OUT="${ROOT}/build/uke-arm64"

[[ -d "${TREE}" ]] || {
	echo "нет ${TREE}: запусти kernel/scripts/prepare-tree.sh" >&2
	exit 1
}
[[ -x "${DTC}" ]] || {
	echo "нет dtc: собери build/tools/dtc (см. tools/extract-stock.sh)" >&2
	exit 1
}

mkdir -p "${OUT}"
SRC="${TREE}/arch/arm64/boot/dts/qcom/${DTS_NAME}.dts"

echo "== cpp =="
cpp -nostdinc \
	-I "${TREE}/arch/arm64/boot/dts/qcom" \
	-I "${TREE}/include" \
	-undef -D__DTS__ -x assembler-with-cpp \
	"${SRC}" -o "${OUT}/${DTS_NAME}.pre.dts"

echo "== dtc =="
"${DTC}" -I dts -O dtb -o "${OUT}/${DTS_NAME}.dtb" "${OUT}/${DTS_NAME}.pre.dts"

echo
echo "DTB: ${OUT}/${DTS_NAME}.dtb"
ls -la "${OUT}/${DTS_NAME}.dtb"
