# Known Issues (uke)

Реестр открытых проблем. По мере решения — переносить в статус «fixed».

| # | Проблема | Статус |
|---|---|---|
| 1 | Панель O82: `mode.clock` и dual-DSI split (hdisplay 1600 vs 3200) не проверены | open |
| 2 | Панель: ESD IRQ (gpio168/169) не обрабатывается драйвером | open |
| 3 | Панель: вариант CSOT vs TM (panel-id) не выбирается | open |
| 4 | Тач: TDDI-синхронизация с панелью; протокол проверен только по коду | open |
| 5 | USB: WCD939x-роут и eUSB2 `param-override` не перенесены | open |
| 6 | Wi-Fi WCN6750: firmware в формате WPSS (`NON-HLOS.bin`), нужна упаковка под ath11k | open |
| 7 | Аудио (WCD939x/WSA/FS19xx) не настроено | open |
| 8 | Датчики/зарядка не портированы | open |
| 9 | **Подтверждено:** Xiaomi ABL не принимает gts9wifi-схему (свой vendor_boot/dtbo/vbmeta) → fastboot. Решение: ztsubaki (boot+init_boot) | fixed-by-design |
| 10 | **Fedora грузится с UFS до login** (ядро → GCC → RPMh → SMMU → UFS PHY → UFS → ext4 → switch_root → systemd) | **fixed** |
| 11 | Часть systemd-сервисов падает при загрузке (нужен разбор `systemctl --failed`) | open |
| 12 | USB RNDIS-функция не поднимается (работает только ACM) — `mkdir rndis.usb0` падает | open |
| 13 | rootfs 3 ГБ (лимит ABL fastboot ~4 ГБ + пропуск нулевых блоков); расширить раздел | open |
| 14 | USB `vccq2-supply` не найден (assumed enabled) — предупреждение | open |

## Fixed

### Kernel patch series (`patches/uke/0001-uke-platform-and-usb-port.patch`)
- `gdsc-regulator-uke`: `devm_ioremap()` вместо `devm_ioremap_resource()` — GDSC-узел
  внутри региона GCC, `request_mem_region` конфликтовал с `gcc-cliffs` (`-EBUSY`).
- `qcom-rpmh-regulator-uke`: снят whitelist из 6 ресурсов — регистрируются все
  RPMh-ресурсы (UFS нужны `smpb2`/`ldod1`/`ldob12`/`ldod3`).
- `ufs-qcom`: interconnect-пути сделаны необязательными (NoC-провайдер покрывает
  только USB; `-EINVAL` больше не роняет probe).
- `phy-qcom-qmp-ufs`: `vdd-phy-gdsc` добавлен в vreg-список (mainline тянет GDSC
  через `power-domains`, которых нет в стоковом DT).
- `arm-smmu-qcom`: SID `0x60` (UFS) разрешён в `qcom_uke_smmu_alloc_context_bank`
  (иначе `-EOPNOTSUPP` → WARN в `iommu_setup_default_domain`).

### DTBO (`images/dtbo/Makefile`)
- fragment@134/135: `ufshc`/`ufsphy_mem` → upstream `qcom,sm8550-ufshc` /
  `qcom,sm8550-qmp-ufs-phy`.
- fragment@136/137: UFS-GDSC (`gdsc@177004`, `gdsc@19e000`) → `qcom,sm7675-usb-gdsc`
  + `regulator-always-on` (иначе UFS при suspend пытается выключить GDSC → `-ETIMEDOUT`
  → линк рвётся).

### Rootfs / сборка
- `rootfs/mk-internal-storage-fastboot.sh`: 3 ГБ (лимит ABL fastboot ~4 ГБ), `-E
  lazy_itable_init=0,lazy_journal_init=0`, отдаёт raw-образ.
- Прошивка: сначала занулить раздел (`dd if=/dev/zero of=/dev/sda32 bs=1M count=4096`),
  затем `fastboot flash userdata` — ABL пропускает нулевые блоки, иначе остаётся мусор.
- initramfs (`boot/build-initramfs-usb.sh`): root-детект сканом `/dev/sda*` (busybox
  `blkid` не умеет `-U`); `dmesg -n 1` + `/status.txt`, чтобы статус не забивался логами;
  shell на `/dev/ttyGS0` для picocom.

### Прочее
- palawan `usb_dp_qmpphy` — пропущена `;` (patch 0001).
- `iris_platform_palawan.h` — лишнее `.num_comv` (patch 0002).
- KVER `+` (грязное git-дерево) — решено через `LOCALVERSION=-uke`.
