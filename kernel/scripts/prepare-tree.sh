#!/usr/bin/env bash
# Подготовить рабочее дерево ядра для uke в build/linux-uke:
#   - git worktree от базы build/src/linux-palawan
#   - применить патчи из kernel/patches/series
#   - положить board-DTS и добавить его в Makefile + qcom.yaml
# База не модифицируется.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE="${ROOT}/build/src/linux-palawan"
TREE="${ROOT}/build/linux-uke"
DTS_NAME="sm7675-xiaomi-uke"
QCOM="${TREE}/arch/arm64/boot/dts/qcom"

[[ -d "${BASE}/.git" ]] || {
	echo "нет базы: запусти kernel/scripts/fetch-base.sh" >&2
	exit 1
}

echo "== worktree =="
if [[ -e "${TREE}/.git" ]]; then
	git -C "${TREE}" reset --hard HEAD
	git -C "${TREE}" clean -fd
else
	[[ -e "${TREE}" ]] && rm -rf "${TREE}"
	git -C "${BASE}" worktree add --detach "${TREE}" HEAD
fi

echo "== патчи =="
if [[ -f "${ROOT}/kernel/patches/series" ]]; then
	while IFS= read -r p; do
		[[ -z "${p}" || "${p}" == \#* ]] && continue
		echo "  apply ${p}"
		git -C "${TREE}" apply "${ROOT}/kernel/patches/${p}"
	done <"${ROOT}/kernel/patches/series"
fi

echo "== board-DTS =="
cp "${ROOT}/kernel/dts/${DTS_NAME}.dts" "${QCOM}/"

if ! grep -q "${DTS_NAME}.dtb" "${QCOM}/Makefile"; then
	printf 'dtb-$(CONFIG_ARCH_QCOM)\t+= %s.dtb\n' "${DTS_NAME}" >>"${QCOM}/Makefile"
	echo "  Makefile += ${DTS_NAME}.dtb"
fi

python3 - "${TREE}/Documentation/devicetree/bindings/arm/qcom.yaml" <<'PY'
import sys
path = sys.argv[1]
text = open(path).read()
if "xiaomi,uke" in text:
    print("  qcom.yaml: binding уже есть")
    sys.exit(0)
needle = "          - const: qcom,palawan\n"
block = (
    "          - const: qcom,palawan\n"
    "\n"
    "      - items:\n"
    "          - enum:\n"
    "              - qcom,lamma-qrd\n"
    "              - xiaomi,uke\n"
    "          - const: qcom,lamma\n"
)
if needle not in text:
    print("  qcom.yaml: не найден якорь qcom,palawan — добавь binding вручную", file=sys.stderr)
    sys.exit(1)
open(path, "w").write(text.replace(needle, block, 1))
print("  qcom.yaml: добавлен binding xiaomi,uke / qcom,lamma")
PY

echo "== драйверы =="
PANEL_DIR="${TREE}/drivers/gpu/drm/panel"
BIND_DIR="${TREE}/Documentation/devicetree/bindings/display/panel"
if [[ -f "${ROOT}/kernel/drivers/panel-xiaomi-o82.c" ]]; then
	cp "${ROOT}/kernel/drivers/panel-xiaomi-o82.c" "${PANEL_DIR}/"
	if ! grep -q "DRM_PANEL_XIAOMI_O82" "${PANEL_DIR}/Makefile"; then
		printf 'obj-$(CONFIG_DRM_PANEL_XIAOMI_O82)\t+= panel-xiaomi-o82.o\n' >>"${PANEL_DIR}/Makefile"
		echo "  panel/Makefile += panel-xiaomi-o82.o"
	fi
	if ! grep -q "config DRM_PANEL_XIAOMI_O82" "${PANEL_DIR}/Kconfig"; then
		cat >>"${PANEL_DIR}/Kconfig" <<'EOF'

config DRM_PANEL_XIAOMI_O82
	tristate "Xiaomi O82 dual-DSI DSC panel"
	depends on OF
	depends on DRM_MIPI_DSI
	depends on BACKLIGHT_CLASS_DEVICE
	help
	  Xiaomi Pad 7 (uke) O82 dual-DSI DSC LCD panel.
EOF
		echo "  panel/Kconfig += DRM_PANEL_XIAOMI_O82"
	fi
fi
if [[ -f "${ROOT}/kernel/drivers/xiaomi,o82.yaml" ]]; then
	cp "${ROOT}/kernel/drivers/xiaomi,o82.yaml" "${BIND_DIR}/"
	echo "  binding: xiaomi,o82.yaml"
fi

if [[ -f "${ROOT}/kernel/drivers/nt36532-uke.c" ]]; then
	TS_DIR="${TREE}/drivers/input/touchscreen"
	cp "${ROOT}/kernel/drivers/nt36532-uke.c" "${TS_DIR}/"
	if ! grep -q "TOUCHSCREEN_NT36532_UKE" "${TS_DIR}/Makefile"; then
		printf 'obj-$(CONFIG_TOUCHSCREEN_NT36532_UKE)\t+= nt36532-uke.o\n' >>"${TS_DIR}/Makefile"
		echo "  touchscreen/Makefile += nt36532-uke.o"
	fi
	if ! grep -q "config TOUCHSCREEN_NT36532_UKE" "${TS_DIR}/Kconfig"; then
		cat >>"${TS_DIR}/Kconfig" <<'EOF'

config TOUCHSCREEN_NT36532_UKE
	tristate "Novatek NT36532 touchscreen (Xiaomi Pad 7)"
	depends on SPI
	depends on OF
	help
	  Novatek NT36532 TDDI touchscreen in the Xiaomi Pad 7 (uke).
EOF
		echo "  touchscreen/Kconfig += TOUCHSCREEN_NT36532_UKE"
	fi
fi

echo
echo "Готово: ${TREE}"
