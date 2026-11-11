# Publishing packages to COPR

COPR is the planned update channel: the kernel and the Uke userland packages can
be rebuilt and published there, and the tablet can install them with `dnf`
without reflashing `boot_a` or `userdata`.

## What may be published

- `senemos-uke-kernel-mainline` and the Uke helper packages.
- Desktop integration and tools that are built from this repository.
- `uke-fedora44-oem-data` contains Xiaomi firmware and sensor blobs with
  restricted redistribution. Do **not** publish that package to a public COPR
  project; keep it in the image or use a private project.

## One-time setup

```sh
sudo dnf install copr-cli
```

Create an API token at <https://copr.fedorainfracloud.org/api/> and save it as
`~/.config/copr` (the page shows the exact file). The token is personal; never
commit it.

Create the project and its chroots:

```sh
./tools/copr-bootstrap.sh --dry-run   # print the commands
./tools/copr-bootstrap.sh --apply
```

The default project is `uke-fedora` with `fedora-44-aarch64` (tablet) and
`fedora-44-x86_64` (host tools). Adjust the chroots when the Fedora baseline
moves.

## Build and publish

```sh
make -C senemos-uke-kernel srpm
make -C uke-linux-hardware-support/uke-boot srpm
copr-cli build uke-fedora <path-to.src.rpm>
```

COPR signs the repository metadata. On the tablet:

```sh
sudo dnf copr enable <login>/uke-fedora
sudo dnf upgrade
```

A kernel update must still match the installed boot payload and the module
release; `uke-kernel-update` handles the guarded A/B path. Do not install a COPR
kernel on a tablet whose boot partition was not built for it.

## Automation

`gh workflow` can rebuild the SRPMs and call `copr-cli build` with a
`COPR_CONFIG` secret (base64 of `~/.config/copr`). Keep that workflow manual:
a broken COPR build must not block image builds. The current image workflow
(`build-image.yml`) deliberately does not publish packages.
