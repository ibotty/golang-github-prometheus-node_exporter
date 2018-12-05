#!/bin/bash
set -euo pipefail

VERSION="$1"
OLDVERSION="$(awk '/^Version: /{print $2}' golang-github-prometheus-node_exporter.spec)"

echo "downloading source v$VERSION"
curl -sSLO "https://github.com/prometheus/node_exporter/archive/v${VERSION}.tar.gz"

echo "change version in spec file"
sed -i \
    -e '/^Version:/s/[0-9.]*$/'"$VERSION"'/' \
    -e '/^Release:/s/[0-9]\+/1/' \
    golang-github-prometheus-node_exporter.spec

echo "remove old source tarball and add new one"
git rm "v$OLDVERSION.tar.gz"
git add "v$VERSION.tar.gz"

echo "commit changes"
git commit -m "bump version to v$VERSION"

echo "Now what's left is tito tag and git push --tags origin"
