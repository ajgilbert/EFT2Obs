# EFT2Obs

A tool to automatically parametrize the effect of EFT coefficients on arbitrary observables.

---

The assumption is that the cross section for a bin i can be expressed as the sum

![cross section equation](/resources/docs/sigma_eqn.png)

where  σ_int is the leading term in the EFT expansion (going as 1/Λ^2), and accounts for the interference with the SM amplitude. The SM-independent term is labelled as σ_BSM (going as 1/Λ^4).

Dividing through by the SM cross section, σ_SM, provides a scaling function for each bin

![relative cross section equation](/resources/docs/mu_eqn.png)

which parametrizes deviations in the cross section in terms of the c_j parameters. The EFT2Obs tool determines the coefficients A_j and B_jk by generating events in which matrix element weights for different c_j values are embedded.

Note that this workflow has only been tested on lxplus so far, and for CMS users please ensure the CMSSW environment is **not set** when running scripts in EFT2Obs.

## Initial setup

Follow these steps to set up and install the relevant software packages.

### Software environment

EFT2Obs is officially supported only on EL9/AlmaLinux9 (i.e. the current default lxplus at CERN).
It is recommended to use one of the following software environments, accessible via cvmfs:

 - LCG: `. /cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/setup.sh`
 - CMSSW: `CMSSW_14_1_0_pre4`


Clone the EFT2Obs repository and source the `env.sh` script which sets a number of useful environment variables:

```sh
git clone https://github.com/ajgilbert/EFT2Obs.git
cd EFT2Obs
source env.sh
```

The `env.sh` script should be sourced at the start of each new session, after sourcing the main software environment.

Then run the following scripts to download and install LHAPDF, Madgraph_aMC@NLO, Pythia and Rivet. Note this may take some time to complete.

```sh
./scripts/setup_mg5.sh
./scripts/setup_rivet.sh
```

The first script installs LHAPDF and Magraph, then applies patches to the Madgraph-Pythia interface that are needed to make valid HepMC output with stored event weights and to perform a transformation of these weights that is described in more detail below.

## Setup models

The Madgraph-compatible models you wish to study should be installed next. Scripts are provided to do this for commonly used models: SMEFTsim3, SMEFTatNLO, and the HEL . Other models can be added following their respective instructions.

```sh
./scripts/setup_model_SMEFTsim3.sh
./scripts/setup_model_SMEFTatNLO.sh
./scripts/setup_model_HEL.sh
```

*Note: a patch is provided for the HEL model that will fix the mass of the Z boson, otherwise by default this will vary as a function of the EFT parameters: `patch MG5_aMC_v2_6_7/models/HEL_UFO/parameters.py setup/HEL_fix_MZ__parameters.py.patch`*

## Setup Rivet routines

The Rivet routines which define the fiducial regions and obserbables of interest should be placed in the `EFT2Obs/RivetPlugins` directory. A routine for the Higgs STXS is already provided: `HiggsTemplateCrossSections`  which contain the stage 1.2 definitions. Whenever new routines are added or existing ones modified they should be recompiled with:

```sh
./scripts/setup_rivet_plugins.sh
```

## Process-specific workflow

The main steps for defining a process, generating events and extracting scaling factors for observables are outlined below:

![workflow](/resources/docs/EFT2Obs.jpeg)

In this section for clarity we will follow a specific example, ZH production in the SMEFT model with the STXS Rivet routine, but the steps are generic and it should be straightforward to run with other processes or models.

It is also possible to generate events at NLO in QCD and apply reweighting with an NLO-capable UFO model. In some places an alternative script must be used, and in others it is sufficient to add the `--nlo` flag to the usual script.

### Setup process

Each process+model combination we want to study first needs a dedicated sub-directory in `EFT2Obs/cards`. In this case we will use the pre-existing one for `zh-SMEFTsim3`. Here we add a `proc_card.dat` specifying the model to import and the LO process we wish to generate:

```
import model SMEFTsim_U35_MwScheme_UFO-massless

generate p p > h mu+ mu- NP<=1 @0

output zh-SMEFTsim3
```

Notes on the `proc_card.dat` format:

 - A restriction on the number of new physics vertices to be less than one should be applied. In many models this is achieved with adding `NP<=1` at the end of each process, but check the model-specific documentation for guidance. See the **Known limitations** section below for more details.
 - The argument to the `output` command at the end must match the `cards` sub-directory name.

To initialise this process in Madgraph run

```sh
./scripts/setup_process.sh zh-SMEFTsim3
```

which creates the directory `MG5_aMC_v2_9_16/zh-SMEFTsim3`.

For an NLO process (with `[QCD]` in the process definition), use the `setup_process_NLO.sh` script instead.

> :information_source: A process directory can also be located in a subdirectory within `cards`. Some commands must then be adapted, e.g. `./scripts/setup_process.sh mydir/zh-SMEFTsim3`. The `output [dir]` command in `proc_card.dat` should still give only the final directory, e.g. `zh-SMEFTsim3`. 

### Prepare Madgraph cards

There are four further configuration cards that we need to specify: the `run_card.dat`, `pythia8_card.dat`, `param_card.dat` and `reweight_card.dat`. For NLO generation the `pythia8_card.dat` card is replaced by `shower_card.dat`. For the first two we can start from the default cards Madgraph created in the `MG5_aMC_v2_9_16/zh-SMEFTsim3/Cards` directory. If these files do not already exist in our `cards/zh-SMEFTsim3` directory then they will have been copied there in the `setup_process.sh` step above. If necessary edit these cards to set the desired values for the generation or showering parameters. In this example the cards have already been configured in the repository. *Note for CMS users: to emulate the Pythia configuration in official CMS sample production the lines in `resources/pythia8/cms_default_2018.dat` can be added to the `pythia8_card.cat`*.

For NLO generation some care must be taken with the `run_card.dat`:

 - The precision for the integration grids is controlled by `req_acc`. We recommend setting this to `0.001`, as recommended by the MG authors are typically used in official CMS production.
 - Make sure `parton_shower` is set to `PYTHIA8`.
 - To use Madgraph's NLO-correct reweighting, the `store_rwgt_info` flag must be set to true. For this information to be stored, one of `reweight_scale` or `reweight_PDF` must be set to true as well. We recommend `reweight_scale`, and setting both `rw_rscale` and `rw_fscale` to `1.0`.
 - Check that `ickkw` is set appropriately if you will use FxFx merging.

#### Config file

To define `param_card.dat` and create `reweight_card.dat` we first need to make an EFT2Obs-specific configuration file that will keep track of which (subset of) model parameters we want to study and what values they should be set to in the reweighting procedure. The initial config is generated with

```
python scripts/make_config.py -p zh-SMEFTsim3 -o cards/zh-SMEFTsim3/config.json \
 --pars SMEFT:4,5,7,8,9,21,22,23,24,25,26,27,30  --def-val 0.01 --def-sm 0.0 --def-gen 0.0
```

where:

  - `-p` gives our process label
  - `-o` the output name for the config file
  - `--pars` specifies which parameters we are interested in
  - `--def-val` is a default nominal non-SM value to be used in the reweighting
  - `--def-sm` is the default value of the parameters that corresponds to the SM expectation
  - `--def-gen` the default parameter value used to generate the events

The `--pars` option supports multiple arguments of the form `[BLOCK]:[ID1],[ID2],...[IDN]`. The block name and numbers correspond to those in the `param_card.dat` that Madgraph produces in the `MG5_aMC_v2_9_16/zh-SMEFTsim3/Cards` directory. The resulting file looks like:

```json
{
    "blocks": [
        "SMEFT"
    ],
    "inactive": {
        "default_val": 0.0,
        "parameters": []
    },
    "parameter_defaults": {
        "block": "SMEFT",
        "gen": 0.0,
        "sm": 0.0,
        "val": 0.01
    },
    "parameters": [
        {"index": 4, "name": "chbox"},
        {"index": 5, "name": "chdd"},
        {"index": 7, "name": "chw"},
        {"index": 8, "name": "chb"},
        {"index": 9, "name": "chwb"},
        {"index": 21, "name": "chl1"},
        {"index": 22, "name": "chl3"},
        {"index": 23, "name": "che"},
        {"index": 24, "name": "chq1"},
        {"index": 25, "name": "chq3"},
        {"index": 26, "name": "chu"},
        {"index": 27, "name": "chd"},
        {"index": 30, "name": "cll1"}
    ]
```
All properties in the `parameter_defaults` block are assumed to apply to each parameter specified in the `parameters` list, however these can be modified on a parameter-by-parameter basis by setting, e.g. `{"index": 4, "name": "chbox", "val": 0.02}`.

Note that all parameters in the specified blocks not explicitly listed here will be set to `default_val` in the `inactive` part of the config. This will usually correspond to the SM value for the parameters. If some parameters should take a different value then this can be set with the argument `--set-inactive [BLOCK]:[ID1]=[VAL1],[ID2]=[VAL2] ...`.

#### param_card.dat

Next we make the `param_card.dat` that will be used for the initial event generation:

```sh
python scripts/make_param_card.py -p zh-SMEFTsim3 -c cards/zh-SMEFTsim3/config.json -o cards/zh-SMEFTsim3/param_card.dat
```

The script take the default card in `MG5_aMC_v2_9_16/zh-SMEFTsim3/Cards` and will report which parameter values are changed.

#### reweight_card.dat

The reweight card specifies a set of parameter points that should be evaluated in the matrix element reweighting step. It is generated using the config with:

```sh
python scripts/make_reweight_card.py cards/zh-SMEFTsim3/config.json cards/zh-SMEFTsim3/reweight_card.dat
```

For NLO processes, an extra line should be added to the `reweight_card.dat` to select the NLO-correct reweighting mode (if desired):

```sh
python scripts/make_reweight_card.py cards/zh-SMEFTsim3/config.json cards/zh-SMEFTsim3/reweight_card.dat --prepend 'change mode NLO'
```

### Make the gridpack

To make the event generation more efficient and easier to run in parallel we first produce a gridpack for the process:

```sh
./scripts/make_gridpack.sh zh-SMEFTsim3 # for LO
./scripts/make_gridpack_NLO.sh zh-SMEFTsim3  # for NLO
```

Once complete the gridpack `gridpack_zh-SMEFTsim3.tar.gz` will be copied to the main directory. The script can also produce a standalone version of the matrix-element code. This can be useful for reweighting events outside of the EFT2Obs tool. To produce this, add an additional flag:

```sh
./scripts/make_gridpack.sh zh-SMEFTsim3 1
```

An addtional file, `rw_module_zh-SMEFTsim3.tar.gz` is also produced. See the section below on standalone reweighting for more information. Note that standalone reweighting with NLO matrix elements is not currently possible.

The full set of options supported by the `make_gridpack.sh` script are:

```sh
./scripts/make_gridpack.sh [card dir] [make standalone=0/1] [no. cores] [postfit] [extra param/run card settings ...]
```

Set `no. cores` to 2 or more to use multiple CPU cores in parallel. The `postfix` setting adds an optional extra label to the output: `gridpack_[process][postfix].tar.gz`. All remaining arguments are interpreted as commands that should be passed to Madgraph to modify the param or run cards. For example, `""set htjmin 800"`.

### Event generation step

Now everything is set up we can proceed to the event generation.

This is handled by `scripts/run_gridpack.py`, which runs through the LHE file generation with Madgraph, the EFT model reweighting, showering with Pythia and finally processing with Rivet. The output is a yoda file containing all the Rivet routine histograms. We exploit the feature that in Rivet 3.X a copy of each histogram is saved for every weight. The following command generates 500 events:

```sh
export HIGGSPRODMODE=ZH
python scripts/run_gridpack.py --gridpack gridpack_zh-SMEFTsim3.tar.gz -s 1 -e 500 \
  -p HiggsTemplateCrossSectionsStage1,HiggsTemplateCrossSections \
  -o test-zh [--nlo]
```

where the full set of options is:

 - `--gridpack [file]` relative or absolute path to the gridpack
 - `--nlo` should be set if the input is an NLO gridpack
 - `-s X` the RNG seed which will be passed to Madgraph. This is also used to index the output files from the job, e.g. `Rivet_[X].yoda`.
 - `-e N` number of events per job, in this case 500.
 - `-p [RivetRoutine1],[RivetRoutine2],...` comma separated list of Rivet routines to run
 - `-o [dir]` the output directory for the yoda files, will be created if it does not exist
 - `--save-lhe [path]` save the intermediate LHE files (containing the event weights) to the relative or absolute directory given by `[path]`. The output file will be of the form `[path]/events_[X].lhe.gz` where `[X]` is the RNG seed.
 - `--save-hepmc [path]` save the intermediate HepMC files to the relative or absolute directory given by `[path]`. The output file will be of the form `[path]/events_[X].hepmc.gz` where `[X]` is the RNG seed.
 - `--load-lhe [path]` load the existing LHE file from the relative or absolute directory given by `[path]`. The input file must be of the form `[path]/events_[X].lhe.gz` where `[X]` is the RNG seed. All prior steps are skipped.
 - `--load-hepmc [path]` load the existing HepMC file from the relative or absolute directory given by `[path]`. The input file must be of the form `[path]/events_[X].hepmc.gz` where `[X]` is the RNG seed. All prior steps are skipped. Note that it does not make sense to set both `--load-lhe` and `--load-hepmc`.
 - `--rivet-ignore-beams` sets the `--ignore-beams` option when running Rivet, useful for cases where only a particle decay is simulated, instead of a full collision.
 - `--no-cleanup` prevents the local working directory (named `gridpack_run_[X]`) from being deleted at the end, can be useful for debugging.
 - `--to-step [lhe,shower,rivet]` stop after the given step, no further processing is performed. Useful if, for example, you only want to generate the LHE files and not run the rivet routine.

Since it is usually not feasible to generate the desired number of events in a single job, a wrapper script `scripts/launch_jobs.py` is provided which can automate running a set of jobs in parallel, each with a different RNG seed so that the events are statistically independent. This script passes through all command line options to `run_gridpack.py`, but adds several extra options to control how the jobs run:

 - `-j N` the number of jobs to run
 - `-s X` the initial RNG seed for the first job. Subsequent jobs i use `X + i` as the seed.
 - `--job-mode` supported options are interactive or submission to batch farms, e.g. condor
 - `--parallel X` number of parallel jobs to run in interactive mode
 - `--env X1=Y1,X2=Y2,..` any environment variables that should be set in the job. In this example the STXS Rivet routines require the Higgs production mode to be specified.

The following command runs four jobs, each generating 500 events:

```sh
python scripts/launch_jobs.py --gridpack gridpack_zh-SMEFTsim3.tar.gz -j 4 -s 1 -e 500 \
  -p HiggsTemplateCrossSectionsStage1,HiggsTemplateCrossSections \
  -o test-zh --job-mode interactive --parallel 4 --env HIGGSPRODMODE=ZH
```

To submit jobs to htcondor at CERN the `--job-mode interactive --parallel 4` options can be replaced by `--job-mode condor --task-name stxs --sub-opts '+JobFlavour = "longlunch"'`. Anything specified in `--sub-opts` will be added to the condor submit file.

Note that during the workflow the event weights that are added by Madgraph are transformed before they are utilised by Rivet. This is done to isolate the separate terms that will appear in the final parametrization, and to more easily keep track of their statistical uncertainties. The table below illustrates the weight transformation for a simple example with two model parameters, c_1 and c_2. For each weighting point, labelled W_i, the expression for the default and transformed weights are given as a function of the D_1 and D_2 constants, which take the values specified in the config file.

![weight_table](/resources/docs/weight_table.png)

### Extract scaling functions

In this final step we first merge the yoda output files:

```sh
yodamerge -o test-zh/Rivet.yoda test-zh/Rivet_*
```

and then use the script `get_scaling.py` to extract the A_j and B_jk coefficients and their statistical uncertainties:

```sh
python scripts/get_scaling.py -c cards/zh-SMEFTsim3/config.json [--nlo] \
  -i test-zh/Rivet.yoda --hist "/HiggsTemplateCrossSections/pT_V" \
  --save json,txt,tex --translate-tex resources/translate_tex.json \
  --rebin 0,10,20,30,40,50,60,70,80,90,100,120,140,160,180,200,250,300,350,400
```

where the options are

 - `-c` the config file to use
 - `--nlo` should be set if the output came from NLO reweighting
 - `-i` the yoda file input
 - `--hist` the histogram in the yoda file to parametrize, note that the leading "/" is important!
 - `--save [json,txt,tex]` a comma separated list of the output formats to save in
 - `--translate-tex` a json dictionary file that converts the parameter names to latex format - only needed when `tex` is chosen in `--save`
 - `--rebin` optionally re-bin the histogram first by providing a list of the new bin edges
 - `--filter-params` a comma separated list of a subset of the parameters to keep (all others will be dropped)
 - `--print-style` either "perBin" or "perTerm", which specifies the format for printing to the screen
 - `--color-above` when using --print-style perTerm, highlight relative uncertainties above this threshold in red

The terms calculated for each bin are printed to the screen, e.g.

```
[...]
Bin 5    numEntries: 1676       mean: 3.09e-11   stderr: 6.4e-15   
         edges: [50.0, 60.0]
-----------------------------------------------------------------
Term                 |          Val |       Uncert | Rel. uncert.
-----------------------------------------------------------------
1                    |       1.0000 |       0.0002 |       0.0002
chbox                |       0.1220 |       0.0001 |       0.0005
chbox * chbox        |       0.0037 |       0.0000 |       0.0067
chdd                 |       0.0342 |       0.0050 |       0.1475
chdd * chdd          |       0.0109 |       0.0002 |       0.0202
chw                  |       0.6960 |       0.0090 |       0.0130
chw * chw            |       0.1619 |       0.0056 |       0.0345
chb                  |       0.0727 |       0.0068 |       0.0931
chb * chb            |       0.0209 |       0.0054 |       0.2576
chwb                 |       0.3313 |       0.0064 |       0.0194
chwb * chwb          |       0.0456 |       0.0018 |       0.0402
chl1                 |       0.1351 |       0.0027 |       0.0198
chl1 * chl1          |       0.0076 |       0.0002 |       0.0233
[...]
```

The output in `json` format is intended for further processing. It contains information on the histogram edges as contents as well as all the scaling terms and their statistical uncertainties. The `txt` and `tex` formats provide a more readable format:

**HiggsTemplateCrossSections_pT_V.txt**
```
50-60:1 + 0.073*chb + 0.122*chbox + -0.152*chd + 0.034*chdd + -0.104*che + 0.135*chl1 + -0.229*chl3 + -0.058*chq1 + 1.208*chq3 + 0.217*chu + 0.696*chw + 0.331*chwb + 0.182*cll1 + 0.021*chb*chb + 0.004*chb*chbox + -0.075*chb*chd + -0.007*chb*chdd + -0.005*chb*che + 0.004*chb*chl1 + -0.009*chb*chl3 + 0.045*chb*chq1 + 0.008*chb*chq3 + 0.069*chb*chu + 0.006*chb*chw + 0.017*chb*chwb + [...]
```

**HiggsTemplateCrossSections_pT_V.tex**

![tex table](/resources/docs/tex_table.png)

A script is available for plotting the histogram overlaying the expectation for arbitrary values of the parameters. For this ROOT (and the PyROOT interface) must be available. The script relies only on the json output file from the above step, for example:

```sh
python scripts/makePlot.py --hist HiggsTemplateCrossSections_pT_V.json -c cards/zh-SMEFTsim3/config.json --x-title "p_{T}(Z) [GeV]" --title-left "qq #rightarrow Hl^{+}l^{-}" --title-right "SMEFTsim3" --ratio 0.9,1.95 --draw chw=0.005:4 chwb=0.005:2 chb=0.005:8 chbox=0.05:12 --show-unc --y-min 1E-9 --translate resources/translate_root.json
```

where the arguments to `--draw` are of the format `PAR1=X1,PAR2=X2,..:COLOR`. This example gives the output:


![pT_V](/resources/docs/HiggsTemplateCrossSections_pT_V.png)

## Standalone reweighting

The matrix element library madgraph generates can be exported and used standalone with a python interface. EFT2Obs includes a wrapper python module, `scripts/standalone_reweight.py` that makes it straightforward to run the full set of reweighting points on a given event. This module has no dependencies on other EFT2Obs code so can be run from any location.

The steps to making a complete standalone directory are:

1) The standalone module can be produced in one of two ways. The first is when running `make_gridpack.sh`, we can add an extra flag to also export the standalone matrix element library:

```sh
./scripts/make_gridpack.sh zh-SMEFTsim3 1
# An addtional file, rw_module_zh-SMEFTsim.tar.gz, is created
```

Alternatively, if we are not interested in actually generating events, we can skip the integration and just generate and compile the matrix element code:

```sh
./scripts/setup_process_standalone.sh zh-SMEFTsim3
```

This generates a special process directory with the `-standalone` postfix in the Madgraph directory.

2) Run the script `make_standalone.py`. This creates a directory, specified by `-o` which will contain: the matix library from madgraph, a copy of the EFT2Obs config file (specified with `-c`), and a set of full param_cards, one for each reweighting point.

If using the gridpack output in 1):

```sh
python scripts/make_standalone.py -p zh-SMEFTsim3 -o rw_zh-SMEFTsim3 -c cards/zh-SMEFTsim3/config.json --rw-module rw_module_zh-SMEFTsim3.tar.gz
```

If using `setup_process_standalone.sh` without making a gridpack:

```sh
python scripts/make_standalone.py -p zh-SMEFTsim3 -o rw_zh-SMEFTsim3 -c cards/zh-SMEFTsim3/config.json --rw-dir MG5_aMC_v2_6_7/zh-SMEFTsim3-standalone
```

3) The output directory can then be used in conjunction with the `standalone_reweight.py` module:

```py
from standalone_reweight import *

rw = StandaloneReweight('rw_zh-SMEFTsim3')

# Now specify the list of ingoing and outgoing particles and other properties.
# NB: all lists must be the same length!
parts = [
  # Incoming parton 1:   [E, px, py, pz],
  # Incoming parton 2:   [E, px, py, pz],
  # Outgoing particle 1: [E, px, py, pz],
  # ...
  #Outgoing particle N:  [E, px, py, pz]
]
pdgs = []  # List PDGs corresponding to the above particles [int]
helicities = [] # List of helicities corresponding to the above particles [int]
status = [] # # List of status codes, should be -1 for incoming, +1 for outgoing [int]
alphas = 0.137 # event-specific value of alphas
use_helicity = True # Set to False to sum over helicity states, e.g. if helicity information not available

# Returns a list of weights in the same order specified by the EFT2Obs reweight_card.dat
weights = rw.ComputeWeights(parts, pdgs, helicities, status, alphas, use_helicity)
```

The ComputeWeights function will print an error message if the particle configuration is not defined in the matrix element library. These raw weights are not always useful for further processing, so a transformation function is provided that isolates the different linear and quadratic components the same way in normal EFT2Obs usage:

```
transformed_weights = rw.TransformWeights(weights)
```

Given the transformed weights, a new weight can be calculated for arbitrary coefficient values:

```
new_weight = rw.CalculateWeight(transformed_weights, cW=0.1, cHW=0.1)
```

## Known limitations

The following limitations currently apply. Links to GitHub issues indicate which are being actively worked on. Other issues or feature requests should also be reported there.

 - Processes are limited to one new-physics vertex (i.e. `NP <= 1` syntax required in the process definition).
 - Some incompatibilities with the CMSSW environment have been reported. For now this should not be set when running EFT2Obs.

## Reading LHE files 

If the LHE files are directly saved, in order to plot from these, some dedicated scripts can be found in `EFT2Obs/scripts`. These use the [lhereader](https://pypi.org/project/lhereader/) package, and to run them, it is necessary to install a python environment:

```
virtualenv --python=$(which python3) .venv
source ./.venv/bin/activate
pip install lhereader
```
Once this step has finished and lhereader is installed (it is possible that a few warnings or errors appear, but if the package got installed it's okay) and change the file that can be found in the new environment: `.venv/lib/python[your_version]/site-packages/lhereader/__init__.py` by the file found in `EFT2Obs/scripts/lhereader/__init__.py`.

Further packages might need to be installed like:

```
pip install pyarrow
```

Once the environment has been set up, before running `produce_plots_lhe.py` it is required to remove all the `NP<=1` or `NP<=0` inside the LHE files as these characters are not supported by the xml reader.  Once the condor jobs have finised, the output is given by `events_1_lhe.gz`. To use it as input, it is necessary to unzip them and remove the unwanted charcters by doing:

```
gunzip events_*_lhe.gz
for i in {1..N}; do sed 's/NP<=//' events_${i}.lhe &> events_${i}_nonp.lhe ; done
```
Replace `N` by your number of files. Now that the LHE files are in the correct format, it is finally possible to start producing plots. To optimize the plotting time, it is necessary to start by loading the events into parquet files. (Note that the parquet path is for now hardcoded)

```
 python3 scripts/produce_plots_lhe.py --parquet --file chg_cpv_H2j 
```

And once the parquet file has been created it is possible to plot the observables:

```
python3 scripts/produce_plots_lhe.py --file chg_cpv_H2j --output test-ggF-H
```

Note: for the ratio plots, the first element of `weight_dataset` in `produce_plots_lhe` will be the denominator. Therefore, if the goal is to compare different histograms to the nominal one, the first element of `weight_dataset` needs to be the one having the weights corresponding to `wilson_coeff=0` .