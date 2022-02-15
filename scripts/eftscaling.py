import numpy as np
import json


def load(filename):
    with open(filename) as jsonfile:
        input = json.load(jsonfile)
    return EFT2ObsHist(
        params=input['params'],
        sumW=np.array(input['sumW']),
        sumW2=np.array(input['sumW2']),
        numEntries=np.array(input['numEntries']),
        bin_edges=input['bin_edges'],
        bin_labels=input['bin_labels'])

class EFT2ObsHist(object):
    def __init__(self, params, sumW, sumW2, numEntries, bin_edges=list(), bin_labels=list()):
        self.params = list(params)
        self.sumW = np.array(sumW)
        self.sumW2 = np.array(sumW2)
        self.numEntries = np.array(numEntries)
        self.bin_edges = bin_edges
        self.bin_labels = bin_labels
        self.SM_vals = np.zeros(self.nbins())
        self.initPoints()

    def nbins(self):
        return self.sumW.shape[1]
    
    def nparams(self):
        return len(self.params)
    
    def initPoints(self):
        self.points = list()
        self.points.append(list('1'))
        for i in range(self.nparams()):
            self.points.append([self.params[i]])
            self.points.append([self.params[i], self.params[i]])
        for ix in range(0, self.nparams()):
            for iy in range(ix + 1, self.nparams()):
                self.points.append([self.params[ix], self.params[iy]])

    # def validate(self):
    def add(self, other):
        self.sumW += other.sumW
        self.sumW2 += other.sumW2
        self.numEntries += other.numEntries


    def zeroTerms(self, terms=list(), allow_subset_match=False):
        for term in terms:
            for ip, point in enumerate(self.points):
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
                "params": self.params,
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
    
    def getOrderedEntries(self):
        res = [0]
        res.extend([ip * 2 + 1 for ip in range(self.nparams())])
        res.extend([ip * 2 + 2 for ip in range(self.nparams())])
        res.extend([1 + self.nparams() * 2 + ic for ic in range((self.nparams() * (self.nparams() - 1)) / 2)])
        return res

    def printToScreen(self, skip_empty_bins=True, relative=True):
        n_divider = 65
        print('-' * n_divider)
        vals, uncerts = self.binStats()
        if relative:
            norm_vals = np.divide(vals, vals[0], out=np.zeros_like(vals), where=vals[0]>0)
            norm_uncerts = np.divide(uncerts, vals[0], out=np.zeros_like(uncerts), where=vals[0]>0)
        else:
            norm_vals = np.copy(vals)
            norm_uncerts = np.copy(uncerts)
        norm_reluncerts = np.divide(norm_uncerts, norm_vals, out=np.zeros_like(norm_uncerts), where=norm_vals!=0)

        for ib in range(self.nbins()):
            print('Bin %-4i numEntries: %-10i mean: %-10.3g stderr: %-10.3g' % (ib, self.numEntries[0][ib], vals[0][ib], uncerts[0][ib]))
            extra_label = ''
            if self.bin_labels is not None:
                extra_label += ', label=%s' % self.bin_labels[ib]
            print('         edges: %s%s' % (self.bin_edges[ib], extra_label))
            print('-' * n_divider)
            if skip_empty_bins and self.numEntries[0][ib] == 0:
                continue
            print('%-20s | %12s | %12s | %12s' % ('Term', 'Val', 'Uncert', 'Rel. uncert.'))
            print('-' * n_divider)
            for ip in self.getOrderedEntries():
                val = norm_vals[ip][ib]
                uncert = norm_uncerts[ip][ib]
                reluncert = norm_reluncerts[ip][ib]
                print('%-20s | %12.4f | %12.4f | %12.4f' % (' * '.join(self.points[ip]), val, uncert, abs(reluncert)))
            print('-' * n_divider)
