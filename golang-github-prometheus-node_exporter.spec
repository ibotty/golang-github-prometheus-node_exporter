# If any of the following macros should be set otherwise,
# you can wrap any of them with the following conditions:
# - %%if 0%%{centos} == 7
# - %%if 0%%{?rhel} == 7
# - %%if 0%%{?fedora} == 23
# Or just test for particular distribution:
# - %%if 0%%{centos}
# - %%if 0%%{?rhel}
# - %%if 0%%{?fedora}
#
# Be aware, on centos, both %%rhel and %%centos are set. If you want to test
# rhel specific macros, you can use %%if 0%%{?rhel} && 0%%{?centos} == 0 condition.
# (Don't forget to replace double percentage symbol with single one in order to apply a condition)

# Generate devel rpm
%global with_devel 1
# Build project from bundled dependencies
%global with_bundled 1
# Build with debug info rpm
%global with_debug 0
# Run tests in check section
%global with_check 1
# Generate unit-test rpm
%global with_unit_test 0

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif


%global provider        github
%global provider_tld    com
%global project         prometheus
%global repo            node_exporter
# https://github.com/prometheus/node_exporter
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}
%global commit          0e60bb8e005c638605e59ac3f307e3d47e891a9f
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

Name:           golang-%{provider}-%{project}-%{repo}
Version:        0.14.0_rc2
Release:        1%{?dist}
Summary:        Exporter for machine metrics
License:        ASL 2.0
URL:            https://%{provider_prefix}
Source0:        https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz

# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 aarch64 %{arm}}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}



%description
%{summary}

%if 0%{?with_devel}
%package devel
Summary:       %{summary}
BuildArch:     noarch

%if 0%{?with_check} && ! 0%{?with_bundled}
BuildRequires: golang(github.com/beevik/ntp)
BuildRequires: golang(github.com/coreos/go-systemd/dbus)
BuildRequires: golang(github.com/godbus/dbus)
BuildRequires: golang(github.com/golang/protobuf/proto)
BuildRequires: golang(github.com/kolo/xmlrpc)
BuildRequires: golang(github.com/mdlayher/wifi)
BuildRequires: golang(github.com/prometheus/client_golang/prometheus)
BuildRequires: golang(github.com/prometheus/client_model/go)
BuildRequires: golang(github.com/prometheus/common/expfmt)
BuildRequires: golang(github.com/prometheus/common/log)
BuildRequires: golang(github.com/prometheus/procfs)
BuildRequires: golang(github.com/soundcloud/go-runit/runit)
BuildRequires: golang(golang.org/x/sys/unix)
%endif

Requires:      golang(github.com/beevik/ntp)
Requires:      golang(github.com/coreos/go-systemd/dbus)
Requires:      golang(github.com/godbus/dbus)
Requires:      golang(github.com/golang/protobuf/proto)
Requires:      golang(github.com/kolo/xmlrpc)
Requires:      golang(github.com/mdlayher/wifi)
Requires:      golang(github.com/prometheus/client_golang/prometheus)
Requires:      golang(github.com/prometheus/client_model/go)
Requires:      golang(github.com/prometheus/common/expfmt)
Requires:      golang(github.com/prometheus/common/log)
Requires:      golang(github.com/prometheus/procfs)
Requires:      golang(github.com/soundcloud/go-runit/runit)
Requires:      golang(golang.org/x/sys/unix)

Provides:      golang(%{import_path}/collector) = %{version}-%{release}
Provides:      golang(%{import_path}/collector/ganglia) = %{version}-%{release}

%description devel
%{summary}

This package contains library source intended for
building other packages which use import path with
%{import_path} prefix.
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%package unit-test-devel
Summary:         Unit tests for %{name} package
%if 0%{?with_check}
#Here comes all BuildRequires: PACKAGE the unit tests
#in %%check section need for running
%endif

# test subpackage tests code from devel subpackage
Requires:        %{name}-devel = %{version}-%{release}

%if 0%{?with_check} && ! 0%{?with_bundled}
BuildRequires: golang(github.com/prometheus/client_golang/prometheus/promhttp)
%endif

Requires:      golang(github.com/prometheus/client_golang/prometheus/promhttp)

%description unit-test-devel
%{summary}

This package contains unit tests for project
providing packages with %{import_path} prefix.
%endif

%prep
%setup -q -n %{repo}-%{commit}

%build
mkdir -p _build/src/github.com/prometheus
ln -s $(pwd) _build/src/github.com/prometheus/node_exporter

%if ! 0%{?with_bundled}
export GOPATH=$(pwd)/_build:%{gopath}
%else
# Since we aren't packaging up the vendor directory we need to link
# back to it somehow. Hack it up so that we can add the vendor
# directory from BUILD dir as a gopath to be searched when executing
# tests from the BUILDROOT dir.
ln -s ./ ./vendor/src # ./vendor/src -> ./vendor
export GOPATH=$(pwd)/_build:$(pwd)/vendor:%{gopath}
%endif

%gobuild -o _build/node_exporter %{provider_prefix}

%install
install -d -p   %{buildroot}%{_bindir} \
                %{buildroot}%{_defaultdocdir}/node_exporter
install -p -m 0755 ./_build/node_exporter %{buildroot}%{_bindir}/node_exporter
#cp -pav text_collector_examples %{buildroot}%{_defaultdocdir}/node_exporter
#cp -pav *.md %{buildroot}%{_defaultdocdir}/node_exporter

# source codes for building projects
%if 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
echo "%%dir %%{gopath}/src/%%{import_path}/." >> devel.file-list
# find all *.go but no *_test.go files and generate devel.file-list
for file in $(find . \( -iname "*.go" -or -iname "*.s" \) \! -iname "*_test.go" | grep -v "vendor") ; do
    dirprefix=$(dirname $file)
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$dirprefix
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> devel.file-list

    while [ "$dirprefix" != "." ]; do
        echo "%%dir %%{gopath}/src/%%{import_path}/$dirprefix" >> devel.file-list
        dirprefix=$(dirname $dirprefix)
    done
done
%endif

# testing files for this project
%if 0%{?with_unit_test} && 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *_test.go files and generate unit-test-devel.file-list
for file in $(find . -iname "*_test.go" | grep -v "vendor") ; do
    dirprefix=$(dirname $file)
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$dirprefix
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> unit-test-devel.file-list

    while [ "$dirprefix" != "." ]; do
        echo "%%dir %%{gopath}/src/%%{import_path}/$dirprefix" >> devel.file-list
        dirprefix=$(dirname $dirprefix)
    done
done
%endif

%if 0%{?with_devel}
sort -u -o devel.file-list devel.file-list
%endif

%check
%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}
%if ! 0%{?with_bundled}
export GOPATH=%{buildroot}/%{gopath}:%{gopath}
%else
# Since we aren't packaging up the vendor directory we need to link
# back to it somehow. Hack it up so that we can add the vendor
# directory from BUILD dir as a gopath to be searched when executing
# tests from the BUILDROOT dir.
ln -s ./ ./vendor/src # ./vendor/src -> ./vendor

export GOPATH=%{buildroot}/%{gopath}:$(pwd)/vendor:%{gopath}
%endif

%if ! 0%{?gotest:1}
%global gotest go test
%endif

%gotest %{import_path}
%gotest %{import_path}/collector
%endif

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%if 0%{?with_devel}
%files devel -f devel.file-list
%dir %{gopath}/src/%{provider}.%{provider_tld}/%{project}
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%files unit-test-devel -f unit-test-devel.file-list
%endif

%files
%license LICENSE
%doc *.md text_collector_examples
%{_bindir}/*

%pre
getent group node_exporter > /dev/null || groupadd -r node_exporter
getent passwd node_exporter > /dev/null || \
    useradd -rg node_exporter -d /var/lib/node_exporter -s /sbin/nologin \
            -c "Prometheus node exporter"

%changelog
* Wed Mar 08 2017 Tobias Florek <tob@butter.sh> 0.14.0_rc2-1
- bump version (tob@butter.sh)
- don't use git annex (tob@butter.sh)

* Wed Mar 08 2017 Tobias Florek <tob@butter.sh> 0.14.0_rc1-7
- actually build (tob@butter.sh)

* Wed Mar 08 2017 Tobias Florek <tob@butter.sh> 0.14.0_rc1-6
- install text_collector_examples (tob@butter.sh)
- don't run tests on build (tob@butter.sh)

* Wed Mar 08 2017 Tobias Florek <tob@butter.sh> 0.14.0_rc1-5
- build with bundled deps (tob@butter.sh)

* Wed Mar 08 2017 Tobias Florek <tob@butter.sh> 0.14.0_rc1-4
- add node_exporter source (tob@butter.sh)
- delete git-annex pointer (tob@butter.sh)
- add source file (tob@butter.sh)

* Wed Mar 08 2017 Tobias Florek <tob@butter.sh> 0.14.0_rc1-3
- use git annex to download source (tob@butter.sh)

* Wed Mar 08 2017 Tobias Florek <tob@butter.sh> 0.14.0_rc1-2
- new package built with tito

