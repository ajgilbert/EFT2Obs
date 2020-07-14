import json
import sys
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('config', help="Input config file")
parser.add_argument('output', help="Output name for the reweight_card.dat")
parser.add_argument('--prepend', nargs='*', default=None)

args = parser.parse_args()


def PrintBlock(pars, vals, index):
    res = []
    res.append('launch --rwgt_name=rw%.4i' % index)
    for par, val in zip(pars, vals):
        res.append('set %s %i %g' % (par['block'], par['index'], val))
    return res


with open(args.config) as jsonfile:
    cfg = json.load(jsonfile)

pars = cfg['parameters']
defs = cfg['parameter_defaults']

for p in pars:
    for k in defs:
        if k not in p:
            p[k] = defs[k]
# print pars

output = ['change rwgt_dir rwgt']

if args.prepend is not None:
    output.extend(args.prepend)

initvals = [X['sm'] for X in pars]

current_i = 0
output.extend(PrintBlock(pars, initvals, current_i))
current_i += 1

for i in xrange(len(pars)):
    vals = list(initvals)
    vals[i] = (pars[i]['val'] + initvals[i]) / 2.
    output.extend(PrintBlock(pars, vals, current_i))
    current_i += 1
    vals[i] = pars[i]['val']
    output.extend(PrintBlock(pars, vals, current_i))
    current_i += 1

for i in xrange(len(pars)):
    for j in xrange(i + 1, len(pars)):
        # print i,j
        vals = list(initvals)
        vals[i] = pars[i]['val']
        vals[j] = pars[j]['val']
        output.extend(PrintBlock(pars, vals, current_i))
        current_i += 1


with open(args.output, 'w') as outfile:
        outfile.write('\n'.join(output))

print '>> Created %s with %i reweighting points' % (args.output, current_i)