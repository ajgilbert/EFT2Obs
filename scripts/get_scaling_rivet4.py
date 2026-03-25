from __future__ import print_function
from builtins import range
from array import array
import math
import json
import argparse
import sys
import yoda
from eftscaling_rivet4 import EFT2ObsHist, EFTScaling

parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', default="Rivet.yoda")
parser.add_argument('--output', '-o', default=None)
parser.add_argument('--config', '-c', default="Rivet.yoda")
parser.add_argument('--hist', default='/HiggsTemplateCrossSectionsStage1/HTXS_stage1_pTjet30')
parser.add_argument('--exclude-rel', default=None, help="Exclude terms with magnitude below this value relative to largest")
parser.add_argument('--rebin', default=None, help="Comma separated list of new bin edges")
parser.add_argument('--save', default='json', help="Comma separated list of output formats (json, txt, latex)")
parser.add_argument('--save-raw', action='store_true', help="Save the raw histogram information as JSON, for further processing")
parser.add_argument('--legacy', action='store_true', help="Use the legacy format for json ouput (if requested)")
parser.add_argument('--translate-tex', default=None, help="json file to translate parameter names to latex")
parser.add_argument('--translate-txt', default=None, help="json file to translate parameter names in the text file")
parser.add_argument('--bin-labels', default=None, help="json file to translate bin labels")
parser.add_argument('--nlo', action='store_true', help="Set if weights came from NLO reweighting")
parser.add_argument('--filter-params', default=None, help="Specify a subset of parameters to include")
parser.add_argument('--print-style', default="perBin", choices=["perBin", "perTerm"], help="Specify the format for printing to the screen")
parser.add_argument('--color-above', default=None, type=float, help="When using --print-style perTerm, highlight relative uncertainties above this threshold")
args = parser.parse_args()


with open(args.config) as jsonfile:
    cfg = json.load(jsonfile)
pars = cfg['parameters']
defs = cfg['parameter_defaults']

if args.output is None:
    auto_name = args.hist
    if auto_name.startswith('/'):
        auto_name = auto_name[1:]
    args.output = auto_name.replace('/', '_')

save_formats = args.save.split(',')

translate_tex = {}
if args.translate_tex is not None:
    with open(args.translate_tex) as jsonfile:
        translate_tex = json.load(jsonfile)

translate_txt = {}
if args.translate_txt is not None:
    with open(args.translate_txt) as jsonfile:
        translate_txt = json.load(jsonfile)

ao_dict = yoda.read(args.input, asdict=True)

def _has_scalable(hist):
    return hasattr(hist, 'scaleW')


def _resolve_hist_path(requested, available):
    if requested in available and _has_scalable(available[requested]):
        return requested
    if requested in available:
        print(f"INFO: requested {requested} cannot be scaled (BinnedEstimate); looking for RAW fallback")
    if requested.startswith('/CMS_'):
        raw_path = '/RAW' + requested
        if raw_path in available:
            print(f"INFO: switching from {requested} to {raw_path} so get_scaling can scale weights")
            return raw_path
        raw_alt = requested.replace('/CMS_', '/RAW/CMS_', 1)
        if raw_alt in available:
            print(f"INFO: switching from {requested} to {raw_alt} so get_scaling can scale weights")
            return raw_alt
    if requested.startswith('/RAW/'):
        cms_alt = requested.replace('/RAW/', '/', 1)
        if cms_alt in available:
            print(f"INFO: raw path {requested} exists but using {cms_alt} instead")
            return cms_alt
    print(f"ERROR: histogram {requested} not found in {args.input}")
    print("Available histogram paths (first 5):")
    for path in list(available.keys())[:5]:
        print('  ', path)
    sys.exit(1)

hname = _resolve_hist_path(args.hist, ao_dict)

bin_labels = list()
if args.bin_labels is not None:
    with open(args.bin_labels) as jsonfile:
        label_map = json.load(jsonfile)
    if hname in label_map:
        bin_labels = label_map[hname]
    elif args.hist in label_map:
        print(f"INFO: bin label map had {args.hist} entries; using them for {hname}")
        bin_labels = label_map[args.hist]
    elif hname.startswith('/RAW/') and hname.replace('/RAW/', '/', 1) in label_map:
        alt = hname.replace('/RAW/', '/', 1)
        print(f"INFO: using bin labels from {alt} for resolved histogram {hname}")
        bin_labels = label_map[alt]
    elif args.hist.startswith('/RAW/') and args.hist.replace('/RAW/', '/', 1) in label_map:
        alt = args.hist.replace('/RAW/', '/', 1)
        print(f"INFO: using bin labels from {alt} for requested histogram {args.hist}")
        bin_labels = label_map[alt]
    else:
        print(f"WARNING: neither {hname} nor {args.hist} found in {args.bin_labels}, leaving bin_labels empty")
        bin_labels = []

n_pars = len(pars)
n_hists = int(1 + n_pars * 2 + (n_pars * n_pars - n_pars) / 2)

filter = list()
if args.filter_params is not None:
    filter = args.filter_params.split(',')

hists = []
for i in range(n_hists):
    if args.nlo:
        hists.append(ao_dict['%s[rw%.4i_nlo]' % (hname, i)])
    else:
        hists.append(ao_dict['%s[rw%.4i]' % (hname, i)])

# print hists
is2D = isinstance(hists[0], yoda.Histo2D)
is3D = hasattr(yoda, 'Histo3D') and isinstance(hists[0], yoda.Histo3D)

if args.rebin is not None and not is2D and not is3D:
    rebin = [float(X) for X in args.rebin.split(',')]
    for h in hists:
        h.rebinTo(rebin)

nbins = hists[0].numBins()

# Helper: bin edge accessors compatible with YODA 9 (BinWrapper objects use
# .xMin()/.xMax() etc. rather than .xEdges()/.yEdges(); areas via .dVol())
def _get_edges_and_areas(hist, n):
    bins = hist.bins()
    if is3D:
        # Flatten 3D edges to [xlo, xhi, ylo, yhi, zlo, zhi] per bin
        edges_out = [[b.xMin(), b.xMax(), b.yMin(), b.yMax(), b.zMin(), b.zMax()]
                     for b in bins[:n]]
    elif is2D:
        edges_out = [[[b.xMin(), b.xMax()], [b.yMin(), b.yMax()]] for b in bins[:n]]
    else:
        edges_out = [[b.xMin(), b.xMax()] for b in bins[:n]]
    areas_out = [b.dVol() for b in bins[:n]]
    return edges_out, areas_out

edges, areas = _get_edges_and_areas(hists[0], nbins)
if not is2D and not is3D:
    print(nbins)

for p in pars:
    for k in defs:
        if k not in p:
            p[k] = defs[k]

n_divider = 65


def PrintEntry(label, val, err):
    print('%-20s | %12.4f | %12.4f | %12.4f' % (label, val, err, abs(err / val)))


# Generate a list of constants that need to be divided out of each entry
eftconstants = [1.] # for the SM
for ip in range(len(pars)):
    eftconstants.append(pars[ip]['val'])
    eftconstants.append(pars[ip]['val'] * pars[ip]['val'])
for ix in range(0, len(pars)):
    for iy in range(ix + 1, len(pars)):
        eftconstants.append(pars[ix]['val'] * pars[iy]['val'])
assert(len(eftconstants) == len(hists))

for ip, hist in enumerate(hists):
    hist.scaleW(1. / eftconstants[ip])


def initTerms(params):
    points = list()
    points.append(list('1'))
    for i in range(len(params)):
        points.append([params[i]])
        points.append([params[i], params[i]])
    for ix in range(0, len(params)):
        for iy in range(ix + 1, len(params)):
            points.append([params[ix], params[iy]])
    return points

e2ohist = EFT2ObsHist(
    terms=initTerms([X['name'] for X in pars]),
    sumW=[[hist.bins()[ib].sumW() for ib in range(nbins)] for hist in hists],
    sumW2=[[hist.bins()[ib].sumW2() for ib in range(nbins)] for hist in hists],
    numEntries=[[hist.bins()[ib].numEntries() for ib in range(nbins)] for hist in hists],
    bin_edges=edges,
    bin_labels=bin_labels)

e2ohist.printToScreen(style=args.print_style, colorAbove=args.color_above)
e2oscaling = EFTScaling.fromEFT2ObsHist(e2ohist, filter=filter)

if args.save_raw:
    print('>> Saving EFT2ObsHist as %s_raw.json' % args.output)
    e2ohist.writeToJSON('%s_raw.json' % args.output)

if 'json' in save_formats:
    print('>> Saving histogram parametrisation to %s.json' % args.output)
    e2oscaling.writeToJSON('%s.json' % args.output, legacy=args.legacy)

if 'yaml' in save_formats:
    print('>> Saving histogram parametrisation to %s.yaml' % args.output)
    e2oscaling.writeToYAML('%s.yaml' % args.output)

if 'txt' in save_formats:
    print('>> Saving histogram parametrisation to %s.txt' % args.output)
    e2oscaling.writeToTxt('%s.txt' % args.output, translate_txt)

if 'tex' in save_formats:
    print('>> Saving histogram parametrisation to %s.tex' % args.output)
    e2oscaling.writeToTex('%s.tex' % args.output, translate_tex)
