"""
The point of this script is to validate the standalone reweighting modules and the
standalone_reweight.py script. The idea is that you produce an lhe file and ask 
MadGraph to do the reweighting at the same time. Then you use the standalone 
reweighting module to calculate the reweights. If the reweights produced by the
standalone module agree with those produced by MadGraph at the time of generation,
then things are working as expected.

The script will comapre each pair (standalone and MG) of reweights and will decide 
if they are the same based upon a threshold that is 1% as default. It will print
the fraction of events that fail at the end.

To run do:
  python scripts/rw_module_tester.py my_lhe_file.lhe my_rw_module <VERB>
<VERB> = 0 -> Minimal output
<VERB> = 1 -> Prints out event that fail
<VERB> = 2 -> Prints out all events
"""
from __future__ import print_function

from builtins import next
from builtins import str
from builtins import range
import sys
import lhe_interface
import numpy as np
import imp
import standalone_reweight

def weightsSame(event, rw, fromfile_weights_gen, threshold=0.01, VERB=0):
  calculated_weights = event.getReweights(rw)
  fromfile_weights = next(fromfile_weights_gen)

  passed = True
  for i in range(len(calculated_weights)):
    a = calculated_weights[i] - 1 #compare the difference from 1
    b = fromfile_weights[i] - 1
    if abs(a-b)/b > threshold:
      passed = False
      break

  if (VERB==1) and not passed:
    print(event)
    print("Passed: " + str(passed))
    print("Calculated weights: " + str(calculated_weights))
    print("From file weights: " + str(fromfile_weights))
    print("")
  elif (VERB>=2):
    print(event)
    print("Passed: " + str(passed))
    print("Calculated weights: " + str(calculated_weights))
    print("From file weights: " + str(fromfile_weights))
    print("")

  return passed

if __name__=="__main__":
  filename = sys.argv[1]
  process = sys.argv[2]
  try:
    VERB = int(sys.argv[3])
  except:
    VERB = 0

  rw = standalone_reweight.StandaloneReweight(process)

  events = lhe_interface.getEvents(filename)
  fromfile_weights_gen = lhe_interface.getReweightsFromFile(filename, rw.N, True)

  no_events = 0
  no_failed = 0

  for event in events:
    no_events += 1
    if not weightsSame(event, rw, fromfile_weights_gen, 0.01, VERB):
      no_failed += 1

  print("Fraction failed:%f" %(float(no_failed)/float(no_events)))
