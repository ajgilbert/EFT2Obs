import json
import sys

def PrintBlock(pars, vals, label):
    res = []
    res.append('launch --rwgt_name=%s' % label)
    for par, val in zip(pars, vals):
        res.append('set %s %i %g' % (par['block'], par['index'], val))
    return res

with open(sys.argv[1]) as jsonfile:
    pars = json.load(jsonfile)

print pars

output = []

initvals = [0.] * len(pars)

current_i = 0
output.extend(PrintBlock(pars, initvals, 'rw%s' % current_i))
current_i += 1

for i in xrange(len(pars)):
    vals = list(initvals)
    vals[i] = pars[i]['step'] / 2.
    output.extend(PrintBlock(pars, vals, 'rw%s' % current_i))
    current_i += 1
    vals[i] = pars[i]['step']
    output.extend(PrintBlock(pars, vals, 'rw%s' % current_i))
    current_i += 1

print '\n'.join(output)

if len(sys.argv) > 2:
    with open(sys.argv[2], 'w') as outfile:
            outfile.write('\n'.join(output))
