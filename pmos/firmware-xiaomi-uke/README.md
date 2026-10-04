# firmware-xiaomi-uke

Проприетарные блобы uke. **В репозиторий не входят** (лицензия proprietary).
Пакет собирается из `firmware.tar.gz`, который нужно сгенерировать из стоковой
прошивки скриптом `tools/make-firmware-tar.sh`.

## Как собрать тарбол

```sh
# 1. распаковать сток (см. docs/STOCK-SUPER.md, tools/extract-stock.sh)
# 2. собрать тарбол в каталог пакета
tools/make-firmware-tar.sh /путь/к/извлечённому/стоку pmos/firmware-xiaomi-uke
```

Раскладка внутри тарбола = `firmware.files`. Источники:
- `vendor/firmware`, `odm/firmware` — GPU, тач, аудио;
- `NON-HLOS.bin` (раздел `modem`) — WLAN WCN6750 (`wpss.*`, `amss.bin`, `bdwlan.b01`, `bd_o82.elf`),
  требует переупаковки под `ath11k` (TODO).

## Зависимости

`linux-firmware-qcom`, `linux-firmware-ath11k` (общие блобы).
