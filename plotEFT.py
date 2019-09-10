import ROOT
import plotting as plot
from array import array

ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.AddDirectory(False)
plot.ModTDRStyle()

f = ROOT.TFile('Rivet.root')

hists = []

N_weights = 7

targets = [
    (2, 12, 0.0001, 2, 'cG'), # divide by 16*pi*pi to follow convention
    (4, 30, 0.0001, 4, 'c3G'),
    (6, 33, 0.0001, 12, 'c2G')
]

def VariableRebin(hist, binning):
    newhist = hist.Rebin(len(binning) - 1, "", array('d', binning))
    return newhist


for i in range(N_weights):
    hists.append(VariableRebin(
        f.Get('HiggsTemplateCrossSectionsStage1/pT_Higgs[rw%i]' % i),
        [0, 10, 20, 30, 40, 60, 100, 150, 200]))
    hists[-1].Scale(1, 'width')


canv = ROOT.TCanvas('eft_demo', '')
pads = plot.TwoPadSplit(0.27, 0.01, 0.01)

# Get the data and create axis hist
h_nominal = hists[0]

h_axes = [h_nominal.Clone() for x in pads]
for h in h_axes:
    h.Reset()

h_axes[1].GetXaxis().SetTitle('Higgs p_{T} (GeV)')

h_axes[0].GetYaxis().SetTitle('d#sigma/dp_{T}')
h_axes[0].Draw()
if True:
    pads[0].SetLogy()
    h_axes[0].SetMinimum(1E-4)

# A dict to keep track of the hists
legend = ROOT.TLegend(0.60, 0.86 - 0.04 * 5, 0.90, 0.91, '', 'NBNDC')

legend.AddEntry(h_nominal, 'SM', 'L')

plot.Set(h_nominal, LineColor=1, LineWidth=2)

h_nominal.Draw('HISTSAMEE')

for tgt in targets:
    plot.Set(hists[tgt[0]], LineColor=tgt[3], LineWidth=2)
    hists[tgt[0]].Draw('HISTSAME')
    ci = tgt[2]
    if len(tgt) >= 6:
        ci = ci * tgt[5]
    legend.AddEntry(hists[tgt[0]], '%s = %.3g' % (tgt[4], ci), 'L')


plot.FixTopRange(pads[0], plot.GetPadYMax(pads[0]), 0.43)
legend.Draw()

# # Do the ratio plot
pads[1].cd()
pads[1].SetGrid(0, 1)
h_axes[1].Draw()

ratio_hists = []
for h in hists:
    ratio_hists.append(plot.MakeRatioHist(h, hists[0], False, False))
for tgt in targets:
    ratio_hists[tgt[0]].Draw('HISTSAME')

plot.SetupTwoPadSplitAsRatio(
    pads, plot.GetAxisHist(
        pads[0]), plot.GetAxisHist(pads[1]), 'Ratio to SM', True, 0.0, 5.0)

# Go back and tidy up the axes and frame
pads[0].cd()
pads[0].GetFrame().Draw()
pads[0].RedrawAxis()

# CMS logo
# plot.DrawCMSLogo(pads[0], 'Les Houches', '2019', 11, 0.045, 0.05, 1.0, '', 1.0)
plot.DrawTitle(pads[0], 'pp #rightarrow H / Hj', 1)
plot.DrawTitle(pads[0], 'HEL UFO', 3)


canv.Print('.png')
canv.Print('.pdf')

for ib in xrange(1, h_nominal.GetNbinsX() + 1):
    line = 'xsec / SM for bin %i [%g, %g] = 1.0' % (ib, h_nominal.GetXaxis().GetBinLowEdge(ib), h_nominal.GetXaxis().GetBinUpEdge(ib))
    for tgt in targets:
        x_tot = hists[tgt[0]].GetBinContent(ib)
        x_sm = h_nominal.GetBinContent(ib)
        ci = tgt[2]
        x_int = (x_tot - x_sm) / ci
        x_int = x_int / x_sm
        if len(tgt) >= 6:
            x_int = x_int / tgt[5]
        sign = '+' if x_int >= 0 else '-'
        line += ' %s %.3g*%s' % (sign, abs(x_int), tgt[4])
    print line