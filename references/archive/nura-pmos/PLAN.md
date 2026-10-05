# Historical Nura/postmarketOS Plan

The original plan targeted Nura/postmarketOS using `pmbootstrap`, a custom
Palawan 7.2 kernel package, and a new `uke` board DTS. It proposed a sequence of
offline source collection, simplefb first-light, Nura initramfs/rootfs bring-up,
then device support for display, touch, USB, Wi-Fi, audio, sensors, and GPU.

The project no longer uses this plan. Fedora on ztsubaki Linux v6.12 is the
working boot path, and the Palawan tree is archived under `../palawan-7.2/`.
