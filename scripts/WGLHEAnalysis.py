import ROOT
import argparse
from array import array
from collections import defaultdict


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser.add_argument('--cards', default='rw_config')
    # parser.add_argument('--config', default='test.json')
    parser.add_argument('-i', '--input', default='input.lhe')
    parser.add_argument('-o', '--output', default='output.lhe')
    args = parser.parse_args()

    binning = {
        'l0p0_dr': [0.7, 1.0, 1.3, 1.6, 1.9, 2.2, 2.5, 2.8, 3.1, 3.4, 3.7, 4.0, 4.5, 5.0]
        }

    hists = {
        'l0p0_dr': ROOT.TH1D('l0p0_dr', 'l0p0_dr', len(binning['l0p0_dr']) - 1, array('d', binning['l0p0_dr']))
    }


    ROOT.gROOT.ProcessLine('#include "LHEF.h"')

    # // Create Reader and Writer object
    reader = ROOT.LHEF.Reader(args.input)
    neve = 0
    # // Read each event and write them out again.
    sumweights = 0.
    sumselected = 0.
    while reader.readEvent():
        neve += 1

        real_events = []
        if reader.hepeup.isGroup:
            real_events = reader.hepeup.subevents
        else:
            real_events.append(reader.hepeup)

        # print '-- Event --'
        for evt in real_events:
            sumweights += evt.XWGTUP
            parts = []
            l0 = None
            p0 = None
            n0 = None
            for ip in xrange(evt.NUP):
                part = ROOT.Math.PxPyPzEVector(evt.PUP[ip][0], evt.PUP[ip][1], evt.PUP[ip][2], evt.PUP[ip][3])
                part.pdgid = evt.IDUP[ip]
                part.status = evt.ISTUP[ip]
                parts.append(part)
                if part.status == 1 and abs(part.pdgid) in [11, 13, 15]:
                    l0 = part
                if part.status == 1 and abs(part.pdgid) in [22]:
                    p0 = part
                if part.status == 1 and abs(part.pdgid) in [12, 14, 16]:
                    n0 = part

            final_parts = [X for X in parts if X.status == 1]

            l0p0_dr = ROOT.Math.VectorUtil.DeltaR(l0, p0)

            if l0.pt() > 30. and abs(l0.eta()) < 2.5 and p0.pt() > 30 and abs(p0.eta()) < 2.5 and n0.pt() > 40. and l0p0_dr > 0.7:
                sumselected += evt.XWGTUP
                hists['l0p0_dr'].Fill(l0p0_dr, evt.XWGTUP)
            else:
                print l0.pt(), l0.eta(), p0.pt(), p0.eta(), n0.pt(), l0p0_dr
            # for p in final_parts:
            #     print p.pt(), p.eta(), p.phi(), p.pdgid, p.status

            # print parts

        if neve % 5000 == 0:
            print '>> Done %i events' % neve
        # if neve == 10000:
        #     break
        # print hels

print '==> Sum of weights = %f/%f' % (sumselected, sumweights)

outf = ROOT.TFile(args.output, 'RECREATE')

for h in hists.values():
    h.Write()

outf.Close()
