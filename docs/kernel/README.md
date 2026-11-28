# Kernel source and updates

The image build stages the kernel, matching modules and audio data from the upstream core RPM pinned in [`kernel/senemos-prebuilt.json`](../../kernel/senemos-prebuilt.json). The builder caches the extracted payload in `build/cache/senemos-stage/`. Kernel source and driver code are available in the [Senemos submodule](../../kernel/senemos), pinned to `38c2f657506822a73a5bc6e7626e08d6c16ecaec` to match the current RPM reference. Local kernel compilation is a separate bring-up milestone.

Slot-A images block the modular CoreSight core at kernel level. The pinned Senemos kernel forces its built-in command line, so the wrapper makes a fixed-width argument replacement in the verified kernel payload and checks the resulting digest. The original RPM payload and signed modules are used for rootfs staging. Review the command line and the wrapped kernel digest when changing the pin.

Keep port-specific integration and any downstream patches alongside the submodule. When updating Senemos, record the chosen revision and any corresponding `uke-linux` reference used to select it. [Reference submodule configuration](https://github.com/MCC45TR/uke-linux/blob/Fedora/.gitmodules)

Inventory what Senemos needs for kernel compilation and packaging, and what the rest of the upstream workspace contributes to boot image assembly and device integration. Use the newer `uke-fedora` slot-A recipe to guide host-side checks. Use a matched kernel, modules, device trees, and boot image when composing the rewrite. Revisit local compilation after the prebuilt artifact path is understood.

The [bring-up dependency inventory](../build/DEPENDENCIES.md) records the upstream prebuilt candidate and the slot-A reference.

Review the old `uke-fedora` Senemos fork for useful fixes. For each change we take, record the original commit and why it is needed, check whether upstream already covers it, and carry it as a small patch when practical.

When source builds are introduced, cross-compile the AArch64 kernel with native Clang on x86_64. Keep the kernel build separate from rootfs operations that execute target binaries.

The maintainer's COPR will supply kernel and port-specific userspace updates. For the planned slot A install, a kernel RPM installed into the root filesystem leaves the old boot image in use until `boot_a` is updated. The update workflow must keep the boot image and kernel modules matched and provide a way to restore a known-good boot image. [COPR package rules](https://docs.copr.fedorainfracloud.org/user_documentation.html#what-i-can-build-in-copr)

The [Uke battery-status patch](../../kernel/patches/0001-uke-report-net-battery-discharge.patch) is a source candidate against the released 7.3.5-47 driver. It uses the existing charge-status path to report net discharge while preserving confirmed charge caps. The unmodified driver reconstructed from the signed Senemos parent SRPM matched the release's published source digest. The patched function passed 21 cases on AArch64 with simulated firmware replies. Tablet validation requires a matched boot image and modules signed by a key trusted by that kernel.

## Focus Keyboard

The pinned 7.3.5-47 RPM includes `hid-nanosic-uke` for the WN8030. It requests `qcom/uke/nanosic/MCU_Upgrade.bin`. The optional image input uses the exact O81 firmware from the legacy keyboard PR. That PR tested a different driver, `hid-nanosic-wn8030`, on 7.3.1 with `mi_auth=0`. The pinned RPM uses a different device-tree binding and exposes no `mi_auth` module option. Sustained typing, touchpad input, backlight, and reattach on the rewrite still need physical tests. [Legacy keyboard PR](https://github.com/linuxgamer/uke-fedora/pull/26) · [Legacy driver revision](https://github.com/linuxgamer/senemos-uke-kernel-mainline/commit/5c87b0ff7e20f151b9c13ee0280ac4a9085a776d)
