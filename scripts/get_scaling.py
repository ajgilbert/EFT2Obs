from array import array
import math
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

bin_labels = {}
if args.bin_labels is not None:
    with open(args.bin_labels) as jsonfile:
        bin_labels = json.load(jsonfile)

hname = args.hist

aos = yoda.read(args.input, asdict=True)

n_pars = len(pars)
n_hists = 1 + n_pars * 2 + (n_pars * n_pars - n_pars) / 2

hists = []
for i in xrange(n_hists):
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
    edges = [[list(hists[0].bins[ib].xEdges), list(hists[0].bins[ib].yEdges)] for ib in xrange(nbins)]
    # areas = list(hists[0].volumes())
    areas = [hists[0].bins[ib].volume for ib in xrange(nbins)]
else:
    edges = [list(hists[0].bins[ib].xEdges) for ib in xrange(nbins)]
    areas = list(hists[0].areas())

res = {
    "edges": edges,
    "areas": areas,
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

if args.bin_labels is not None:
    res["bin_labels"] = bin_labels[args.hist]

for ib in xrange(nbins):
    terms = []
    sm = BinStats(hists[0].bins[ib])
    print '-' * n_divider
    print 'Bin %-4i numEntries: %-10i mean: %-10.3g stderr: %-10.3g' % (ib, hists[0].bins[ib].numEntries, sm[0], sm[1])
    extra_label = ''
    if args.bin_labels is not None:
        extra_label += ', label=%s' % res["bin_labels"][ib]
    print '         edges: %s%s' % (res['edges'][ib], extra_label)
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
        if abs(term[0]) < 1E-10:
            continue
        filtered_terms.append(term)
    res["bins"].append(filtered_terms)

if 'json' in save_formats:
    print '>> Saving histogram parametrisation to %s.json' % args.output
    with open('%s.json' % args.output, 'w') as outfile:
            outfile.write(json.dumps(res, sort_keys=False, indent=2, separators=(',', ': ')))

if 'txt' in save_formats:
    print '>> Saving histogram parametrisation to %s.txt' % args.output
    txt_out = []
    for ib in xrange(nbins):
        if is2D:
            bin_label = '%g-%g,%g-%g' % (res['edges'][ib][0][0], res['edges'][ib][0][1], res['edges'][ib][1][0], res['edges'][ib][1][1])
        else:
            bin_label = '%g-%g' % (res['edges'][ib][0], res['edges'][ib][1])
        if args.bin_labels is not None:
            bin_label = bin_labels[args.hist][ib]
        line = '%s:1' % bin_label
        for term in res['bins'][ib]:
            terms = []
            terms.append('%.3f' % term[0])
            terms.extend([Translate(X, translate_txt) for X in term[2:]])
            line += (' + ' + (' * '.join(terms)))
        txt_out.append(line)
    with open('%s.txt' % args.output, 'w') as outfile:
            outfile.write('\n'.join(txt_out))

if 'tex' in save_formats:
    print '>> Saving histogram parametrisation to %s.tex' % args.output
    txt_out = []
    txt_out.append(r"""\begin{table}[htb]
    \centering
    \setlength\tabcolsep{10pt}
    \begin{tabular}{|c|c|}
        \hline""")
    for ib in xrange(nbins):
        if is2D:
            line = '$%g$--$%g$, $%g$--$%g$ & ' % (res['edges'][ib][0][0], res['edges'][ib][0][1], res['edges'][ib][1][0], res['edges'][ib][1][1])
        else:
            line = '$%g$--$%g$ & ' % (res['edges'][ib][0], res['edges'][ib][1])
        line += r"""\parbox{0.8\columnwidth}{$1 """
        for term in res['bins'][ib]:
            terms = []
            terms.append('%.2f\\,' % term[0])
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

