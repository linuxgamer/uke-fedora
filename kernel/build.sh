#!/usr/bin/env bash
# Собрать ядро uke: prepare + defconfig + fragment + Image + DTB + модули.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TREE="${ROOT}/build/linux-uke"
OUT="${ROOT}/build/uke-build"
FRAG="${ROOT}/kernel/files/config-uke.fragment"
DTS="qcom/sm7675-xiaomi-uke.dtb"

"${ROOT}/kernel/prepare.sh"

make -C "${TREE}" O="${OUT}" ARCH=arm64 LLVM=1 defconfig
cat "${FRAG}" >>"${OUT}/.config"
make -C "${TREE}" O="${OUT}" ARCH=arm64 LLVM=1 olddefconfig
make -C "${TREE}" O="${OUT}" ARCH=arm64 LLVM=1 -j"$(nproc)" Image "${DTS}" modules

echo
echo "Image:   ${OUT}/arch/arm64/boot/Image"
echo "DTB:     ${OUT}/arch/arm64/boot/dts/${DTS}"
echo "Modules: $(find "${OUT}" -name '*.ko' | wc -l)"
