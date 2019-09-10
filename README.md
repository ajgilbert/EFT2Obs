# EFT2Obs-Demo
Automatically parameterise the effect of EFT coefficients on arbitrary observables.

## Instructions

Note that this workflow has only been tested on lxplus.

**At the moment LHAPDF is not installed automatically. Please edit `env.sh` to change the path for `lhapdf-config` if you do not have /cvmfs mounted.**

Then run the following setup scripts in order:

 -  `setup_mg5.sh`: download and compile madgraph_amc@nlo. Applies a patch to the madgraph-pythia8 interface that is needed to make valid hepmc output with stored event weights.
 -  `setup_model_HEL.sh`: download the Higgs Effective Lagrangian (HEL) UFO model
 -  `setup_rivet.sh`: Download and install rivet
 -  `setup_rivet_plugins.sh`: Compile the Higgs STXS rivet plugins, located in the `Classification` directory, we will use in this example
 - `setup_process.sh ggF`: Run madgraph to initialise a directory for gluon-fusion Higgs production, using the process definition in `cards/ggF/proc_card.dat`

Once this is done, it is necessary to set up the right environment (should be done in every new session): `source env.sh`.

We now need to generate a new `param_card.dat` as well as config file that will steer the subsequent steps. Run: `python make_config.py -p ggF --default-value 1E-4 --limit-pars 12,30,33 --default-value-inactive 0` to do this. Here we select a subset of the EFT coefficients (`12,30,33`) in the HEL UFO to generate the scaling terms for. The non-SM values of these coefficients will be set to `1E-4`, while all others will remain fixed to zero.

Copy the `param_card.dat` produced by this script into the `cards/ggF/` directory. A `config.json` file is also produced. Run `python make_reweight_card.py config.json reweight_card.dat` to produce a new reweight card and copy this into `cards/ggF/` too.

Next, do `run.sh ggF` to generate the events. This will copy the pre-modified madgraph cards to the process directory created above, then generate events which will be showered with pythia8 and passed directly to the Rivet routine. As a demonstration, the Rivet routine will produce histograms of the STXS classification as well as several kinematic distributions under the different EFT weighting scenarios given in `cards/ggF/reweight_card.dat`.

To calculate the scaling coefficients for a particular distribution run `python get_scaling.py config.json /HiggsTemplateCrossSectionsStage1/HTXS_stage1_pTjet30`.
