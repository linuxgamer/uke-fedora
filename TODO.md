# TODO — фаза 0 (офлайн-подготовка, устройство не требуется)

План: [`docs/PLAN.md`](docs/PLAN.md) · Источники: [`docs/RESEARCH.md`](docs/RESEARCH.md) ·
Доноры: [`docs/PRIOR-ART.md`](docs/PRIOR-ART.md) · Gap-анализ: [`docs/BRINGUP-NOTES.md`](docs/BRINGUP-NOTES.md).
База: palawan-mainline `palawan/v7.2-rc2` (`0d9f7fdf7`) + uke-специфика из ztsubaki.

## Сделано
- [x] Оценка окружения (EndeavourOS, 389 ГБ, android/dt-инструменты).
- [x] Клон базы: `build/src/linux-palawan` (`kernel/prepare.sh`).
- [x] Клоны доноров: `references/ztsubaki-uke-linux`, `references/MCC45TR-uke-linux`.
- [x] Gap-анализ: palawan уже содержит платформу; ztsubaki-драйверы `cliffs` не нужны.
- [x] Черновики: `kernel/files/config-uke.fragment`, `boot/cmdline.txt`, `boot/bootconfig.txt`, `device/deviceinfo`.
- [x] Скачан downstream uke DTS: `references/downstream-uke/` (MiCode `uke-v-oss`).

## Требует sudo (пакеты Arch)
- [ ] `bc` (нужен Kbuild).
- [ ] `dtc` (`device-tree-compiler`: `dtc`, `fdtput`, `fdtget`, `fdtoverlay`).
- [ ] Кросс-тулчейн `aarch64-linux-gnu-*` **или** положиться на pmbootstrap.
- [ ] `pmbootstrap` (AUR/chaotic-aur или pip).

## Требует решений / данных
- [ ] Профиль прошивки для извлечения: CN `OS3.0.302.0.WOZCNXM` / Global `OS3.0.303.0.WOZMIXM` / Turkey.
- [ ] Где брать стоковую прошивку (источник и контрольная сумма).
- [ ] Согласовать `uke.dts`: чистая board-DTS vs stock DTB + overlay на первом этапе.

## Далее
- [x] Извлечь DTB/DTBO из стока + декомпиляция (`tools/extract-stock.sh`).
- [x] Извлечь `super.img` → `vendor`/`odm`/`*_dlkm`; `modules.load`, `fstab.qcom`, firmware
      (`docs/STOCK-SUPER.md`).
- [x] Черновик `kernel/files/sm7675-xiaomi-uke.dts` (на базе `lamma-qrd.dts`).
- [x] DTS в Makefile + binding `xiaomi,uke` в `qcom.yaml` (`prepare-tree.sh`).
- [x] DTB собирается без ошибок (`build-dtb.sh`, cpp+dtc).
- [x] Панель O82: драйвер `panel-xiaomi-o82.c` (dual-DSI DSC) + `uke.dts`; компилируется.
- [x] Тач NT36532: исходники найдены, драйвер с протоколом (report MT-B) и firmware update.
- [ ] Тач: ESD/WDT-recovery, стилус, MP.
- [ ] WCD939x USB-роут.
- [x] Baseline-ядро собрано (`kernel/build.sh`): `Image` 50.5 МБ,
      1641 модуль, DTB; версия `7.2.0-rc2`.
- [x] APKBUILD в `pmos/` (device / linux / firmware) + firmware-тарбол скрипт.
- [ ] `pmbootstrap init` + сборка пакетов и `install`/`flasher` (нужен пользователь).

## Найдено в базе (нужен фикс)
- [x] `palawan.dtsi`: у `usb_dp_qmpphy` пропущена `;` в `compatible` — DTB не компилировался.
      Патч: `kernel/patches/0001-arm64-dts-palawan-fix-usb-dp-phy-compatible.patch`.
- [x] `iris_platform_palawan.h`: лишнее `.num_comv` в `struct platform_inst_caps` —
      `VIDEO_QCOM_IRIS` не компилировался. Патч: `kernel/patches/0002-media-iris-fix-palawan-inst-caps.patch`.

## Открытые техвопросы (фаза 0–1)
- [ ] Куда класть mainline DTB (boot / vendor_boot / dtbo / appended).
- [ ] Примет ли ABL совмещённый `boot.img` (kernel+initramfs) или нужен split boot/init_boot.
- [ ] Нужны ли USB handoff quirks (GCC clock hold, SMMU context bank, GDSC) поверх palawan.
- [ ] Проверить, что generic `qcom,snps-dwc3` покрывает palawan (dwc3-qcom match).

## Планшет (crDroid 12.7 + root)
- [x] Полный бэкап: `/sdcard`, `/data` (app data+settings), разделы boot/init_boot/vendor_boot/dtbo/vbmeta/persist
      -> `~/uke-backup` (+ SHA256SUMS), скрипт `tools/backup-device.sh`.
- [ ] `pmbootstrap init` + сборка пакетов.
- [ ] Первая прошивка (boot.img), проверить загрузку.
