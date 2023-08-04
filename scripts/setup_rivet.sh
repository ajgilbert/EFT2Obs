#!/usr/bin/env bash
set -e

source env.sh

if [ -z "${RIVET_VERSION}" ]; then echo "ERROR: environment variable RIVET_VERSION is not set"; exit 1; fi

wget "https://gitlab.com/hepcedar/rivetbootstrap/raw/${RIVET_VERSION}/rivet-bootstrap" -O rivet-bootstrap
enable_root=no CMAKE=cmake3 bash rivet-bootstrap
