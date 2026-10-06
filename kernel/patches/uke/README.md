# Uke Kernel Patch Series

`0001-uke-platform-and-usb-port.patch` is the complete patch required on top of
upstream Linux v6.12 commit `adc218676eef25575469234709c2d87185ca223a`.

It contains the Uke GCC/TCSR, RPMh, GDSC, TLMM, NoC, USB, eUSB2, SMMU, WCD939x
USB route, regulator, and UFS bring-up work. Apply the series only through
`kernel/prepare.sh`; do not modify the fetched upstream source before applying it.

The companion DTBO transformation is `boot/build-dtbo.sh`.
