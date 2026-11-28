# Root filesystem

Start from a Fedora Everything-style base and use stock Fedora packages for hardware services such as BlueZ and UPower. Keep device-specific files in `rootfs/`. Start with one device-support RPM if those files need independent COPR updates.

DNF composes the Fedora 45 AArch64 base from [the common package list](../../rootfs/packages.txt) and the selected [profile](../../rootfs/profiles.toml). The packager adds common configuration, any profile-specific files, local firmware, and matching Senemos modules and audio data. All profiles include DNF with the COPR plugin, NetworkManager, BlueZ, and the diagnostics tools `evtest`, `lsusb`, and `ip`.

| Build profile | First login |
| --- | --- |
| `plasma` (default) | Plasma Setup creates the local account. Plasma Login Manager launches KDE Plasma. |
| `gnome` | GNOME Initial Setup creates the local account. GDM offers GNOME. |
| `kde` | Plasma Setup creates the local account. Plasma Login Manager preselects Plasma Mobile and also offers desktop Plasma. |
| `phosh-gnome` | GNOME Initial Setup creates the local account. GDM offers Phosh and GNOME, with Phosh configured as the fallback. |
| `tty` | `systemd-firstboot` prompts for a root password on tty1. Buffyboard provides touch input on the framebuffer. |

Graphical profiles use Fedora's default zram swap configuration. After boot, check it with `swapon --show`.

The packaged root account starts unprovisioned. The target initializes its machine ID on first boot. [systemd-firstboot](https://www.freedesktop.org/software/systemd/man/latest/systemd-firstboot.html)

- [Boot, power, and clock](RUNTIME.md)
- [Desktop and console defaults](DESKTOPS.md)
- [Device integration](DEVICE-INTEGRATION.md)
