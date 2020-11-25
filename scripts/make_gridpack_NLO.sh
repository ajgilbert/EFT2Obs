#!/usr/bin/env bash
source env.sh

set -e

if [[ $# -lt 1 ]]; then
    echo "Insufficient number of arguments, usage is ./run_gridpack_NLO.sh name [cores=N]"
    exit 1
fi

PROCESS=$1
CORES=${2-0}
IWD=${PWD}

### SET ENVIRONMENT VARIABLES HERE
RUNLABEL="pilotrun"
###

cp cards/${PROCESS}/{param,reweight,run,shower}_card.dat ${MG_DIR}/${PROCESS}/Cards/
# Also need to overwrite the default card, or we might lose some options
# cp cards/${PROCESS}/pythia8_card.dat ${MG_DIR}/${PROCESS}/Cards/pythia8_card_default.dat

pushd ${MG_DIR}/${PROCESS}
# Create MG config
{
  echo "shower=ON"
  echo "reweight=ON"
  echo "done"
  # echo "set gridpack True"
  echo "done"
} > mgrunscript

if [ -d "${MG_DIR}/${PROCESS}/Events/${RUNLABEL}" ]; then rm -r ${MG_DIR}/${PROCESS}/Events/${RUNLABEL}; fi

if [ "$CORES" -gt "0" ]; then
	./bin/generate_events aMC@NLO --nb_core="${CORES}" -n ${RUNLABEL} < mgrunscript
	# ./bin/generate_events ${RUNLABEL} --nb_core="${CORES}" -n < mgrunscript
else
	./bin/generate_events aMC@NLO -n ${RUNLABEL} < mgrunscript
	# ./bin/generate_events ${RUNLABEL} -n < mgrunscript
fi
popd

pushd "${MG_DIR}"
	cp -r "${PROCESS}" "gridpack_${PROCESS}"
	pushd "gridpack_${PROCESS}"
		rm -r Events/pilotrun
		rm -r MCatNLO/RUN_PYTHIA8_*
		find ./ -name "*.ps" | xargs -r rm
		find ./ -name "*.lhe" | xargs -r rm
		find ./ -name "*.lhe.gz" | xargs -r rm
		find ./ -name "*.lhe.rwgt" | xargs -r rm
		find ./ -name "check_poles" | xargs -r rm
		find ./ -name "test_MC" | xargs -r rm
		find ./ -name "test_ME" | xargs -r rm
		find ./ -name "*.f" | xargs -r rm
		find ./ -name "*.F" | xargs -r rm
		# find ./ -name "*.cc" | xargs -r rm
		find ./ -name "*.html" | xargs -r rm
		find ./ -name "gensym" | xargs -r rm
		find ./ -name "ftn25" | xargs -r rm
		find ./ -name "ftn26" | xargs -r rm
		find ./ -name "core.*" | xargs -r rm
		find ./ -name "LSFJOB_*" | xargs -r rm -r
		find ./ -wholename "*SubProcesses/*/*.o" | xargs -r rm
		cp "${IWD}/scripts/run_NLO.sh" ./run.sh
		tar -zcf "../gridpack_${PROCESS}.tar.gz" ./*
	popd
	rm -rf "gridpack_${PROCESS}"
	cp "gridpack_${PROCESS}.tar.gz" "${IWD}/gridpack_${PROCESS}.tar.gz"
popd



# pushd "gridpack_${PROCESS}"
# 	tar -xf ../${RUNLABEL}_gridpack.tar.gz
# 	mkdir -p madevent/Events/${RUNLABEL}
# 	cp ../Events/${RUNLABEL}/unweighted_events.lhe.gz madevent/Events/${RUNLABEL}
# 	pushd madevent
# 		cp Cards/.reweight_card.dat Cards/reweight_card.dat.backup
# 		{
# 			echo "change rwgt_dir rwgt"
# 			echo "launch"
# 		} > Cards/reweight_card.dat
# 		echo "0" | ./bin/madevent --debug reweight pilotrun
# 		cp Cards/reweight_card.dat.backup Cards/reweight_card.dat
# 		if [ "$EXPORTRW" -eq "1" ]; then
# 			tar -zcf "rw_module_${PROCESS}.tar.gz" rwgt
# 			cp "rw_module_${PROCESS}.tar.gz" "${IWD}/"
# 			echo ">> Reweighting module ${IWD}/rw_module_${PROCESS}.tar.gz has been successfully created"
# 		fi
# 	popd
# 	rm -r madevent/Events/${RUNLABEL}
# 	tar -zcf "../gridpack_${PROCESS}.tar.gz" ./*
# popd

# rm -r "gridpack_${PROCESS}"
# cp "gridpack_${PROCESS}.tar.gz" "${IWD}/gridpack_${PROCESS}.tar.gz"

# # cp "${RUNLABEL}_gridpack.tar.gz" "${IWD}/gridpack_${PROCESS}.tar.gz"
# popd

# echo ">> Gridpack ${IWD}/gridpack_${PROCESS}.tar.gz has been successfully created"
