# Historical Fedora Pivot Record

The project moved away from Nura/postmarketOS because its package mirrors were
impractical for the developer's environment and the project needed a directly
maintainable Fedora path. The initially proposed Fedora architecture still used
the Palawan 7.2 tree and a five-image Android boot bundle; both assumptions were
superseded.

The implemented design is ztsubaki-based Linux v6.12, stock `vendor_boot`/`dtbo`/
`vbmeta`, custom `boot` and `init_boot`, and a Fedora rootfs in `userdata`.
