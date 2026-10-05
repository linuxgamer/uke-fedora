#!/usr/bin/env bash
# Quick board-DTB-only build (cpp plus dtc; no cross-toolchain required).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TREE="${ROOT}/build/linux-uke"
DTS_NAME="sm7675-xiaomi-uke"
DTC="${ROOT}/build/tools/dtc/dtc"
OUT="${ROOT}/build/uke-arm64"
[[ -x "${DTC}" ]] || {
	echo "missing dtc: build build/tools/dtc" >&2
	exit 1
}
mkdir -p "${OUT}"
SRC="${TREE}/arch/arm64/boot/dts/qcom/${DTS_NAME}.dts"
cpp -nostdinc -I "${TREE}/arch/arm64/boot/dts/qcom" -I "${TREE}/include" \
	-undef -D__DTS__ -x assembler-with-cpp "${SRC}" -o "${OUT}/${DTS_NAME}.pre.dts"
"${DTC}" -I dts -O dtb -o "${OUT}/${DTS_NAME}.dtb" "${OUT}/${DTS_NAME}.pre.dts"
echo "DTB: ${OUT}/${DTS_NAME}.dtb"
