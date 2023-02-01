from __future__ import print_function
from builtins import range
from array import array
import math
import json
import argparse
import yoda
from eftscaling import EFT2ObsHist, EFTScaling

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

bin_labels = list()
if args.bin_labels is not None:
    with open(args.bin_labels) as jsonfile:
        bin_labels = json.load(jsonfile)[args.hist]

hname = args.hist

aos = yoda.read(args.input, asdict=True)

n_pars = len(pars)
n_hists = 1 + n_pars * 2 + (n_pars * n_pars - n_pars) / 2

hists = []
for i in range(n_hists):
    if args.nlo:
        hists.append(aos['%s[rw%.4i_nlo]' % (hname, i)])
    else:
        hists.append(aos['%s[rw%.4i]' % (hname, i)])

# print hists
is2D = isinstance(hists[0], yoda.Histo2D)

if args.rebin is not None and not is2D:
    rebin = [float(X) for X in args.rebin.split(',')]
    for h in hists:
        h.rebinTo(rebin)

nbins = hists[0].numBins

if is2D:
    edges = [[list(hists[0].bins[ib].xEdges), list(hists[0].bins[ib].yEdges)] for ib in range(nbins)]
    # areas = list(hists[0].volumes())
    areas = [hists[0].bins[ib].volume for ib in range(nbins)]
else:
    edges = [list(hists[0].bins[ib].xEdges) for ib in range(nbins)]
    areas = list(hists[0].areas())
    # print (areas,  [hists[0].bins[ib].sumW for ib in range(nbins)])

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
    sumW=[[hist.bins[ib].sumW for ib in range(nbins)] for hist in hists],
    sumW2=[[hist.bins[ib].sumW2 for ib in range(nbins)] for hist in hists],
    numEntries=[[hist.bins[ib].numEntries for ib in range(nbins)] for hist in hists],
    bin_edges=edges,
    bin_labels=bin_labels)

e2ohist.printToScreen()
e2oscaling = EFTScaling.fromEFT2ObsHist(e2ohist)

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
