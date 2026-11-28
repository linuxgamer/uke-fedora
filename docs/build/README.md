# Build the images

Use a Fedora Linux build host or a Fedora distro under WSL2. In WSL2, put the checkout on the Linux filesystem so the builder can preserve Linux metadata and use hard links for staging. Use Python 3.12 or newer and build as root.

```sh
sudo dnf5 install git-core python3 dnf5 rpm systemd e2fsprogs libselinux android-tools
git submodule update --init --recursive --depth 1
```

On x86_64, also install `qemu-user-static-aarch64` for RPM scriptlets and the chroot check. Check that `/proc/sys/fs/binfmt_misc/qemu-aarch64` exists and reports `enabled`.

If DNF times out fetching Fedora mirror lists on WSL2, try adding `ip_resolve=4` under `[main]` in the distro's `/etc/dnf/dnf.conf`. This resolved the timeouts on the Fedora 45 test instance.

Run from the checkout with these three inputs.

```sh
sudo python3 build/build.py \
  --senemos-rpm /path/to/senemos-uke-linux-kernel-mainline-core-7.3.5-47.fc46.aarch64.rpm \
  --stock-boot build/inputs/local/boot.img \
  --firmware-zip build/inputs/local/console-firmware.zip
```

- [Build inputs](INPUTS.md)
- [Build cache and disk use](CACHE.md)
