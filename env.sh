#!/usr/bin/env bash
export LHAPDF_CONFIG_PATH="/cvmfs/cms.cern.ch/slc7_amd64_gcc630/external/lhapdf/6.2.1-ghjeda/bin/lhapdf-config"
export RIVET_ANALYSIS_PATH=${PWD}/Classification
export HIGGSPRODMODE=GGF
export MG_DIR="MG5_aMC_v2_6_6"
export MG_TARBALL="MG5_aMC_v2.6.6.tar.gz"
export RIVET_VERSION="3.0.1"

if [ -f "local/rivetenv.sh" ]; then
	source local/rivetenv.sh
fi

[[ ":$PYTHONPATH:" != *":$PWD/${MG_DIR}:"* ]] && PYTHONPATH="$PWD/${MG_DIR}:${PYTHONPATH}"
