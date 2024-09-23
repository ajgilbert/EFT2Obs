from builtins import str
from builtins import object
import numpy as np

VERB=True

class Particle(object):
  def __init__(self, p, pdg_id, status, helicity=None):
    self.p = p
    self.pdg_id = pdg_id
    self.status = status
    self.helicity = helicity

  def getP(self):
    return self.p

  def getPT(self):
    return np.sqrt(self.p[1]**2 + self.p[2]**2) 

  def getPdg_id(self):
    return self.pdg_id

  def getStatus(self):
    return self.status

  def getHelicity(self):
    return self.helicity

  def isJet(self):
    if self.status==1:
      if (abs(self.pdg_id)<=9) or (self.pdg_id==21):
        return True
    return False

  def __str__(self):
    p_strs = [("%.1f"%p_i).rjust(10, ' ') for p_i in self.p]

    string = str(pdg_dict[self.pdg_id]).rjust(10, ' ') + str(self.status).rjust(10, ' ') + str(self.helicity).rjust(10, ' ') + " "*5 + ''.join(p_strs)

    return string

class Event(object):
  def __init__(self, event_id, weight, gen_particles, alphas=0.137, scale2=0.0):
    self.event_id = event_id
    self.gen_particles = gen_particles
    self.alphas = alphas
    self.weight = weight
    self.scale2 = scale2

  def getWeight(self):
    return self.weight

  def getParticles(self):
    return self.gen_particles

  def getReweightInfo(self):
    parts = []
    pdgs = []
    helicities = []
    status = []
    for particle in self.gen_particles:
      parts.append(particle.getP())
      pdgs.append(particle.getPdg_id())
      helicities.append(particle.getHelicity())
      status.append(particle.getStatus())

    return parts, pdgs, helicities, status

  def useHelicity(self, helicities):
    """
    If all gen_particles have helicity information return True.
    Else, return False.
    """
    for h in helicities:
      if h==None:
        return False
    return True

  def getReweights(self, rw):
    parts, pdgs, helicities, status = self.getReweightInfo()

    use_helicity = self.useHelicity(helicities)
    reweights = rw.ComputeWeights(parts, pdgs, helicities, status, self.alphas, use_helicity, VERB)
    return reweights

  def __str__(self):
    strings = []
    strings.append("-"*75)
    strings.append(" Particle | status  | helicity |   | E       | P_x     | P_y     | P_z      ")
    strings.append("-"*75)
    for particle in self.gen_particles:
      strings.append(str(particle))
    return "\n".join(strings)

"""
Credit to https://github.com/scikit-hep/particle for the csv file
https://doi.org/10.5281/zenodo.2552429
"""
import csv
pdg_dict = {}
with open("pdgid_to_evtgenname.csv", "r") as f:
  line_no = 0
  for row in csv.reader(f):
    if line_no>1:
      pdg_dict[int(row[0])] = row[1]
    line_no += 1
