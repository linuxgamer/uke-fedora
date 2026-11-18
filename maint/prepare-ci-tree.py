#!/usr/bin/env python3
"""Apply the CI-only overlay to the pinned submodule trees.

The submodules point at upstream repositories this fork cannot push to, so the
build workflow applies this overlay on the runner before building. Every
replacement is asserted: a silent no-op means a broken image, not a skipped
feature.
"""
import argparse
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def replace_once(rel, old, new, writes):
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{rel}: expected exactly one match, found {count}: {old[:70]!r}")
    if writes:
        path.write_text(text.replace(old, new, 1))


def write_file(rel, content, writes):
    path = ROOT / rel
    if writes:
        path.write_text(content)


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate patterns without writing")
    args = parser.parse_args()
    writes = not args.check

    builder = "uke-fedora-builder"
    kernel = "senemos-uke-kernel"
    hardware = "uke-linux-hardware-support"

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

    # Audio assets live in the umbrella repository, outside the container rootfs.
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

    # KDE image uses GDM with a pre-created uke/fedora wheel account.
    replace_once(
        f"{builder}/build-rootfs.sh",
        '                install noopenh264 "${common[@]}" "${desktop[@]}"\n',
        '                install noopenh264 "${common[@]}" "${desktop[@]}"\n'
        '            if [[ $profile == kde ]]; then\n'
        '                rm -f "$root/etc/systemd/system/display-manager.service"\n'
        '                dnf_install_with_download_retry -y --use-host-config --installroot="$root" \\\n'
        '                    --releasever=44 --setopt=install_weak_deps=False install gdm\n'
        '            fi\n',
        writes)
    replace_once(
        f"{builder}/src/public/desktop-setup.sh",
        '''            systemctl --root="$root" enable plasma-setup.service plasmalogin.service
''',
        '''            if [[ $desktop == kde ]]; then
                for unit in sddm.service plasmalogin.service plasma-setup.service; do
                    systemctl --root="$root" disable "$unit" 2>/dev/null || true
                    systemctl --root="$root" mask "$unit" 2>/dev/null || true
                done
                mkdir -p "$root/etc/gdm" "$root/var/lib/AccountsService/users"
                if ! grep -q '^uke:' "$root/etc/passwd"; then
                    chroot "$root" /usr/sbin/useradd --create-home --groups wheel --shell /usr/bin/bash uke
                fi
                printf 'uke:fedora\n' | chroot "$root" /usr/sbin/chpasswd
                printf 'root:fedora\n' | chroot "$root" /usr/sbin/chpasswd
                chroot "$root" /usr/sbin/usermod -U root || true
                printf '[User]\nSession=plasma\nXSession=plasma\nSystemAccount=false\n' > "$root/var/lib/AccountsService/users/uke"
                chmod 600 "$root/var/lib/AccountsService/users/uke"
                printf '[daemon]\nInitialSetupEnable=false\nAutomaticLoginEnable=false\nTimedLoginEnable=false\n' > "$root/etc/gdm/custom.conf"
                systemctl --root="$root" enable gdm.service
                systemctl --root="$root" set-default graphical.target
            else
                systemctl --root="$root" enable plasma-setup.service plasmalogin.service
            fi
''',
        writes)

    # root/fedora on every image, including the TTY consoles.
    replace_once(
        f"{builder}/build-rootfs.sh",
        '            systemctl --root="$root" enable "$display.service"\n',
        '            if [[ $profile == kde ]]; then\n'
        '                systemctl --root="$root" enable gdm.service\n'
        '            else\n'
        '                systemctl --root="$root" enable "$display.service"\n'
        '            fi\n',
        writes)
    replace_once(f"{builder}/src/public/stage.sh",
                 'chroot "$root" /usr/sbin/usermod -L root\n',
                 'printf \'root:fedora\\n\' | chroot "$root" /usr/sbin/chpasswd\n'
                 'chroot "$root" /usr/sbin/usermod -U root || true\n', writes)

    # Pre-created uke/fedora account and working GDM for the GNOME image.
    replace_once(
        f"{builder}/src/public/desktop-setup.sh",
        '''        gnome)
            rpm --root "$root" -q gdm gnome-initial-setup gnome-shell >/dev/null
            mkdir -p "$root/etc/gdm"
            printf '[daemon]\\nInitialSetupEnable=true\\n' > "$root/etc/gdm/custom.conf"
            systemctl --root="$root" enable gdm.service
            printf '{"account_setup":"gnome-initial-setup","credentials_included":false}\\n' > "$receipt";;
''',
        '''        gnome)
            rpm --root "$root" -q gdm gnome-initial-setup gnome-shell >/dev/null
            mkdir -p "$root/etc/gdm" "$root/var/lib/AccountsService/users"
            if ! grep -q '^uke:' "$root/etc/passwd"; then
                chroot "$root" /usr/sbin/useradd --create-home --groups wheel --shell /usr/bin/bash uke
            fi
            printf 'uke:fedora\\n' | chroot "$root" /usr/sbin/chpasswd
            printf 'root:fedora\\n' | chroot "$root" /usr/sbin/chpasswd
            chroot "$root" /usr/sbin/usermod -U root || true
            printf '[User]\\nSession=gnome\\nXSession=gnome\\nSystemAccount=false\\n' > "$root/var/lib/AccountsService/users/uke"
            chmod 600 "$root/var/lib/AccountsService/users/uke"
            printf '[daemon]\\nInitialSetupEnable=false\\nAutomaticLoginEnable=false\\nTimedLoginEnable=false\\n' > "$root/etc/gdm/custom.conf"
            systemctl --root="$root" enable gdm.service
            systemctl --root="$root" set-default graphical.target
            printf '{"account_setup":"precreated-uke","credentials_included":true,"public_test_account":"uke","password_change_required":false,"autologin_enabled":false}\\n' > "$receipt";;
''',
        writes)
    replace_once(f"{builder}/src/public/desktop-setup.sh",
                 "awk -F: '$3>=1000 && $3<65534 {exit 1}'",
                 "awk -F: '$3>=1000 && $3<65534 && $1!=\"uke\" {exit 1}'", writes)

    # GDM must still come up when the storage gate fails; keep the ordering but
    # do not make the display manager a hard dependency.
    replace_once(
        f"{builder}/src/public/first-boot-policy.sh",
        "printf '[Unit]\\nRequires=uke-root-capacity.service uke-swap-ready.service\\n"
        "After=uke-root-capacity.service uke-swap-ready.service\\n'",
        "printf '[Unit]\\nWants=uke-root-capacity.service uke-swap-ready.service\\n"
        "After=uke-root-capacity.service uke-swap-ready.service\\n'",
        writes)

    # codeberg.org no longer resolves for the runners; the Ubuntu pool
    # carries the exact same 0.4.4 tarball (same sha256).
    replace_once(
        f"{hardware}/uke-sensors/Makefile",
        "url=https://codeberg.org/DylanVanAssche/libssc/archive/v0.4.4.tar.gz",
        "url=https://archive.ubuntu.com/ubuntu/pool/universe/libs/libssc/libssc_0.4.4.orig.tar.gz",
        writes)

    # TTY image: root gets an autologin shell on tty1-4. The account is
    # created by the existing first-boot unit after the image audit, so the
    # frozen rootfs still contains no ordinary user.
    replace_once(
        f"{builder}/build-rootfs.sh",
        "            systemctl --root=\"$root\" enable uke-create-user.service\n"
        "            systemctl --root=\"$root\" set-default multi-user.target\n"
        "            systemctl --root=\"$root\" enable getty@tty1.service\n",
        "            systemctl --root=\"$root\" enable uke-create-user.service\n"
        "            systemctl --root=\"$root\" set-default multi-user.target\n"
        "            for tty in 1 2 3 4; do\n"
        "                install -d -m0755 \"$root/etc/systemd/system/getty@tty$tty.service.d\"\n"
        "                printf '[Service]\\nExecStart=\\nExecStart=-/sbin/agetty --autologin root --noclear %%I $TERM\\n' > \"$root/etc/systemd/system/getty@tty$tty.service.d/autologin.conf\"\n"
        "                systemctl --root=\"$root\" enable \"getty@tty$tty.service\"\n"
        "            done\n"
        "            for tty in tty1 tty2 tty3 tty4; do\n"
        "                grep -qx \"$tty\" \"$root/etc/securetty\" 2>/dev/null || printf '%s\\n' \"$tty\" >> \"$root/etc/securetty\"\n"
        "            done\n",
        writes)

    # Replace the interactive tty1 wizard with the fixed account requested for
    # this headless TTY image. It still runs after the frozen-root audit.
    write_file(
        f"{builder}/configs/firstboot/uke-create-user",
        r"""#!/usr/bin/bash
set -Eeuo pipefail
umask 077
state_dir=/var/lib/uke-firstboot
marker=$state_dir/user-created
[[ ! -e $marker ]] || exit 0
install -d -m 0700 "$state_dir"
if ! getent passwd uke >/dev/null; then
    useradd --create-home --groups wheel --shell /usr/bin/bash uke
fi
printf 'uke:fedora\n' | chpasswd
install -d -m 0750 /etc/sudoers.d
printf 'uke ALL=(ALL:ALL) ALL\n' > /etc/sudoers.d/uke
chmod 0440 /etc/sudoers.d/uke
touch "$marker"
""",
        writes)

    print("CI overlay applied" if writes else "CI overlay patterns validated")


if __name__ == "__main__":
    main()
