# Higgs gluon fusion with SMEFTatNLO

🚧 These notes are a work-in-progress 🚧

We will limit ourselves to the `cpG`, `ctp` and `ctG` operators in SMEFTatNLO, which are known to affect the shape of the ggH pT distribution.

We have both loop-induced and tree-level contributions to consider (and the interference between them).
These cannot all be evaluated in one Madgraph run, so instead we break it into three parts.
In each one we will generate events according to the SM, i.e. loop only, and set `NP=0`.
The difference comes in the reweighting step, where we will use the functionality to change the process definition to be loop-only, tree-only or loop-tree interference.
Summing the Rivet output from the three reweighting configurations should give us the correct total scaling.

A set of example input cards are provided in the `cards/ggF-SMEFTatNLO-[0/1/2]jet-[loop/tree/tree-loop]` directories.
The 0- and 1-jet processes can be run interactively fairly quickly, whereas the 2jet processes will probably need batch submission for the gridpack generation.

⚠️ At some point updates to the Madgraph external package installation caused problems with compiling these processes.
Setting `collier = None` in `MG5_aMC_v2_6_7/input/mg5_configuration.txt` might work as a temporary fix.

### Model restrict file

A restrict file has been prepared which limits NP vertices to the operators above:

```shell
cp setup/SMEFTatNLO__restrict_ggFshape.dat MG5_aMC_v2_6_7/models/SMEFTatNLO/restrict_ggFshape.dat
```

### Process definition

For the 2-jet case we exclude bbH production, e.g.:

```
define pl = g u c d s u~ c~ d~ s~

generate p p > H QED=1 NP=0 [noborn=QCD]
add process p p > H j QED=1 NP=0 [noborn=QCD]
add process pl pl > H j j QED=1 NP=0 [noborn=QCD]
```

### make_config

Create the EFT2Obs json config file:

```shell
python scripts/make_config.py -p ggF-SMEFTatNLO \
 -o config_SMEFTatNLO_ggFshape.json --pars dim6:8 dim62f:19,24 \
 --def-val 0.01 --def-sm 0 --def-gen 1E-8 --set-inactive dim6:1=1.000000e+03
```

### reweight_card

We need to inject the correct `change process` lines. Example for 1jet cards:

```shell
python scripts/make_reweight_card.py \
 config_SMEFTatNLO_ggFshape.json cards/ggF-SMEFTatNLO-1jet-loop/reweight_card.dat \
 --prepend \
  'change process p p > h NP=2 QED=1 [noborn=QCD]' \
  'change process p p > h j NP=2 QED=1 [noborn=QCD] --add'

python scripts/make_reweight_card.py \
 config_SMEFTatNLO_ggFshape.json cards/ggF-SMEFTatNLO-1jet-tree/reweight_card.dat \
 --prepend \
  'change process p p > h NP=2 QED=1' \
  'change process p p > h j NP=2 QED=1 --add'

python scripts/make_reweight_card.py \
 config_SMEFTatNLO_ggFshape.json cards/ggF-SMEFTatNLO-1jet-tree-loop/reweight_card.dat \
 --prepend \
  'change process p p > h NP=2 QED=1 [virt=QCD]' \
  'change process p p > h j NP=2 QED=1 [virt=QCD] --add'
```

### make_gridpack

```shell
# 1-jet (using four cores, takes a few mins per job)

for TYPE in loop tree tree-loop; do ./scripts/make_gridpack.sh ggF-SMEFTatNLO-1jet-${TYPE} 0 4; done

# 2-jet (submit to condor using 8 cores, takes several hours)

for TYPE in loop tree tree-loop; do python scripts/launch_gridpack.py ggF-SMEFTatNLO-2jet-${TYPE} -c 8 \
 --job-mode condor --task-name gp-ggF-SMEFTatNLO-2jet-${TYPE} --dir jobs/ \
 --sub-opts '+MaxRuntime = 36000\nRequestCpus = 8\nrequirements = (OpSysAndVer =?= "CentOS7")'; done
```

### run_gridpack

Local test run for 1-jet:

```shell
HIGGSPRODMODE=GGF python scripts/run_gridpack.py --seed 1 -e 1000 -p HiggsTemplateCrossSections \
 --gridpack gridpack_ggF-SMEFTatNLO-1jet-loop.tar.gz -o localtest-ggF-SMEFTatNLO-1jet-loop

HIGGSPRODMODE=GGF python scripts/run_gridpack.py --seed 1 -e 1000 -p HiggsTemplateCrossSections \
 --gridpack gridpack_ggF-SMEFTatNLO-1jet-tree.tar.gz -o localtest-ggF-SMEFTatNLO-1jet-tree

HIGGSPRODMODE=GGF python scripts/run_gridpack.py --seed 1 -e 1000 -p HiggsTemplateCrossSections \
 --gridpack gridpack_ggF-SMEFTatNLO-1jet-tree-loop.tar.gz -o localtest-ggF-SMEFTatNLO-1jet-tree-loop
```

Batch run for 2-jet:

```shell
DIR="ggF-SMEFTatNLO-2jet-loop"; python scripts/launch_jobs.py \
 --gridpack gridpack_${DIR}.tar.gz -j 200 -s 1 -e 2500 -p HiggsTemplateCrossSections \
 -o test-${DIR} --sub-opts '+MaxRuntime = 18000\nrequirements = (OpSysAndVer =?= "CentOS7")' \
 --task-name test-${DIR} --dir jobs --job-mode condor --env "HIGGSPRODMODE=GGF"
```

### yodamerge

Note that the options `--add` and `--no-veto-empty` are important.
The first tells yodamege that we want to sum the individual histograms (instead of the usual averaging procedure).
The `--no-veto-empty` option stops yodamerge from skipping empty histograms.
These are expected to occur for some reweighting points, e.g. where there are no contributions from a particular operator for tree or loop.
Skipping those histograms in the sum causes the histogram statistics to be incorrect for the number of entries, and we rely on these for giving the correct predictions for the scaling terms.

Example of merging the output from the 1-jet test runs above:

```shell
mkdir localtest-ggF-SMEFTatNLO-1jet
yodamerge -o localtest-ggF-SMEFTatNLO-1jet/RivetFullNoVeto.yoda \
 localtest-ggF-SMEFTatNLO-1jet-*/Rivet_1.yoda --add --no-veto-empty
```

### get_scaling

```shell
python scripts/get_scaling.py -c config_SMEFTatNLO_ggFshape.json \
 -i localtest-ggF-SMEFTatNLO-1jet/RivetFullNoVeto.yoda \
 --hist "/HiggsTemplateCrossSections/HTXS_stage1_2_pTjet30" \
 --bin-labels resources/STXS_bin_labels.json
```







