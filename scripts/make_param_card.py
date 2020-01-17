import os
import sys
import json

process = sys.argv[1]

sys.path.append('%s/%s' % (os.environ['PWD'], os.environ['MG_DIR']))
sys.path.append(os.path.join(os.environ['MG_DIR'], process, 'bin', 'internal'))

import check_param_card as param_card_mod


with open(sys.argv[2]) as jsonfile:
    cfg = json.load(jsonfile)

for p in cfg['parameters']:
    for k in cfg['parameter_defaults']:
        if k not in p:
            p[k] = cfg['parameter_defaults'][k]

param_card = param_card_mod.ParamCard('%s/%s/Cards/param_card.dat' % (os.environ['MG_DIR'], process))
# then to modify an entry of such object you can do

for block in cfg['blocks']:
    ids = [X[0] for X in param_card[block].keys()]
    print ids

    for i in ids:
        par = param_card[block].param_dict[(i,)]
        par.value = cfg['inactive']['val']

    for p in cfg['parameters']:
        par = param_card[block].param_dict[(p['index'],)]
        par.value = p['gen']

param_card.write('param_card.dat')
