#!/usr/bin/env bash
set -e

source env.sh

if [ -z "${RIVET_VERSION}" ]; then echo "ERROR: environment variable RIVET_VERSION is not set"; exit 1; fi

wget "https://phab.hepforge.org/source/rivetbootstraphg/browse/${RIVET_VERSION}/rivet-bootstrap?view=raw" -O rivet-bootstrap
enable_root=no bash rivet-bootstrap
