#!/usr/bin/env bash
export LHAPDF_CONFIG_PATH="${PWD}/lhapdf/bin/lhapdf-config"
export PYTHONPATH="${PWD}/lhapdf/lib64/python2.7/site-packages:${PYTHONPATH}"
export LD_LIBRARY_PATH="${PWD}/lhapdf/lib:${LD_LIBRARY_PATH}"
export RIVET_ANALYSIS_PATH=${PWD}/RivetPlugins
export MG_DIR="MG5_aMC_v2_6_7"
export MG_TARBALL="MG5_aMC_v2.6.7.tar.gz"
export RIVET_VERSION="3.0.1"
export DEBUG_SCRIPTS=0

if [ -f "local/rivetenv.sh" ]; then
	source local/rivetenv.sh
fi

if [ "$DEBUG_SCRIPTS" -eq "1" ]; then
	set -x
fi

#[[ ":$PYTHONPATH:" != *":$PWD/${MG_DIR}:"* ]] && PYTHONPATH="$PWD/${MG_DIR}:${PYTHONPATH}"
