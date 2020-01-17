# import ROOT
# import plotting as plot
from array import array
import math
import sys
import json
import argparse
import yoda


def BinStats(b):
    if b.numEntries == 0:
        return [0., 0.]
    mean = b.sumW / b.numEntries
    stderr2 = (b.sumW2 / b.numEntries) - math.pow(mean, 2)
    if stderr2 < 0.:
        stderr = 0.
    else:
        stderr = math.sqrt(stderr2 / b.numEntries)
    return [mean, stderr]


def Translate(arg, translations):
    if arg in translations:
        return translations[arg]
    else:
        return arg

parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', default="Rivet.yoda")
parser.add_argument('--output', '-o', default=None)
parser.add_argument('--config', '-c', default="Rivet.yoda")
parser.add_argument('--hist', default='/HiggsTemplateCrossSectionsStage1/HTXS_stage1_pTjet30')
parser.add_argument('--exclude-rel', default=None, help="Exclude terms with magnitude below this value relative to largest")
parser.add_argument('--rebin', default=None, help="Comma separated list of new bin edges")
parser.add_argument('--save', default='json', help="Comma separated list of output formats (json, txt, latex)")
parser.add_argument('--translate-tex', default=None, help="json file to translate parameter names to latex")
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

# hname = '/HiggsTemplateCrossSectionsStage1/HTXS_stage1_pTjet30'
hname = args.hist

aos = yoda.read(args.input, asdict=True)

n_pars = len(pars)
n_hists = 1 + n_pars * 2 + (n_pars * n_pars - n_pars) / 2

hists = []
for i in xrange(n_hists):
    hists.append(aos['%s[rw%.4i]' % (hname, i)])

#hists = [h for h in aos if h.path.startswith(hname)]
#hists = hists[1:]  # skip the first one
print hists

# rebin = None
if args.rebin is not None:
    rebin = [float(X) for X in args.rebin.split(',')]
    for h in hists:
        h.rebinTo(rebin)
# for h in hists:
#     print h
#     print h.path, h.sumW(), math.sqrt(h.sumW2())


nbins = hists[0].numBins


res = {
    "edges": list(hists[0].xEdges()),
    "areas": list(hists[0].areas()),
    "parameters": [X['name'] for X in pars],
    "bins": []
}

for p in pars:
    for k in defs:
        if k not in p:
            p[k] = defs[k]

n_divider = 65


def PrintEntry(label, val, err):
    print '%-20s | %12.4f | %12.4f | %12.4f' % (label, val, err, abs(err / val))


for ib in xrange(nbins):
    terms = []
    sm = BinStats(hists[0].bins[ib])
    print '-' * n_divider
    print 'Bin %-4i numEntries: %-10i mean: %-10.3g stderr: %-10.3g' % (ib, hists[0].bins[ib].numEntries, sm[0], sm[1])
    print '-' * n_divider
    if sm[0] == 0:
        res["bins"].append(terms)
        continue
    else:
        print '%-20s | %12s | %12s | %12s' % ('Term', 'Val', 'Uncert', 'Rel. uncert.')
        print '-' * n_divider
    for ip in xrange(len(pars)):
        lin = BinStats(hists[ip * 2 + 1].bins[ib])
        if lin[0] == 0.:
            continue
        lin[0] = lin[0] / (sm[0] * pars[ip]['val'])
        lin[1] = lin[1] / (sm[0] * pars[ip]['val'])
        PrintEntry(pars[ip]['name'], lin[0], lin[1])
        terms.append([lin[0], lin[1], pars[ip]['name']])
    for ip in xrange(len(pars)):
        sqr = BinStats(hists[ip * 2 + 2].bins[ib])
        if sqr[0] == 0.:
            continue
        sqr[0] = sqr[0] / (sm[0] * pars[ip]['val'] * pars[ip]['val'])
        sqr[1] = sqr[1] / (sm[0] * pars[ip]['val'] * pars[ip]['val'])

        PrintEntry('%s^2' % pars[ip]['name'], sqr[0], sqr[1])
        # print '(%f +/- %f) * %s^2 (%f)' % (sqr[0], sqr[1], pars[ip]['name'], sqr[1]/sqr[0])
        terms.append([sqr[0], sqr[1], pars[ip]['name'], pars[ip]['name']])
    ic = 0
    for ix in xrange(0, len(pars)):
        for iy in xrange(ix + 1, len(pars)):
            cross = BinStats(hists[1 + (len(pars) * 2) + ic].bins[ib])
            if cross[0] != 0.:
                cross[0] = cross[0] / (sm[0] * pars[ix]['val'] * pars[iy]['val'])
                cross[1] = cross[1] / (sm[0] * pars[ix]['val'] * pars[iy]['val'])
                # print '(%f +/- %f) * %s *%s (%f)' % (cross[0], cross[1], pars[ix]['name'], pars[iy]['name'], cross[1]/cross[0])
                PrintEntry('%s * %s' % (pars[ix]['name'], pars[iy]['name']), cross[0], cross[1])
                terms.append([cross[0], cross[1], pars[ix]['name'], pars[iy]['name']])
            ic += 1
    filtered_terms = []
    for term in terms:
        if term[0] < 1E-5:
            continue
        filtered_terms.append(term)
    res["bins"].append(filtered_terms)

if 'json' in save_formats:
    print '>> Saving histogram parametrisation to %s.json' % args.output
    with open('%s.json' % args.output, 'w') as outfile:
            outfile.write(json.dumps(res, sort_keys=False, indent=2, separators=(',', ': ')))

if 'txt' in save_formats:
    txt_out = []
    for ib in xrange(nbins):
        line = '%g-%g:1' % (res['edges'][ib], res['edges'][ib + 1])
        for term in res['bins'][ib]:
            terms = []
            terms.append('%.3f' % term[0])
            terms.extend(term[2:])
            line += (' + ' + (' * '.join(terms)))
        txt_out.append(line)
    with open('%s.txt' % args.output, 'w') as outfile:
            outfile.write('\n'.join(txt_out))

if 'tex' in save_formats:
    txt_out = []
    txt_out.append(r"""\begin{table}[htb]
    \centering
    \setlength\tabcolsep{10pt}
    \begin{tabular}{|c|c|}
        \hline""")
    for ib in xrange(nbins):
        line = '$%g$--$%g$ & ' % (res['edges'][ib], res['edges'][ib + 1])
        line += r"""\parbox{0.8\columnwidth}{$1 """
        for term in res['bins'][ib]:
            terms = []
            terms.append('%.1f\\,' % term[0])
            if len(term[2:]) == 2 and term[2] == term[3]:
                terms.append('{%s}^{2}' % Translate(term[2], translate_tex))
            else:
                terms.extend([Translate(X, translate_tex) for X in term[2:]])
            line += (' + ' + ('\\,'.join(terms)))
        line += """$} \\\\"""
        txt_out.append(line)
        txt_out.append("""\\hline""")
    txt_out.append(r"""\end{tabular}
    \end{table}""")
    with open('%s.tex' % args.output, 'w') as outfile:
            outfile.write('\n'.join(txt_out))

#\parbox{0.6\columnwidth}{$175\:c_{WW}\,\!^{2} + 14.3\:c_{B}\,\!^{2} + 10.4\:c_{HW}\,\!^{2} + 7.78\:c_{A}\,\!^{2} + 97.5\:c_{WW}\,c_{B} + 74.5\:c_{WW}\,c_{HW} + 64.2\:c_{WW}\,c_{A} + 21\:c_{B}\,c_{HW} + 20.1\:c_{B}\,c_{A} + 12.8\:c_{HW}\,c_{A}$} \\
