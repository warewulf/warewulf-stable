%global debug_package %{nil}

%global api 0

%if 0%{?suse_version}
%global tftpdir /srv/tftpboot
%else
# Assume Fedora-based OS if not SUSE-based
%global tftpdir /var/lib/tftpboot
%endif
%global srvdir %{_sharedstatedir}

%global wwgroup warewulf

%if 0%{?fedora}
%define _build_id_links none
%endif


Name: warewulf
Summary: A provisioning system for large clusters of bare metal and/or virtual systems
Version: 4.6.0rc2
Release: 1%{?dist}
License: BSD-3-Clause
URL:     https://github.com/warewulf/warewulf
Source:  https://github.com/warewulf/warewulf/releases/download/v%{version}/%{name}-%{version}.tar.gz

ExclusiveOS: linux

Conflicts: warewulf < 4
Conflicts: warewulf-common
Conflicts: warewulf-cluster
Conflicts: warewulf-vnfs
Conflicts: warewulf-provision
Conflicts: warewulf-ipmi

%if 0%{?suse_version} || 0%{?sle_version}
#!BuildIgnore: brp-check-suse
BuildRequires: distribution-release
BuildRequires: systemd-rpm-macros
BuildRequires: go >= 1.16
BuildRequires: firewall-macros
BuildRequires: firewalld
BuildRequires: tftp
BuildRequires: yq
Requires: tftp
Requires: nfs-kernel-server
Requires: firewalld
Requires: ipxe-bootimgs
%else
# Assume Red Hat/Fedora build
BuildRequires: system-release
BuildRequires: systemd
BuildRequires: golang >= 1.16
BuildRequires: firewalld-filesystem
Requires: tftp-server
Requires: nfs-utils
%if 0%{?rhel} < 8
Requires: ipxe-bootimgs
%else
Requires: ipxe-bootimgs-x86
Requires: ipxe-bootimgs-aarch64
%endif
%endif

%if 0%{?rhel} >= 8 || 0%{?suse_version} || 0%{?fedora}
Requires: dhcp-server
%else
# rhel < 8
Requires: dhcp
%endif

BuildRequires: git
BuildRequires: make
BuildRequires: gpgme-devel
%if %{api}
BuildRequires: libassuan-devel
%endif

Recommends: logrotate
Recommends: ipmitool

%description
Warewulf is a stateless and diskless provisioning
system for large clusters of bare metal and/or virtual systems.

%package dracut
Summary: A dracut module for loading a Warewulf image
BuildArch: noarch

BuildRequires: dracut
Requires: dracut
%if 0%{?suse_version}
%else
Requires: dracut-network
%endif
Requires: curl
Requires: cpio
Requires: dmidecode

%description dracut
Warewulf is a stateless and diskless provisioning
system for large clusters of bare metal and/or virtual systems.

This subpackage contains a dracut module that can be used to generate
an initramfs that can fetch and boot a Warewulf node image from a
Warewulf server.

%prep
%setup -q -n %{name}-%{version} -b0 %if %{?with_offline:-a2}


%build
export OFFLINE_BUILD=1
make defaults \
    PREFIX=%{_prefix} \
    BINDIR=%{_bindir} \
    SYSCONFDIR=%{_sysconfdir} \
    DATADIR=%{_datadir} \
    LOCALSTATEDIR=%{_sharedstatedir} \
    SHAREDSTATEDIR=%{_sharedstatedir} \
    MANDIR=%{_mandir} \
    INFODIR=%{_infodir} \
    DOCDIR=%{_docdir} \
    SRVDIR=%{srvdir} \
    TFTPDIR=%{tftpdir} \
    SYSTEMDDIR=%{_unitdir} \
    BASHCOMPDIR=%{_datadir}/bash-completion/completions \
    FIREWALLDDIR=/usr/lib/firewalld/services \
    WWCLIENTDIR=/warewulf \
    IPXESOURCE=/usr/share/ipxe \
    DRACUTMODDIR=/usr/lib/dracut/modules.d \
    CACHEDIR=%{_localstatedir}/cache
make build
%if %{api}
make api
%endif


%check
make test


%install
export OFFLINE_BUILD=1
export NO_BRP_STALE_LINK_ERROR=yes
make install \
    DESTDIR=%{buildroot}
%if %{api}
make installapi \
    DESTDIR=%{buildroot}
%endif

%if 0%{?suse_version} || 0%{?sle_version}
yq e '
  .tftp.ipxe."00:00" = "undionly.kpxe" |
  .tftp.ipxe."00:07" = "ipxe-x86_64.efi" |
  .tftp.ipxe."00:09" = "ipxe-x86_64.efi" |
  .tftp.ipxe."00:0B" = "snp-arm64.efi" ' \
  -i %{buildroot}%{_sysconfdir}/warewulf/warewulf.conf
%endif

%pre
getent group %{wwgroup} >/dev/null || groupadd -r %{wwgroup}
%systemd_pre warewulfd.service
# use ipxe images from the distribution


%post
%systemd_post warewulfd.service
%firewalld_reload


%preun
%systemd_preun warewulfd.service


%postun
%systemd_postun_with_restart warewulfd.service
%firewalld_reload


%files
%defattr(-, root, root)

%dir %{_sysconfdir}/warewulf
%config(noreplace) %{_sysconfdir}/warewulf/warewulf.conf
%config(noreplace) %attr(0640,-,%{wwgroup}) %{_sysconfdir}/warewulf/nodes.conf
%config(noreplace) %{_sysconfdir}/warewulf/examples
%config(noreplace) %{_sysconfdir}/warewulf/ipxe
%config(noreplace) %{_sysconfdir}/warewulf/grub
%{_datadir}/bash-completion/completions/ww*
%config(noreplace) %{_sysconfdir}/logrotate.d

%dir %{_sharedstatedir}/warewulf
%dir %{_sharedstatedir}/warewulf/chroots
%dir %{_sharedstatedir}/warewulf/overlays

%dir %{_datadir}/warewulf
%{_datadir}/warewulf/bmc
%dir %{_datadir}/warewulf/overlays
%dir %{_datadir}/warewulf/overlays/*
%dir %{_datadir}/warewulf/overlays/*/rootfs
%{_datadir}/warewulf/overlays/NetworkManager/rootfs/*
%{_datadir}/warewulf/overlays/debian.interfaces/rootfs/*
%{_datadir}/warewulf/overlays/debug/rootfs/*
%{_datadir}/warewulf/overlays/fstab/rootfs/*
%{_datadir}/warewulf/overlays/host/rootfs/*
%{_datadir}/warewulf/overlays/hostname/rootfs/*
%{_datadir}/warewulf/overlays/hosts/rootfs/*
%{_datadir}/warewulf/overlays/ifcfg/rootfs/*
%{_datadir}/warewulf/overlays/ignition/rootfs/*
%{_datadir}/warewulf/overlays/issue/rootfs/*
%{_datadir}/warewulf/overlays/netplan/rootfs/*
%{_datadir}/warewulf/overlays/resolv/rootfs/*
%attr(700, -, -) %{_datadir}/warewulf/overlays/ssh.authorized_keys/rootfs/root
%attr(700, -, -) %{_datadir}/warewulf/overlays/ssh.authorized_keys/rootfs/root/.ssh
%attr(600, -, -) %{_datadir}/warewulf/overlays/ssh.authorized_keys/rootfs/root/.ssh/authorized_keys.ww
%{_datadir}/warewulf/overlays/ssh.host_keys/rootfs/*
%{_datadir}/warewulf/overlays/syncuser/rootfs/*
%{_datadir}/warewulf/overlays/systemd.netname/rootfs/*
%{_datadir}/warewulf/overlays/udev.netname/rootfs/*
%{_datadir}/warewulf/overlays/wicked/rootfs/*
%{_datadir}/warewulf/overlays/wwclient/rootfs/*
%{_datadir}/warewulf/overlays/wwinit/rootfs/*
%{_datadir}/warewulf/overlays/localtime/rootfs/*

%{_bindir}/wwctl
%{_prefix}/lib/firewalld/services/warewulf.xml
%{_unitdir}/warewulfd.service
%{_mandir}/man1/wwctl*
%{_mandir}/man5/*.5*

%dir %{_docdir}/warewulf
%license %{_docdir}/warewulf/LICENSE.md

%if %{api}
%{_bindir}/wwapi*
%config(noreplace) %{_sysconfdir}/warewulf/wwapi*.conf
%endif


%files dracut
%defattr(-, root, root)
%dir %{_prefix}/lib/dracut/modules.d/90wwinit
%attr(755, -, -) %{_prefix}/lib/dracut/modules.d/90wwinit/*.sh


%changelog
* Sat Feb 1 2025 Jonathon Anderson <janderson@ciq.com>
- Add Recommends: ipmitool

* Thu Sep 12 2024 Jonathon Anderson <janderson@ciq.com>
- Split overlays into separate directories

* Tue Jun 18 2024 Josh Burks <jeburks2@asu.edu>
- Add curl, cpio, and dracut as requires for warewulf-dracut

* Thu Apr 18 2024 Jonathon Anderson <janderson@ciq.com>
- New warewulf-dracut subpackage

* Wed Apr 17 2024 Jonathon Anderson <janderson@ciq.com>
- Don't build the API on EL7

* Sat Mar 9 2024 Jonathon Anderson <janderson@ciq.com> - 4.5.0-1
- Update source to github.com/warewulf
- Fix ownership of overlay files
- Add packaging for new grub support
- Add dependencies on distribution ipxe packages
- Fix offline builds
- Accommodate new Makefile behavior
- Designate config files in /etc/warewulf/ as "noreplace"
- Updated path to shell completions

* Mon Oct 17 2022 Jeremy Siadal <jeremy.c.siadal@intel.com> - 4.4.0-1
- Add offline build support -- prepping for bcond
- Add more BuildRequires for new golang vendor modules

* Wed Jan 26 2022 Jeremy Siadal <jeremy.c.siadal@intel.com> - 4.2.0-1
- Add license install
- Updates for RH and SUSE RPM guidelines

* Sat Jan 15 2022 Gregory Kurtzer <gmkurtzer@gmail.com> - 4.2.0-1
- Integrated genconfig Make options
- Cleaned up SPEC to use default RPM macros

* Tue Jan 11 2022 Jeremy Siadal <jeremy.c.siadal@intel.com> - 4.2.0-1
- Merge overlay subdirectories
- Add configuration options to make
- Relocate tftpboot for OpenSUSE
- Remove libexecdir macro; changing in OpenSUSE 15.4

* Mon Nov 1 2021 Jeremy Siadal <jeremy.c.siadal@intel.com> - 4.2.0-1
- Add support for OpenSUSE
- Update file attribs
- Update license string
- Make shared store relocatable

* Fri Sep 24 2021 Michael L. Young <myoung@ciq.com> - 4.2.0-1
- Update spec file to use systemd macros
- Use macros to refer to system paths
- Update syntax

* Tue Jan 26 2021 14:46:24 JST Brian Clemens <bclemens@ciq.com> - 4.0.0
- Initial release
