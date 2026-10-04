#!/usr/bin/env bash
# Собрать firmware.tar.gz для пакета firmware-xiaomi-uke из извлечённого стока.
# Использование: tools/make-firmware-tar.sh <stock_rootfs_dir> <pkg_dir>
#   <stock_rootfs_dir> — каталог с vendor/ и odm/ (build/stock/rootfs)
set -euo pipefail

SRC="${1:?usage: make-firmware-tar.sh <stock_rootfs_dir> <pkg_dir>}"
PKG="${2:?usage: make-firmware-tar.sh <stock_rootfs_dir> <pkg_dir>}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/lib/firmware/qcom/sm7675"

# GPU
for f in gen71100_gmu.bin gen71100_sqe.fw; do
    [[ -f "$SRC/vendor/firmware/$f" ]] && cp "$SRC/vendor/firmware/$f" "$STAGE/lib/firmware/qcom/sm7675/"
done
for f in gen71100_zap.mbn gen70900_gmu.bin gen70900_sqe.fw gen70900_zap.mbn; do
    [[ -f "$SRC/odm/firmware/$f" ]] && cp "$SRC/odm/firmware/$f" "$STAGE/lib/firmware/qcom/sm7675/"
done

# Тач + аудио
for f in novatek_nt36532_o82_fw_csot.bin novatek_nt36532_o82_fw_tm.bin \
         novatek_nt36532_o82_mp_csot.bin novatek_nt36532_o82_mp_tm.bin; do
    [[ -f "$SRC/odm/firmware/$f" ]] && cp "$SRC/odm/firmware/$f" "$STAGE/lib/firmware/"
done
[[ -f "$SRC/odm/firmware/fs19xx.fsm" ]] && cp "$SRC/odm/firmware/fs19xx.fsm" "$STAGE/lib/firmware/"

echo "WLAN (ath11k) НЕ добавляется автоматически — нужна переупаковка WPSS (TODO)." >&2

( cd "$STAGE" && tar czf "$OLDPWD/firmware.tar.gz" . )
mv firmware.tar.gz "$PKG/firmware.tar.gz"
echo "Готово: $PKG/firmware.tar.gz"
