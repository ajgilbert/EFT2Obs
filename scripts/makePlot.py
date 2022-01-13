from __future__ import print_function
from builtins import range
import argparse
import ROOT
import json
import math
import plotting as plot
from array import array

ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.AddDirectory(False)
plot.ModTDRStyle()


def Translate(arg, translations):
    if arg in translations:
        return translations[arg]
    else:
        return arg


def MakeHist(name, jhist, vals=dict(), noSquare=False, noCross=False):
    is2D = False
    label_list = []
    if isinstance(jhist['edges'][0][0], list):
        is2D = True
        print('>> Unrolling 2D hist')
        edge_list = [0.]
        x_edge_list = [0.]
        x_label_list = []
        width_list = []
        for X in jhist['edges']:
            # Add the width of this bin in Y to the previous edge
            edge_list.append(edge_list[-1] + (X[1][1] - X[1][0]))
            width_list.append((X[0][1] - X[0][0]) * (X[1][1] - X[1][0]))
            label_list.append('[%.2g, %.2g]' % (X[1][0], X[1][1]))
        for iX, X in enumerate(jhist['edges']):
            if iX == 0:
                x_label_list.append(jhist['edges'][iX][0])
                continue
            if jhist['edges'][iX][0] != x_label_list[-1]:
                x_label_list.append(jhist['edges'][iX][0])
            if jhist['edges'][iX][0] != jhist['edges'][iX - 1][0]:
                x_edge_list.append(edge_list[iX])

        x_edge_list.append(edge_list[-1])
        print(x_label_list)
        # print edge_list
        # print x_edge_list
        # print edge_list
        # print width_list
        edges = array('d', edge_list)
    else:
        edges = array('d', [jhist['edges'][0][0]] + [X[1] for X in jhist['edges']])
        width_list = [(X[1] - X[0]) for X in jhist['edges']]

    h = ROOT.TH1D(name, name, len(edges) - 1, edges)
    h_dev = ROOT.TH1D(name, name, len(edges) - 1, edges)
    for i in range(1, h.GetNbinsX() + 1):
        term = 0.0
        term_err = 0.0
        if is2D:
            h.GetXaxis().SetBinLabel(i, label_list[i - 1])
            h_dev.GetXaxis().SetBinLabel(i, label_list[i - 1])
        if 'bin_labels' in jhist:
            h.GetXaxis().SetBinLabel(i, jhist['bin_labels'][i - 1])
            h_dev.GetXaxis().SetBinLabel(i, jhist['bin_labels'][i - 1])
        for bininfo in jhist['bins'][i - 1]:
            val = bininfo[0]
            err = bininfo[1]
            pars = bininfo[2:]
            if noSquare and len(pars) == 2:
                continue
            if noCross and len(pars) == 2 and pars[0] != pars[1]:
                continue
            for p in pars:
                if p in vals:
                    val *= vals[p]
                    err *= vals[p]
                else:
                    val *= 0.0
                    err *= 0.0
            term += val
            term_err += (err * err)
            # print bininfo, val
        # print term, term_err
        h.SetBinContent(i, jhist['areas'][i - 1] / width_list[i - 1])
        h.SetBinError(i, 0.0)
        h_dev.SetBinContent(i, term * h.GetBinContent(i))
        h_dev.SetBinError(i, math.sqrt(term_err) * h.GetBinContent(i))
    # h.Print("range")
    # h_dev.Print("range")
    if 'bin_labels' in jhist:
        h.GetXaxis().SetLabelSize(h.GetXaxis().GetLabelSize() * 0.5)
    h.Add(h_dev)

    if is2D:
        h.x_edge_list = x_edge_list
        h.x_label_list = x_label_list
        h.GetXaxis().LabelsOption('v')
        h.GetXaxis().SetLabelSize(h.GetXaxis().GetLabelSize() * 0.6)
    # h.Scale(1, 'width')
    return h


parser = argparse.ArgumentParser()
parser.add_argument('--hist', default='ggF')
parser.add_argument('--config', '-c', default='config.json')
parser.add_argument('--draw', nargs='+')
parser.add_argument('--x-title', default='variable')
parser.add_argument('--title-left', default='')
parser.add_argument('--title-right', default='')
parser.add_argument('--logy', action='store_true')
parser.add_argument('--y-min', default=1E-4, type=float)
parser.add_argument('--ratio', default='0,5')
parser.add_argument('--show-unc', action='store_true')
parser.add_argument('--no-square', action='store_true')
parser.add_argument('--no-cross', action='store_true')
parser.add_argument('--translate', default=None, help="json file to translate parameter names to latex")

args = parser.parse_args()


with open(args.hist) as jsonfile:
    jhist = json.load(jsonfile)

with open(args.config) as jsonfile:
    cfg = json.load(jsonfile)

translate_tex = {}
if args.translate is not None:
    with open(args.translate) as jsonfile:
        translate_tex = json.load(jsonfile)


pars = cfg['parameters']
defs = cfg['parameter_defaults']


canv = ROOT.TCanvas(args.hist.replace('.json', ''), '')
pads = plot.TwoPadSplit(0.27, 0.01, 0.01)

hists = []
hist_errs = []

h_nominal = MakeHist('nominal', jhist)

hists.append(h_nominal)
hist_errs.append(h_nominal)

h_axes = [h_nominal.Clone() for x in pads]
for h in h_axes:
    h.Reset()

h_axes[1].GetXaxis().SetTitle(args.x_title)

h_axes[0].GetYaxis().SetTitle('a.u.')
h_axes[0].Draw()
if args.logy:
    pads[0].SetLogy()
    h_axes[0].SetMinimum(args.y_min)

# A dict to keep track of the hists
legend = ROOT.TLegend(0.60, 0.88 - 0.05 * len(args.draw), 0.90, 0.91, '', 'NBNDC')

legend.AddEntry(h_nominal, 'Nominal', 'L')

plot.Set(h_nominal, LineColor=1, LineWidth=3)

h_nominal.Draw('HISTSAMEE')

for tgt in args.draw:
    val_part = tgt.split(':')[0]
    opt_part = tgt.split(':')[1:]
    vals = {}
    labels = []
    for X in val_part.split(','):
        label = X.split('=')[0]
        val = float(X.split('=')[1])
        vals[label] = float(val)
        labels.append('%s=%g' % (Translate(label, translate_tex), val))
    h = MakeHist('hist1', jhist, vals, args.no_square, args.no_cross)
    h_err = h.Clone()

    hists.append(h)
    hist_errs.append(h_err)
    plot.Set(h_err, LineColor=int(opt_part[0]), LineWidth=2, MarkerColor=int(opt_part[0]), MarkerSize=0, FillColorAlpha=(int(opt_part[0]), 0.3))
    plot.Set(h, LineColor=int(opt_part[0]), LineWidth=2)
    if args.show_unc:
        legend.AddEntry(h_err, ', '.join(labels), 'LF')
        h_err.Draw('E2SAME')
    else:
        legend.AddEntry(h, ', '.join(labels), 'L')
    h.Draw('HISTSAME')


plot.FixTopRange(pads[0], plot.GetPadYMax(pads[0]), 0.30)
print(h_axes[0].GetMinimum(), h_axes[0].GetMaximum())
if hasattr(hists[0], 'x_edge_list'):
    x_edge_list = hists[0].x_edge_list
    x_label_list = hists[0].x_label_list
    print(x_edge_list)
    line = ROOT.TLine()
    text = ROOT.TLatex()
    plot.Set(text, TextAlign=22, TextFont=42, TextSize=0.02)
    y_height = h_axes[0].GetMinimum() + 0.2 * (h_axes[0].GetMaximum() - h_axes[0].GetMinimum())
    if args.logy:
        y_height = math.pow(10, math.log10(h_axes[0].GetMinimum()) + 0.1 * (math.log10(h_axes[0].GetMaximum()) - math.log10(h_axes[0].GetMinimum())))
    plot.Set(line, LineStyle=2)
    for ix in range(1, len(x_edge_list) - 1):
        line.DrawLine(x_edge_list[ix], h_axes[0].GetMinimum(), x_edge_list[ix], h_axes[0].GetMaximum())
    for ix in range(len(x_label_list)):
        print(ix, len(x_edge_list), len(x_label_list))
        text.DrawLatex((x_edge_list[ix + 1] + x_edge_list[ix]) / 2., y_height, '[%g, %g]' % (x_label_list[ix][0], x_label_list[ix][1]))

        # plot.DrawVerticalLine(pads[0], line, x_edge)
legend.Draw()

# # Do the ratio plot
pads[1].cd()
pads[1].SetGrid(0, 1)
h_axes[1].Draw()

ratio_hists = []
ratio_hist_errs = []
if args.show_unc:
    for h in hist_errs:
        ratio_hist_errs.append(plot.MakeRatioHist(h, hists[0], True, False))
        ratio_hist_errs[-1].Draw('E2SAME')

for h in hists:
    ratio_hists.append(plot.MakeRatioHist(h, hists[0], False, False))
    ratio_hists[-1].Draw('HISTSAME')

plot.SetupTwoPadSplitAsRatio(
    pads, plot.GetAxisHist(
        pads[0]), plot.GetAxisHist(pads[1]), 'Ratio to SM', True, float(args.ratio.split(',')[0]), float(args.ratio.split(',')[1]))

# Go back and tidy up the axes and frame
pads[0].cd()
pads[0].GetFrame().Draw()
pads[0].RedrawAxis()


# CMS logo
plot.DrawTitle(pads[0], args.title_left, 1)
plot.DrawTitle(pads[0], args.title_right, 3)


canv.Print('.png')
canv.Print('.pdf')
