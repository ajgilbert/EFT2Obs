"""
Automatically detect which parameters are relavant for a provided process.
Given this information, create a process-specific config file.

Two methods:
1) Look at the coupl.inc file in the SubProcesses directory of a process. This file
   contains a block labeled by 'COMMON/COUPLINGS/'. The meaning of these couplings can
   be found in the model's couplings.py file. Relevant parameters can be found by seeing
   whether they appear in these couplings.
2) [SMEFTsim-only method] Look at the postscript files containing the feynman diagrams.
   Each diagram has associated coupling orders, e.g. NPcHG, NPcHB. If NPcHG=1 then this
   means that cHG is relevant for this diagrams. By looping over all diagrams, we can
   find all the relevant parameters.

By default, the script will perform both methods as a way of validation. If not using
SMEFTsim, use the --noValidation tag to use only method 1 (which is model-independent).
"""

import sys
import os
import importlib
from collections import OrderedDict as od
import argparse

MG_DIR = os.environ.get("MG_DIR")

def loadModel(process):
  with open(os.path.join("cards", process, "proc_card.dat"), "r") as f:
    model_name = f.readline().strip("\n").split("import model")[1].split("-")[0].strip(" ")
  
  print(">> Loading model: %s"%model_name)  

  models_path = os.path.join(MG_DIR, "models")
  sys.path.insert(1, models_path)
  model = importlib.import_module(model_name)
  return model

def getParameters(model, blocks=["SMEFT", "SMEFTcpv"]):
  params = []
  for param in model.all_parameters:
    if param.lhablock in blocks:
      params.append(param.name)
  return params

def makeConfig(process, model, params):
  relevant_blocks = set([getattr(model.parameters, param_name).lhablock for param_name in params])
  block_param_nums = ""
  for block in relevant_blocks:
    nums = sorted([getattr(model.parameters, param_name).lhacode[0] for param_name in params if getattr(model.parameters, param_name).lhablock==block])
    block_param_nums += "%s:"%block + ",".join([str(num) for num in nums]) + " "

  command = "python scripts/make_config.py -p %s -o cards/%s/config.json --pars %s"%(process, process, block_param_nums)
  print(command)
  os.system(command)


"""Method 1"""

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

  params = []

  coupling_str = ""
  for coup in model.all_couplings:
    info = coup.get_all()
    if info['name'] in couplings:
      coupling_str += info['value']

  for param in possible_params:
    if param+"*" in coupling_str:
      params.append(param)

  return params


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
  params.remove("cpv")
  
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


parser = argparse.ArgumentParser()
parser.add_argument('--process', '-p', default='zh-HEL', help="Label of the process, must correspond to the dir name that was created in the MG dir")
parser.add_argument('--blocks', '-b', default="SMEFT", help="Comma seperated list of parameters blocks to consider, e.g. SMEFT,SMEFTcpv")
parser.add_argument('--noValidation', default=False, action="store_true", help="Only use method 1. Do not bother using method 2 to validate")

args = parser.parse_args()

process = args.process
blocks = args.blocks.split(",")

model = loadModel(process)
possible_params = getParameters(model, blocks)
p1 = findRelevantParameters1(process, possible_params)
print("Method 1 relevant parameters:", sorted(p1))
if not args.noValidation: 
  p2 = findRelevantParameters2(process, possible_params)
  print("Method 2 relevant parameters:", sorted(p2))
  assert sorted(p1)==sorted(p2)

makeConfig(process, model, p1)
