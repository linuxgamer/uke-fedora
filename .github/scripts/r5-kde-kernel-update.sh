#!/usr/bin/env bash
# One-cohort host-only update. Mount only a newly decoded regular-file image.
set -Eeuo pipefail
export LC_ALL=C
repo=$(cd -- "$(dirname -- "$0")/../.." && pwd)
work=$(realpath -m "${R5_WORK:?}")
r4=$(realpath "${R4_RECEIPTS:?}")
[[ ! -e $work && $work != / && $work != "$repo" && $(uname -m) == aarch64 ]]
mkdir -p "$work"/{inputs,receipts,delivery,root}
receipts=$work/receipts
inputs=$work/inputs
root=$work/root
raw=$work/root.raw
base=senemos-uke-linux-kernel-mainline
new=7.3.1-1101
evr=7.3.1-1101.fc46
source_commit=99b0762b241c317d3c06ab921509b16b78437a0a
fingerprint=DAFC3C5A881FB49C7167EE2D6F772E3D487BD13E
copr=https://download.copr.fedorainfracloud.org/results/mcc45tr/uke-linux-test:custom:o82-variants-20261103/fedora-rawhide-aarch64/11247906-senemos-uke-linux-kernel-mainline
r4url=https://github.com/MCC45TR/uke-linux/releases/download/fedora-rawhide-uke-senemos-021126-r4
image=fedora-rawhide-kde-plasma-uke-senemos-system-031126-r5.img.zst
boot=fedora-rawhide-uke-senemos-boot-031126-r5.img
cp -R "$r4" "$receipts/r4"
manifest=$r4/images/fedora-rawhide-kde-plasma-uke-senemos-system-021126-r4.img.zst.json
jq -e '.root_raw_sha256=="93934229fa61c97530ac040002dddd9265a9b48ac10110361a20ce3bfc0e40e5" and .kernel_release=="7.3.1-1010" and .desktop=="kde" and .device_private_data_included==false' "$manifest"

# This opt-in producer must finish all package tests and signing before consumption.
for ((attempt=0; attempt<120; attempt++)); do
    curl -fLsS --retry 2 --max-time 30 https://copr.fedorainfracloud.org/api_3/build/11247906 > "$receipts/copr-build.json"
    state=$(jq -er .state "$receipts/copr-build.json")
    case $state in
        succeeded) break;;
        pending|starting|running|importing|waiting) echo "COPR 11247906: $state"; sleep 60;;
        *) echo "COPR candidate did not succeed: $state" >&2; exit 1;;
    esac
done
jq -e '.state=="succeeded" and .project_dirname=="uke-linux-test:custom:o82-variants-20261103" and .source_package.version=="7.3.1-1101" and .chroots==["fedora-rawhide-aarch64"]' "$receipts/copr-build.json"
curl -fLsS --retry 2 --max-time 30 https://download.copr.fedorainfracloud.org/results/mcc45tr/uke-linux-test/pubkey.gpg -o "$inputs/test-key.asc"
for component in '' -core -modules -dtbs -boot -singleboot; do
    curl -fLsS --retry 3 --max-time 300 "$copr/$base$component-$evr.aarch64.rpm" -o "$inputs/$base$component-$evr.aarch64.rpm"
done
curl -fLsS --retry 2 --max-time 30 https://download.copr.fedorainfracloud.org/results/mcc45tr/uke-linux-unstable/pubkey.gpg -o "$inputs/unstable-key.asc"
for component in uke-kernel-update uke-installation-profile uke-boot-integration; do
    curl -fLsS --retry 3 --max-time 300 "https://download.copr.fedorainfracloud.org/results/mcc45tr/uke-linux-unstable/fedora-rawhide-aarch64/Packages/u/$component-1.8.30-1.fc46.aarch64.rpm" -o "$inputs/$component-1.8.30-1.fc46.aarch64.rpm"
done
curl -fLsS --retry 3 --max-time 300 https://download.copr.fedorainfracloud.org/results/mcc45tr/uke-linux-unstable/fedora-rawhide-aarch64/Packages/u/uke-pipewire-plugin-libcamera-1.6.10-2.fc46.aarch64.rpm -o "$inputs/uke-pipewire-plugin-libcamera-1.6.10-2.fc46.aarch64.rpm"
for component in linux-firmware linux-firmware-whence; do
    curl -fLsS --retry 3 --max-time 300 "https://dl.fedoraproject.org/pub/fedora/linux/development/rawhide/Everything/aarch64/os/Packages/l/$component-20261019-1.fc46.noarch.rpm" -o "$inputs/$component-20261019-1.fc46.noarch.rpm"
done
cp "$repo/builder/configs/keys/fedora-46.asc" "$inputs/fedora-key.asc"
cat > "$receipts/support-RPM-SHA256SUMS" <<'HASHES'
af528aff8cccc1d7698b9d80682b51e6a0da148219e79a45343431dec64160ea  uke-kernel-update-1.8.30-1.fc46.aarch64.rpm
037b27a687c2d4c5c979c9fccbd7d12972bac65e992657e226172d714300ea81  uke-installation-profile-1.8.30-1.fc46.aarch64.rpm
7300cf7637af078af3d8fc126a392e67d7e097079792d243f19892e0defb4ada  uke-boot-integration-1.8.30-1.fc46.aarch64.rpm
HASHES
cat > "$receipts/additional-RPM-SHA256SUMS" <<'HASHES'
af5c05803ce198d10b8f9359a1d64d9e05458c8951e0d259e89f9ec945985362  uke-pipewire-plugin-libcamera-1.6.10-2.fc46.aarch64.rpm
3be523505091c31c89ad1d75ed465a09fd4c1f57203d6de8ea2173145aedeca2  linux-firmware-20261019-1.fc46.noarch.rpm
ab9814b174894d320fa0973b9b2c844931bf9a3975c77e4bdee7ef8178759a9e  linux-firmware-whence-20261019-1.fc46.noarch.rpm
HASHES
(cd "$inputs"; sha256sum -c "$receipts/support-RPM-SHA256SUMS")
(cd "$inputs"; sha256sum -c "$receipts/additional-RPM-SHA256SUMS")
(cd "$inputs"; sha256sum -- *.rpm) > "$receipts/RPM-SHA256SUMS"

# The server SDK is separate from the target root. No target package manager,
# package scriptlet, systemd service, boot writer or target executable is run.
worker=r5-kde-kernel-update:$GITHUB_RUN_ID
fedora_base=$(jq -er .fedora_rawhide_images.aarch64 "$repo/builder/configs/build-rules.json")
cat > "$work/Containerfile" <<'DOCKER'
ARG BASE_IMAGE=scratch
FROM ${BASE_IMAGE}
RUN --mount=type=secret,id=proxy_ca if [ -f /run/secrets/proxy_ca ]; then printf '\nsslcacert=/run/secrets/proxy_ca\n' >> /etc/dnf/dnf.conf; fi && dnf5 -y --setopt=install_weak_deps=False install rpm kmod cpio jq gnupg2 policycoreutils && dnf5 clean all && sed -i '/^sslcacert=\/run\/secrets\/proxy_ca$/d' /etc/dnf/dnf.conf
DOCKER
build=(docker build --build-arg "BASE_IMAGE=$fedora_base" -f "$work/Containerfile" -t "$worker")
[[ -z ${CODEX_PROXY_CERT:-} ]] || build+=(--secret "id=proxy_ca,src=$CODEX_PROXY_CERT")
"${build[@]}" "$work"
docker image inspect "$worker" --format '{{.Id}}' > "$receipts/worker-image.txt"
c++ -std=c++20 -O2 -Wall -Wextra -Werror "$repo/.github/scripts/r5-root-inventory.cpp" -lcrypto -o "$work/inventory"
c++ -std=c++20 -O2 -Wall -Wextra -Werror "$repo/builder/src/boot/boot-image.cpp" -o "$work/boot-image"
c++ -std=c++20 -O2 -Wall -Wextra -Werror "$repo/builder/src/boot-pair/android-sparse.cpp" -o "$work/android-sparse"

curl -fLsS --retry 3 --max-time 600 "$r4url/fedora-rawhide-kde-plasma-uke-senemos-system-021126-r4.img.zst" -o "$inputs/r4.img.zst"
curl -fLsS --retry 3 --max-time 300 "$r4url/fedora-rawhide-uke-senemos-boot-021126-r4.img" -o "$inputs/r4-boot.img"
printf '%s  %s\n' 92978ad81acd87127739e93f2ea7570f5516c948234546c7cefdc44cbbf51b55 r4.img.zst 74edd331899945932e78aa9916e5ed3ed581751fb7f7f6fb3422d8cbd3165b50 r4-boot.img > "$receipts/input-SHA256SUMS"
(cd "$inputs"; sha256sum -c "$receipts/input-SHA256SUMS")
zstd -dc "$inputs/r4.img.zst" > "$work/r4.sparse"
[[ $(sha256sum "$work/r4.sparse" | cut -d' ' -f1) == 68c5ca744d124eb0c99420c46576f52579abb48aa0f82ea6df6c86537f5ace4e ]]
simg2img "$work/r4.sparse" "$raw"
[[ $(stat -c %s "$raw") == 8589934592 && $(sha256sum "$raw" | cut -d' ' -f1) == 93934229fa61c97530ac040002dddd9265a9b48ac10110361a20ce3bfc0e40e5 ]]
rm "$work/r4.sparse" "$inputs/r4.img.zst"
fallocate -d "$raw"
e2fsck -fn "$raw" > "$receipts/input-fsck.txt" 2>&1
[[ $(blkid -p -s TYPE -o value "$raw") == ext4 && $(blkid -p -s LABEL -o value "$raw") == UKE_LINUX ]]
[[ -f $raw && ! -L $raw && ! -b $raw ]]
cleanup() {
    status=$?
    if mountpoint -q "$root"; then sudo umount "$root" || status=1; fi
    sudo chown -R "$(id -u):$(id -g)" "$receipts" "$work/delivery" || status=1
    exit "$status"
}
trap cleanup EXIT
sudo mount -o loop,rw,noatime,nosuid,nodev,noexec "$raw" "$root"
sudo "$work/inventory" "$root" | tee "$receipts/before.tsv" >/dev/null

cat > "$inputs/update.sh" <<'UPDATE'
#!/usr/bin/env bash
set -Eeuo pipefail
trap 'status=$?; printf "Offline update failed at line %s: %s (status %s)\n" "$LINENO" "$BASH_COMMAND" "$status" >&2; exit "$status"' ERR
export LC_ALL=C
base=senemos-uke-linux-kernel-mainline
old=7.3.1-1010
new=7.3.1-1101
evr=7.3.1-1101.fc46
kernel_archives=(/inputs/senemos-*.aarch64.rpm)
support_archives=(/inputs/uke-*-1.8.30-1.fc46.aarch64.rpm)
additional_archives=(/inputs/uke-pipewire-plugin-libcamera-1.6.10-2.fc46.aarch64.rpm /inputs/linux-firmware-20261019-1.fc46.noarch.rpm /inputs/linux-firmware-whence-20261019-1.fc46.noarch.rpm)
archives=("${kernel_archives[@]}" "${support_archives[@]}" "${additional_archives[@]}")
[[ ${#kernel_archives[@]} == 6 && ${#support_archives[@]} == 3 && ${#additional_archives[@]} == 3 && ${#archives[@]} == 12 ]]
mkdir /tmp/gpg /tmp/keydb /tmp/support-keydb /tmp/fedora-keydb
chmod 700 /tmp/gpg
[[ $(gpg --homedir /tmp/gpg --batch --show-keys --with-colons /inputs/test-key.asc | awk -F: '$1=="fpr" {print $10;exit}') == DAFC3C5A881FB49C7167EE2D6F772E3D487BD13E ]]
rpmkeys --dbpath /tmp/keydb --import /inputs/test-key.asc
for archive in "${kernel_archives[@]}"; do
    rpmkeys --dbpath /tmp/keydb --checksig "$archive" | tee -a /receipts/signatures.txt | grep -F 'signatures OK'
    [[ $(rpm -qp --qf '%{VERSION}-%{RELEASE}.%{ARCH}' "$archive") == "$evr.aarch64" ]]
done
[[ $(gpg --homedir /tmp/gpg --batch --show-keys --with-colons /inputs/unstable-key.asc | awk -F: '$1=="fpr" {print $10;exit}') == 2204A661EA630A5303500085538797E72A3E4ECA ]]
rpmkeys --dbpath /tmp/support-keydb --import /inputs/unstable-key.asc
for archive in "${support_archives[@]}"; do
    rpmkeys --dbpath /tmp/support-keydb --checksig "$archive" | tee -a /receipts/support-signatures.txt | grep -F 'signatures OK'
    [[ $(rpm -qp --qf '%{VERSION}-%{RELEASE}.%{ARCH}' "$archive") == 1.8.30-1.fc46.aarch64 ]]
done
rpmkeys --dbpath /tmp/support-keydb --checksig "${additional_archives[0]}" | tee -a /receipts/additional-signatures.txt | grep -F 'signatures OK'
[[ $(rpm -qp --qf '%{VERSION}-%{RELEASE}.%{ARCH}' "${additional_archives[0]}") == 1.6.10-2.fc46.aarch64 ]]
[[ $(gpg --homedir /tmp/gpg --batch --show-keys --with-colons /inputs/fedora-key.asc | awk -F: '$1=="fpr" {print $10;exit}') == D924B10D3E810DABDD8B56B596E7E91491211FCE ]]
rpmkeys --dbpath /tmp/fedora-keydb --import /inputs/fedora-key.asc
for archive in "${additional_archives[@]:1}"; do
    rpmkeys --dbpath /tmp/fedora-keydb --checksig "$archive" | tee -a /receipts/additional-signatures.txt | grep -F 'signatures OK'
    [[ $(rpm -qp --qf '%{VERSION}-%{RELEASE}.%{ARCH}' "$archive") == 20261019-1.fc46.noarch ]]
done
# RPM 6's payload reader consults the SDK's own keyring as well. Import the
# already fingerprint-verified public key into this disposable SDK only.
# The target root's R4 trust store remains unchanged.
rpmkeys --import /inputs/test-key.asc
rpmkeys --import /inputs/unstable-key.asc
rpmkeys --import /inputs/fedora-key.asc
mkdir /tmp/expected
for archive in "${archives[@]}"; do
    rpm2cpio "$archive" > /tmp/archive.cpio
    cpio -t --quiet < /tmp/archive.cpio > /tmp/archive.paths
    awk '/^\/|(^|\/)\.\.($|\/)/ {bad=1} END {exit bad}' /tmp/archive.paths
    (cd /tmp/expected; cpio -idm --quiet --no-absolute-filenames < /tmp/archive.cpio)
done
source /builder/src/public/cohort.sh
[[ $(cohort_repository_release /tmp/expected 7.3.1-1101) == "$new" ]]
cohort_payload_inventory "/tmp/expected/usr/lib/modules/$new" > /receipts/producer-payload.sha256
rpm -qp --qf '%{NEVRA}\t%{SOURCERPM}\t%{VENDOR}\n' "${kernel_archives[@]}" | sort > /receipts/new-kernel-rpms.tsv
rpm -qp --qf '%{NEVRA}\t%{SOURCERPM}\t%{VENDOR}\n' "${support_archives[@]}" | sort > /receipts/new-boot-support-rpms.tsv
rpm -qp --qf '%{NEVRA}\t%{SOURCERPM}\t%{VENDOR}\n' "${additional_archives[@]}" | sort > /receipts/added-dependency-rpms.tsv
rpm --root /target -qa --qf '%{NAME}\t%{NEVRA}\t%{SOURCERPM}\t%{VENDOR}\n' | sort > /receipts/rpms-before.tsv
names=()
for component in '' -core -modules -dtbs -boot -singleboot; do
    name=$base$component
    [[ $(rpm --root /target -q --qf '%{VERSION}-%{RELEASE}.%{ARCH}' "$name") == 7.3.1-1010.1.fc46.aarch64 ]]
    names+=("$name")
done
additional_names=(uke-pipewire-plugin-libcamera linux-firmware linux-firmware-whence)
for name in "${additional_names[@]}"; do
    if rpm --root /target -q "$name" >/dev/null 2>&1; then echo "Dependency unexpectedly already present: $name" >&2; exit 1; fi
done
support_names=(uke-kernel-update uke-installation-profile uke-boot-integration)
for name in "${support_names[@]}"; do
    [[ $(rpm --root /target -q --qf '%{VERSION}-%{RELEASE}.%{ARCH}' "$name") == 1.8.24-1.fc46.aarch64 ]]
    names+=("$name")
done
find /target -xdev -type d -printf '%P\n' | sort > /tmp/directories-before
sha256sum /target/etc/senemos/kernel-update.conf /target/etc/senemos/userdata-update.conf > /receipts/activation-config-before.sha256
# Save exact owned paths; directory ownership does not allow modifying children.
{ rpm --root /target -ql "${names[@]}"; rpm -qpl "${kernel_archives[@]}" "${support_archives[@]}"; } | sed 's|^/||' | sort -u > /receipts/allowed-owned-paths.txt
rpm -qpl "${additional_archives[@]}" | sed 's|^/||' | sort -u > /receipts/addition-owned-paths.txt
# Additional dependencies may add new paths, but never exempt existing R4
# files from the content/metadata preservation check (especially OEM firmware).
awk -F '\t' 'NR==FNR {before[$1]=1;next} !($0 in before)' /receipts/before.tsv /receipts/addition-owned-paths.txt > /receipts/allowed-added-paths.txt
cat /receipts/allowed-owned-paths.txt /receipts/allowed-added-paths.txt | sort -u > /receipts/allowed-mutation-paths.txt
cat /receipts/allowed-owned-paths.txt /receipts/addition-owned-paths.txt | sort -u > /receipts/all-owned-paths.txt
rpm --root /target -qa --qf '%{NEVRA}\t%{SOURCERPM}\t%{VENDOR}\n' | sort > /receipts/installed-rpms-before.tsv
cmp /receipts/r4/builds/fedora-rawhide-kde-plasma-uke-senemos-system-021126-r4/installed-rpms.tsv /receipts/installed-rpms-before.tsv
cmp /inputs/r4-boot.img "/target/usr/lib/senemos/kernel-updates/$old/userdata.img"
/inputs/boot-image extract /inputs/r4-boot.img /tmp/r4.Image
cmp /tmp/r4.Image "/target/usr/lib/modules/$old/vmlinuz"
# Independent keydb verified every archive above; preserve the target's R4 key set.
# No dependency bypass, force, scriptlets or triggers are permitted.
if ! rpm --root /target -U --test --noscripts --notriggers --nosignature "${archives[@]}" > /receipts/rpm-plan.txt 2>&1; then
    cat /receipts/rpm-plan.txt >&2
    printf '%s\n' 'The exact twelve-RPM transaction did not close. No dependency bypass or additional package update is permitted; no transaction was applied.' >&2
    exit 1
fi
rpm --root /target -Uvh --noscripts --notriggers --nosignature "${archives[@]}" > /receipts/rpm-transaction.txt 2>&1
for component in '' -core -modules -dtbs -boot -singleboot; do
    [[ $(rpm --root /target -q --qf '%{VERSION}-%{RELEASE}.%{ARCH}' "$base$component") == "$evr.aarch64" ]]
done
for name in "${support_names[@]}"; do
    [[ $(rpm --root /target -q --qf '%{VERSION}-%{RELEASE}.%{ARCH}' "$name") == 1.8.30-1.fc46.aarch64 ]]
done
[[ $(rpm --root /target -q --qf '%{VERSION}-%{RELEASE}.%{ARCH}' uke-pipewire-plugin-libcamera) == 1.6.10-2.fc46.aarch64 ]]
for name in linux-firmware linux-firmware-whence; do
    [[ $(rpm --root /target -q --qf '%{VERSION}-%{RELEASE}.%{ARCH}' "$name") == 20261019-1.fc46.noarch ]]
done
names+=("${additional_names[@]}")
sha256sum -c /receipts/activation-config-before.sha256 > /receipts/activation-config-preserved.txt
# RPM may create implicit parent directories omitted from its ownership list.
# Admit only new, real directories derived from signed package path ancestors;
# existing R4 directories and unowned files receive no additional exemption.
: > /tmp/package-ancestors
while IFS= read -r relative; do
    while [[ $relative == */* ]]; do
        relative=${relative%/*}
        [[ -n $relative && $relative != . ]] || exit 1
        printf '%s\n' "$relative" >> /tmp/package-ancestors
    done
done < /receipts/all-owned-paths.txt
sort -u /tmp/package-ancestors > /tmp/package-ancestors-sorted
: > /receipts/generated-parent-directories.txt
while IFS= read -r relative; do
    if [[ -d /target/$relative && ! -L /target/$relative ]] && ! grep -Fxq "$relative" /tmp/directories-before; then
        printf '%s\n' "$relative" >> /receipts/generated-parent-directories.txt
    fi
done < /tmp/package-ancestors-sorted
cat /receipts/allowed-mutation-paths.txt /receipts/generated-parent-directories.txt | sort -u > /tmp/mutation-paths
mv /tmp/mutation-paths /receipts/allowed-mutation-paths.txt
cat /receipts/all-owned-paths.txt /receipts/generated-parent-directories.txt | sort -u > /tmp/label-owned-paths
mv /tmp/label-owned-paths /receipts/all-owned-paths.txt
rpm --root /target -qa --qf '%{NAME}\t%{NEVRA}\t%{SOURCERPM}\t%{VENDOR}\n' | sort > /receipts/rpms-after.tsv
awk -F '\t' '$1 !~ /^senemos-uke-linux-kernel-mainline($|-)/ && $1 !~ /^(uke-(kernel-update|installation-profile|boot-integration|pipewire-plugin-libcamera)|linux-firmware|linux-firmware-whence)$/' /receipts/rpms-before.tsv > /receipts/userland-before.tsv
awk -F '\t' '$1 !~ /^senemos-uke-linux-kernel-mainline($|-)/ && $1 !~ /^(uke-(kernel-update|installation-profile|boot-integration|pipewire-plugin-libcamera)|linux-firmware|linux-firmware-whence)$/' /receipts/rpms-after.tsv > /receipts/userland-after.tsv
cmp /receipts/userland-before.tsv /receipts/userland-after.tsv
diff -u --label R4 --label R5 /receipts/rpms-before.tsv /receipts/rpms-after.tsv > /receipts/package-changes.diff || [[ $? == 1 ]]
[[ $(find /target/usr/lib/modules -mindepth 1 -maxdepth 1 -printf '%f\n') == "$new" ]]
[[ $(cat /target/usr/share/senemos/uke/$new/source-commit) == 99b0762b241c317d3c06ab921509b16b78437a0a ]]
jq -e '.kernel_release=="7.3.1-1101" and .panel_variants==["o82_36_02_0a","o82_42_02_0b"] and .touch_variants==["tianma","csot"] and .firmware_payload_included==false and .physical_acceptance==false' "/target/usr/share/senemos/uke/$new/source-composition.json"
cp "/target/usr/share/senemos/uke/$new/source-composition.json" /receipts/kernel-source-composition.json
(cd "/target/usr/lib/modules/$new"; sha256sum -c "/target/usr/lib/senemos/kernel-updates/$new/modules.sha256") > /receipts/module-hashes.txt
cohort_payload_inventory "/target/usr/lib/modules/$new" > /receipts/root-payload.sha256
cmp /receipts/producer-payload.sha256 /receipts/root-payload.sha256
# Retain producer indexes when present, or generate only this ABI's missing indexes.
if [[ ! -s /target/usr/lib/modules/$new/modules.dep.bin ]]; then depmod -b /target "$new"; fi
find "/target/usr/lib/modules/$new/kernel" -type f -name '*.ko*' -print0 | while IFS= read -r -d '' module; do
    [[ $(modinfo -F vermagic "$module") == "$new "* ]]
    [[ -n $(modinfo -F signer "$module") ]]
done
for selector in linux userdata; do
    /inputs/boot-image check-root "/target/usr/lib/senemos/kernel-updates/$new/$selector.img" "$selector"
    /inputs/boot-image extract "/target/usr/lib/senemos/kernel-updates/$new/$selector.img" "/tmp/$selector.Image"
    cmp "/tmp/$selector.Image" "/target/usr/lib/modules/$new/vmlinuz"
done
for variant in o82_36_02_0a o82_42_02_0b; do
    grep -aqF "msm_drm.dsi_display0=qcom,mdss_dsi_${variant}_dualdsi_dsc_vid" "/target/usr/lib/modules/$new/vmlinuz"
done
# Both generic supplier firmware files must already exist in R4, with kernel-pinned bytes.
printf '%s  %s\n' a4f949fb89c7eaad9da85a5885cd2dcc1fffbf08bc1e7ffe9f0bb97c1769b310 /target/usr/lib/firmware/qcom/uke/touch/csot/normal.bin 12ce2693b965a35e3469984fd95afebb4c0a740ca908159b0a5e6bdad5968619 /target/usr/lib/firmware/qcom/uke/touch/tm/normal.bin | sha256sum -c - > /receipts/touch-firmware.txt
[[ $(awk '$1 !~ /^#/ && $2=="/" {print $1 " " $3}' /target/etc/fstab) == 'PARTLABEL=userdata ext4' ]]
grep -Fxq automatic=0 /target/etc/senemos/kernel-update.conf
# Label only the changed kernel subtrees, owned nondirectories and RPM database.
# Shared directory ownership never permits recursively relabeling userland.
# Use the unchanged R4 text policy, avoiding compiled PCRE cache ABI differences
# between the disposable SDK and R4. No target policy/cache file is modified.
mkdir /tmp/label-policy
for suffix in '' .local .homedirs .subs .subs_dist; do
    candidate=/target/etc/selinux/targeted/contexts/files/file_contexts$suffix
    if [[ -f $candidate && ! -L $candidate ]]; then cp "$candidate" "/tmp/label-policy/file_contexts$suffix"; fi
done
contexts=/tmp/label-policy/file_contexts
label_roots=("/target/usr/lib/modules/$new" "/target/usr/lib/senemos/kernel-updates/$new" "/target/usr/share/senemos/uke/$new" /target/usr/lib/sysimage/rpm)
for candidate in "/target/usr/lib/firmware/$new" "/target/usr/share/licenses/$base-boot-$evr"; do
    [[ ! -d $candidate ]] || label_roots+=("$candidate")
done
while IFS= read -r relative; do
    candidate=/target/$relative
    if [[ -d $candidate && ! -L $candidate ]] && ! grep -Fxq "$relative" /tmp/directories-before; then
        label_roots+=("$candidate")
    fi
done < /receipts/all-owned-paths.txt
setfiles -F -m -r /target "$contexts" "${label_roots[@]}"
: > /tmp/label-paths
while IFS= read -r relative; do
    candidate=/target/$relative
    if [[ ! -d $candidate && ( -e $candidate || -L $candidate ) ]]; then printf '%s\n' "$candidate" >> /tmp/label-paths; fi
done < /receipts/all-owned-paths.txt
setfiles -F -m -r /target -f /tmp/label-paths "$contexts"
rpm --root /target -V "${names[@]}" > /receipts/kernel-rpm-verify.txt || {
    # Image-owned config overrides must be unchanged according to the whole-root diff.
    awk '$2!="c" || ($3!="/etc/senemos/kernel-update.conf" && $3!="/etc/senemos/userdata-update.conf") {bad=1} END {exit bad}' /receipts/kernel-rpm-verify.txt
}
UPDATE
chmod 755 "$inputs/update.sh"
cp "$work/boot-image" "$inputs/boot-image"
# security.selinux xattrs need SYS_ADMIN on a host without the SELinux LSM.
# Only this disposable regular-file image is writable; no host device is passed.
docker run --rm --network=none --cap-add SYS_ADMIN \
    --mount "type=bind,src=$inputs,dst=/inputs,readonly" \
    --mount "type=bind,src=$root,dst=/target" \
    --mount "type=bind,src=$receipts,dst=/receipts" \
    --mount "type=bind,src=$repo/builder,dst=/builder,readonly" \
    "$worker" bash /inputs/update.sh
sudo "$work/inventory" "$root" | tee "$receipts/after.tsv" >/dev/null
# Kernel/boot-support owned exact paths, ABI subtrees and the RPM database are
# the complete mutation boundary. Directory ownership never exempts descendants.
diff -u --label R4 --label R5 "$receipts/before.tsv" "$receipts/after.tsv" > "$receipts/all-file-changes.diff" || [[ $? == 1 ]]
filter_inventory() {
    awk -F '\t' 'NR==FNR {owned[$0]=1;next}
      !owned[$1] && $1 !~ /^usr\/lib\/modules\/7[.]3[.]1-(1010|1101)(\/|$)/ &&
      $1 !~ /^usr\/lib\/sysimage\/rpm(\/|$)/ && $1 !~ /^var\/lib\/rpm\// {print}' "$receipts/allowed-mutation-paths.txt" "$1"
}
filter_inventory "$receipts/before.tsv" > "$receipts/unchanged-before.tsv"
filter_inventory "$receipts/after.tsv" > "$receipts/unchanged-after.tsv"
diff -u --label R4 --label R5 "$receipts/unchanged-before.tsv" "$receipts/unchanged-after.tsv" > "$receipts/userland-diff.txt"
# Full new payload independently matches the signed RPM archives, including DTs.
cp "$root/usr/lib/senemos/kernel-updates/$new/userdata.img" "$work/delivery/$boot"
"$work/boot-image" inspect "$work/delivery/$boot" > "$receipts/boot-header.json"
"$work/boot-image" inspect "$inputs/r4-boot.img" > "$receipts/r4-boot-header.json"
cmp <(jq -S 'del(.kernel_bytes,.payload_end)' "$receipts/r4-boot-header.json") <(jq -S 'del(.kernel_bytes,.payload_end)' "$receipts/boot-header.json")
"$work/boot-image" check-root "$work/delivery/$boot" userdata
"$work/boot-image" extract "$work/delivery/$boot" "$work/delivered.Image"
cmp "$work/delivered.Image" "$root/usr/lib/modules/$new/vmlinuz"
(cd "$root/usr/lib/modules/$new"; sha256sum dtb/qcom/sm7675-xiaomi-uke.dtb) > "$receipts/dtb.sha256"
sudo umount "$root"
e2fsck -fn "$raw" > "$receipts/output-fsck.txt" 2>&1
raw_hash=$(sha256sum "$raw" | cut -d' ' -f1)
"$work/android-sparse" encode "$raw" "$work/r5.sparse"
# Decode with the independent original AOSP tool and compare every raw byte.
simg2img "$work/r5.sparse" "$work/readback.raw"
cmp "$raw" "$work/readback.raw"
e2fsck -fn "$work/readback.raw" > "$receipts/serialized-fsck.txt" 2>&1
rm "$work/readback.raw"
sparse_hash=$(sha256sum "$work/r5.sparse" | cut -d' ' -f1)
zstd -T2 -8 --check "$work/r5.sparse" -o "$work/delivery/$image"
zstd --test "$work/delivery/$image"
[[ $(zstd -dc "$work/delivery/$image" | sha256sum | cut -d' ' -f1) == "$sparse_hash" ]]
(cd "$work/delivery"; sha256sum "$image" "$boot" > SHA256SUMS)
cp "$work/delivery/SHA256SUMS" "$receipts/SHA256SUMS"
cp "$repo/.github/testing/R5-KDE-1101.md" "$work/delivery/INSTALL.md"
jq -n --arg raw "$raw_hash" --arg sparse "$sparse_hash" --arg source "$source_commit" --arg signer "$fingerprint" --arg run "$GITHUB_RUN_ID" --arg workflow "$GITHUB_SHA" \
    '{date:"2026-11-03",revision:"r5",desktop:"kde",origin:"verified R4 published KDE and shared boot",r4_run:"41430801872",r4_system_sha256:"92978ad81acd87127739e93f2ea7570f5516c948234546c7cefdc44cbbf51b55",r4_boot_sha256:"74edd331899945932e78aa9916e5ed3ed581751fb7f7f6fb3422d8cbd3165b50",kernel_release:"7.3.1-1101",kernel_rpm_version_release:"7.3.1-1101.fc46",kernel_source_commit:$source,kernel_copr_build:11247906,signer_fingerprint:$signer,boot_support_version_release:"1.8.30-1.fc46",boot_support_packages:["uke-kernel-update","uke-installation-profile","uke-boot-integration"],boot_support_signer_fingerprint:"2204A661EA630A5303500085538797E72A3E4ECA",changed_package_count:12,upgraded_package_count:9,added_package_count:3,added_dependencies:["uke-pipewire-plugin-libcamera-1.6.10-2.fc46.aarch64","linux-firmware-20261019-1.fc46.noarch","linux-firmware-whence-20261019-1.fc46.noarch"],fedora_signer_fingerprint:"D924B10D3E810DABDD8B56B596E7E91491211FCE",dependency_check_passed:true,root_raw_bytes:8589934592,root_raw_sha256:$raw,root_sparse_sha256:$sparse,unrelated_r4_userland_preserved:true,generic_oem_firmware_preserved:true,kernel_owned_topology_updated:true,out_of_scope_content_and_metadata_compared:true,automatic_activation_config_preserved:true,rpm_scriptlets_executed:false,target_programs_executed:false,aosp_decoder_roundtrip:true,physical_boot_tested:false,hardware_tested:false,rollback_tested:false,github_release_created:false,artifact_retention_days:90,workflow_run:$run,workflow_commit:$workflow}' > "$receipts/result.json"
cp "$receipts/result.json" "$work/delivery/PROVENANCE.json"
cat "$work/delivery/SHA256SUMS" >> "$GITHUB_STEP_SUMMARY"
echo 'R4-derived R5 KDE + matching signed 1101 userdata boot: all host checks passed. Physical testing remains pending. No Release was created.' >> "$GITHUB_STEP_SUMMARY"
