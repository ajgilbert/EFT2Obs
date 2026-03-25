#!/usr/bin/env bash
# run_rivet4_job.sh - Convert HepMC2 to HepMC3 and run Rivet 4 (CMSSW)
#
# Usage: run_rivet4_job.sh <input_hepmc2.gz> <output.yoda>
#   input_hepmc2.gz : path to HepMC2 file (AFS or /eos/... path)
#   output.yoda     : destination for YODA output (AFS or /eos/... path)

# NOTE:
# This script is written for CERN lxplus where CMSSW is typically available via CVMFS
# and the user CMSSW area lives on AFS. When running on a non-lxplus
# machine (e.g. LLR), you must:
#   - update CMSSW_BASE to point to your local CMSSW release area (or otherwise ensure cmsenv works)
#   - choose INPUT_HEPMC / OUTPUT_YODA paths that are valid and writable on your site
#   - adapt EOS/XRootD endpoints if you are not using CERN EOS (this script uses root://eosuser.cern.ch)
#   - RIVET_PLUGINS should point to the directory containing the compiled Rivet analysis plugin (shared library) and/or analysis sources used by Rivet.

# Converter note:
#   This workflow expects a hepmc2to3 binary. If you keep the source in this repo as
#   scripts/hepmc2to3.cxx, compile it to scripts/hepmc2to3 and set HEPMC2TO3 accordingly.
set -euo pipefail

INPUT_HEPMC="${1:-}"
OUTPUT_YODA="${2:-}"

if [[ -z "$INPUT_HEPMC" || -z "$OUTPUT_YODA" ]]; then
    echo "Usage: $0 <input_hepmc2.gz> <output.yoda>"
    exit 1
fi

# Paths (adjust if CMSSW location changes)
CMSSW_BASE="/afs/cern.ch/work/g/gsokmen/EFT2Obs/CMSSW_15_0_15"
RIVET_PLUGINS="${CMSSW_BASE}/src/RivetPlugins"
HEPMC2TO3="${CMSSW_BASE}/src/hepmc2to3"
ANALYSIS="CMS_2021_PAS_SMP_20_005"
# --------------------------------------------------

echo "=== Rivet 4 job ==="
echo "Input  : $INPUT_HEPMC"
echo "Output : $OUTPUT_YODA"

# Clear any inherited Rivet/Python environment from the submitting shell
# (e.g. EFT2Obs/local/ paths set by setup_rivet.sh) so CMSSW sets up cleanly.
unset PYTHONPATH
unset LD_LIBRARY_PATH
unset RIVET_ANALYSIS_PATH
unset RIVET_DATA_PATH
unset RIVETDIR
unset YODASYS

source /cvmfs/cms.cern.ch/cmsset_default.sh
cd "${CMSSW_BASE}/src"
eval "$(scramv1 runtime -sh)"
export RIVET_ANALYSIS_PATH="${RIVET_PLUGINS}"
export RIVET_DATA_PATH="${RIVET_PLUGINS}"
echo "CMSSW/Rivet 4 sourced: rivet $(rivet --version 2>&1 | head -1)"

# Create a temporary working directory (cleaned up on exit)
if [[ -n "$TMPDIR" ]]; then
    WORK_DIR=$(mktemp -d "$TMPDIR/rivet4_XXXXXX")
else
    WORK_DIR=$(mktemp -d /tmp/rivet4_XXXXXX)
fi
trap "echo '>> Cleaning up $WORK_DIR'; rm -rf '$WORK_DIR'" EXIT

# Copy input to local scratch 
INPUT_LOCAL="${WORK_DIR}/input.hepmc.gz"
if [[ "$INPUT_HEPMC" == /eos/* ]]; then
    echo ">> xrdcp from EOS..."
    xrdcp "root://eosuser.cern.ch/${INPUT_HEPMC}" "$INPUT_LOCAL"
else
    cp "$INPUT_HEPMC" "$INPUT_LOCAL"
fi

# Convert HepMC2 to HepMC3 
HEPMC3_LOCAL="${WORK_DIR}/input.hepmc3"
echo ">> Converting HepMC2 -> HepMC3..."
zcat "$INPUT_LOCAL" | "${HEPMC2TO3}" /dev/stdin "$HEPMC3_LOCAL"
echo "   Conversion done."

# Run Rivet 4 
YODA_LOCAL="${WORK_DIR}/output.yoda"
echo ">> Running Rivet 4 (${ANALYSIS})..."
rivet --analysis="${ANALYSIS}" "$HEPMC3_LOCAL" -o "$YODA_LOCAL"

# Copy output 
OUTPUT_DIR=$(dirname "$OUTPUT_YODA")
if [[ "$OUTPUT_YODA" == /eos/* ]]; then
    echo ">> xrdcp output to EOS..."
    xrdcp "$YODA_LOCAL" "root://eosuser.cern.ch/${OUTPUT_YODA}"
else
    mkdir -p "$OUTPUT_DIR"
    cp "$YODA_LOCAL" "$OUTPUT_YODA"
fi

echo "=== Done: $OUTPUT_YODA ==="
