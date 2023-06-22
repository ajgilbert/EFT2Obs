#!/usr/bin/env bash
set -e

IWD=${PWD}
source env.sh

if [ -z "${LHAPDF_CONFIG_PATH}" ]; then echo "ERROR: environment variable LHAPDF_CONFIG_PATH is not set"; exit 1; fi
if [ -z "${MG_DIR}" ]; then echo "ERROR: environment variable MG_DIR is not set"; exit 1; fi
if [ -z "${MG_TARBALL}" ]; then echo "ERROR: environment variable MG_TARBALL is not set"; exit 1; fi

LHAPDF_VERSION="LHAPDF-6.2.1"
wget "https://lhapdf.hepforge.org/downloads/?f=${LHAPDF_VERSION}.tar.gz" -O "${LHAPDF_VERSION}.tar.gz"
tar xf "${LHAPDF_VERSION}.tar.gz"
rm "${LHAPDF_VERSION}.tar.gz"
mkdir lhapdf
pushd "${LHAPDF_VERSION}"
	./configure --prefix="${IWD}/lhapdf/"
	make
	make install
popd
rm -r "${LHAPDF_VERSION}"


if [ -d "${MG_DIR}" ]; then
  echo "Directory ${MG_DIR} already exists, remove this first to re-install"
  exit 1
fi
wget "https://launchpad.net/mg5amcnlo/lts/2.6.x/+download/${MG_TARBALL}"
tar -zxf "${MG_TARBALL}"
rm "${MG_TARBALL}"

# Create MG config
{
	echo "set lhapdf ${LHAPDF_CONFIG_PATH}"
	echo "set auto_update 0"
	echo "set automatic_html_opening False"
	echo "save options"
  echo "install pythia8"
} > mgconfigscript

pushd "${MG_DIR}"
	./bin/mg5_aMC ../mgconfigscript
  patch madgraph/core/helas_objects.py "${IWD}/setup/helas_objects.py.patch"
  patch madgraph/interface/master_interface.py "${IWD}/setup/master_interface.py.patch"
	pushd HEPTools/MG5aMC_PY8_interface
		patch MG5aMC_PY8_interface.cc "${IWD}/setup/MG5aMC_PY8_interface.cc.patch"
		patch MG5aMC_PY8_interface.cc "${IWD}/setup/corrector_MG5aMC_PY8_interface.cc.patch"
		ln -s "${IWD}/setup/WeightCorrector.h" ./
		python compile.py ../pythia8
	popd
	pushd HEPTools/pythia8/include/Pythia8Plugins
		ln -s "${IWD}/setup/WeightCorrector.h" ./
	popd
	pushd Template/NLO/MCatNLO
		# Fix the order in which LD_LIBRARY_PATH is constructed, otherwise we will
		# pick up the (incompatible) hepmc library from RIVET
		patch shower_template.sh "${IWD}/setup/shower_template.sh.patch"
		# Minimal changes to add the reweighting weights to the hepmc output and do
		# the weight transformation
		patch srcPythia8/Pythia82_hep.cc "${IWD}/setup/Pythia82_hep.cc.patch"
	popd
popd
