Name:       dnscrypt-proxy
Version:    1.4.3
Release:    5%{?dist}
Group:      System Environment/Daemons
Summary:    A tool for securing communications between a client and a DNS resolver
License:    BSD
URL:        https://github.com/opendns/dnscrypt-proxy

Source0:    http://download.dnscrypt.org/dnscrypt-proxy/dnscrypt-proxy-1.4.3.tar.bz2
Source1:    dnscrypt-proxy.service
Source2:    dnscrypt-proxy.default

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires:  libsodium-devel
Requires:       libsodium
Requires:       systemd

%description
DNSCrypt is a slight variation on DNSCurve.

DNSCurve improves the confidentiality and integrity of DNS requests using high-speed high-security elliptic-curve cryptography. Best of all, DNSCurve has very low overhead and adds virtually no latency to queries.

DNSCurve aims at securing the entire chain down to authoritative servers. However, it only works with authoritative servers that explicitly support the protocol. And unfortunately, DNSCurve hasn't received much adoption yet.

The DNSCrypt protocol is very similar to DNSCurve, but focuses on securing communications between a client and its first-level resolver. While not providing end-to-end security, it protects the local network (which is often the weakest link in the chain) against man-in-the-middle attacks. It also provides some confidentiality to DNS queries.

The DNSCrypt daemon acts as a DNS proxy between a regular client, like a DNS cache or an operating system stub resolver, and a DNSCrypt-aware resolver, like OpenDNS.

%prep
%setup -q

%build
./configure --prefix=%{_datadir}/%{name} \
    --bindir=%{_bindir} \
    --sbindir=%{_sbindir} \
    --datadir=%{_datadir} \
    --mandir=%{_mandir}

make %{?_smp_mflags}

%install
%{__rm} -rf $RPM_BUILD_ROOT
%{__make} DESTDIR=$RPM_BUILD_ROOT install
%{__mkdir} -p $RPM_BUILD_ROOT%{_unitdir}
%{__mkdir} -p $RPM_BUILD_ROOT%{_sysconfdir}/default
%{__install} -m644 %SOURCE1 $RPM_BUILD_ROOT%{_unitdir}/%{name}.service
%{__install} -m644 %SOURCE2 $RPM_BUILD_ROOT%{_sysconfdir}/default/%{name}

%clean
%{__rm} -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)

%{_bindir}/hostip
%{_sbindir}/dnscrypt-proxy

%{_datadir}/%{name}
%{_mandir}/man8/%{name}.8.gz
%{_mandir}/man8/hostip.8.gz

%{_unitdir}/dnscrypt-proxy.service
%config(noreplace) %{_sysconfdir}/default/dnscrypt-proxy

%post
selinuxenabled && chcon -t named_exec_t /usr/sbin/dnscrypt-proxy
#if [ $1 -eq 1]; then
#    /usr/bin/systemctl preset dnscrypt-proxy.service
#fi

%preun
/usr/bin/systemctl --no-reload disable dnscrypt-proxy.service >/dev/null 2>&1 ||:
/usr/bin/systemctl stop dnscrypt-proxy.service >/dev/null 2>&1 ||:

%postun
/usr/bin/systemctl daemon-reload >/dev/null 2>&1 ||:

