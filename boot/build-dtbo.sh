#!/usr/bin/env bash
# Transform the matching stock Uke DTBO entry for the v6.12 boot path.
# Usage: build-dtbo.sh --stock-dtbo F --out F
set -euo pipefail

while [ $# -gt 0 ]; do
	case "$1" in
	--stock-dtbo)
		stock_dtbo="$2"
		shift 2
		;;
	--out)
		out="$2"
		shift 2
		;;
	*)
		echo "unknown argument: $1" >&2
		exit 1
		;;
	esac
done

for f in "${stock_dtbo:-}"; do
	[ -f "$f" ] || {
		echo "missing stock DTBO: $f" >&2
		exit 1
	}
done
[ -n "${out:-}" ] || {
	echo "missing --out" >&2
	exit 1
}

for tool in mkdtboimg fdtput fdtget; do
	command -v "$tool" >/dev/null || {
		echo "missing required tool: $tool" >&2
		exit 1
	}
done

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
entry_base="$tmp/stock.dtbo"
entry="$entry_base.0"
overlay="$tmp/uke.dtbo"

mkdtboimg dump "$stock_dtbo" -b "$entry_base" >/dev/null
[ -f "$entry" ] || {
	echo "stock DTBO has no entry 0" >&2
	exit 1
}
cp "$entry" "$overlay"

node=/fragment@2/__overlay__/qcom,pmxr2230@1/qcom,flash_led@ee00
for child in qcom,flash_0 qcom,flash_1 qcom,flash_2 qcom,flash_3 qcom,torch_0 qcom,torch_1 qcom,torch_2 qcom,torch_3 qcom,led_switch_0 qcom,led_switch_1 qcom,led_switch_2; do
	fdtput -t s "$overlay" "$node/$child" status disabled
done
fdtput -t s "$overlay" "$node" compatible qcom,pm8350c-flash-led qcom,spmi-flash-led
fdtput -c "$overlay" "$node/led-0"
fdtput -t s "$overlay" "$node/led-0" function torch
fdtput -t x "$overlay" "$node/led-0" color 0
fdtput -t x "$overlay" "$node/led-0" led-sources 1 4
fdtput -t x "$overlay" "$node/led-0" led-max-microamp c350

usb_fragment=/fragment@125
usb_overlay="$usb_fragment/__overlay__"
usb_dwc3="$usb_overlay/dwc3@a600000"
fdtput -c "$overlay" "$usb_fragment"
fdtput -t s "$overlay" "$usb_fragment" target-path /soc/ssusb@a600000
fdtput -c "$overlay" "$usb_overlay"
fdtput -t s "$overlay" "$usb_overlay" compatible qcom,sm7675-dwc3 qcom,dwc-usb3-msm
fdtput -t bx "$overlay" "$usb_overlay" qcom,select-utmi-as-pipe-clk
fdtput -t bx "$overlay" "$usb_overlay" extcon
fdtput -c "$overlay" "$usb_dwc3"
fdtput -t s "$overlay" "$usb_dwc3" dr_mode peripheral
fdtput -t s "$overlay" "$usb_dwc3" maximum-speed high-speed
fdtput -t s "$overlay" /fragment@38/__overlay__/dwc3@a600000 maximum-speed high-speed
fdtput -t x "$overlay" "$usb_dwc3" usb-phy ffffffff
fdtput -t s "$overlay" /__fixups__ eusb2_phy0 "$(fdtget -t s "$overlay" /__fixups__ eusb2_phy0)" "$usb_dwc3:usb-phy:0"
fdtput -t bx "$overlay" "$usb_dwc3" phys
fdtput -t s "$overlay" "$usb_dwc3" phy-names ""

fdtput -c "$overlay" /fragment@126
fdtput -t s "$overlay" /fragment@126 target-path /soc/hsphy@88e3000
fdtput -c "$overlay" /fragment@126/__overlay__
fdtput -t s "$overlay" /fragment@126/__overlay__ compatible qcom,sm7675-snps-eusb2-phy qcom,usb-snps-eusb2-phy
fdtput -t s "$overlay" /fragment@126/__overlay__ clock-names ref_clk_src ref_clk

fdtput -c "$overlay" /fragment@127
fdtput -t s "$overlay" /fragment@127 target-path /soc/qcom,gdsc@139004
fdtput -c "$overlay" /fragment@127/__overlay__
fdtput -t s "$overlay" /fragment@127/__overlay__ compatible qcom,sm7675-usb-gdsc qcom,gdsc
fdtput -t x "$overlay" /fragment@127/__overlay__ reg 139004 8

fdtput -c "$overlay" /fragment@128
fdtput -t s "$overlay" /fragment@128 target-path /soc/qcom,qupv3_0_geni_se@ac0000/i2c@a80000/wcd939x_i2c@e
fdtput -c "$overlay" /fragment@128/__overlay__
fdtput -t s "$overlay" /fragment@128/__overlay__ compatible qcom,sm7675-wcd939x-usb2 qcom,wcd939x-i2c
fdtput -t x "$overlay" /fragment@61/__overlay__ reset-gpios ffffffff 77 1

fdtput -c "$overlay" /fragment@130
fdtput -t s "$overlay" /fragment@130 target-path /soc/qcom,qupv3_0_geni_se@ac0000/i2c@a80000
fdtput -c "$overlay" /fragment@130/__overlay__
fdtput -t s "$overlay" /fragment@130/__overlay__ compatible qcom,geni-i2c qcom,i2c-geni
fdtput -t s "$overlay" /fragment@130/__overlay__ clock-names se

fdtput -c "$overlay" /fragment@129
fdtput -t s "$overlay" /fragment@129 target-path /soc/qcom,gpi-dma@a00000
fdtput -c "$overlay" /fragment@129/__overlay__
fdtput -t s "$overlay" /fragment@129/__overlay__ compatible qcom,sm8450-gpi-dma qcom,gpi-dma
fdtput -t x "$overlay" /fragment@129/__overlay__ dma-channels c
fdtput -t x "$overlay" /fragment@129/__overlay__ dma-channel-mask 1e

fdtput -c "$overlay" /fragment@131
fdtput -t s "$overlay" /fragment@131 target-path /soc/apps-smmu@15000000
fdtput -c "$overlay" /fragment@131/__overlay__
fdtput -t s "$overlay" /fragment@131/__overlay__ compatible qcom,sm7675-usb-smmu

fdtput -c "$overlay" /fragment@132
fdtput -t s "$overlay" /fragment@132 target-path /soc/pinctrl@f000000
fdtput -c "$overlay" /fragment@132/__overlay__
fdtput -t x "$overlay" /fragment@132/__overlay__ gpio-reserved-ranges 8 4 38 5
fdtput -t s "$overlay" /fragment@23/__overlay__/qcom,pm7550ba@7/eusb2-repeater@fd00 compatible qcom,pm8550b-eusb2-repeater qcom,pmic-eusb2-repeater

fdtput -t bx "$overlay" /fragment@80/__overlay__/splash_region no-map
fdtput -c "$overlay" /fragment@133
fdtput -t s "$overlay" /fragment@133 target-path /chosen
fdtput -c "$overlay" /fragment@133/__overlay__
fdtput -t x "$overlay" /fragment@133/__overlay__ '#address-cells' 2
fdtput -t x "$overlay" /fragment@133/__overlay__ '#size-cells' 2
fdtput -t bx "$overlay" /fragment@133/__overlay__ ranges
fdtput -t s "$overlay" /fragment@133/__overlay__ stdout-path /chosen/framebuffer@e3940000
fb_node=/fragment@133/__overlay__/framebuffer@e3940000
fdtput -c "$overlay" "$fb_node"
fdtput -t s "$overlay" "$fb_node" compatible simple-framebuffer
fdtput -t x "$overlay" "$fb_node" reg 0 e3940000 0 1a13000
fdtput -t u "$overlay" "$fb_node" width 3200
fdtput -t u "$overlay" "$fb_node" height 2136
fdtput -t u "$overlay" "$fb_node" stride 12800
fdtput -t s "$overlay" "$fb_node" format a8r8g8b8
fdtput -t s "$overlay" "$fb_node" status okay
fdtput -t x "$overlay" "$fb_node" display ffffffff
fdtput -t s "$overlay" /__fixups__ mdss_mdp "$(fdtget -t s "$overlay" /__fixups__ mdss_mdp)" "$fb_node:display:0"

fdtput -c "$overlay" /fragment@134
fdtput -t s "$overlay" /fragment@134 target-path /soc/ufshc@1d84000
fdtput -c "$overlay" /fragment@134/__overlay__
fdtput -t s "$overlay" /fragment@134/__overlay__ compatible qcom,sm8550-ufshc qcom,ufshc
fdtput -t s "$overlay" /fragment@134/__overlay__ status okay
fdtput -t s "$overlay" /fragment@15/__overlay__ compatible qcom,sm8550-qmp-ufs-phy qcom,qmp-ufs-phy

fdtput -c "$overlay" /fragment@135
fdtput -t s "$overlay" /fragment@135 target-path /soc/ufsphy_mem@1d80000
fdtput -c "$overlay" /fragment@135/__overlay__
fdtput -t s "$overlay" /fragment@135/__overlay__ compatible qcom,sm8550-qmp-ufs-phy qcom,qmp-ufs-phy
fdtput -t s "$overlay" /fragment@135/__overlay__ status okay

for fragment in 136 137; do
	case "$fragment" in
	136) reg=177004 ;;
	137) reg=19e000 ;;
	esac
	fdtput -c "$overlay" "/fragment@$fragment"
	fdtput -t s "$overlay" "/fragment@$fragment" target-path "/soc/qcom,gdsc@$reg"
	fdtput -c "$overlay" "/fragment@$fragment/__overlay__"
	fdtput -t s "$overlay" "/fragment@$fragment/__overlay__" compatible qcom,sm7675-usb-gdsc qcom,gdsc
	fdtput -t x "$overlay" "/fragment@$fragment/__overlay__" reg "$reg" 8
done

mkdir -p "$(dirname "$out")"
mkdtboimg create "$out" --page_size=4096 "$overlay"
mkdtboimg dump "$out" -b "$tmp/check" >/dev/null
fdtget -t s "$tmp/check.0" /fragment@134/__overlay__ compatible | grep -qx 'qcom,sm8550-ufshc qcom,ufshc'
fdtget -t s "$tmp/check.0" /fragment@135/__overlay__ compatible | grep -qx 'qcom,sm8550-qmp-ufs-phy qcom,qmp-ufs-phy'
echo "DTBO image: $out"
