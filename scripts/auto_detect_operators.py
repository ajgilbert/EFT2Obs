"""
Automatically detect which parameters are relavant for a provided process.
Given this information, create a process-specific config file and reweight card.

The following two methods will extract parameters that contribute to a process via
the insertion of EFT vertices. 

Two methods:
1) Look at the coupl.inc file in the SubProcesses directory of a process. This file
   contains a block labeled by 'COMMON/COUPLINGS/'. The meaning of these couplings can
   be found in the model's couplings.py file. Relevant parameters can be found by seeing
   whether they appear in these couplings.
2) [SMEFTsim v3-only method] Look at the postscript files containing the feynman diagrams.
   Each diagram has associated coupling orders, e.g. NPcHG, NPcHB. If NPcHG=1 then this
   means that cHG is relevant for this diagrams. By looping over all diagrams, we can
   find all the relevant parameters.

By default, the script will perform both methods as a way of validation. If not using
SMEFTsim v3, the script will automatically detect this and only use method 1. In case this
automatic detection fails, use the --noValidation tag to use only method 1.

If the model is SMEFTsim v3, the script will then look for parameters that contribute
via propagator corrections. To do this, the dummy particles: h1, w1, z1 and t1 are looked
for in the diagram postscript files. Supposing that h1 is found, the parameter dWH would be
searched for in the UFO model. Since this parameter is a function of other parameters,
the script recusively searches through the parameters to find which Wilson coefficients
change the value of dWH.
"""

import sys
import os
import importlib
from collections import OrderedDict as od
import argparse
import re

MG_DIR = os.environ.get("MG_DIR")
sys.path.append(os.path.join(MG_DIR))
sys.path.append(os.path.join(MG_DIR, "models"))

import check_param_card as param_card_mod


def loadModel(process):
  with open(os.path.join("cards", process, "proc_card.dat"), "r") as f:
    model_name = f.readline().strip("\n").split("import model")[1].split("-")[0].strip(" ")
  
  print(">> Loading model: %s"%model_name)  
  model = importlib.import_module(model_name)
  return model

def getParameters(process, model, blocks):
  """
  Find all parameters belonging to blocks and then cross-check with the param card.
  There may be fewer parameters in the param card if a restrict card was used.
  """
  param_card = param_card_mod.ParamCard(os.path.join(MG_DIR, process, "Cards", "param_card.dat"))

  params = []
  for param in model.all_parameters:
    block = param.lhablock
    if block in blocks:
      #check that this block exists in param card
      assert block.lower() in param_card.keys() #block names appear in lower case in param card
      
      #if this param in param card
      if (param.lhacode[0],) in param_card[block.lower()].keys():
        params.append(param.name)
  return params

def makeConfig(process, model, params, args):
  print(">> Making config json")

  relevant_blocks = set([getattr(model.parameters, param_name).lhablock for param_name in params])
  block_param_nums = ""
  for block in relevant_blocks:
    nums = sorted([getattr(model.parameters, param_name).lhacode[0] for param_name in params if getattr(model.parameters, param_name).lhablock==block])
    block_param_nums += "%s:"%block + ",".join([str(num) for num in nums]) + " "

  extra_args = " --def-val %s --def-sm %s --def-gen %s"%(args.def_val, args.def_sm, args.def_gen)
  if args.set_inactive != None: extra_args += " --set-inactive %s"%" ".join(args.set_inactive)
  command = "python scripts/make_config.py -p %s -o cards/%s/config.json --pars %s"%(process, process, block_param_nums) + extra_args
  print(command)
  os.system(command)

def makeReweight(process):
  print(">> Making reweight card")
  command = "python scripts/make_reweight_card.py cards/%s/config.json cards/%s/reweight_card.dat"%(process, process)
  os.system(command)


"""Method 1"""

#used to split an equation into its terms
delims = "()-+*/"
regex = "".join(["\%s|"%delim for delim in delims])[:-1]

def findRelevantParameters1(process, possible_params):
  with open(os.path.join(MG_DIR, process, "SubProcesses", "coupl.inc"), "r") as f:
    couplings = []

    end = False
    while not end:
      line = f.readline().strip("\n")
      if "COMMON/COUPLINGS/" in line:
        end = True
        couplings = line.split("COMMON/COUPLINGS/")[1]
        line = f.readline().strip("\n")
        while "$" in line:
          couplings += line.split("$")[1]
          line = f.readline().strip("\n")

  couplings = couplings.replace(" ", "").split(",")

  parameters = []
  for coup in model.all_couplings:
    info = coup.get_all()
    if info['name'] in couplings:
      parameters.extend(re.split(regex, info['value'].replace(" ", ""))) #split according to +-/*()

  return set(possible_params).intersection(parameters)


"""Method 2"""

def getPSFiles(process):
  #assume all directories in SubProcesses folder are subprocesses
  SubProcesses_path = os.path.join(MG_DIR, process, "SubProcesses")  
  subprocesses = os.walk(SubProcesses_path).next()[1]

  ps_files = []
  for subprocess in subprocesses:
    path = os.path.join(SubProcesses_path, subprocess)
    ps_files_in_subprocess = filter(lambda x: x[-3:]==".ps", os.listdir(path))
    ps_files.extend([os.path.join(path,ps_file) for ps_file in ps_files_in_subprocess])

  return ps_files

def findRelevantParameters2(process, possible_params):
  ps_files = getPSFiles(process)

  params = []
  for ps_file in ps_files:
    with open(ps_file, "r") as f:
      content = f.read()
    
    for line in content.split("\n"):
       if line[:5] == " (NP=":
         coupling_orders = line.split(",")[1:] #exclude NP=1 for list
         for coupling_order in coupling_orders:
           if ("=1" in coupling_order) and ("NP" in coupling_order):
             params.append(coupling_order.split("NP")[1].split("=")[0])

  params = list(set(params)) #remove copies
  
  """
  If parameter is complex then it will have a Re and Im component but will not
  appear this way in coupling orders -> add Re and Im to parameters where 
  neccessary.
  Will also remove parameters that do not exist in possible_params, even when
  considering Re component.
  """
  complex_params = []
  to_remove = []
  for param in params:
    if param not in possible_params:
      if param+"Re" in possible_params:
        complex_params.append(param)
      else:
        to_remove.append(param)

  for param in to_remove:
    params.remove(param)

  for param in complex_params:
    params.remove(param)
    params.append(param+"Re")
    if param+"Im" in possible_params: #if SMEFTcpv is not a required block, Im component not needed
      params.append(param+"Im")

  return params

"""SMEFTsim propagator corrections"""

def isnum(string):
  try:
    float(string)
  except:
    return False
  return True

def expandParameters(params, model, level=0):
  """
  Recursively find the dependence of a set of parameters on other parameters.
  The recursion stops when it find a parameter that is not dependent on any other
  i.e. it is just a number.
  """
  offset=level*2*" "
  
  new_params = []
  #print(offset+"Expanding: %s"%params)
  for param in params:
    #print(offset+" "+param)
    value = getattr(model.parameters, param).value
    if isnum(value): 
      #print(offset+"  Is a num")
      new_params.append(param)
    else:
      maybe_params = re.split(regex, value.replace(" ", ""))
      filtered_params = set(filter(lambda x: hasattr(model.parameters, x), maybe_params)) 
      new_params.extend(expandParameters(filtered_params, model, level+1))
  return new_params

def getRelevantParametersPropCorr(process, possible_params, model):
  dummy_particles = ["h1", "z1", "w1+", "w1-", "t1", "t1~"]
  dummy_to_parameter = {"h1": "dWH",
                        "z1": "dWZ",
                        "w1+": "dWW",
                        "w1-": "dWW",
                        "t1": "dWT",
                        "t1~":"dWT"}
  dependent_parameters = []
 
  ps_files = getPSFiles(process)
  for ps_file in ps_files:
    with open(ps_file, "r") as f:
      content = f.read()
      for dummy in dummy_particles:
        if "(%s)   show"%dummy in content:
          dependent_parameters.append(dummy_to_parameter[dummy])
  dependent_parameters = set(dependent_parameters)
  dependent_parameters = set(expandParameters(dependent_parameters, model))
 
  return set(possible_params).intersection(dependent_parameters) 


parser = argparse.ArgumentParser()
parser.add_argument('--process', '-p', default='zh-HEL', help="Label of the process, must correspond to the dir name that was created in the MG dir")
parser.add_argument('--blocks', '-b', default="SMEFT", help="Comma seperated list of parameters blocks to consider, e.g. SMEFT,SMEFTcpv")
parser.add_argument('--noValidation', default=False, action="store_true", help="Only use method 1. Do not bother using method 2 to validate")
parser.add_argument('--noReweightCard', default=False, action="store_true", help="Do not make a reweight card.")
parser.add_argument('--noConfigJson', default=False, action="store_true", help="Do not make a config json.")


parser.add_argument('--def-val', type=float, default=0.01)
parser.add_argument('--set-inactive', type=str, nargs='*', help='')
parser.add_argument('--def-sm', type=float, default=0.0)
parser.add_argument('--def-gen', type=float, default=0.0)

args = parser.parse_args()

process = args.process
blocks = args.blocks.split(",")

model = loadModel(process)
smeftsim_v3 = ("SMEFTsim" in model.__name__) and (int(model.__version__[0]) == 3)

if not smeftsim_v3:
  print(">> Not using SMEFTsim v3 -> using only method 1")
  args.noValidation = True

possible_params = getParameters(process, model, blocks)
print(">> Possible parameters: %s"%possible_params)

p1 = sorted(findRelevantParameters1(process, possible_params))
print(">> Method 1 relevant parameters: %s"%p1)
if not args.noValidation: 
  p2 = sorted(findRelevantParameters2(process, possible_params))
  print(">> Method 2 relevant parameters: %s"%p2)
  assert p1==p2

if smeftsim_v3:
  prop_corr_p = sorted(getRelevantParametersPropCorr(process, possible_params, model))
  print(">> Relevant parameters from propagator corrections: %s"%prop_corr_p)
  relevant_params = sorted(set(p1).union(prop_corr_p))
else:
  relevant_params = sorted(p1)

print(">> Final relevant parameters: %s"%relevant_params)

if not args.noConfigJson:
  makeConfig(process, model, relevant_params, args)
if not args.noConfigJson and not args.noReweightCard:
  makeReweight(process)
