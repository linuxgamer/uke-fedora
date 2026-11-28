# Install Fedora on your tablet

You’ll download one ZIP on your computer and use a USB data cable to install it. **Installation replaces Android and erases the tablet’s apps and files.** You need an unlocked bootloader and a way to restore Android before starting.

## 1. Back up and check your tablet

1. Check the model in Android under **Settings → About tablet**. The image targets Xiaomi Pad 7 and POCO Pad X1. Hardware testing so far is on Xiaomi Pad 7. Check the [hardware support table](../README.md#hardware-support), especially if you need the cameras.
2. Copy your photos, files, and authenticator recovery codes to another device. Open a few files there to check your backup. Unlocking the bootloader can also erase data.
3. Save Xiaomi’s factory Android download, called a **fastboot ROM**, for your exact model and region. It lets you reinstall Android. Keep a version at least as recent as the firmware on your tablet. Try entering your recovery environment before writing anything. If you already use TWRP on slot B, check that it opens. [Xiaomi ROM download guide](https://new.c.mi.com/global/post/101089) · [Xiaomi flashing instructions](https://new.c.mi.com/global/miuidownload/detail/guide/global/global/miuidownload/index)

The bootloader is the part that starts Android or Fedora. If it is locked, use Xiaomi’s official unlock process before continuing. On supported devices, pair your Xiaomi account in **Settings → Developer options → Mi Unlock status**, then use Xiaomi’s Mi Unlock tool on a Windows PC. Check Xiaomi’s current requirements for your model, account, and region. [Xiaomi’s bootloader guide](https://www.mi.com/global/support/faq/details/KA-07238/)

The build uses firmware from Global HyperOS `OS3.0.304.0.WOZMIXM` on Xiaomi Pad 7. Use the compatibility notes for the image you downloaded and the matching Android recovery ROM for your tablet.

## 2. Download Fedora and open a terminal

1. Open **Release 2** and expand **Assets**. Choose the **KDE** ZIP for Plasma Mobile and Plasma, or **Phosh + GNOME** for Phosh and GNOME. [Release 2 downloads](https://github.com/linuxgamer/uke-fedora/releases/tag/r2)
2. Extract the ZIP and open the folder containing `boot.img`, `userdata.img`, `manifest.json`, and `SHA256SUMS`. Keep the four files together.
3. Download and extract **Android SDK Platform-Tools** for your computer. This is Google’s download containing `fastboot`, the tool that sends the install files to your tablet over USB. [Platform-Tools downloads](https://developer.android.com/tools/releases/platform-tools#downloads)

**Windows 11.** In File Explorer, put the extracted `platform-tools` folder directly inside **Downloads**. In the Fedora image folder, right-click a blank area and choose **Open in Terminal**. Use the PowerShell tab and paste these two lines.

```powershell
$env:Path = "$HOME\Downloads\platform-tools;$env:Path"
fastboot --version
```

**Linux.** Open a terminal in the Fedora image folder. Add the extracted `platform-tools` directory to your shell’s `PATH` and run `fastboot --version`.

Keep this terminal open for the rest of the guide. If you see a version number, it can find Fastboot. If Windows says it can’t find `fastboot`, check that `fastboot.exe` is inside **Downloads → platform-tools**.

## Verify the image pair

This check catches damaged downloads and files mixed from different builds. On Linux, run `sha256sum -c SHA256SUMS`. On Windows, paste the whole block into the PowerShell terminal you just opened. It checks the files for you.

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

## 3. Check the tablet before installing

Charge the tablet and power it off. Hold **Volume Down** and **Power** until you see the fastboot screen. Connect it to the computer with a USB data cable and run the following checks one at a time.

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

| Check | What you should see |
| --- | --- |
| `devices` | One line for your tablet. If the list is empty, try a different USB data cable or port. |
| `product` | `uke` |
| `unlocked` | `yes` |
| `is-userspace` and `is-logical:userdata` | `no` for both |
| `current-slot` | Save the reported slot for your recovery notes. |
| `partition-size:boot_a` | At least **96 MiB**, shown as `0x6000000` in Fastboot. |
| `partition-size:userdata` | At least **4 GiB** for either Release 2 image, shown as `0x100000000`. |

Stop if the checks fail. For other builds, the file `manifest.json` gives the required space in `userdata_logical_bytes`. On Windows, `[Convert]::ToInt64('6000000', 16)` converts Fastboot’s numbers to bytes. Replace the sample digits with the digits after `0x`.

## 4. Install Fedora

**This step erases the tablet’s apps and files.** Run each command separately and wait for it to succeed. If a write fails, stop and save the error before changing the active slot or rebooting. The commands write the boot image to slot A and preserve slot B for recovery.

```text
fastboot flash userdata userdata.img
fastboot flash boot_a boot.img
fastboot set_active a
fastboot reboot
```

Follow the setup screens to create an account. Connect to Wi-Fi once to set the clock. To switch between mobile and desktop, sign out and choose a session on the login screen. On Phosh + GNOME, select your account first to reveal the gear menu. Both sessions use the same account and files. [First-login details](rootfs/README.md)

## Recover from a failed boot

Record the last message or take a photo. If you previously verified TWRP on slot B, return to bootloader fastboot and run `fastboot set_active b` followed by `fastboot reboot recovery`. Use [Uke Debug](extra/README.md) to collect the Fedora journal if TWRP can mount it. Follow the [bug report guide](../.github/ISSUE_TEMPLATE/bug_report.md) and include the image profile and checksum.

To retry a verified Fedora installation, return to bootloader fastboot and use `fastboot set_active a` followed by `fastboot reboot`. Reflashing `userdata` erases your Fedora files.

## Return to Android

Back up any Fedora files you want to keep. Use the **clean install** option in Xiaomi’s flashing tool or the clean-install script supplied with the full stock fastboot ROM for your exact tablet model and region. Choose the option that leaves the bootloader unlocked. The stock install wipes `userdata` again. Restore your separate Android backup after it boots. Slot B can get you to recovery, but it cannot restore Android’s erased data. [Xiaomi flashing instructions](https://new.c.mi.com/global/miuidownload/detail/guide/global/global/miuidownload/index)
