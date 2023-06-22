#!/usr/bin/env bash

# If we have a local lhapdf install, use it
if command -v lhapdf-config &> /dev/null; then
  export LHAPDF_CONFIG_PATH=$(command -v lhapdf-config)
  export EFTOBS_LOCAL_LHAPDF=0
else
  export EFTOBS_LOCAL_LHAPDF=1
  export LHAPDF_CONFIG_PATH="${PWD}/lhapdf/bin/lhapdf-config"
  export PYTHONPATH="${PWD}/$(echo lhapdf/lib64/python*/site-packages):${PYTHONPATH}"
  export LD_LIBRARY_PATH="${PWD}/lhapdf/lib:${LD_LIBRARY_PATH}"
fi
# or if we have some pre-installed lhapdf, use that instead
export RIVET_ANALYSIS_PATH=${PWD}/RivetPlugins
export MG_DIR="MG5_aMC_v2_9_15"
export MG_TARBALL="MG5aMC_LTS_2.9.15.tgz"
export RIVET_VERSION="3.0.1"
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
