#!/usr/bin/env bash
# Prepare the uke kernel tree in build/linux-uke:
#   - fetch palawan-mainline if needed
#   - create a Git worktree from the base
#   - apply kernel/patches/series
#   - install the board DTS and drivers from kernel/files and register Kconfig/Makefile entries
# The build/src/linux-palawan base checkout is not modified.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="${ROOT}/build/src/linux-palawan"
TREE="${ROOT}/build/linux-uke"
FILES="${ROOT}/kernel/files"
DTS_NAME="sm7675-xiaomi-uke"
QCOM="${TREE}/arch/arm64/boot/dts/qcom"
BRANCH="${PALAWAN_BRANCH:-palawan/v7.2-rc2}"
URL="${PALAWAN_URL:-https://codeberg.org/palawan-mainline/linux.git}"

echo "== base =="
if [[ ! -d "${BASE}/.git" ]]; then
	mkdir -p "$(dirname "${BASE}")"
	git clone --depth 1 --single-branch --branch "${BRANCH}" "${URL}" "${BASE}"
fi

echo "== worktree =="
BASE_HEAD="$(git -C "${BASE}" rev-parse HEAD)"
if [[ -e "${TREE}/.git" ]]; then
	git -C "${TREE}" reset --hard "${BASE_HEAD}"
	git -C "${TREE}" clean -fd
	rm -f "${TREE}/localversion-uke"
else
	[[ -e "${TREE}" ]] && rm -rf "${TREE}"
	git -C "${BASE}" worktree add --detach "${TREE}" "${BASE_HEAD}"
fi

echo "== patches =="
while IFS= read -r p; do
	[[ -z "${p}" || "${p}" == \#* ]] && continue
	echo "  apply ${p}"
	git -C "${TREE}" apply "${ROOT}/kernel/patches/${p}"
done <"${ROOT}/kernel/patches/series"

echo "== board-DTS =="
cp "${FILES}/${DTS_NAME}.dts" "${QCOM}/"
grep -q "${DTS_NAME}.dtb" "${QCOM}/Makefile" ||
	printf 'dtb-$(CONFIG_ARCH_QCOM)\t+= %s.dtb\n' "${DTS_NAME}" >>"${QCOM}/Makefile"
python3 - "${TREE}/Documentation/devicetree/bindings/arm/qcom.yaml" <<'PY'
import sys
p = sys.argv[1]; t = open(p).read()
if "xiaomi,uke" in t: sys.exit(0)
needle = "          - const: qcom,palawan\n"
block = needle + ("\n      - items:\n          - enum:\n"
                  "              - qcom,lamma-qrd\n              - xiaomi,uke\n"
                  "          - const: qcom,lamma\n")
if needle not in t: sys.exit("qcom.yaml: missing qcom,palawan anchor")
open(p, "w").write(t.replace(needle, block, 1))
PY

echo "== panel driver =="
PANEL="${TREE}/drivers/gpu/drm/panel"
cp "${FILES}/panel-xiaomi-o82.c" "${PANEL}/"
grep -q "DRM_PANEL_XIAOMI_O82" "${PANEL}/Makefile" ||
	printf 'obj-$(CONFIG_DRM_PANEL_XIAOMI_O82)\t+= panel-xiaomi-o82.o\n' >>"${PANEL}/Makefile"
grep -q "config DRM_PANEL_XIAOMI_O82" "${PANEL}/Kconfig" || cat >>"${PANEL}/Kconfig" <<'K'
config DRM_PANEL_XIAOMI_O82
	tristate "Xiaomi O82 dual-DSI DSC panel"
	depends on OF
	depends on DRM_MIPI_DSI
	depends on BACKLIGHT_CLASS_DEVICE
K
cp "${FILES}/xiaomi,o82.yaml" "${TREE}/Documentation/devicetree/bindings/display/panel/"

echo "== touchscreen driver =="
TS="${TREE}/drivers/input/touchscreen"
cp "${FILES}/nt36532-uke.c" "${TS}/"
grep -q "TOUCHSCREEN_NT36532_UKE" "${TS}/Makefile" ||
	printf 'obj-$(CONFIG_TOUCHSCREEN_NT36532_UKE)\t+= nt36532-uke.o\n' >>"${TS}/Makefile"
grep -q "config TOUCHSCREEN_NT36532_UKE" "${TS}/Kconfig" || cat >>"${TS}/Kconfig" <<'K'
config TOUCHSCREEN_NT36532_UKE
	tristate "Novatek NT36532 touchscreen (Xiaomi Pad 7)"
	depends on SPI
	depends on OF
K

# Commit the prepared tree so setlocalversion does not append "+" to KVER.
git -C "${TREE}" add -A
git -C "${TREE}" -c user.email=uke@local -c user.name=uke \
	commit -q -m "uke: prepared kernel tree" 2>/dev/null || true

echo "Complete: ${TREE}"
