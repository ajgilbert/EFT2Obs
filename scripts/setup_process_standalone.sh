#!/usr/bin/env bash
source env.sh

set -e

if [[ $# -lt 1 ]]; then
    echo "Insufficient number of arguments, usage is ./setup_process.sh [name]]"
    exit 1
fi

PROCESS=$1

pushd "${MG_DIR}"
if [ -d "${PROCESS##*/}-standalone" ]; then
	echo "Process directory already exists, remove this first to run setup"
	exit 1
fi

cat "../cards/${PROCESS}/proc_card.dat" | sed "s/^output .*/output standalone ${PROCESS##*/}-standalone --prefix=int/" | ./bin/mg5_aMC
	pushd "${PROCESS##*/}-standalone/SubProcesses"
		make allmatrix2py.so
	popd
popd

if [ -f "cards/${PROCESS}/run_card.dat" ]; then
	echo ">> File cards/${PROCESS}/run_card.dat already exists, it will not be modified"
else
	echo ">> File cards/${PROCESS}/run_card.dat does not exist, copying from ${MG_DIR}/${PROCESS}/Cards/run_card.dat"
	cp "${MG_DIR}/${PROCESS}/Cards/run_card.dat" "cards/${PROCESS##*/}/run_card.dat"
fi

if [ -f "cards/${PROCESS}/pythia8_card.dat" ]; then
	echo ">> File cards/${PROCESS}/pythia8_card.dat already exists, it will not be modified"
else
	echo ">> File cards/${PROCESS}/pythia8_card.dat does not exist, copying from ${MG_DIR}/${PROCESS}/Cards/pythia8_card_default.dat"
	cp "${MG_DIR}/${PROCESS}/Cards/pythia8_card_default.dat" "cards/${PROCESS}/pythia8_card.dat"
fi
