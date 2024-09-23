"""
Simple interface for lhe files. 
Can be used interactively to search through an lhe file by doing:
  python scripts/lhe_interface.py my_lhe_file.lhe
If you want to also see the reweights in the lhe file do:
  python scripts/lhe_interface.py my_lhe_file.lhe <number of reweights>
"""
from __future__ import print_function

from builtins import input
from builtins import str
from builtins import next
from builtins import range
import ROOT
from event import *
import numpy as np

ROOT.gROOT.ProcessLine('#include "LHEF.h"')

def getEvents(filename):  
  print("Reading %s"%filename)
  reader = ROOT.LHEF.Reader(filename)

  n_events = 0
  while(reader.readEvent()):
    n_events += 1
    weight = reader.hepeup.XWGTUP
    alphas = reader.hepeup.AQCDUP
    scale2 = 0.0
    parts = []

    for i in range(reader.hepeup.NUP):        
      p = reader.hepeup.PUP[i]
      pdg = reader.hepeup.IDUP[i]
      status = reader.hepeup.ISTUP[i]
      helicity = reader.hepeup.SPINUP[i]

      parts.append(Particle([p[3],p[0],p[1],p[2]], pdg, status, helicity))

    yield Event(n_events-1, weight, parts, alphas, scale2)

def getReweightsFromFile(filename, n_rw, normalise=True):
  reader = ROOT.LHEF.Reader(filename)
  
  while(reader.readEvent()):
    w = [i[0] for i in reader.hepeup.weights]
    w = w[-n_rw:] #typically the desired reweights are at the end of the list

    if normalise:
      w = np.array(w)
      w = w/w[0]
      yield list(w)
    else:
      yield w

if __name__=="__main__":
  import sys
 
  filename = sys.argv[1]
  gen = getEvents(filename)

  n_rw = 0
  try:
    n_rw = int(sys.argv[2])
  except:
    pass
  
  if n_rw>0:
    reweights_gen = getReweightsFromFile(filename, n_rw, False)

  end = False
  while not end:
    for i in range(5):
      try:
        print(next(gen))
        if n_rw>0:
          print("Reweights: " + str(next(reweights_gen)))
      except:
        print("End of file reached")
        end = True
        break
    if not end:
      if input("Press enter to continue (input anything else to stop): ")!="":
        end = True
        
