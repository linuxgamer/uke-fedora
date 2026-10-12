# Software dependencies

## Fedora uses normal Fedora packages

Python is allowed. Use Fedora's normal libraries and dependencies rather than
rebuilding GNU/GLib packages only to remove Python.

The hardware-support layer is desktop-independent. GNOME, Plasma and Xfce are
optional selections made by the builder. Themes and the Plasma settings addon
are optional too.

The old no-Python runtime forks are archived, not the default implementation.
Some older core/UEFI build paths still refer to them and remain blocked; the new
console-rootfs route does not make those older paths current.

## Recovery is a separate environment

Recovery needs a small, tested runtime of its own. Allowing Python in Fedora
does not mean copying the whole Fedora root into a recovery ramdisk.

The owner installer bundles matching ARM64 GNU tools and their libraries.
It uses the installed Fedora Python only to verify the completed rootfs.

## Packages and manifests must tell the truth

Check signatures, release identity, ownership, capabilities and payloads.
Do not bypass signatures to make a build succeed.

New manifests describe actual payload/runtime checks. Older manifests may
retain historical no-Python results; do not rewrite them as new acceptance.

## Development access is not production security

The current candidate deliberately offers an unauthenticated USB ACM root shell
when `senemos.debug=cdc-acm` is present. Root password login is locked and SSH is
masked. SELinux is permissive in this candidate, with first-boot relabel still
unqualified. These are development choices, not a secure release configuration.

Private inputs, signing keys, device identifiers, backups and build outputs
must stay out of public commits.
