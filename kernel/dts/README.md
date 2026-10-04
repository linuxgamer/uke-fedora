# kernel/dts/

Board DTS для uke.

- `sm7675-xiaomi-uke.dts` — **черновик** board-DTS на базе `lamma-qrd.dts`
  (palawan `palawan/v7.2-rc2`), сверенный с downstream MiCode uke.

## Размещение в дереве ядра

Файл рассчитан на `arch/arm64/boot/dts/qcom/sm7675-xiaomi-uke.dts` рядом с
`lamma.dtsi` и PMIC-инклюдами (относительные `#include` там резолвятся).

Добавить в `arch/arm64/boot/dts/qcom/Makefile`:

```make
dtb-$(CONFIG_ARCH_QCOM)	+= sm7675-xiaomi-uke.dtb
```

И binding в `Documentation/devicetree/bindings/arm/qcom.yaml`:

```yaml
- items:
    - enum:
        - xiaomi,uke
    - const: qcom,lamma
```

## Сборка только DTB

```sh
make -C build/linux-palawan O=build/uke-arm64 ARCH=arm64 \
     CROSS_COMPILE=aarch64-linux-gnu- qcom/sm7675-xiaomi-uke.dtb
```

(нужен `dtc`/кросс-тулчейн; либо через pmbootstrap.)

## Статус

Черновик. Платформа/регуляторы взяты из `lamma-qrd`. Открытые TODO перечислены в
шапке файла: панель O82 (dual DSI), тач Novatek, подсветка KTZ8866 ×2,
память/reserved-memory, WCD939x. См. `docs/BRINGUP-NOTES.md`.
