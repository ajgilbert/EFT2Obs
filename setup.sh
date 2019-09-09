#!/usr/bin/env bash
set -x
set -e

### SET ENVIRONMENT VARIABLES HERE
LHAPDF_CONFIG_PATH="/cvmfs/cms.cern.ch/slc7_amd64_gcc630/external/lhapdf/6.2.1-ghjeda/bin/lhapdf-config"
MG_DIR="MG5_aMC_v2_6_5"
MG_TARBALL="MG5_aMC_v2.6.5.tar.gz"
PROCESS="ggF"
###

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

pushd ${MG_DIR}/models
wget https://feynrules.irmp.ucl.ac.be/raw-attachment/wiki/HEL/HEL_UFO.tar.gz
tar -zxf HEL_UFO.tar.gz
rm HEL_UFO.tar.gz
popd

pushd ${MG_DIR}
./bin/mg5_aMC ../cards/${PROCESS}/proc_card.dat
popd

wget https://phab.hepforge.org/source/rivetbootstraphg/browse/3.0.1/rivet-bootstrap?view=raw -O rivet-bootstrap
bash rivet-bootstrap

source rivet_env.sh
pushd Classification
rivet-buildplugin RivetHiggsTemplateCrossSections.so HiggsTemplateCrossSections.cc
popd
# git clone https://gitlab.cern.ch/LHCHIGGSXS/LHCHXSWG2/STXS/Classification.git
