# EFT parameterisations for CMS-SMP-20-005

To generate the EFT parameterisations for the $\text{W}\gamma$ measurement using the cards provided in this directory, copy the directory to `EFT2Obs/cards` and follow the instructions [here](../README.md). The full setup starting from scratch is described in this README.


## Process definition

Create a subdirectory `WG-SMEFTsim3` in `EFT2Obs/cards` and add a `proc_card.dat` specifying the model and defining the process:
```
import model SMEFTsim_topU3l_MwScheme_UFO-massless

define lep = mu+ mu- e+ e-
define nu = vm vm~ ve ve~

generate p p > lep nu a NP<=1 @1
add process p p > lep nu a j NP<=1 @2
add process p p > lep nu a j j QED<=4 NP<=1 @3

output WG-SMEFTsim3 -nojpeg
```


## Set up cards

From the main EFT2Obs directory, run
```sh
./scripts/setup_process.sh WG-SMEFTsim3
```
This creates the process directory `MG5_aMC_v2_6_7/WG-SMEFTsim3` and adds two new cards to `cards/WG-SMEFTsim3`: `pythia8_card.dat` and `run_card.dat`. 

In `pythia8_card.dat`, the line `partonlevel:mpi = off` can be uncommented for now. This disables multiparton interactions, which makes the event generation faster.

In `run_card.dat`, two changes have to be made:
- `True = use_syst`: change to `False = use_syst`
- `systematics = systematics_program`: change to `none = systematics_program`

This is necessary because the extra weights that appear when `True = use_syst` is set are not handled correctly by EFT2Obs.

Next, we apply some cuts in the `run_card.dat` to avoid generating events in a phase space that is not used in the analysis:
- `130.0 = pta`
- `25.0  = ptl`
- `35.0  = misset`
- `0.4 = drjl`
- `2.6 = etaa`
- `2.6 = etal`

The remaining cuts we leave at their default values. `xqcut`, a parameter needed for parton matching/merging, we also leave at the default value of `30` for now.


## Identify EFT operators

To automatically detect the EFT operators this process is sensitive to, and set up the reweighting, run
```sh
python scripts/auto_detect_operators.py -p WG-SMEFTsim3
```
This creates two new files in the `cards` subdirectories: `config.json` and `reweight_card.dat`. 

The last file we need to add is `param_card.dat`. To create it, run
```sh
python scripts/make_param_card.py -p WG-SMEFTsim3 -c cards/WG-SMEFTsim3/config.json \
  -o cards/WG-SMEFTsim3/param_card.dat
```

At this point, the contents of the `cards` subdirectory should be exactly the same as the cards provided in this directory.



## Make gridpack

The gridpacks can be created locally with
```sh
./scripts/make_gridpack.sh WG-SMEFTsim3 0 64
```
If this takes too long, use the script `launch_gridpack.py`:
```sh
python scripts/launch_gridpack.py WG-SMEFTsim3 -c 64 --job-mode slurm
```
The file `gridpack_WG-SMEFTsim3.tar.gz` will be copied to the main EFT2Obs directory.


## Generate events

Now we can generate events. This will run through the event generation with `MG5_aMC@NLO`, EFT reweighting, showering with `Pythia`, and event selection with `Rivet`. Now you can generate 1 million events in a set of slurm jobs:
```sh
python scripts/launch_jobs.py --gridpack gridpack_WG-SMEFTsim3.tar.gz -j 50 -s 1 -e 20000 \
  -p CMS_2021_PAS_SMP_20_005 -o WG-SMEFTsim3 --task-name WG --dir jobs --job-mode slurm
```
When using condor, replace `--job-mode slurm` by `--job-mode condor` and add `--sub-opts '+MaxRuntime = 14400\nrequirements = (OpSysAndVer =?= "CentOS7")'`.


## EFT parameterisation

The output of the previous command is 50 YODA files containing all the Rivet routine histograms with a copy for each weight. Merge the yoda files using
```sh
yodamerge -o WG-SMEFTsim3/RivetTotal.yoda WG-SMEFTsim3/Rivet_* --no-veto-empty
```
Then use the script `get_scaling.py` to produce the JSON files with the EFT scaling parameters $A_{i}$ and $B_{ij}$ (first, copy this file to the main EFT2Obs directory: `eft_exercise_bin_labels.json`):
```sh
python scripts/get_scaling.py -i WG-SMEFTsim3/RivetTotal.yoda -o scaling_WG-SMEFTsim3-d54-x01-y01 \
  --hist "/CMS_2021_PAS_SMP_20_005/d54-x01-y01" --bin-labels eft_exercise_bin_labels.json \
  -c cards/WG-SMEFTsim3/config.json
python scripts/get_scaling.py -i WG-SMEFTsim3/RivetTotal.yoda -o scaling_WG-SMEFTsim3-d55-x01-y01 \
  --hist "/CMS_2021_PAS_SMP_20_005/d55-x01-y01" --bin-labels eft_exercise_bin_labels.json \
  -c cards/WG-SMEFTsim3/config.json
python scripts/get_scaling.py -i WG-SMEFTsim3/RivetTotal.yoda -o scaling_WG-SMEFTsim3-d56-x01-y01 \
  --hist "/CMS_2021_PAS_SMP_20_005/d56-x01-y01" --bin-labels eft_exercise_bin_labels.json \
  -c cards/WG-SMEFTsim3/config.json
```
