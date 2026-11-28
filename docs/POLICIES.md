# uke-fedora project policies

Draft for review. The [bring-up plan](BRINGUP.md) tracks work toward the first bootable port.

## Repository and code

- Develop on `dev`. Promote tested commits to `stable`. Keep the previous implementation on `legacy`.
- Keep the seven top-level folders described in the [README](../README.md). Keep the build entry point easy to find and keep contributor and agent instructions short. Use `private/TODO.md` for pending work and `private/HANDOFF.md` for context another agent needs to continue.
- Organize component documentation under `docs/` using the matching project folder name. Keep project-wide documents directly under `docs/`.
- Use Python for project-owned build and maintenance scripts. Call existing tools for tasks such as kernel compilation, package installation, and image creation.
- Reuse upstream components. For imported code, record the upstream URL and revision alongside the import, preserve license notices, and keep downstream changes visible so the import can be updated easily. Use patches against a pinned revision where practical.
- Use MCC45TR's `uke-linux` and its pinned components as the baseline for device integration. Select individual pieces from `uke-fedora` when they preserve a feature or fix a gap in that baseline. Record why each piece was selected and verify it against the chosen upstream version.
- License original port work under [GPL-3.0-only](../LICENSE). Apply the kernel's applicable license terms to kernel work and preserve the applicable licenses and notices of code taken from other ports.
- Keep the project small. Add configuration, tests, and docs where they support a real workflow or catch a specific failure.

## Build and firmware

- Support full builds on a fresh machine from the port checkout and its pinned upstream source submodules, using documented tools and inputs. Keep build paths checkout-relative or explicitly supplied. Both legacy port trees are code references only.
- Aim for one documented build command and one place for build settings, including the Fedora release. Measure cold and warm build time and peak disk usage. Reuse expensive work when its inputs match, make the cache easy to clear, and clean up temporary work after a successful build.
- Verify external firmware inputs before building. Distribute files only when their terms allow redistribution, including when they are embedded in a finished image or package. Keep restricted files local and give users a way to supply them from a source they can obtain themselves.

## Device support and image contents

- Record which models and panel variants were actually tested with each stable release.
- Prefer loadable modules (`=m`) for port-specific drivers when they can be loaded at the point they are needed. For early boot dependencies, preserve the known-working configuration or verify the module and its dependencies are available in the initramfs.
- Ship device drivers through Senemos and its matching module packages. Consolidate any separate driver packages into that kernel build. Keep firmware, configuration, and services that need userspace in the image or a small device-support package. Use stock Fedora packages for ordinary userspace software.

## Installation, recovery, and updates

- Document which data installation overwrites, what users need to back up, and how to return to stock. Before writing to the tablet, verify the target device, partition capacity, and that the boot and root artifacts match. Keep building images and installing them as separate steps.
- Use Fedora repositories for base system updates and the maintainer's COPR for the port kernel and port-specific userspace updates. Before publishing kernel updates to `stable`, verify that the updated boot image and matching modules boot together and that users can recover a known-good boot image.
- Before promotion to `stable`, require a clean build, a boot on hardware, and checks for the features claimed by the release. When publishing an update, test it from the previous stable release too.
