#!/usr/bin/env bash
# source env.sh

set -x
set -e


# ARGS:
# - gridpack
# - number of events
# - rng seed
# - rivet plugins to run

if [[ $# -lt 4 ]]; then
    echo "Insufficient number of arguments, usage is ./run_gridpack.sh [gridpack] [events] [seed] [rivet plugin,..]"
    exit 1
fi

IWD=${PWD}
GRIDPACK=$1
EVENTS=$2
SEED=$3
PLUGINS=$4

GRIDPACK_DIR="gridpack_run_${SEED}"

# Check if TMPDIR is set
if [ -z ${TMPDIR+x} ]; then
	TMPDIR=$(mktemp -d)
	echo ">> No TMPDIR was set, created ${TMPDIR}"
else
	echo ">> TMPDIR is set to ${TMPDIR}"
fi

if [ -d "${GRIDPACK_DIR}" ]; then rm -r "${GRIDPACK_DIR}"; fi

mkdir "${GRIDPACK_DIR}"
tar -xf "${GRIDPACK}" -C "${GRIDPACK_DIR}/"

pushd "${GRIDPACK_DIR}"
	./run.sh "${EVENTS}" "${SEED}"
	mkdir -p madevent/Events/GridRun
	mv events.lhe.gz madevent/Events/GridRun/unweighted_events.lhe.gz

	pushd madevent
		echo "0" |./bin/madevent --debug reweight GridRun
		{
		  echo "pythia8"
		  # echo "set HEPMCoutput:file ${BASEDIR}/events.hepmc"
		  echo "set HEPMCoutput:file fifo@${TMPDIR}/events_${SEED}.hepmc"
		} > mgrunscript
		./bin/madevent --debug shower GridRun < mgrunscript
	popd

	rivet --analysis="${PLUGINS}" "${TMPDIR}/events_${SEED}.hepmc" -o "${IWD}/Rivet_${SEED}.yoda"
popd

rm "${TMPDIR}/events_${SEED}.hepmc"
rm -r "${GRIDPACK_DIR}"
