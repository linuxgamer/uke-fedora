#!/usr/bin/env bash
# Собрать baseline-ядро uke: defconfig + uke.fragment + Image + DTB + модули.
# Требует: bc, clang/ld.lld, llvm-nm/objcopy/readelf, pahole, flex/bison.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TREE="${ROOT}/build/linux-uke"
OUT="${ROOT}/build/uke-build"
FRAG="${ROOT}/kernel/config/uke.fragment"
DTS="qcom/sm7675-xiaomi-uke.dtb"

"${ROOT}/kernel/scripts/prepare-tree.sh"

echo "== defconfig =="
make -C "${TREE}" O="${OUT}" ARCH=arm64 LLVM=1 defconfig

echo "== merge fragment =="
cat "${FRAG}" >>"${OUT}/.config"
make -C "${TREE}" O="${OUT}" ARCH=arm64 LLVM=1 olddefconfig

echo "== Image + DTB + modules =="
make -C "${TREE}" O="${OUT}" ARCH=arm64 LLVM=1 -j"$(nproc)" Image "${DTS}" modules

echo
echo "Image:   ${OUT}/arch/arm64/boot/Image"
echo "DTB:     ${OUT}/arch/arm64/boot/dts/${DTS}"
echo "Modules: $(find "${OUT}" -name '*.ko' | wc -l) шт."
