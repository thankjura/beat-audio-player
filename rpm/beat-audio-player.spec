%global sysname beat

%define build_timestamp %{lua: print(os.date("%Y%m%d"))}

# Git submodules
# * tinytag
%global commit1 2c03b0b4b15056feb7c8051fa39728bcd71be30d
%global shortcommit1 %(c=%{commit1}; echo ${c:0:7})

Name: beat-audio-player
Version: 0
Release: 0.10.%{build_timestamp}%{?dist}
Summary: simple audioplayer for gnome
BuildArch: noarch

License: GPLv3+
URL: https://github.com/thankjura/beat-audio-player
Source0: %{url}/archive/master/%{name}-%{build_timestamp}.tar.gz
Source1: https://github.com/devsnd/tinytag/archive/%{commit1}/tinytag-%{shortcommit1}.tar.gz

BuildRequires: desktop-file-utils
BuildRequires: libappstream-glib
BuildRequires: meson >= 0.51.0
BuildRequires: python3-devel
BuildRequires: pkgconfig(gtk+-3.0) >= 3.24.7
BuildRequires: pkgconfig(pygobject-3.0) >= 3.36.1

Requires: gtk3 >= 3.24.7
Requires: hicolor-icon-theme

Recommends: libappindicator-gtk3

Provides: bundled(tinytag) = 0~git%{shortcommit1}

%description
%{summary}.


%prep
%setup -q -n %{name}-master
%setup -q -D -T -a1 -n %{name}-master

mv tinytag-%{commit1}/* third_party/tinytag

sed -i 's|#!/usr/bin/env python|#!/usr/bin/python3|' \
    third_party/tinytag/tinytag/tinytag.py


%build
%meson
%meson_build


%install
%meson_install
%py_byte_compile %{python3} %{buildroot}%{_datadir}/%{sysname}/%{sysname}/
%find_lang %{sysname}


%check
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/*.xml
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop


%files -f %{sysname}.lang
%license COPYING
%doc README.md
%{_bindir}/%{sysname}
%{_datadir}/%{sysname}/
%{_datadir}/applications/*.desktop
%{_datadir}/glib-2.0/schemas/*.gschema.xml
%{_datadir}/icons/hicolor/scalable/apps/*.svg
%{_metainfodir}/*.xml


%changelog
* Sun Aug 30 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0-0.9.20200830git0186a1c
- Update to latest git snapshot

* Sat Aug 29 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0-0.8.20200827git66c1406
- Update to latest git snapshot

* Tue Aug 25 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0-0.7.20200825git3545b54
- Update to latest git snapshot

* Mon Aug 24 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0-0.6.20200824git72e5c2e
- Update to latest git snapshot

* Sun Aug 23 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0-0.5.20200823gitb61c79f
- Update to latest git snapshot

* Wed Aug 19 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0-0.4.20200819gitc8661ff
- Update to latest git snapshot

* Tue Aug 18 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0-0.3.20200818git5739c38
- Update to latest git snapshot

* Tue Aug 18 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0-0.2.20200818git94edbac
- Update to latest git snapshot

* Tue Aug 18 2020 Artem Polishchuk <ego.cordatus@gmail.com> - 0-0.1.20200818gite180110
- Initial package
