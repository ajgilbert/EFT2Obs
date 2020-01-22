import json
import sys


def PrintBlock(pars, vals, index):
    res = []
    res.append('launch --rwgt_name=rw%.4i' % index)
    for par, val in zip(pars, vals):
        res.append('set %s %i %g' % (par['block'], par['index'], val))
    return res


with open(sys.argv[1]) as jsonfile:
    cfg = json.load(jsonfile)

pars = cfg['parameters']
defs = cfg['parameter_defaults']

for p in pars:
    for k in defs:
        if k not in p:
            p[k] = defs[k]
# print pars

output = []

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


if len(sys.argv) > 2:
    with open(sys.argv[2], 'w') as outfile:
            outfile.write('\n'.join(output))

print '>> Created %s with %i reweighting points' % (sys.argv[2], current_i)