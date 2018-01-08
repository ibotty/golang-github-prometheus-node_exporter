#!/bin/bash
# usage:
#   node_exporter_textfile_wrapper smartmon.sh smartmon
# will atomically replace smartmon.prom in the textfile-collector dir with
# output from smartmon.sh in /etc/prometheus/node_exporter/text_collectors or
# in /usr/share/doc/golang-github-prometheus-node_exporter*/text_collector_examples.

set -eu
set -o pipefail

script="$1"
outname="${2-""}"

dirs_to_consider=( "/etc/prometheus/node_exporter/text_collectors" /usr/share/doc/golang-github-prometheus-node_exporter*/text_collector_examples)

if [[ "$outname" = "" ]]; then
    outname="$(basename "$script")"
    outname="${outname%.*}"
fi

if [[ "$(dirname "$script")" = "." ]]; then
    for dir in "${dirs_to_consider[@]}"; do
        candidate="$dir/$script"
        if [[ -x "$candidate" ]]; then
            script="$candidate"
            break
        fi
    done
fi

tmpout="$(mktemp -p /var/lib/node_exporter/textfile_collector/)"
realout="/var/lib/node_exporter/textfile_collector/$outname.prom"

main() {
    $script > "$tmpout"
    chmod 640 "$tmpout"
    chgrp node_exporter "$tmpout" || chmod a+r "$tmpout"
    mv "$tmpout" "$realout"
}

cleanup() {
    rm -f "$tmpout"
}

trap cleanup EXIT
main
