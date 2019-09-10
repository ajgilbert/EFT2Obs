#!/usr/bin/env bash
set -x
set -e

source env.sh

if [ -z "${LHAPDF_CONFIG_PATH}" ]; then echo "ERROR: environment variable LHAPDF_CONFIG_PATH is not set"; exit 1; fi
if [ -z "${MG_DIR}" ]; then echo "ERROR: environment variable MG_DIR is not set"; exit 1; fi
if [ -z "${MG_TARBALL}" ]; then echo "ERROR: environment variable MG_TARBALL is not set"; exit 1; fi

if [ -d "${MG_DIR}" ]; then
  echo "Directory ${MG_DIR} already exists, remove this first to re-install"
  exit 1
fi
wget https://launchpad.net/mg5amcnlo/2.0/2.6.x/+download/${MG_TARBALL}
tar -zxf ${MG_TARBALL}
rm ${MG_TARBALL}

# Create MG config
{
	echo "set lhapdf ${LHAPDF_CONFIG_PATH}"
	echo "set auto_update 0"
	echo "set automatic_html_opening False"
	echo "save options"
  echo "install pythia8"
} > mgconfigscript

pushd ${MG_DIR}
./bin/mg5_aMC ../mgconfigscript
patch -p0 < ../MG5aMC_PY8_interface.cc.patch
pushd HEPTools/MG5aMC_PY8_interface
python compile.py ../pythia8
popd
popd
