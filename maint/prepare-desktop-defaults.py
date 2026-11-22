#!/usr/bin/env python3
"""Apply desktop defaults to the pinned builder tree.

The builder is a submodule pinned to an upstream repository this fork cannot
push to, so the image workflow runs this overlay before building. Every
replacement is asserted: a drift in the pinned source fails the build instead
of silently shipping the old locale, fonts or power policy.

Set UKE_AUTOLOGIN_USER to pre-create that wheel account and log it in
automatically. Leave it empty to keep the interactive first-run setup.
"""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILDER = "uke-fedora-builder"


def replace_once(rel, old, new, writes):
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{rel}: expected exactly one match, found {count}: {old[:70]!r}")
    if writes:
        path.write_text(text.replace(old, new, 1))


def main():
    writes = "--check" not in sys.argv[1:]
    user = os.environ.get("UKE_AUTOLOGIN_USER", "").strip()

    # English UI plus the fonts needed for symbols, emoji and CJK text.
    replace_once(
        f"{BUILDER}/build-rootfs.sh",
        "                    polkit udisks2 xorg-x11-server-Xwayland glibc-langpack-ru langpacks-ru)\n",
        "                    polkit udisks2 xorg-x11-server-Xwayland glibc-langpack-en langpacks-en\n"
        "                    default-fonts-core-sans default-fonts-core-mono default-fonts-core-serif\n"
        "                    google-noto-sans-fonts google-noto-sans-mono-fonts google-noto-serif-fonts\n"
        "                    google-noto-sans-symbols-fonts google-noto-sans-symbols-2-fonts\n"
        "                    google-noto-sans-math-fonts google-noto-color-emoji-fonts\n"
        "                    google-noto-emoji-fonts google-noto-sans-cjk-vf-fonts\n"
        "                    power-profiles-daemon)\n",
        writes)
    replace_once(
        f"{BUILDER}/build-rootfs.sh",
        "                printf 'LANG=ru_RU.UTF-8\\nLC_TIME=ru_RU.UTF-8\\n' > \"$root/etc/locale.conf\"\n",
        "                printf 'LANG=en_US.UTF-8\\nLC_TIME=en_US.UTF-8\\n' > \"$root/etc/locale.conf\"\n"
        "                printf 'KEYMAP=us\\n' > \"$root/etc/vconsole.conf\"\n",
        writes)

    # Plasma and GNOME read power profiles from power-profiles-daemon.
    replace_once(
        f"{BUILDER}/build-rootfs.sh",
        '            systemctl --root="$root" enable "$display.service"\n',
        '            systemctl --root="$root" enable power-profiles-daemon.service\n'
        '            systemctl --root="$root" enable "$display.service"\n',
        writes)

    if not user:
        print("desktop defaults: UKE_AUTOLOGIN_USER is empty; keeping first-run setup")
        return

    if not user.isalnum() or user[0].isdigit():
        raise SystemExit(f"invalid UKE_AUTOLOGIN_USER: {user!r}")

    # KDE: create the owner account before first boot and skip the wizard.
    replace_once(
        f"{BUILDER}/src/public/desktop-setup.sh",
        "            systemctl --root=\"$root\" enable plasma-setup.service plasmalogin.service\n",
        "            systemctl --root=\"$root\" enable plasma-setup.service plasmalogin.service\n"
        "            if ! grep -q '^" + user + ":' \"$root/etc/passwd\"; then\n"
        "                chroot \"$root\" /usr/sbin/useradd --create-home --groups wheel --shell /usr/bin/bash " + user + "\n"
        "            fi\n"
        f"            printf '{user}:fedora\\n' | chroot \"$root\" /usr/sbin/chpasswd\n"
        "            printf 'root:fedora\\n' | chroot \"$root\" /usr/sbin/chpasswd\n"
        "            chroot \"$root\" /usr/sbin/usermod -U root || true\n"
        "            install -d -m700 \"$root/home/" + user + "/.config\"\n"
        "            printf '[Formats]\\nLANG=en_US.UTF-8\\n\\n[Translations]\\nLANGUAGE=en_US:en\\n' > \"$root/home/" + user + "/.config/plasma-localerc\"\n"
        "            printf 'en_US\\n' > \"$root/home/" + user + "/.config/user-dirs.locale\"\n"
        "            chroot \"$root\" /usr/bin/chown -R " + user + ":" + user + " /home/" + user + "\n"
        "            if [[ -f $root/etc/gdm/custom.conf ]]; then\n"
        "                mkdir -p \"$root/var/lib/AccountsService/users\"\n"
        "                printf '[User]\\nSession=plasma\\nXSession=plasma\\nSystemAccount=false\\nLanguage=en_US.UTF-8\\n' > \"$root/var/lib/AccountsService/users/" + user + "\"\n"
        "                chmod 600 \"$root/var/lib/AccountsService/users/" + user + "\"\n"
        "                printf '[daemon]\\nInitialSetupEnable=false\\nAutomaticLoginEnable=true\\nAutomaticLogin=" + user + "\\nDefaultSession=plasma\\nTimedLoginEnable=false\\n' > \"$root/etc/gdm/custom.conf\"\n"
        "            else\n"
        "                install -d -m755 \"$root/etc/sddm.conf.d\"\n"
        "                printf '[Autologin]\\nUser=" + user + "\\nSession=plasma\\nRelogin=true\\n' > \"$root/etc/sddm.conf.d/10-autologin.conf\"\n"
        "            fi\n"
        "            systemctl --root=\"$root\" disable plasma-setup.service 2>/dev/null || true\n",
        writes)

    # GNOME: GDM autologin for the same owner account.
    replace_once(
        f"{BUILDER}/src/public/desktop-setup.sh",
        "            systemctl --root=\"$root\" enable gdm.service\n"
        "            printf '{\"account_setup\":\"gnome-initial-setup\",\"credentials_included\":false}\\n' > \"$receipt\";;\n",
        "            systemctl --root=\"$root\" enable gdm.service\n"
        "            if ! grep -q '^" + user + ":' \"$root/etc/passwd\"; then\n"
        "                chroot \"$root\" /usr/sbin/useradd --create-home --groups wheel --shell /usr/bin/bash " + user + "\n"
        "            fi\n"
        "            printf '" + user + ":fedora\\n' | chroot \"$root\" /usr/sbin/chpasswd\n"
        "            printf 'root:fedora\\n' | chroot \"$root\" /usr/sbin/chpasswd\n"
        "            chroot \"$root\" /usr/sbin/usermod -U root || true\n"
        "            install -d -m700 \"$root/home/" + user + "/.config\"\n"
        "            printf 'en_US\\n' > \"$root/home/" + user + "/.config/user-dirs.locale\"\n"
        "            chroot \"$root\" /usr/bin/chown -R " + user + ":" + user + " /home/" + user + "\n"
        "            mkdir -p \"$root/var/lib/AccountsService/users\"\n"
        "            printf '[User]\\nSession=gnome\\nXSession=gnome\\nSystemAccount=false\\nLanguage=en_US.UTF-8\\n' > \"$root/var/lib/AccountsService/users/" + user + "\"\n"
        "            chmod 600 \"$root/var/lib/AccountsService/users/" + user + "\"\n"
        "            printf '[daemon]\\nInitialSetupEnable=false\\nAutomaticLoginEnable=true\\nAutomaticLogin=" + user + "\\nDefaultSession=gnome\\nTimedLoginEnable=false\\n' > \"$root/etc/gdm/custom.conf\"\n"
        "            printf '{\"account_setup\":\"precreated-" + user + "\",\"credentials_included\":true,\"autologin_enabled\":true}\\n' > \"$receipt\";;\n",
        writes)
    replace_once(
        f"{BUILDER}/src/public/desktop-setup.sh",
        "        awk -F: '$3>=1000 && $3<65534 {exit 1}' \"$root/etc/passwd\"\n",
        "        awk -F: '$3>=1000 && $3<65534 && $1!=\"" + user + "\" {exit 1}' \"$root/etc/passwd\"\n",
        writes)

    print(f"desktop defaults: autologin user {user}")


if __name__ == "__main__":
    main()
