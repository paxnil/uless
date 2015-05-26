Name:       rssh
Version:    2.3.4
Release:    2%{?dist}
Summary:    restricted shell for scp/sftp
License:    BSD
URL:        https://github.com/opendns/dnscrypt-proxy

Source0:    http://prdownloads.sourceforge.net/rssh/rssh-2.3.4.tar.gz
Patch0:     rssh-rsync-protocol.diff
Patch1:     rssh-Makefile.diff

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root
Requires:       openssh-server
Requires:       rsync

%description
rssh is a restricted shell for use with OpenSSH, allowing only scp and/or sftp. It now also includes support for rdist, rsync, and cvs. For example, if you have a server which you only want to allow users to copy files off of via scp, without providing shell access, you can use rssh to do that. For a list of platforms on which rssh is known to work, see the Platform Support Page.

%prep
%setup -q
%patch0 -p1
%patch1 -p1

%build
./configure --prefix=%{_prefix} \
    --bindir=%{_bindir} \
    --libexecdir=%{_libexecdir} \
    --mandir=%{_mandir} \
    --sysconfdir=%{_sysconfdir}
make %{?_smp_mflags}

%install
%{__rm} -rf $RPM_BUILD_ROOT
%{__make} DESTDIR=$RPM_BUILD_ROOT install
%{__mv} $RPM_BUILD_ROOT%{_sysconfdir}/rssh.conf.default $RPM_BUILD_ROOT%{_sysconfdir}/rssh.conf

%clean
%{__rm} -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)

%{_bindir}/rssh
%{_libexecdir}/rssh_chroot_helper

%{_mandir}/man1/%{name}.1.gz
%{_mandir}/man5/%{name}.conf.5.gz

%config(noreplace) %{_sysconfdir}/%{name}.conf

%post

%preun

%postun

