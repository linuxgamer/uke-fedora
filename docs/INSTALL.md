# Install the Fedora preview on a Uke tablet

Both preview images include a mobile mode and a desktop mode. Check the [profile and hardware status](BRINGUP.md#preview-status) to see which sessions have been tested on your model.

| Image | Mobile mode | Desktop mode |
| --- | --- | --- |
| `kde` | Plasma Mobile | Plasma |
| `phosh-gnome` | Phosh | GNOME |

After setup, sign out and use the login screen’s session menu to switch modes on the same installation. On the Phosh and GNOME image, select your account to reveal the gear menu, then choose **Phosh** or **GNOME** before signing in. Both modes use the same account and files.

**Installing replaces everything in `userdata`, including Android apps, files, and any existing Fedora installation.** It also replaces the boot image in slot A. The commands below preserve slot B.

## Before you start

1. Back up your files, authenticator recovery codes, and anything else you need to a separate device. Check that you can open the backup.
2. Save the full stock **fastboot ROM** for your exact tablet model and region. Keep a copy at least as recent as the firmware already on the tablet. Use the [Xiaomi ROM download guide](https://new.c.mi.com/global/post/101089) and [Xiaomi flashing instructions](https://new.c.mi.com/global/miuidownload/detail/guide/global/global/miuidownload/index).
3. Confirm that the bootloader is unlocked and that you can enter your recovery environment. If you already have working TWRP on slot B, check it now. Check the eligibility for your model and region with [Xiaomi’s bootloader guidance](https://www.mi.com/global/support/faq/details/KA-07238/).
4. Download and extract [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools) on the computer you’ll use to flash. Use a data cable and keep the tablet charged. Open a terminal in the folder containing the image pair.

In Windows PowerShell, if you extracted the tools under Downloads, run `$env:Path = "$HOME\Downloads\platform-tools;$env:Path"` in that terminal. On Linux, add the extracted tools directory to your shell’s `PATH`. Check that the terminal can find the tool with `fastboot --version`.

The reviewed input firmware is Global HyperOS `OS3.0.304.0.WOZMIXM` on Xiaomi Pad 7. Follow the compatibility notes for the image you are testing. The POCO edition needs its own matching stock recovery ROM.

## Verify the image pair

Keep `boot.img`, `userdata.img`, `manifest.json`, and `SHA256SUMS` together from the same build. On Linux, run `sha256sum -c SHA256SUMS`. On Windows, run these PowerShell commands from the image folder.

```powershell
$manifest = Get-Content .\manifest.json -Raw | ConvertFrom-Json
foreach ($part in @('boot_a', 'userdata')) {
    $image = $manifest.images.$part
    $hash = (Get-FileHash -LiteralPath $image.filename -Algorithm SHA256 -ErrorAction Stop).Hash
    if ($hash -ne $image.sha256) { throw "Checksum mismatch for $($image.filename)" }
    "$($image.filename) verified"
}
```

Both files must pass. For local builds, follow the [build guide](build/README.md) to generate the pair.

## Check the tablet in bootloader fastboot

Power off the tablet. Hold Volume Down and Power to open the fastboot screen. Connect it to the computer and run these commands one at a time.

```text
fastboot devices
fastboot getvar product
fastboot getvar unlocked
fastboot getvar is-userspace
fastboot getvar current-slot
fastboot getvar partition-size:boot_a
fastboot getvar partition-size:userdata
fastboot getvar is-logical:userdata
```

Continue when exactly one intended tablet is connected, the product is `uke`, the bootloader is unlocked, and both `is-userspace` and `is-logical:userdata` say `no`. Save the current slot for your recovery notes.

The minimum boot partition size is **96 MiB** (`0x6000000`). The minimum userdata size is **4 GiB** (`0x100000000`) for graphical builds or **2 GiB** (`0x80000000`) for TTY. Compare against `userdata_logical_bytes` in the manifest; the sparse file on disk is smaller. To convert a hex value in PowerShell, use `[Convert]::ToInt64('6000000', 16)`, replacing the digits with the value fastboot reported after `0x`.

## Flash the image pair

Run each command separately. Wait for it to succeed before continuing. If a flash fails, stop and save the error before switching slots or rebooting.

```text
fastboot flash userdata userdata.img
fastboot flash boot_a boot.img
fastboot set_active a
fastboot reboot
```

Create your own account and password using the [first-login instructions for your profile](rootfs/README.md). Connect to Wi-Fi once to set the correct date. A new installation saves a clock sample after its first successful network sync, then can restore time offline on later boots. Follow the [desktop support checklist](TESTING.md#desktop-support-checklist) and keep a USB keyboard handy as a fallback for the TTY test.

## Recover from a failed boot

Record the last message or take a photo. If you previously verified TWRP on slot B, return to bootloader fastboot and run `fastboot set_active b` followed by `fastboot reboot recovery`. Use [Uke Debug](extra/README.md) to collect the Fedora journal if TWRP can mount it. Follow the [bug report guide](../.github/ISSUE_TEMPLATE/bug_report.md) and include the image profile and checksum.

To retry a verified Fedora installation, return to bootloader fastboot and use `fastboot set_active a` followed by `fastboot reboot`. Reflashing `userdata` erases your Fedora files.

## Return to Android

Back up any Fedora files you want to keep. Use the **clean install** option in Xiaomi’s flashing tool or the clean-install script supplied with the full stock fastboot ROM for your exact tablet model and region. Choose the option that leaves the bootloader unlocked. The stock install wipes `userdata` again. Restore your separate Android backup after it boots. Slot B can get you to recovery, but it cannot restore Android’s erased data. [Xiaomi flashing instructions](https://new.c.mi.com/global/miuidownload/detail/guide/global/global/miuidownload/index)
