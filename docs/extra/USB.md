# Diagnostics over USB

### USB capture from a running Fedora tablet

If Wi-Fi is unreachable, connect the PC and tablet directly with a data cable. From Konsole on the tablet, run `sudo python3 /usr/libexec/uke-debug-usb.py` to start a password-protected serial login for the current boot. Earlier images can use `sudo modprobe g_serial && sudo systemctl start serial-getty@ttyGS0.service`.

Install the optional host dependency with `python -m pip install pyserial`. Run the following from an interactive PC terminal with your Fedora login. `auto` selects a single USB serial gadget. You can also pass a port such as `COM3` or `/dev/ttyACM0` explicitly.

```text
python extra/uke_debug.py serial-check auto user all --output private/usb-capture.txt
```

Enter the Fedora password at the prompt. Uke Debug opens the serial login after you enter it and logs out when the capture finishes. The desktop session can stay open for KWin and PipeWire diagnostics. Run `sudo python3 /usr/libexec/uke-debug-usb.py stop` on the tablet to close the temporary login and unload the gadget. On earlier images, use `sudo systemctl stop serial-getty@ttyGS0.service && sudo modprobe -r g_serial`. [Windows USB serial support](https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/usb-driver-installation-based-on-compatible-ids)

If the tablet can still reach the router and the PC cannot connect, use the USB console to send one probe from the tablet to the PC. Replace `192.0.2.2` with the **PC's** Wi-Fi IPv4 address, then retry SSH. The probe needs a direct Wi-Fi route to the PC and runs as the Fedora user.

```text
python extra/uke_debug.py serial-lan-recover auto user 192.0.2.2
```
