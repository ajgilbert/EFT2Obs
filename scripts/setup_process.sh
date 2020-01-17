#!/usr/bin/env bash
source env.sh

set -x
set -e

if [[ $# -lt 1 ]]; then
    echo "Insufficient number of arguments, usage is ./setup_process.sh [name]]"
    exit 1
fi

PROCESS=$1

pushd "${MG_DIR}"
if [ -d "${PROCESS}" ]; then
	echo "Process directory already exists, remove this first to run setup"
	exit 1
fi
./bin/mg5_aMC "../cards/${PROCESS}/proc_card.dat"
popd
