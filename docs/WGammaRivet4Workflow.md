# WGamma Rivet4 Workflow

This document describes the end-to-end workflow used in this branch for:

1. Running the WGamma Rivet analysis with Rivet v4, including 3D EFT histograms.
2. Producing EFT scaling JSON files from merged YODA outputs.
3. Adding bin labels for 1D and 3D EFT histograms.
4. Plotting scaling outputs.

## 1. Environment and when to use each

Use CMSSW environment for Rivet v4 steps (`CMSSW_15_0_15` has Rivet v4, you don't need to install it.):

```bash
cd /path/to/CMSSW_15_0_15/src
cmsenv
cd EFT2Obs
```

Important : Use `source env.sh` when working with Rivet v3 and the original EFT2Obs flow without the Rivet v4 updates.


## 2. Rivet v4 plugin updates

For details of the Rivet v3 to v4 migration, see:

- https://gitlab.com/hepcedar/rivet/-/blob/release-4-1-x/doc/tutorials/mig3to4.md

Files I have updated/added:

- `RivetPlugins/CMS_2021_PAS_SMP_20_005.cc`
- `RivetPlugins/CMS_2021_PAS_SMP_20_005.yoda`
- `scripts/eftscaling_rivet4.py`
- `scripts/get_scaling_rivet4.py`
- `scripts/makePlot_rivet4.py`
- `scripts/set_bin_labels_wgamma.py`
- `scripts/run_rivet4_job.sh`
- `scripts/submit_rivet4.py`

Main analysis updates:

1. Added 3D histogram booking:
   - `eft_pt_phi_theta_3d`
   - pT edges: `[150, 200, 300, 500, 800, 1500]`
   - phi edges: `[0, pi/6, pi/3, pi/2]`
   - theta edges: `[0, pi/3, 2pi/3, pi]`

2. Added the 3x3 split 1D pT histograms:
   - `eft_ext_photon_pt_phi_<i>_theta_<j>` for `i=0..2`, `j=0..2`

3. Kept existing EFT histograms (`eft_phi`, `eft_theta`, and split variants) and filled them consistently with the same kinematics.

Reference data update:

- `RivetPlugins/CMS_2021_PAS_SMP_20_005.yoda` was migrated to the Rivetv4-compatible binned estimate format.

## 3. /RAW in Rivet v4 outputs

In Rivet v4, the YODA output can contain two versions of the same histogram:
- /CMS_... : the “final” objects written after finalize() (often stored as estimate-style objects)
- /RAW/CMS_... : an internal “pre-finalize” copy kept for merging and re-scaling workflows (this is a Rivet v4 feature)

In our workflow, scripts/get_scaling_rivet4.py needs a histogram type that supports weight scaling. If the requested /CMS_... object cannot be scaled, the script automatically switches to the corresponding /RAW/CMS_... object.

Practical rule:
- In commands, always request the /CMS_... path.
- If you see an INFO message about switching to /RAW/..., that is expected and you can ignore it.
- Label mapping supports both standard and RAW paths.

## 4. Label generation

File:

- `scripts/set_bin_labels_wgamma.py`

It generates:

- `bin_labels_wgamma.json`

Current behavior:

1. Labels are stored under /CMS_... keys; get_scaling.py can also apply them when using /RAW/... .
2. Includes labels for `eft_phi`, `eft_theta`, split histograms, and `eft_pt_phi_theta_3d`.
3. Uses the 3D bin order: theta-outer index, phi-middle index, pT-inner index.

Generate labels:

```bash
python3 scripts/set_bin_labels_wgamma.py
```

## 5. Producing scaling JSON from merged YODA

Main script:

- `scripts/get_scaling_rivet4.py`

Relevant updates:

1. YODA supports (`xMin/xMax`, `dVol`, 3D bin edges).
2. Histogram path resolver with `/CMS_ -> /RAW/CMS_` fallback.
3. Bin label mapping support for RAW/CMS paths.

Example for 1D phi:

```bash
python3 scripts/get_scaling_rivet4.py -c cards/WG-NPall_400-800/config.json -i merged_yoda/RivetTotal_cw.yoda --hist "/CMS_2021_PAS_SMP_20_005/eft_phi" --save json --translate-tex resources/translate_tex.json --bin-labels bin_labels_wgamma.json
```

Example for 3D histogram:

```bash
python3 scripts/get_scaling_rivet4.py -c cards/WG-NPall_400-800/config.json -i merged_yoda/RivetTotal_cw.yoda --hist "/CMS_2021_PAS_SMP_20_005/eft_pt_phi_theta_3d" --save json --translate-tex resources/translate_tex.json --bin-labels bin_labels_wgamma.json
```

## 6. Plotting scaling outputs

Main script:

- `scripts/makePlot_rivet4.py`

Example:

```bash
python3 scripts/makePlot_rivet4.py --hist CMS_2021_PAS_SMP_20_005_eft_phi.json -c cards/WG-NPall_400-800/config.json --x-title "\\phi" --title-right "W#gamma, #sqrt{s} = 13.6 TeV" --ratio 0.5,2.0 --draw cw=0.1:6 cw=0.2:215 cw=0.4:68 cw=0.6:221 cw=1.:28 --show-unc --y-min 1E-9 --translate resources/translate_root.json --unit-area
```

## 7. HepMC2 to HepMC3 conversion

This setup currently converts HepMC2 files to HepMC3 before running Rivet v4 because the existing production files I have already saved are in HepMC2 format and Rivet v4 in CMSSW_15_0_15 reads HepMC3 only.

### Can HepMC3 be produced directly?

Direct HepMC3 production is possible if the event generation and shower setup is configured to write HepMC3 output.

Practical note:

1. If your production step already writes HepMC3, you can skip the conversion stage.
2. If your production step writes HepMC2 (current default in this workflow), keep the conversion step.

In other words, direct HepMC3 is possible for new productions, but conversion is required for legacy HepMC2 datasets.

## 8. Batch processing scripts

Files:

- `scripts/run_rivet4_job.sh`
- `scripts/submit_rivet4.py`

Purpose:

1. Convert HepMC2 to HepMC3 when needed.
2. Run Rivet4 analysis for each input file.
3. Write YODA outputs.

## 9. Typical run order

1. Initialize cmssw: `cmsenv` .
2. Generate/update label map (`scripts/set_bin_labels_wgamma.py`).
3. Merge YODA files if needed.
4. Run `scripts/get_scaling_rivet4.py` for target histograms.
5. Plot with `scripts/makePlot_rivet4.py` .

