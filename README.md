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

Clone the EFT2Obs repository and source the `env.sh` script which sets a number of useful environment variables:

```sh
git clone https://github.com/ajgilbert/EFT2Obs.git
cd EFT2Obs
source env.sh
```

The `env.sh` script should be sourced at the start of each new session.

**At the moment LHAPDF is not installed automatically. Please edit `env.sh` first to change the path for `lhapdf-config` if you do not have /cvmfs mounted.**

Then run the following scripts to download and install Madgraph_aMC@NLO, Pythia and Rivet. Note this may take some time to complete.

```sh
./scripts/setup_mg5.sh
./scripts/setup_rivet.sh
```

The first script applies patches to the Madgraph-Pythia interface that are needed to make valid HepMC output with stored event weights and to perform a transformation of these weights that is described in more detail below.

## Setup models

The Madgraph-compatible models you wish to study should be installed next. Scripts are provided to do this for two commonly used models: the Higgs Effective Lagrangian (HEL) and SMEFTsim. Other models can be added following their respective instructions.

```sh
./scripts/setup_model_HEL.sh
./scripts/setup_model_SMEFTsim.sh
```
## Setup Rivet routines

The Rivet routines which define the fiducial regions and obserbables of interest should be placed in the `EFT2Obs/RivetPlugins` directory. Two routines for the Higgs STXS are already provided: `HiggsTemplateCrossSectionsStage1` and `HiggsTemplateCrossSections`  which contain the stage 1 and 1.1 definitions respectively. Whenever new routines are added or existing ones modified they should be recompiled with:

```sh
./scripts/setup_rivet_plugins.sh
```

## Process-specific workflow

The main steps for defining a process, generating events and extracting scaling factors for observables are outlined below:

![workflow](/resources/docs/EFT2Obs.jpeg)

In this section for clarity we will follow a specific example, ZH production in the HEL model with the STXS Rivet routine, but the steps are generic and it should be straightforward to run with other processes or models.

### Setup process

Each process+model combination we want to study first needs a dedicated sub-directory in `EFT2Obs/cards`. In this case we will use the pre-existing one for `zh-HEL`. Here we add a `proc_card.dat` specifying the model to import and the LO process we wish to generate:

```
import model HEL_UFO

# Definitions
define ell+ = e+ mu+ ta+
define ell- = e- mu- ta-
define j2 = g u c d s u~ c~ d~ s~

generate p p > h ell+ ell- / j2 ell+ ell- vl vl~ a h w+ w- NP<=1 @0
add process p p > h vl vl~ / j2 ell+ ell- vl vl~ a h w+ w- NP<=1 @1

output zh-HEL
```

Notes on the `param_card.dat` format:

 - A restriction on the number of new physics vertices to be less than one should be applied. In many models this is achieved with adding `NP<=1` at the end of each process, but check the model-specific documentation for guidance. See the **Known limitations** section below for more details.
 - The argument to the `output` command at the end must match the `cards` sub-directory name.

To initialise this process in Madgraph run

```sh
./scripts/setup_process.sh zh-HEL
```

which creates the directory `MG5_aMC_v2_6_7/zh-HEL`.

### Prepare Madgraph cards

There are four further configuration cards that we need to specify: the `run_card.dat`, `pythia8_card.dat`, `param_card.dat` and `reweight_card.dat`. For the first two we can start from the default cards Madgraph created in the `MG5_aMC_v2_6_7/zh-HEL/Cards` directory. If these files do not already exist in our `cards/zh-HEL` directory then they will have been copied there in the `setup_process.sh` step above. If necessary edit these cards to set the desired values for the generation or showering parameters. In this example the cards have already been configured in the repository.

#### Config file

To define `param_card.dat` and create `reweight_card.dat` we first need to make an EFT2Obs-specific configuration file that will keep track of which (subset of) model parameters we want to study and what values they should be set to in the reweighting procedure. The initial config is generated with

```
python scripts/make_config.py -p zh-HEL -o config_HEL_STXS.json \
  --pars newcoup:4,5,6,7,8,9,10,11,12 --def-val 0.01 --def-sm 0.0 --def-gen 0.0
```

where:

  - `-p` gives our process label
  - `-o` the output name for the config file
  - `--pars` specifies which parameters we are interested in
  - `--def-val` is a default nominal non-SM value to be used in the reweighting
  - `--def-sm` is the default value of the parameters that corresponds to the SM expectation
  - `--def-gen` the default parameter value used to generate the events

The `--pars` option supports multiple arguments of the form `[BLOCK]:[ID1],[ID2],...[IDN]`. The block name and numbers correspond to those in the `param_card.dat` that Madgraph produces in the `MG5_aMC_v2_6_7/zh-HEL/Cards` directory. The resulting file looks like:

```json
{
    "blocks": ["newcoup"],
    "inactive": {
        "default_val": 0.0,
        "parameters": []
    },
    "parameter_defaults": {
        "block": "newcoup", "gen": 0.0, "sm": 0.0, "val": 0.01
    },
    "parameters": [
        {"index": 4, "name": "cu"},
        {"index": 5, "name": "cd"},
        {"index": 6, "name": "cl"},
        {"index": 7, "name": "cww"},
        {"index": 8, "name": "cb"},
        {"index": 9, "name": "chw"},
        {"index": 10, "name": "chb"},
        {"index": 11, "name": "ca"},
        {"index": 12, "name": "cg"}
    ]
}
```
All properties in the `parameter_defaults` block are assumed to apply to each parameter specified in the `parameters` list, however these can be modified on a parameter-by-parameter basis by setting, e.g. `{"index": 4, "name": "cu", "val": 0.02}`.

Note that all parameters in the specified blocks not explicitly listed here will be set to `default_val` in the `inactive` part of the config. This will usually correspond to the SM value for the parameters. If some parameters should take a different value then this can be set with the argument `--set-inactive [BLOCK]:[ID1]=[VAL1],[ID2]=[VAL2] ...`.

#### param_card.dat

Next we make the `param_card.dat` that will be used for the initial event generation:

```sh
python scripts/make_param_card.py -p zh-HEL -c config_HEL_STXS.json -o cards/zh-HEL/param_card.dat
```

The script take the default card in `MG5_aMC_v2_6_7/zh-HEL/Cards` and will report which parameter values are changed.

#### reweight_card.dat

The reweight card specifies a set of parameter points that should be evaluated in the matrix element reweighting step. It is generated using the config with:

```sh
python scripts/make_reweight_card.py config_HEL_STXS.json cards/zh-HEL/reweight_card.dat
```

### Make the gridpack

To make the event generation more efficient and easier to run in parallel we first produce a gridpack for the process:

```sh
 ./scripts/make_gridpack.sh zh-HEL
```

Once complete the gridpack `gridpack_zh-HEL.tar.gz` will be copied to the main directory.

### Event generation step

Now everything is set up we can proceed to the event generation.

This is handled by `scripts/run_gridpack.py`, which runs through the LHE file generation with Madgraph, the EFT model reweighting, showering with Pythia and finally processing with Rivet. The output is a yoda file containing all the Rivet routine histograms. We exploit the feature that in Rivet 3.X a copy of each histogram is saved for every weight. The following command generates 500 events:

```sh
export HIGGSPRODMODE=ZH
python scripts/run_gridpack.py --gridpack gridpack_zh-HEL.tar.gz -s 1 -e 500 \
  -p HiggsTemplateCrossSectionsStage1,HiggsTemplateCrossSections \
  -o test-zh
```

where the full set of options is:

 - `--gridpack [file]` relative or absolute path to the gridpack
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

Since it is usually not feasible to generate the desired number of events in a single job, a wrapper script `scripts/launch_jobs.py` is provided which can automate running a set of jobs in parallel, each with a different RNG seed so that the events are statistically independent. This script passes through all command line options to `run_gridpack.py`, but adds several extra options to control how the jobs run:

 - `-j N` the number of jobs to run
 - `-s X` the initial RNG seed for the first job. Subsequent jobs i use `X + i` as the seed.
 - `--job-mode` supported options are interactive or submission to batch farms, e.g. condor
 - `--parallel X` number of parallel jobs to run in interactive mode
 - `--env X1=Y1,X2=Y2,..` any environment variables that should be set in the job. In this example the STXS Rivet routines require the Higgs production mode to be specified.

The following command runs four jobs, each generating 500 events:

```sh
python scripts/launch_jobs.py --gridpack gridpack_zh-HEL.tar.gz -j 4 -s 1 -e 500 \
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

and then use the script `get_scaling.py` to extract the A_j and B_jk coefficents and their statistical uncertainties:

```sh
python scripts/get_scaling.py -c config_HEL_STXS.json \
  -i test-zh/Rivet.yoda --hist "/HiggsTemplateCrossSections/pT_V" \
  --save json,txt,tex --translate-tex resources/translate_tex.json \
  --rebin 0,10,20,30,40,50,60,70,80,90,100,120,140,160,180,200,250,300,350,400
```

where the options are

 - `-c` the config file to use
 - `-i` the yoda file input
 - `--hist` the histogram in the yoda file to parametrize, note that the leading "/" is important!
 - `--save [json,txt,tex]` a comma separated list of the output formats to save in
 - `--translate-tex` a json dictionary file that converts the parameter names to latex format - only needed when `tex` is chosen in `--save`
 - `--rebin` optionally re-bin the histogram first by providing a list of the new bin edges

The terms calculated for each bin are printed to the screen, e.g.

```
-----------------------------------------------------------------
Bin 0    numEntries: 4182       mean: 1.25e-10   stderr: 1.28e-14
-----------------------------------------------------------------
Term                 |          Val |       Uncert | Rel. uncert.
-----------------------------------------------------------------
cww                  |      23.8014 |       0.0676 |       0.0028
cb                   |       6.5793 |       0.0269 |       0.0041
chw                  |       3.9987 |       0.0165 |       0.0041
chb                  |       1.1975 |       0.0049 |       0.0041
ca                   |       4.5721 |       0.0377 |       0.0083
cww^2                |     146.3984 |       1.3780 |       0.0094
cb^2                 |      11.5790 |       0.1360 |       0.0117
chw^2                |       4.4363 |       0.1007 |       0.0227
chb^2                |       0.3978 |       0.0090 |       0.0227
ca^2                 |       6.7260 |       0.1295 |       0.0193
cww * cb             |      80.3150 |       0.8199 |       0.0102
cww * chw            |      48.3712 |       0.4014 |       0.0083
cww * chb            |      14.4853 |       0.1202 |       0.0083
cww * ca             |      55.4565 |       0.7574 |       0.0137
cb * chw             |      13.3996 |       0.1229 |       0.0092
cb * chb             |       4.0127 |       0.0368 |       0.0092
cb * ca              |      17.0145 |       0.2641 |       0.0155
chw * chb            |       2.6570 |       0.0603 |       0.0227
chw * ca             |       9.1324 |       0.0968 |       0.0106
chb * ca             |       2.7348 |       0.0290 |       0.0106
```

The output in `json` format is intended for further processing. It contains information on the histogram edges as contents as well as all the scaling terms and their statistical uncertainties. The `txt` and `tex` formats provide a more readable format:

**HiggsTemplateCrossSections_pT_V.txt**
```
0-10:1 + 23.801 * cww + 6.579 * cb + 3.999 * chw + 1.197 * chb + 4.572 * ca + 146.398 * cww * cww + 11.579 * cb * cb + 4.436 * chw * chw + 0.398 * chb * chb + 6.726 * ca * ca + 80.315 * cww * cb + 48.371 * cww * chw + 14.485 * cww * chb + 55.456 * cww * ca + 13.400 * cb * chw + 4.013 * cb * chb + 17.014 * cb * ca + 2.657 * chw * chb + 9.132 * chw * ca + 2.735 * chb * ca
10-20:1 + 23.866 * cww + 6.639 * cb + 4.118 * chw + 1.233 * chb + 4.623 * ca + 146.841 * cww * cww + 11.738 * cb * cb + 4.828 * chw * chw + 0.433 * chb * chb + 6.825 * ca * ca + 80.973 * cww * cb + 50.028 * cww * chw + 14.982 * cww * chb + 55.884 * cww * ca + 13.938 * cb * chw + 4.174 * cb * chb + 17.244 * cb * ca + 2.891 * chw * chb + 9.443 * chw * ca + 2.828 * chb * ca
```

**HiggsTemplateCrossSections_pT_V.tex**

![tex table](/resources/docs/tex_table.png)

A script is available for plotting the histogram overlaying the expectation for arbitrary values of the parameters. For this ROOT (and the PyROOT interface) must be available. The script relies only on the json output file from the above step, for example:

```sh
python scripts/makePlot.py --hist HiggsTemplateCrossSections_pT_V.json -c config_HEL_STXS.json --x-title "p_{T}(Z) [GeV]" --title-left "qq #rightarrow Hl^{+}l^{-}" --title-right "HEL UFO" --ratio 0.9,1.95 --draw chw=0.005:4 cww=0.005:2 cb=0.005:8 ca=0.05:12 --show-unc --y-min 1E-9 --translate resources/translate_root.json
```

where the arguments to `--draw` are of the format `PAR1=X1,PAR2=X2,..:COLOR`. This example gives the output:


![pT_V](/resources/docs/HiggsTemplateCrossSections_pT_V.png)

## Known limitations

The following limitations currently apply. Links to GitHub issues indicate which are being actively worked on. Other issues or feature requests should also be reported there.

 - Processes are limited to one new-physics vertex (i.e. `NP <= 1` syntax required in the process definition). This is often acceptable when production and decay can be factorised, for example in the Higgs STXS, but is not a restriction we want to have in general.
 - NLO processes, and therefore models designed to operate on NLO processes are not supported. Conceptually there is not much difference to running on LO, however the technical side of the gridpack production and reweighting has to be tailored for NLO.
 - Some incompatibilities with the CMSSW environment have been reported. For now this should not be set when running EFT2Obs.
 - In future it will be possible to use a gridpack produced elsewhere as input to the event generation step. EFT2Obs will modify the gridpack to include reweighting with the model specified, which need not have been used when setting up the original process.



