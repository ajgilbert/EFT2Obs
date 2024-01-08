#!/usr/bin/env bash
export EFTOBS_LOCAL_LHAPDF=1
export LHAPDF_CONFIG_PATH="${PWD}/lhapdf/bin/lhapdf-config"
export PYTHONPATH="${PWD}/$(echo lhapdf/lib64/python*/site-packages):${PYTHONPATH}"
export LD_LIBRARY_PATH="${PWD}/lhapdf/lib:${LD_LIBRARY_PATH}"
export RIVET_ANALYSIS_PATH=${PWD}/RivetPlugins
export MG_DIR="MG5_aMC_v2_9_16"
export MG_TARBALL="MG5_aMC_v2.9.16.tar.gz"
export RIVET_VERSION="3.1.9"
export DEBUG_SCRIPTS=0

if [ -f "local/rivetenv.sh" ]; then
  source local/rivetenv.sh
fi

if [ "$DEBUG_SCRIPTS" -eq "1" ]; then
	set -x
fi

if [[ ! -z "$PYTHIA8DATA" ]]; then
        export PYTHIA8DATA=""
fi

#[[ ":$PYTHONPATH:" != *":$PWD/${MG_DIR}:"* ]] && PYTHONPATH="$PWD/${MG_DIR}:${PYTHONPATH}"
