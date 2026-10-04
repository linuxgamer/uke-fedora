#!/bin/bash
# Собрать local-assets/ (firmware, модули, ssh-ключ) с подключённого планшета
# ИЛИ из извлечённого стока. Требует adb (и root).
set -euo pipefail
script_dir="$(cd "$(dirname "$0")" && pwd)"; repo_dir="$(dirname "$script_dir")"
assets="$repo_dir/local-assets"; kver="${UKE_KERNEL_VERSION:-7.2.0-rc2-uke}"
mkdir -p "$assets/modules" "$assets/boot-files"
# firmware из rootfs/firmware.tar.gz (или из стока)
if [ -f "$repo_dir/rootfs/firmware.tar.gz" ]; then
    cp -v "$repo_dir/rootfs/firmware.tar.gz" "$assets/firmware.tar.gz"
fi
# модули из build/uke-modules
if [ -d "$repo_dir/build/uke-modules/usr/lib/modules/$kver" ]; then
    cp -a "$repo_dir/build/uke-modules/usr/lib/modules/$kver" "$assets/modules/"
fi
# ssh ключ
[ -f "$HOME/.ssh/id_ed25519.pub" ] && cp -v "$HOME/.ssh/id_ed25519.pub" "$assets/ssh-key.pub" || true
echo "local-assets готовы: $assets"
