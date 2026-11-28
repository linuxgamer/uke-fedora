# Preview status and release plan

The rewrite is preparing a **multi-desktop preview led by Plasma Mobile and Phosh**. Advertise preview support for each profile and device combination after it passes the hardware checklist below. Keep the [legacy releases](https://github.com/linuxgamer/uke-fedora/releases) available during the transition.

## Preview status

| Profile | Test status | Next hardware check |
| --- | --- | --- |
| **Plasma Mobile and desktop Plasma** | The `kde` image has both sessions. Tablet testing started in Plasma Mobile. An earlier desktop-only build passed setup, login, and cold boot on Xiaomi Pad 7. | Qualify both sessions on the same release image. |
| **Phosh and GNOME** | The `phosh-gnome` image includes both sessions. Tablet testing is pending. | Complete touch-only setup and qualify both sessions on the same image. |
| TTY | Host-verified Fedora 45 image with Buffyboard. | Check password setup and console typing using touch on the tablet. |

The POCO Pad X1 shares the `uke` target. The hardware results here are from the Xiaomi Pad 7.

- **Verified in Plasma.** Hardware rendering, internal audio, Bluetooth, rotation, cover input, suspend-to-idle, automatic slot A acknowledgement, ext4 growth, and zram have live evidence. The PMIC restored time during an offline cold boot after the initial network sync. An earlier test verified native hardware video with the optional Iris firmware.
- **Known issues.** LAN access from the PC can time out after idle on the tested access point. HTTPS worked after suspend, and an intermittent HTTPS and PackageKit timeout recovered on retry. The battery can discharge while connected to low-power USB even when the kernel reports Charging.
- **Hardware still to qualify.** Focus Keyboard, stylus, docks, external displays, and the POCO variant have pending tests. Camera capture and offline charging remain outside this preview.

## Bring-up scope

- Use the old `uke-fedora` and MCC45TR's `uke-linux` checkouts only as code references. A tester reports success with `uke-fedora` R1 and newer commits. Record the exact build and device configuration when available.
- Rewrite the port around Senemos. The kernel source is pinned under `kernel/senemos/`. Keep port-specific kernel integration in `ukelinux` and evaluate legacy kernel fixes individually.
- Target Xiaomi Pad 7 and POCO Pad X1 with one `uke` image.
- Install Fedora in `userdata` and boot from slot A. This wipes Android user data. Leave dual boot outside the initial scope and document how to return to stock.
- Include a desktop in the first tablet candidate. Defer stable release planning until the image builds and boots reliably.

## First rewrite release

1. Review firmware redistribution terms before publishing images. Keep restricted blobs out of public artifacts.
2. Verify the exact release pair from a clean checkout using the documented inputs. Run the [installation and recovery steps](INSTALL.md) on the test device, including a return to the matching stock ROM before declaring that path tested.
3. Qualify Plasma Mobile and Phosh first. Ship one KDE image (`kde`) and one Phosh and GNOME image (`phosh-gnome`) after their respective sessions pass on hardware. Keep images with pending checks labeled as test builds.
4. List the known LAN timeout and escalate it if basic internet access, updates, or Wi-Fi reconnect after resume fail, or if the peer timeout reproduces on another network.

- [Preview testing](TESTING.md)
- [Remaining feature parity](PARITY.md)

## Component docs

- [Build and firmware inputs](build/README.md)
- [Kernel source and updates](kernel/README.md)
- [Root filesystem](rootfs/README.md)
