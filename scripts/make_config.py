import argparse
import os
import sys
import json

sys.path.append('%s/%s' % (os.environ['PWD'], os.environ['MG_DIR']))

parser = argparse.ArgumentParser()
parser.add_argument('--process', '-p', default='ggF')
parser.add_argument('--output', '-o', default='config.json')
parser.add_argument('--block', default='newcoup')
parser.add_argument('--def-val', type=float, default=0.01)
parser.add_argument('--def-sm', type=float, default=0.0)
parser.add_argument('--def-gen', type=float, default=0.0)
parser.add_argument('--pars', type=str, default=None)
# parser.add_argument('--def-inactive', type=float, default=0.0)
args = parser.parse_args()

sys.path.append(os.path.join(os.environ['MG_DIR'], args.process, 'bin', 'internal'))

import check_param_card as param_card_mod

param_card = param_card_mod.ParamCard('%s/%s/Cards/param_card.dat' % (os.environ['MG_DIR'], args.process))
# then to modify an entry of such object you can do
ids = [X[0] for X in param_card[args.block].keys()]
print ids

pars = list(ids)
if args.pars is not None:
    pars = [int(X) for X in args.pars.split(',')]

# for i in ids:
#     par = param_card[args.block].param_dict[(i,)]
#     if args.def_val is not None and i in pars:
#         par.value = args.def_val
#     if i not in pars and args.def_inactive is not None:
#         par.value = args.def_inactive

# param_card.write('param_card.dat')

output = {
    'blocks': [args.block],
    'parameter_defaults': {
        'block': args.block,
        'gen': args.def_gen,
        'val': args.def_val,
        'sm': args.def_sm
    },
    'parameters': [],
    'inactive': {
        'val': args.def_sm
    }
}

for i in pars:
    if i not in pars:
        continue
    par = param_card[args.block].param_dict[(i,)]
    output['parameters'].append({
        "name": par.comment.strip(),
        "index": i
        })

with open(args.output, 'w') as outfile:
        outfile.write(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))
# param_card[block].param_dict[lhaid].value = value