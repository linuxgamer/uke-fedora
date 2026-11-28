# Preview testing

## Desktop support checklist

Start from a clean install of the image you intend to qualify. Follow the [installation guide](INSTALL.md) and record the device model, profile, and checksums in `SHA256SUMS`. Use touch throughout the test and record any step that needs a keyboard, mouse, or workaround.

1. **Set up and sign in.** Complete first boot, create an account, enter a Wi-Fi password, and reach the expected session. Shut down fully, power back on, and sign in again.
2. **Use two apps.** Open the file manager and terminal from the launcher. Switch between them and close them. In a text field, check letters, numbers, symbols, backspace, and Enter. Dismiss the on-screen keyboard and bring it back.
3. **Rotate and check touch.** Turn the tablet between landscape and portrait with an app open. Check that text and controls are readable, taps land on the controls you touch, and the keyboard leaves the active field visible.
4. **Check sound and internet.** Play a short sound through the built-in speakers and change the volume. Verify HTTPS over Wi-Fi with an installed browser or `curl -I https://fedoraproject.org/`.
5. **Sleep and wake.** Suspend from the shell menu, wait about a minute, and wake the tablet. Unlock if prompted. Check that touch, typing, sound, and HTTPS still work. Separately record what a short power-button press and closing and reopening the magnetic cover do.

| Profile | Extra checks |
| --- | --- |
| Plasma Mobile | Check that it is preselected at sign-in. Use quick settings, the home gesture, and the task switcher. Check that the session resumes unlocked. Open Plasma Mobile Settings and search for a Fedora RPM in Discover. |
| Phosh | Check which session GDM selects after first-run setup, and sign into Phosh. Open the overview and quick settings, and check that Stevia appears and types into an app. Phosh locks on suspend. Check that you can unlock by touch. |
| GNOME | Sign out of Phosh, select GNOME from the GDM gear menu, and sign in with the same account. Test Activities, Quick Settings, the built-in keyboard, and display scaling. Sign back into Phosh without reflashing. |
| Desktop Plasma | Sign out of Plasma Mobile, select Plasma at login, and sign in with the same account. Check System Settings and Discover, then follow the [Plasma pre-preview test](#plasma-pre-preview-test) for power, lock, and display defaults. Sign back into Plasma Mobile without reflashing. |

For the **TTY** profile, use tty1 to set the root password and sign in using Buffyboard. Enter `echo uke` and check symbols and backspace. Shut down, power back on, and sign in with touch again. Report a USB keyboard requirement if you need one to finish.

Mark each step **Pass**, **Fail**, or **Blocked**. For a failure, record the step, what happened, and whether it repeats. Use [Uke Debug over USB](extra/USB.md#usb-capture-from-a-running-fedora-tablet) for a running session or [collect logs from recovery](INSTALL.md#recover-from-a-failed-boot) if it never reaches login.

## Plasma pre-preview test

Use a matched pair and verify both files against `SHA256SUMS`. Installation overwrites `userdata` and the slot-A boot image. Back up any data you need, confirm the recovery path before writing, and preserve slot B. Record the tablet model and image checksums with the results.

1. Complete Plasma Setup and sign in using touch alone. Check that the internal display starts at 250% scaling. The power button and lid should turn off the display, and inactivity should suspend the tablet. In Screen Locking, check that automatic locking reads **Never** and that locking after waking from sleep is off. With the display off, check touch wake.
2. Check that Wi-Fi connects and HTTPS works before and after suspend. Open Discover and confirm it lists Fedora software sources and finds an RPM application. Try LAN access after resume and record the network if it times out.
3. Connect long enough to synchronize the clock and save the PMIC anchor. Power off and boot with Wi-Fi unavailable, then compare the tablet time against a separate clock. Check that the normal boot acknowledged slot A. See [Uke Debug](extra/README.md) for collecting diagnostics.
4. Check speakers, Bluetooth, rotation, the battery widget, and hardware rendering. On an image built with the optional Iris firmware, run the [native hardware video checks](rootfs/DESKTOPS.md#native-hardware-video).
5. At Plasma Login, check scrolling and password entry, and capture the greeter's KWin renderer if it feels slow. Check double-tap wake after the screen blanks and try closing and reopening the cover. Test those separately from waking after system suspend.

The pre-preview uses the pinned Senemos kernel. On low-power USB, the battery can lose charge under load while the kernel reports Charging. The battery status patch still needs a signed kernel and a tablet test. The Focus Keyboard needs accessory testing by someone with the hardware.
