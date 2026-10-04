%define flavor uke
%define debug_package %{nil}
%define kversion 7.2.0-rc2

Name:           linux-%{flavor}
Version:        7.2.0
Release:        0.1.rc2%{?dist}
Summary:        Mainline Linux kernel for Xiaomi Pad 7 (uke, SM7675)
License:        GPL-2.0-only
URL:            https://codeberg.org/palawan-mainline/linux
BuildArch:      aarch64
ExclusiveArch:  aarch64
Provides:       kernel-uname-r
AutoReqProv:    no

Source0:        linux-prepared.tar.gz

%description
Mainline 7.2-rc2 (palawan-mainline fork) + uke-специфика: board-DTS SM7675,
драйвер панели O82 (dual-DSI DSC), драйвер тача Novatek NT36532, фиксы базы.
uname: %{kversion}-%{flavor}.

%prep
%setup -q -n linux-prepared

%build
unset LDFLAGS
make ARCH=arm64 LLVM=1 LOCALVERSION=-%{flavor} %{?_smp_mflags} \
     KBUILD_BUILD_VERSION="%{release}.%{flavor}"

%install
krel=$(make ARCH=arm64 LLVM=1 LOCALVERSION=-%{flavor} kernelrelease)
make ARCH=arm64 LLVM=1 LOCALVERSION=-%{flavor} \
     modules_install dtbs_install \
     INSTALL_MOD_PATH=%{buildroot}/usr \
     INSTALL_DTBS_PATH=%{buildroot}/boot/dtbs-%{krel} \
     INSTALL_MOD_STRIP=1
install -Dm0644 arch/arm64/boot/Image %{buildroot}/boot/vmlinuz-$krel
install -Dm0644 System.map %{buildroot}/boot/System.map-$krel
depmod -b %{buildroot}/usr -a %{krel}
rm -f %{buildroot}/usr/lib/modules/*/build %{buildroot}/usr/lib/modules/*/source

%files
%license COPYING
/boot/*
/usr/lib/modules/*

%changelog
* Sun Oct 04 2026 linuxgamer <stastera2@gmail.com> - 7.2.0-0.1.rc2
- Initial RPM packaging for the uke Fedora port.
