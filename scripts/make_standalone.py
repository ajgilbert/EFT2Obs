import json
import sys
import os
import tools
import argparse
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument('--process', '-p', default='zh-HEL', help="Label of the process, must correspond to the dir name that was created in the MG dir")
parser.add_argument('--rw-module', default='rw_module_zh-HEL.tar.gz', help="Reweighting module exported in the make_gridpack.sh step")
parser.add_argument('--output', '-o', default='rw_config', help="Output name for directory")
parser.add_argument('--config', '-c', default='config.json')
args = parser.parse_args()

process = args.process

os.mkdir(args.output)

# Copy the rwgt directory
subprocess.check_call(['tar', '-xf', args.rw_module, '-C', args.output])
subprocess.check_call(['cp', args.config, '%s/config.json' % args.output])

sys.path.append('%s/%s' % (os.environ['PWD'], os.environ['MG_DIR']))
sys.path.append(os.path.join(os.environ['MG_DIR'], process, 'bin', 'internal'))

import check_param_card as param_card_mod

cfg = tools.GetConfigFile(args.config)

param_card_path = 'cards/%s/param_card.dat' % process
print '>> Parsing %s' % param_card_path
param_card = param_card_mod.ParamCard(param_card_path)


pars = cfg['parameters']
initvals = [X['sm'] for X in pars]

current_i = 0
param_card.write('%s/param_card_%i.dat' % (args.output, current_i))
current_i += 1

for i in xrange(len(pars)):
    vals = list(initvals)
    vals[i] = (pars[i]['val'] + initvals[i]) / 2.

    for ix, x in enumerate(pars):
        param_card[x['block']].param_dict[(x['index'],)].value = vals[ix]
    param_card.write('%s/param_card_%i.dat' % (args.output, current_i))
    current_i += 1

    vals[i] = pars[i]['val']

    for ix, x in enumerate(pars):
        param_card[x['block']].param_dict[(x['index'],)].value = vals[ix]
    param_card.write('%s/param_card_%i.dat' % (args.output, current_i))
    current_i += 1

for i in xrange(len(pars)):
    for j in xrange(i + 1, len(pars)):
        vals = list(initvals)
        vals[i] = pars[i]['val']
        vals[j] = pars[j]['val']

        for ix, x in enumerate(pars):
            param_card[x['block']].param_dict[(x['index'],)].value = vals[ix]
        param_card.write('%s/param_card_%i.dat' % (args.output, current_i))
        current_i += 1

print '>> Created %s with %i reweighting points' % (args.output, current_i)