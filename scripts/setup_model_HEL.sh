#!/usr/bin/env bash
set -x
set -e

source env.sh

if [ -z "${MG_DIR}" ]; then echo "ERROR: environment variable MG_DIR is not set"; exit 1; fi

pushd ${MG_DIR}/models
wget https://feynrules.irmp.ucl.ac.be/raw-attachment/wiki/HEL/HEL_UFO.tar.gz
tar -zxf HEL_UFO.tar.gz
rm HEL_UFO.tar.gz
popd