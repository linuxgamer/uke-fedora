#!/usr/bin/env bash
# Собрать ядро uke: prepare + defconfig + fragment + Image + DTB + модули.
# Модули -> build/uke-modules/usr/lib/modules/<kver> (для rootfs/dracut).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TREE="${ROOT}/build/linux-uke"
OUT="${ROOT}/build/uke-build"
STAGE="${ROOT}/build/uke-modules"
FRAG="${ROOT}/kernel/files/config-uke.fragment"
DTS="qcom/sm7675-xiaomi-uke.dtb"
LOCALVERSION="-uke"

MAKE=(make -C "${TREE}" O="${OUT}" ARCH=arm64 LLVM=1 LOCALVERSION="${LOCALVERSION}")

"${ROOT}/kernel/prepare.sh"

"${MAKE[@]}" defconfig
cat "${FRAG}" >>"${OUT}/.config"
"${MAKE[@]}" olddefconfig
"${MAKE[@]}" -j"$(nproc)" Image "${DTS}" modules

echo "== modules_install -> ${STAGE} =="
rm -rf "${STAGE}"
"${MAKE[@]}" INSTALL_MOD_PATH="${STAGE}/usr" INSTALL_MOD_STRIP=1 modules_install
KVER="$("${MAKE[@]}" -s kernelrelease)"

echo
echo "KVER:    ${KVER}"
echo "Image:   ${OUT}/arch/arm64/boot/Image"
echo "DTB:     ${OUT}/arch/arm64/boot/dts/${DTS}"
echo "Modules: ${STAGE}/usr/lib/modules/${KVER} ($(find "${STAGE}" -name '*.ko' | wc -l) .ko)"
