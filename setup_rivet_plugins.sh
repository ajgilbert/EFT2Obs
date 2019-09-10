#!/usr/bin/env bash
set -x
set -e

source env.sh

if [ -z "${RIVET_ANALYSIS_PATH}" ]; then echo "ERROR: environment variable RIVET_ANALYSIS_PATH is not set"; exit 1; fi

pushd Classification
rivet-buildplugin RivetPlugins.so ./*.cc
popd
