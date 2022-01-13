#!/usr/bin/env bash
set -e

source env.sh

if [ -z "${MG_DIR}" ]; then echo "ERROR: environment variable MG_DIR is not set"; exit 1; fi

pushd ${MG_DIR}/models
MODEL_FILENAME="v3.0.2.tar.gz"
wget https://github.com/SMEFTsim/SMEFTsim/archive/refs/tags/${MODEL_FILENAME}
tar -zxf ${MODEL_FILENAME}
rm ${MODEL_FILENAME}
popd
