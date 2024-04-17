from __future__ import print_function
import argparse
import os
import sys
import json

sys.path.append('%s/%s' % (os.environ['PWD'], os.environ['MG_DIR']))

parser = argparse.ArgumentParser()
parser.add_argument('--process', '-p', default='zh-HEL', help="Label of the process, must correspond to the dir name that was created in the MG dir")
parser.add_argument('--output', '-o', default='config.json', help="Output name for the config file")
parser.add_argument('--def-val', type=float, default=0.01)
parser.add_argument('--set-inactive', type=str, nargs='*', help='')
parser.add_argument('--def-sm', type=float, default=0.0)
parser.add_argument('--def-gen', type=float, default=0.0)
parser.add_argument('--pars', type=str, nargs='+', help="List of parameters by block, e.g.: block1:1,2,3 block2:4,5,6")
args = parser.parse_args()

sys.path.append(os.path.join(os.environ['MG_DIR'], args.process.split('/')[-1], 'bin', 'internal'))

import check_param_card as param_card_mod

param_card_path = '%s/%s/Cards/param_card.dat' % (os.environ['MG_DIR'], args.process.split('/')[-1])
print('>> Parsing %s to get the list of model parameters' % param_card_path)

param_card = param_card_mod.ParamCard(param_card_path)

# for i in ids:
#     par = param_card[args.block].param_dict[(i,)]
#     if args.def_val is not None and i in pars:
#         par.value = args.def_val
#     if i not in pars and args.def_inactive is not None:
#         par.value = args.def_inactive

# param_card.write('param_card.dat')

output = {
    'blocks': [],
    'parameter_defaults': {
        'gen': args.def_gen,
        'val': args.def_val,
        'sm': args.def_sm
    },
    'parameters': [],
    'inactive': {
        'default_val': args.def_sm,
        'parameters': [
        ]
    }
}

if len(args.pars) == 1:
    output['parameter_defaults']['block'] = args.pars[0].split(':')[0]

for parset in args.pars:
    if ':' in parset:
        block = parset.split(':')[0]
        ids = [X[0] for X in list(param_card[block].keys())]
        userpars = [int(X) for X in parset.split(':')[1].split(',')]
    else:
        block = parset
        ids = [X[0] for X in list(param_card[block].keys())]
        userpars = list(ids)

    output['blocks'].append(block)
    print('>> Selecting %i/%i parameters in block %s:' % (len(userpars), len(ids), block))

    if len(args.pars) == 1:
        output['parameter_defaults']['block'] = block

    for i in userpars:
        if i not in ids:
            print('>> The index %i in block %s was requested, but not found' % (i, block))
            continue
        par = param_card[block].param_dict[(i,)]
        output['parameters'].append({
            "name": par.comment.strip(),
            "index": i
            })
        if len(args.pars) > 1:
            output['parameters'][-1]['block'] = block
        print('    - [%i] %s' % (output['parameters'][-1]['index'], output['parameters'][-1]['name']))


if args.set_inactive is not None:
    for parset in args.set_inactive:
        block = parset.split(':')[0]
        userpars = parset.split(':')[1].split(',')
        if block not in output['blocks']:
            continue
        for userpar in userpars:
            idx = int(userpar.split('=')[0])
            output['inactive']['parameters'].append({
                "block": block,
                "name": param_card[block].param_dict[(idx,)].comment.strip(),
                "index": idx,
                "val": float(userpar.split('=')[1])
                })


print('>> Writing config file %s' % args.output)

with open(args.output, 'w') as outfile:
        outfile.write(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))
