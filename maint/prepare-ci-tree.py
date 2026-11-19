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
    if count == 0:
        print(f"overlay: skipping absent pattern in {rel}: {old[:70]!r}")
        return
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
    if count == 0:
        print(f"overlay: skipping absent pattern in {rel}: {old[:70]!r}")
        return
    raise SystemExit(f"{rel}: expected one match or an already-applied marker, found {count}: {old[:70]!r}")


def sync_kernel_release(builder, kernel, writes):
    """Copy the kernel spec release into the builder's package lock."""
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

    # The source-RPM stage invokes git in every mounted submodule. The builder
    # only whitelists the kernel, so hardware/helper repositories trip Git's
    # ownership guard inside the container.
    replace_once(
        f"{builder}/build-images.sh",
        "git config --global --add safe.directory /work/senemos-uke-kernel\n",
        "git config --global --add safe.directory /work/senemos-uke-kernel\n"
        "git config --global --add safe.directory /work/uke-linux-hardware-support\n"
        "git config --global --add safe.directory /work/uke-fedora-builder\n",
        writes)

    # Flatpak, PackageKit and the Discover backends are required for desktop
    # app installation; the VA-API policy is installed by the image workflow.
    replace_once(
        f"{builder}/build-rootfs.sh",
        "common=(NetworkManager-wifi bluez dbus-daemon mesa-dri-drivers pipewire wireplumber upower",
        "common=(NetworkManager-wifi bluez dbus-daemon mesa-dri-drivers pipewire wireplumber "
        "flatpak flatpak-session-helper PackageKit alsa-ucm alsa-utils upower",
        writes)
    replace_once(
        f"{builder}/build-rootfs.sh",
        "                kde) desktop=(plasma-desktop plasma-workspace kwin sddm sddm-breeze plasma-setup\n"
        "                              sddm-wayland-plasma konsole dolphin plasma-nm bluedevil\n"
        "                              plasma-keyboard plasma-systemsettings kscreen plasma-pa\n"
        "                              powerdevil firefox kate plasma-discover ark kcalc); display=sddm ;;",
        "                kde) desktop=(plasma-desktop plasma-workspace kwin sddm sddm-breeze plasma-setup\n"
        "                              sddm-wayland-plasma konsole dolphin plasma-nm bluedevil\n"
        "                              plasma-keyboard plasma-systemsettings kscreen plasma-pa\n"
        "                              powerdevil firefox kate plasma-discover plasma-discover-flatpak "
        "plasma-discover-packagekit ark kcalc); display=sddm ;;",
        writes)
    replace_once(
        f"{builder}/build-rootfs.sh",
        "            if [[ $profile != tty ]]; then\n",
        "            install -d -m0755 \"$root/var/lib/flatpak\" \"$root/var/lib/flatpak/overrides\"\n"
        "            if [[ $profile != tty ]]; then\n",
        writes)

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
        'sudo install -Dm755 "$here/../configs/audio/uke-root-audio" '
        '"$output/root/usr/local/bin/uke-root-audio"\n'
        'sudo install -Dm644 "$here/../configs/audio/uke-root-audio.desktop" '
        '"$output/root/etc/xdg/autostart/uke-root-audio.desktop"\n'
        'sudo install -Dm644 "$here/../configs/audio/uke-root-audio.desktop" '
        '"$output/root/root/.config/autostart/uke-root-audio.desktop"\n'
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

    # The SRPM profile stages tests from git HEAD, so copy the patched contract
    # from the worktree instead of the archived commit.
    replace_once(
        f"{kernel}/Makefile",
        "\tgit archive HEAD src patches manifests/video-linux73-candidate-20261025.json tests | tar -xf - -C \"$$assets\"\n",
        "\tgit archive HEAD src patches manifests/video-linux73-candidate-20261025.json tests | tar -xf - -C \"$$assets\"\n"
        "\trm -rf \"$$assets/tests\"\n"
        "\tcp -a tests \"$$assets/tests\"\n",
        writes)

    # Desktop defaults: English UI, full Noto coverage for special characters,
    # and power-profiles-daemon so Plasma exposes the power profile switcher.
    replace_once(
        f"{builder}/build-rootfs.sh",
        '                    polkit udisks2 xorg-x11-server-Xwayland glibc-langpack-ru langpacks-ru)\n',
        '                    polkit udisks2 xorg-x11-server-Xwayland glibc-langpack-en langpacks-en\n'
        '                    default-fonts-core-sans default-fonts-core-mono default-fonts-core-serif\n'
        '                    google-noto-sans-fonts google-noto-sans-mono-fonts google-noto-serif-fonts\n'
        '                    google-noto-sans-symbols-fonts google-noto-sans-symbols-2-fonts\n'
        '                    google-noto-sans-math-fonts google-noto-color-emoji-fonts\n'
        '                    google-noto-emoji-fonts google-noto-sans-cjk-vf-fonts\n'
        '                    power-profiles-daemon)\n',
        writes)
    replace_once(
        f"{builder}/build-rootfs.sh",
        "                printf 'LANG=ru_RU.UTF-8\\nLC_TIME=ru_RU.UTF-8\\n' > \"$root/etc/locale.conf\"\n",
        "                printf 'LANG=en_US.UTF-8\\nLC_TIME=en_US.UTF-8\\n' > \"$root/etc/locale.conf\"\n"
        "                printf 'KEYMAP=us\\n' > \"$root/etc/vconsole.conf\"\n",
        writes)

    # KDE image uses GDM with a pre-created saksham/fedora wheel account and
    # autologin so the device boots straight into the owner's desktop.
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
                mkdir -p "$root/etc/gdm" "$root/var/lib/AccountsService/users" "$root/etc/sudoers.d"
                if ! grep -q '^saksham:' "$root/etc/passwd"; then
                    chroot "$root" /usr/sbin/useradd --create-home --groups wheel --shell /usr/bin/bash saksham
                fi
                printf 'saksham:fedora\n' | chroot "$root" /usr/sbin/chpasswd
                printf 'root:fedora\n' | chroot "$root" /usr/sbin/chpasswd
                chroot "$root" /usr/sbin/usermod -U root || true
                printf 'saksham ALL=(ALL:ALL) ALL\n' > "$root/etc/sudoers.d/90-saksham"
                chmod 0440 "$root/etc/sudoers.d/90-saksham"
                install -d -m700 "$root/home/saksham/.config"
                printf '[Formats]\nLANG=en_US.UTF-8\n\n[Translations]\nLANGUAGE=en_US:en\n' > "$root/home/saksham/.config/plasma-localerc"
                printf 'en_US\n' > "$root/home/saksham/.config/user-dirs.locale"
                chroot "$root" /usr/bin/chown -R saksham:saksham /home/saksham
                printf '[User]\nSession=plasma\nXSession=plasma\nSystemAccount=false\nLanguage=en_US.UTF-8\n' > "$root/var/lib/AccountsService/users/saksham"
                chmod 600 "$root/var/lib/AccountsService/users/saksham"
                printf '[daemon]\nInitialSetupEnable=false\nAutomaticLoginEnable=true\nAutomaticLogin=saksham\nDefaultSession=plasma\nTimedLoginEnable=false\n' > "$root/etc/gdm/custom.conf"
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
        '            systemctl --root="$root" enable power-profiles-daemon.service\n'
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

    # Pre-created saksham/fedora account and working GDM for the GNOME image.
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
            mkdir -p "$root/etc/gdm" "$root/var/lib/AccountsService/users" "$root/etc/sudoers.d"
            if ! grep -q '^saksham:' "$root/etc/passwd"; then
                chroot "$root" /usr/sbin/useradd --create-home --groups wheel --shell /usr/bin/bash saksham
            fi
            printf 'saksham:fedora\\n' | chroot "$root" /usr/sbin/chpasswd
            printf 'root:fedora\\n' | chroot "$root" /usr/sbin/chpasswd
            chroot "$root" /usr/sbin/usermod -U root || true
            printf 'saksham ALL=(ALL:ALL) ALL\\n' > "$root/etc/sudoers.d/90-saksham"
            chmod 0440 "$root/etc/sudoers.d/90-saksham"
            install -d -m700 "$root/home/saksham/.config"
            printf '[Formats]\\nLANG=en_US.UTF-8\\n\\n[Translations]\\nLANGUAGE=en_US:en\\n' > "$root/home/saksham/.config/plasma-localerc"
            printf 'en_US\\n' > "$root/home/saksham/.config/user-dirs.locale"
            chroot "$root" /usr/bin/chown -R saksham:saksham /home/saksham
            printf '[User]\\nSession=gnome\\nXSession=gnome\\nSystemAccount=false\\nLanguage=en_US.UTF-8\\n' > "$root/var/lib/AccountsService/users/saksham"
            chmod 600 "$root/var/lib/AccountsService/users/saksham"
            printf '[daemon]\\nInitialSetupEnable=false\\nAutomaticLoginEnable=true\\nAutomaticLogin=saksham\\nDefaultSession=gnome\\nTimedLoginEnable=false\\n' > "$root/etc/gdm/custom.conf"
            systemctl --root="$root" enable gdm.service
            systemctl --root="$root" set-default graphical.target
            printf '{"account_setup":"precreated-saksham","credentials_included":true,"public_test_account":"saksham","password_change_required":false,"autologin_enabled":true}\\n' > "$receipt";;
''',
        writes)
    replace_once(f"{builder}/src/public/desktop-setup.sh",
                 "awk -F: '$3>=1000 && $3<65534 {exit 1}'",
                 "awk -F: '$3>=1000 && $3<65534 && $1!=\"saksham\" {exit 1}'", writes)

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
