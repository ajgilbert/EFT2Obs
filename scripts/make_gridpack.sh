#!/usr/bin/env bash
source env.sh

set -e

if [[ $# -lt 1 ]]; then
    echo "Insufficient number of arguments, usage is ./run_gridpack.sh [name]]"
    exit 1
fi

PROCESS=$1
IWD=${PWD}

### SET ENVIRONMENT VARIABLES HERE
RUNLABEL="pilotrun"
###

cp cards/${PROCESS}/{param,reweight,run,pythia8}_card.dat ${MG_DIR}/${PROCESS}/Cards/

pushd ${MG_DIR}/${PROCESS}
# Create MG config
{
  echo "shower=OFF"
  echo "reweight=OFF"
  echo "done"
  echo "set gridpack True"
  echo "done"
} > mgrunscript

if [ -d "${MG_DIR}/${PROCESS}/Events/${RUNLABEL}" ]; then rm -r ${MG_DIR}/${PROCESS}/Events/${RUNLABEL}; fi
./bin/generate_events ${RUNLABEL} -n < mgrunscript

cp "${RUNLABEL}_gridpack.tar.gz" "${IWD}/gridpack_${PROCESS}.tar.gz"


# The part below initialises the reweighting in the new gridpack,
# but it doesn't seem to be necessary.

# mkdir "gridpack_${PROCESS}"

# pushd "gridpack_${PROCESS}"
# 	tar -xf ../${RUNLABEL}_gridpack.tar.gz
# 	mkdir -p madevent/Events/${RUNLABEL}
# 	cp ../Events/${RUNLABEL}/unweighted_events.lhe.gz madevent/Events/${RUNLABEL}
# 	# Do we really need to do this??
# 	# pushd madevent
# 	# 	echo "0" | ./bin/madevent --debug reweight pilotrun
# 	# popd
# 	rm -r madevent/Events/${RUNLABEL}
# 	tar -zcf "../gridpack_${PROCESS}.tar.gz" ./*
# popd

# rm -r "gridpack_${PROCESS}"
# popd

echo ">> Gridpack ${IWD}/gridpack_${PROCESS}.tar.gz has been successfully created"
