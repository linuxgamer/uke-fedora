# kernel/

Bring-up mainline-ядра для `uke`.

| Подпапка | Содержимое |
|---|---|
| `config/` | config-фрагменты (`uke.fragment`), дельта к `defconfig` |
| `dts/` | `uke.dts` на базе `palawan.dtsi`/`lamma.dtsi` и оверлеи |
| `patches/` | упорядоченная серия патчей (из ztsubaki + свои), формат `series` |
| `scripts/` | получение базы palawan, подготовка дерева, сборка |

База: `palawan-mainline/linux`, ветка `palawan/v7.2-rc2`.
Патчи применять к одноразовому дереву сборки, базу не модифицировать.
