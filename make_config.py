import argparse
import os
import sys
import json

parser = argparse.ArgumentParser()
parser.add_argument('--process', '-p', default='ggF')
parser.add_argument('--output', '-o', default='config.json')
parser.add_argument('--block', default='newcoup')
parser.add_argument('--default-value', type=float, default=None)
parser.add_argument('--limit-pars', type=str, default=None)
parser.add_argument('--default-value-inactive', type=float, default=None)
args = parser.parse_args()

sys.path.append(os.path.join(os.environ['MG_DIR'], args.process, 'bin', 'internal'))

import check_param_card as param_card_mod

param_card = param_card_mod.ParamCard('%s/%s/Cards/param_card.dat' % (os.environ['MG_DIR'], args.process))
# then to modify an entry of such object you can do
ids = [X[0] for X in param_card[args.block].keys()]
print ids

limit_pars = list(ids)
if args.limit_pars is not None:
    limit_pars = [int(X) for X in args.limit_pars.split(',')]

for i in ids:
    par = param_card[args.block].param_dict[(i,)]
    if args.default_value is not None and i in limit_pars:
        par.value = args.default_value
    if i not in limit_pars and args.default_value_inactive is not None:
        par.value = args.default_value_inactive

param_card.write('param_card.dat')

output = []

for i in limit_pars:
    if i not in limit_pars:
        continue
    par = param_card[args.block].param_dict[(i,)]
    output.append({
        "name": par.comment,
        "block": args.block,
        "index": i,
        "step": args.default_value
        })

with open(args.output, 'w') as outfile:
        outfile.write(json.dumps(output, sort_keys=True, indent=4))
# param_card[block].param_dict[lhaid].value = value