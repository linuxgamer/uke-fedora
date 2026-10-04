#!/usr/bin/env bash
# Получить базовое дерево ядра (palawan-mainline) в build/src/.
# База не коммитится. Патчи применяются поверх отдельным деревом сборки.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE_BRANCH="${PALAWAN_BRANCH:-palawan/v7.2-rc2}"
REPO_URL="${PALAWAN_URL:-https://codeberg.org/palawan-mainline/linux.git}"
DEST="${ROOT}/build/src/linux-palawan"

if [[ -d "${DEST}/.git" ]]; then
	echo "Уже клонировано: ${DEST}"
	echo "Обновить: git -C '${DEST}' fetch --depth 1 origin '${BASE_BRANCH}' && git -C '${DEST}' reset --hard FETCH_HEAD"
	exit 0
fi

mkdir -p "$(dirname "${DEST}")"
echo "Клонирую ${REPO_URL} (${BASE_BRANCH}) -> ${DEST}"
git clone --depth 1 --single-branch --branch "${BASE_BRANCH}" "${REPO_URL}" "${DEST}"

echo
echo "Версия:"
make -s -C "${DEST}" kernelversion 2>/dev/null || true
git -C "${DEST}" log -1 --oneline
