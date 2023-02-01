import numpy as np
import json
import yaml
from array import array

def Translate(arg, translations):
    if arg in translations:
        return translations[arg]
    else:
        return arg
class EFTTerm(object):
    def __init__(self, params, val, uncert):
        self.params = tuple(sorted(params))
        self.val = np.array(val)
        self.uncert = np.array(uncert)
    
    @classmethod
    def fromJSON(cls, t):
        return cls(t[0], t[1], t[2])

    def sortKey(self):
        return (self.params != ('1',), len(self.params), self.params)

    def asJSON(self):
        return [self.params, self.val.tolist(), self.uncert.tolist()]

    def oldJSONForBin(self, bin):
        return [self.val[bin], self.uncert[bin]] + list(self.params)


class EFTScaling(object):

    def __init__(self, nbins, bin_edges, bin_labels, sm_vals, terms):
        self.nbins = int(nbins)
        self.bin_edges = list(bin_edges)
        self.bin_labels = list(bin_labels)
        self.sm_vals = np.array(sm_vals)
        self.terms = list(terms)

    @classmethod
    def fromEFT2ObsHist(cls, e2ohist):
        norm_vals, norm_uncerts = e2ohist.normedBinStats()
        assert(norm_vals.shape[0] == norm_uncerts.shape[0] == len(e2ohist.terms))
        terms = list()
        for params, vals, uncerts in zip(e2ohist.terms, norm_vals, norm_uncerts):
            if len(params) == 1 and params[0] == '1':
                # Skip the SM point
                continue
            terms.append(EFTTerm(params, vals, uncerts))
        terms.sort(key=lambda x : x.sortKey())
        return cls(nbins=len(e2ohist.sumW[0]), bin_edges=e2ohist.bin_edges, bin_labels=e2ohist.bin_labels, sm_vals=e2ohist.sumW[0], terms=terms)

    @classmethod
    def fromJSON(cls, filename):
        with open(filename) as jsonfile:
            input = json.load(jsonfile)
        return cls.fromDict(input)

    @classmethod
    def fromDict(cls, d):
        return cls(nbins=d["nbins"], bin_edges=d["bin_edges"], bin_labels=d["bin_labels"], sm_vals=np.array(d["sm_vals"]), terms=[
            EFTTerm.fromJSON(t) for t in d['terms']
        ])

    def parameters(self):
        res = set()
        for t in self.terms:
            for p in t.params:
                res.add(p)
        return list(res)

    def getScaled(self, hist, coeffs={}, lin_terms=True, square_terms=True, cross_terms=True):
        """Apply to an array or ROOT TH1"""
        isROOT = False
        # There's probably a better way to check this, but want to avoid
        # importing ROOT if we don't need to
        if hasattr(hist, 'GetBinContent'):
            isROOT = True
            nominal = [hist.GetBinContent(ib + 1) for ib in range(hist.GetNbinsX())]
        else:
            nominal = np.array(hist)
        assert(len(nominal) == self.nbins)

        scaling = np.zeros_like(nominal)
        scaling_err = np.zeros_like(nominal)

        for term in self.terms:
            if len(term.params) == 1 and not lin_terms:
                print('Skipping {}'.format(term.params))
                continue
            if len(term.params) == 2 and len(set(term.params)) == 1 and not square_terms:
                print('Skipping {}'.format(term.params))
                continue
            if len(term.params) == 2 and len(set(term.params)) == 2 and not cross_terms:
                print('Skipping {}'.format(term.params))
                continue
            x = np.copy(term.val)
            x_err = np.copy(term.uncert)            
            for p in term.params:
                x *= (coeffs[p] if p in coeffs else 0.)
                x_err *= (coeffs[p] if p in coeffs else 0.)
            # print('Adding: {}, {}'.format(term.params, x))
            scaling += x
            scaling_err += (x_err * x_err)
        
        result = (1. + scaling) * nominal
        result_err = np.sqrt(scaling_err) * nominal

        if isROOT:
            h_result = hist.Clone()
            h_result.Reset()
            for i in range(h_result.GetNbinsX()):
                h_result.SetBinContent(i + 1, result[i])
                h_result.SetBinError(i + 1, result_err[i])
            return h_result
        else:
            return result, result_err
    
    def getNominalTH1(self, name):
        proto = self.makeTH1Prototype(name)
        for ib in range(proto.GetNbinsX()):
            proto.SetBinContent(ib + 1, self.sm_vals[ib])
            proto.SetBinError(ib + 1, 0.)
        return proto

    def makeTH1Prototype(self, name):
        import ROOT

        label_list = []
        if self.is2D():
            edge_list = [0.]
            x_edge_list = [0.]
            x_label_list = []
            width_list = []
            for X in self.bin_edges:
                # Add the width of this bin in Y to the previous edge
                edge_list.append(edge_list[-1] + (X[1][1] - X[1][0]))
                width_list.append((X[0][1] - X[0][0]) * (X[1][1] - X[1][0]))
                label_list.append('[%.2g, %.2g]' % (X[1][0], X[1][1]))
            for iX, X in enumerate(self.bin_edges):
                if iX == 0:
                    x_label_list.append(self.bin_edges[iX][0])
                    continue
                if self.bin_edges[iX][0] != x_label_list[-1]:
                    x_label_list.append(self.bin_edges[iX][0])
                if self.bin_edges[iX][0] != self.bin_edges[iX - 1][0]:
                    x_edge_list.append(edge_list[iX])
            x_edge_list.append(edge_list[-1])
            edges = array('d', edge_list)
        else:
            edges = array('d', [self.bin_edges[0][0]] + [X[1] for X in self.bin_edges])
            width_list = [(X[1] - X[0]) for X in self.bin_edges]
        if len(self.bin_labels):
            label_list = list(self.bin_labels)
        h = ROOT.TH1D(name, name, len(edges) - 1, edges)
        if len(label_list):
            for i in range(1, h.GetNbinsX() + 1):
                h.GetXaxis().SetBinLabel(i, label_list[i - 1])
        return h

    def is2D(self):
        return isinstance(self.bin_edges[0][0], list)
    
    def writeToJSON(self, filename, legacy=False, translate_txt=dict()):
        with open(filename, 'w') as outfile:
            if legacy:
                res = {
                    "bins": [[X.oldJSONForBin(ib) for X in self.terms] for ib in range(self.nbins)],
                    "nbins": self.nbins,
                    "areas": self.sm_vals.tolist(),
                    "edges": self.bin_edges,
                    "bin_labels": self.bin_labels
                }
            else:
                res = {
                    "terms": [X.asJSON() for X in self.terms],
                    "nbins": int(self.nbins),
                    "sm_vals": self.sm_vals.tolist(),
                    "bin_edges": self.bin_edges,
                    "bin_labels": self.bin_labels,
                    "parameters": self.parameters() # this is as a convenience for other scripts, we won't parse it when reading in
                }
            outfile.write(json.dumps(res, sort_keys=False))

    def writeToYAML(self, filename):
        with open(filename, 'w') as outfile:
            res = {
                "terms": [X.asJSON() for X in self.terms],
                "nbins": int(self.nbins),
                "sm_vals": self.sm_vals.tolist(),
                "bin_edges": self.bin_edges,
                "bin_labels": self.bin_labels
            }
            outfile.write(yaml.safe_dump(res, width=1E6))


    def writeToTxt(self, filename, translate_txt=dict()):
        txt_out = []
        for ib in range(self.nbins):
            if self.is2D():
                bin_label = '%g-%g,%g-%g' % (self.bin_edges[ib][0][0], self.bin_edges[ib][0][1], self.bin_edges[ib][1][0], self.bin_edges[ib][1][1])
            else:
                bin_label = '%g-%g' % (self.bin_edges[ib][0], self.bin_edges[ib][1])
            if len(self.bin_labels):
                bin_label = self.bin_labels[ib]
            line = '%s:1' % bin_label
            for term in self.terms:
                terms = []
                terms.append('%.3f' % term.val[ib])
                # terms.extend(term.params)
                terms.extend([Translate(X, translate_txt) for X in term.params])
                line += (' + ' + ('*'.join(terms)))
            txt_out.append(line)
        with open(filename, 'w') as outfile:
                outfile.write('\n'.join(txt_out))


    def writeToTex(self, filename, translate_tex=dict()):
        txt_out = []
        txt_out.append(r"""\begin{table}[htb]
        \centering
        \setlength\tabcolsep{10pt}
        \begin{tabular}{|c|c|}
            \hline""")
        for ib in range(self.nbins):
            if self.is2D():
                line = '$%g$--$%g$, $%g$--$%g$ & ' % (self.bin_edges[ib][0][0], self.bin_edges[ib][0][1], self.bin_edges[ib][1][0], self.bin_edges[ib][1][1])
            else:
                line = '$%g$--$%g$ & ' % (self.bin_edges[ib][0], self.bin_edges[ib][1])
            line += r"""\parbox{0.8\columnwidth}{$1 """
            for term in self.terms:
                terms = []
                terms.append('%.2f\\,' % term.val[ib])
                if len(term.params) == 2 and term.params[0] == term.params[1]:
                    terms.append('{%s}^{2}' % Translate(term.params[1], translate_tex))
                else:
                    terms.extend([Translate(X, translate_tex) for X in term.params])
                line += (' + ' + ('\\,'.join(terms)))
            line += """$} \\\\"""
            txt_out.append(line)
            txt_out.append("""\\hline""")
        txt_out.append(r"""\end{tabular}
        \end{table}""")
        with open(filename, 'w') as outfile:
                outfile.write('\n'.join(txt_out))

class EFT2ObsHist(object):
    def __init__(self, terms, sumW, sumW2, numEntries, bin_edges=list(), bin_labels=list()):
        self.terms = list(terms)
        self.sumW = np.array(sumW)
        self.sumW2 = np.array(sumW2)
        self.numEntries = np.array(numEntries)
        self.bin_edges = bin_edges
        self.bin_labels = bin_labels
    
    @classmethod
    def fromJSON(cls, filename):
        with open(filename) as jsonfile:
            input = json.load(jsonfile)
        return cls(
            terms=input['terms'],
            sumW=np.array(input['sumW']),
            sumW2=np.array(input['sumW2']),
            numEntries=np.array(input['numEntries']),
            bin_edges=input['bin_edges'],
            bin_labels=input['bin_labels'])

    def nbins(self):
        return self.sumW.shape[1]
    
    def add(self, other):
        self.sumW += other.sumW
        self.sumW2 += other.sumW2
        self.numEntries += other.numEntries


    def zeroTerms(self, terms=list(), allow_subset_match=False):
        for term in terms:
            for ip, point in enumerate(self.terms):
                do_zero = False
                if allow_subset_match and len(term) < len(point) and term[0] in point:
                    do_zero = True
                if sorted(term) == sorted(point):
                    do_zero = True
                if do_zero:
                    print('>> Zero out %s term' % point)
                    self.sumW[ip] = np.zeros(self.nbins())
                    self.sumW2[ip] = np.zeros(self.nbins())


    def writeToJSON(self, filename):
        with open(filename, 'w') as outfile:
            res = {
                "terms": self.terms,
                "sumW": self.sumW.tolist(),
                "sumW2": self.sumW2.tolist(),
                "numEntries": self.numEntries.tolist(),
                "bin_edges": self.bin_edges,
                "bin_labels": self.bin_labels
            }
            outfile.write(json.dumps(res, sort_keys=False))

    def binStats(self):
        # Need to protect against numEntries == 0: default to zero 
        meanW = np.divide(self.sumW, self.numEntries, out=np.zeros_like(self.sumW), where=self.numEntries!=0)
        meanW2 = np.divide(self.sumW2, self.numEntries, out=np.zeros_like(self.sumW2), where=self.numEntries!=0)
        stddev2 = meanW2 - meanW**2
        stderr = np.sqrt(np.divide(stddev2, self.numEntries, out=np.zeros_like(stddev2), where=((self.numEntries!=0) & (stddev2 > 0))))
        return meanW, stderr
    
    def normedBinStats(self, divide_index=0):
        vals, uncerts = self.binStats()
        norm_vals = np.divide(vals, vals[divide_index], out=np.zeros_like(vals), where=vals[divide_index]>0)
        norm_uncerts = np.divide(uncerts, vals[divide_index], out=np.zeros_like(uncerts), where=vals[divide_index]>0)
        return norm_vals, norm_uncerts

    def printToScreen(self, skip_empty_bins=True, relative=True):
        n_divider = 65
        print('-' * n_divider)
        vals, uncerts = self.binStats()
        if relative:
            norm_vals, norm_uncerts = self.normedBinStats()
        else:
            norm_vals = np.copy(vals)
            norm_uncerts = np.copy(uncerts)
        norm_reluncerts = np.divide(norm_uncerts, norm_vals, out=np.zeros_like(norm_uncerts), where=norm_vals!=0)

        for ib in range(self.nbins()):
            print('Bin %-4i numEntries: %-10i mean: %-10.3g stderr: %-10.3g' % (ib, self.numEntries[0][ib], vals[0][ib], uncerts[0][ib]))
            extra_label = ''
            if len(self.bin_labels) > 0:
                extra_label += ', label=%s' % self.bin_labels[ib]
            print('         edges: %s%s' % (self.bin_edges[ib], extra_label))
            print('-' * n_divider)
            if skip_empty_bins and self.numEntries[0][ib] == 0:
                continue
            print('%-20s | %12s | %12s | %12s' % ('Term', 'Val', 'Uncert', 'Rel. uncert.'))
            print('-' * n_divider)
            for ip in range(len(self.terms)):
                val = norm_vals[ip][ib]
                uncert = norm_uncerts[ip][ib]
                reluncert = norm_reluncerts[ip][ib]
                print('%-20s | %12.4f | %12.4f | %12.4f' % (' * '.join(self.terms[ip]), val, uncert, abs(reluncert)))
            print('-' * n_divider)
