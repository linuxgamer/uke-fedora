#!/usr/bin/env python3
"""Apply the CI-only overlay to the pinned submodule trees.

The submodules point at upstream repositories this fork cannot push to, so the
build workflow applies this overlay on the runner before building. Every
replacement is asserted: a silent no-op means a broken image, not a skipped
feature.
"""
import argparse
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def replace_once(rel, old, new, writes):
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{rel}: expected exactly one match, found {count}: {old[:70]!r}")
    if writes:
        path.write_text(text.replace(old, new, 1))


def replace_or_skip(rel, old, new, writes, already):
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    if count == 1:
        if writes:
            path.write_text(text.replace(old, new, 1))
        return
    if count == 0 and any(marker in text for marker in already):
        return
    raise SystemExit(f"{rel}: expected one match or an already-applied marker, found {count}: {old[:70]!r}")


def sync_kernel_release(builder, kernel, writes):
    """Copy the kernel spec release into the builder's package lock.

    build-rootfs.sh resolves the kernel RPM by the NEVRA pinned in
    configs/package-lock.json, so a lock that lags the spec fails the rootfs
    stage after the whole kernel has been compiled.
    """
    spec = ROOT / kernel / "packaging/senemos-uke-linux-kernel-mainline.spec"
    match = re.search(r"^%global senemos_build_release ([0-9]+)$",
                      spec.read_text(), re.MULTILINE)
    if match is None:
        raise SystemExit(f"{spec.name}: no senemos_build_release line")
    release = match.group(1)
    lock = ROOT / builder / "configs/package-lock.json"
    text = lock.read_text()
    updated, count = re.subn(r'("kernel_release":\s*")[0-9]+(")',
                             rf"\g<1>{release}\g<2>", text)
    if count != 1:
        raise SystemExit(f"{lock.name}: expected one kernel_release, found {count}")
    if writes and updated != text:
        lock.write_text(updated)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate patterns without writing")
    args = parser.parse_args()
    writes = not args.check

    builder = "uke-fedora-builder"
    kernel = "senemos-uke-kernel"
    hardware = "uke-linux-hardware-support"

    # Keep the builder pointed at the kernel release the spec actually builds.
    sync_kernel_release(builder, kernel, writes)

    # OEM firmware count grows with the uke-oem-data RPM.
    replace_once(f"{builder}/src/image/verify-oem-rpm.sh",
                 "[[ $count == 74 ]]", "[[ $count == 75 ]]", writes)
    replace_once(f"{builder}/src/image/audit-rootfs.sh",
                 "((firmware_count == 74))", "((firmware_count == 75))", writes)

    # The workflow runs the builder with Docker on the runner.
    replace_once(f"{builder}/build-rootfs.sh",
                 "if command -v podman >/dev/null; then container=podman",
                 "if [[ -n ${UKE_CONTAINER:-} ]]; then container=$UKE_CONTAINER; "
                 "elif command -v podman >/dev/null; then container=podman", writes)

    # Pull the OEM data RPM into the primary transaction.
    replace_once(f"{builder}/build-rootfs.sh",
                 "        /core-rpm/uke-core-meta.rpm\n",
                 "        /core-rpm/uke-core-meta.rpm /hardware-rpms/uke-fedora*-oem-data-*.rpm\n",
                 writes)

    # The COPR repository file is written by the outer (non-container) script.
    replace_once(f"{builder}/build-rootfs.sh",
                 '    install -Dm644 "$here/configs/images/uke-copr.repo"',
                 '    sudo install -Dm644 "$here/configs/images/uke-copr.repo"', writes)

    # Touch firmware must also exist at the path the kernel requests.
    replace_once(
        f"{builder}/build-rootfs.sh",
        '            install -Dm600 "/local-blobs/touch/$variant/$name" "$root/var/lib/uke-touch/$variant/$name"\n',
        '            install -Dm600 "/local-blobs/touch/$variant/$name" "$root/var/lib/uke-touch/$variant/$name"\n'
        '            install -Dm644 "/local-blobs/touch/$variant/$name" "$root/usr/lib/firmware/qcom/uke/touch/$variant/$name"\n',
        writes)
    replace_once(
        f"{builder}/build-rootfs.sh",
        '        chmod 0700 "$root/var/lib/uke-touch/$variant"\n',
        '        chmod 0700 "$root/var/lib/uke-touch/$variant"\n'
        '        chmod 0755 "$root/usr/lib/firmware/qcom/uke/touch/$variant"\n',
        writes)
    replace_once(
        f"{builder}/build-rootfs.sh",
        '    install -Dm600 /local-blobs/touch/reference.bin "$root/var/lib/uke-touch/reference.bin"\n',
        '    install -Dm600 /local-blobs/touch/reference.bin "$root/var/lib/uke-touch/reference.bin"\n'
        '    install -Dm644 /local-blobs/touch/reference.bin "$root/usr/lib/firmware/qcom/uke/touch/reference.bin"\n',
        writes)

    # Assets live in the umbrella repository, outside the container rootfs.
    # The Nanosic keyboard MCU firmware is loaded by the HID driver at probe
    # time, so a missing file means no keyboard at all. The auth daemon has to
    # run from boot: it answers /dev/nanosic_auth before any login, so it is
    # enabled the way "systemctl enable" would, as a multi-user.target want.
    replace_once(
        f"{builder}/build-rootfs.sh",
        "if [[ $copr == 1 ]]; then\n",
        'sudo install -Dm644 "$here/../configs/audio/fs19xx.fsm" '
        '"$output/root/usr/lib/firmware/qcom/uke/audio/fs19xx.fsm"\n'
        'sudo install -Dm644 "$here/../configs/audio/asound.state" '
        '"$output/root/var/lib/alsa/asound.state"\n'
        'sudo install -Dm644 "$here/../configs/wireplumber/85-uke-speaker-priority.conf" '
        '"$output/root/usr/share/wireplumber/wireplumber.conf.d/85-uke-speaker-priority.conf"\n'
        'sudo install -Dm644 "$here/../configs/nanosic/MCU_Upgrade.bin" '
        '"$output/root/usr/lib/firmware/nanosic/MCU_Upgrade.bin"\n'
        'sudo install -Dm755 "$here/../configs/nanosic/nanosic-authd.py" '
        '"$output/root/usr/local/sbin/nanosic-authd"\n'
        'sudo install -Dm644 "$here/../configs/nanosic/nanosic-authd.service" '
        '"$output/root/usr/lib/systemd/system/nanosic-authd.service"\n'
        'sudo install -d "$output/root/etc/systemd/system/multi-user.target.wants"\n'
        'sudo ln -sf /usr/lib/systemd/system/nanosic-authd.service '
        '"$output/root/etc/systemd/system/multi-user.target.wants/nanosic-authd.service"\n'
        'printf "%s\\n" hid-nanosic-wn8030 | '
        'sudo tee "$output/root/etc/modules-load.d/nanosic.conf" >/dev/null\n'
        "if [[ $copr == 1 ]]; then\n",
        writes)

    # One KMS device for both display and GPU.
    replace_once(f"{kernel}/packaging/native/native.config",
                 " msm.separate_gpu_kms=1", "", writes)
    replace_once(f"{hardware}/uke-desktop-integration/src/modprobe.d/uke-gpu-options.conf",
                 "options msm separate_gpu_kms=1", "# options msm separate_gpu_kms=1", writes)

    # Allow locally built modules to load on the installed system. Signing stays
    # enabled, but neither forced signatures nor forced integrity lockdown block
    # insmod of unsigned test modules.
    replace_or_skip(f"{kernel}/packaging/native/native.config",
                    "CONFIG_MODULE_SIG_FORCE=y", "# CONFIG_MODULE_SIG_FORCE is not set",
                    writes,
                    ("# CONFIG_MODULE_SIG_FORCE is not set",
                     "# CONFIG_MODULE_SIG is not set"))
    replace_once(f"{kernel}/packaging/native/native.config",
                 "CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY=y",
                 "# CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY is not set", writes)
    # The resolved-config test still requires integrity lockdown, which the
    # line above deliberately clears so unsigned local modules can be loaded.
    replace_once(
        f"{kernel}/tests/kernel-hardening-config-contract.sh",
        "    SECURITY_LOCKDOWN_LSM SECURITY_LOCKDOWN_LSM_EARLY LOCK_DOWN_KERNEL_FORCE_INTEGRITY \\\n",
        "    SECURITY_LOCKDOWN_LSM SECURITY_LOCKDOWN_LSM_EARLY \\\n",
        writes)
    replace_or_skip(
        f"{kernel}/tests/kernel-hardening-config-contract.sh",
        "for symbol in MODULE_SIG MODULE_SIG_FORCE MODULE_SIG_ALL MODULE_SIG_SHA256 \\\n"
        "    MODULE_SIG_KEY_TYPE_RSA SYSTEM_TRUSTED_KEYRING SECURITY_DMESG_RESTRICT \\\n"
        "    SECURITY_LOCKDOWN_LSM SECURITY_LOCKDOWN_LSM_EARLY LOCK_DOWN_KERNEL_FORCE_INTEGRITY \\\n"
        "    SECURITY_YAMA SECURITY_SELINUX FORTIFY_SOURCE HARDENED_USERCOPY \\\n"
        "    RANDOMIZE_BASE STACKPROTECTOR_STRONG STRICT_KERNEL_RWX STRICT_MODULE_RWX; do\n",
        "for symbol in MODULE_SIG MODULE_SIG_ALL MODULE_SIG_SHA256 \\\n"
        "    MODULE_SIG_KEY_TYPE_RSA SYSTEM_TRUSTED_KEYRING SECURITY_DMESG_RESTRICT \\\n"
        "    SECURITY_LOCKDOWN_LSM SECURITY_LOCKDOWN_LSM_EARLY \\\n"
        "    SECURITY_YAMA SECURITY_SELINUX FORTIFY_SOURCE HARDENED_USERCOPY \\\n"
        "    RANDOMIZE_BASE STACKPROTECTOR_STRONG STRICT_KERNEL_RWX STRICT_MODULE_RWX; do\n",
        writes,
        ("grep -Fxq '# CONFIG_MODULE_SIG_FORCE is not set'",))

    # The SRPM profile stages tests from git HEAD, so copy the patched contract
    # from the worktree instead of the archived commit.
    replace_once(
        f"{kernel}/Makefile",
        "\tgit archive HEAD src patches manifests/video-linux73-candidate-20261025.json tests | tar -xf - -C \"$$assets\"\n",
        "\tgit archive HEAD src patches manifests/video-linux73-candidate-20261025.json tests | tar -xf - -C \"$$assets\"\n"
        "\trm -rf \"$$assets/tests\"\n"
        "\tcp -a tests \"$$assets/tests\"\n",
        writes)

    # Simplified Chinese replaces the upstream Russian default. glibc-langpack-zh
    # carries the zh_CN locales and langpacks-zh_CN the desktop translations;
    # google-noto-sans-cjk-fonts supplies the Han glyph coverage the Plasma
    # packages do not pull in on their own.
    replace_once(
        f"{builder}/build-rootfs.sh",
        "                    polkit udisks2 xorg-x11-server-Xwayland glibc-langpack-ru langpacks-ru)\n",
        "                    polkit udisks2 xorg-x11-server-Xwayland glibc-langpack-zh langpacks-zh_CN\n"
        "                    google-noto-sans-cjk-fonts)\n",
        writes)
    replace_once(
        f"{builder}/build-rootfs.sh",
        "printf 'LANG=ru_RU.UTF-8\\nLC_TIME=ru_RU.UTF-8\\n' > \"$root/etc/locale.conf\"",
        "printf 'LANG=zh_CN.UTF-8\\nLC_TIME=zh_CN.UTF-8\\n' > \"$root/etc/locale.conf\"",
        writes)

    # authselect owns /etc/pam.d/system-auth and /etc/pam.d/password-auth as
    # ghost files: only its posttrans creates them, and that script discards its
    # own errors. An image built without them still reaches the display manager
    # and the desktop, but every password prompt fails, because sddm, sudo and
    # the console all include those files. Re-apply the stock Fedora profile and
    # fail the build if the PAM stack is still absent.
    replace_once(
        f"{builder}/build-rootfs.sh",
        "    phase_done profile-packages-and-configuration\n",
        '    chroot "$root" /usr/bin/authselect select local with-silent-lastlog --force --nobackup\n'
        '    for pam in system-auth password-auth; do\n'
        '        [[ -s $root/etc/pam.d/$pam ]] || die "PAM stack is missing: /etc/pam.d/$pam"\n'
        "    done\n"
        "    phase_done profile-packages-and-configuration\n",
        writes)

    # The KDE image keeps the stock SDDM and Plasma first-run setup: no
    # pre-created account, root stays locked, and first-boot-policy keeps
    # its Requires= ordering. The earlier GDM overlay created the demo
    # account in src/public/desktop-setup.sh, which only the public COPR
    # stage sources; build-rootfs.sh never ran it, so the CI image shipped
    # no password-capable account at all.
    print("CI overlay applied" if writes else "CI overlay patterns validated")


if __name__ == "__main__":
    main()
