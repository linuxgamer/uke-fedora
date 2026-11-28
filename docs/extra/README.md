# Uke Debug

Uke Debug is a desktop GUI for the running Fedora port. It uses Python with Tk and the host's OpenSSH client. On Windows, open `extra/Uke Debug.pyw` or run `python extra/uke_debug.py` from the checkout. On Linux, run `python3 extra/uke_debug.py`. The tablet needs Python 3 and an SSH server.

## Connect

Connect both devices to a trusted network that allows clients to reach each other. On the tablet, run these commands in Konsole or another terminal with your Fedora account. [Fedora OpenSSH server package](https://packages.fedoraproject.org/pkgs/openssh/openssh-server/)

```sh
sudo dnf install openssh-server
sudo systemctl start sshd
whoami
ip -4 -br address
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Enter `username@address` in Uke Debug and leave port 22 unless you configured another port. OpenSSH can use a key you already authorized. Otherwise, click **Authorize key…** to create a dedicated host key under `~/.ssh/uke-debug-ed25519` and add its public key to the tablet account. Compare the SSH host fingerprint with the tablet before accepting it, then enter the Fedora password in the native terminal. Click **Connect** after authorization succeeds. Use **Open shell** for a full interactive session.

If the connection times out, confirm the tablet is awake and check its Wi-Fi address again. Try a different access point or a password-protected PC hotspot if the tablet can reach its router but the PC cannot reach the tablet. `systemctl is-enabled sshd` shows whether Fedora will start SSH at boot. Use `sudo systemctl disable --now sshd` to stop it and turn off startup.

## Run checks

- **All checks** collects boot and storage state, GPU and display diagnostics, input devices, networking and USB, IIO sensors, audio routes, camera and video nodes, and power and clock readings. Individual categories are available from the menu. Missing optional utilities or blocked journal access are reported in the output.
- **Hardware checklist** lists the 73 hardware rows from the upstream Fedora README, including experimental and disabled features. Select a row for test instructions and click **Collect evidence** for its diagnostic group. Record a result and observation in the checklist. **Not tested** is the default. Use **Blocked** when the test needs an accessory, tool, or setup you do not have. [Upstream hardware tables](https://github.com/MCC45TR/uke-linux/blob/e6725304b4e40001705f043952e5db099a440b39/README.md#hardware-support)
- **Play test tone** sends a short tone to the tablet's current default PipeWire output. Record whether you heard it in the matching audio checklist row.
- **Save report…** saves the checklist results, observations, collected diagnostics, and tester notes as a local text file. Save before closing the app. Review the report before sharing.

Sign in on the tablet with the same Fedora account used for SSH before capturing desktop rendering or audio routes. Keep the display awake for brightness measurements. Hardware that enumerates can still fail its functional test. Follow the checklist instructions for physical actions such as plugging in a dock, rotating the tablet, or rebooting. The harness leaves those actions to the tester.

Live stats use signed battery current when the Uke gauge reports Charging while the battery is supplying more than 100 mA. The power diagnostics include the firmware status, USB input limit, and battery charge counter.

With one tablet in TWRP and Android Platform Tools on the host, **TWRP shell** opens its USB shell. **Pull TWRP logs…** copies the Fedora journal and pstore into a local folder after TWRP mounts `userdata` at `/data`. It needs no SSH connection.

- [Diagnostics over USB](USB.md)
- [Uke Debug command line](CLI.md)
