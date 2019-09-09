#!/usr/bin/env bash
export LHAPDF_CONFIG_PATH="/cvmfs/cms.cern.ch/slc7_amd64_gcc630/external/lhapdf/6.2.1-ghjeda/bin/lhapdf-config"
source local/rivetenv.sh
export RIVET_ANALYSIS_PATH=${PWD}/Classification
export HIGGSPRODMODE=GGF
