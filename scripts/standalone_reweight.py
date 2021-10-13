import sys
import os
import ROOT
import imp
import subprocess
import argparse
import math
import json
import numpy
import copy
from collections import defaultdict


def GetConfigFile(filename):
    with open(filename) as jsonfile:
        cfg = json.load(jsonfile)

    for p in cfg['parameters']:
        for k in cfg['parameter_defaults']:
            if k not in p:
                p[k] = cfg['parameter_defaults'][k]
    return cfg

import contextlib
#from MadGraph misc.py, useful for supressing output
@contextlib.contextmanager
def stdchannel_redirected(stdchannel, dest_filename):
    """                                                                                                                                                                                                     
    A context manager to temporarily redirect stdout or stderr                                                                                                                                              
                                                                                                                                                                                                            
    e.g.:                                                                                                                                                                                                   
                                                                                                                                                                                                            
                                                                                                                                                                                                            
    with stdchannel_redirected(sys.stderr, os.devnull):                                                                                                                                                     
        if compiler.has_function('clock_gettime', libraries=['rt']):                                                                                                                                        
            libraries.append('rt')                                                                                                                                                                          
    """

    try:
        oldstdchannel = os.dup(stdchannel.fileno())
        dest_file = open(dest_filename, 'w')
        os.dup2(dest_file.fileno(), stdchannel.fileno())
        yield
    finally:
        if oldstdchannel is not None:
            os.dup2(oldstdchannel, stdchannel.fileno())
            os.close(oldstdchannel)
        if dest_file is not None:
            dest_file.close()


class StandaloneReweight:

    def __init__(self, rw_pack, no_match_behaviour='sm weights'):
        self.mode = 0
        self.references = {}
        self.caches = {}
        self.tocache = ['couplings', 'weak', 'rscale', 'strong', 'masses', 'widths']

        """Decide what to do when given particles do not match rw module
        no_match_behaviour = 'sm weights' -> return 1.0 for all reweights
        no_match_behaviour = 'return False' -> return False"""
        self.no_match_behaviour=no_match_behaviour

        self.target_dir = os.path.abspath(rw_pack)
        self.cfg = GetConfigFile(os.path.join(self.target_dir, 'config.json'))
        # self.module = module
        # self.cards = cards_dir
        self.Npars = len(self.cfg['parameters'])
        self.parVals = [X['val'] for X in self.cfg['parameters']]
        self.pars = [X['name'] for X in self.cfg['parameters']]

        self.N = 1 + self.Npars * 2 + (self.Npars * self.Npars - self.Npars) / 2

        print '>> %i parameters, %i reweight points' % (self.Npars, self.N)
        self.checkNLO()
        if self.nlo:
            print(">> NLO Reweighting")
        else:
            print(">> LO Reweighting")
        print(">> Initialising modules...")
        self.InitModules()

        rw_me = self.mods[0]
        ## The following code adapted from Madgraph, rweight_interface.py: L1770
        self.all_pdgs = [[pdg for pdg in pdgs if pdg!=0] for pdgs in rw_me.get_pdg_order()]
        self.all_prefix = [''.join(j).strip().lower() for j in rw_me.get_prefix()]
        prefix_set = set(self.all_prefix)

        # Prepare the helicity dict
        self.hel_dict = {}
        for prefix in prefix_set:
            if hasattr(rw_me, '%sprocess_nhel' % prefix):
                nhel = getattr(rw_me, '%sprocess_nhel' % prefix).nhel
                self.hel_dict[prefix] = {}
                for i, onehel in enumerate(zip(*nhel)):
                    self.hel_dict[prefix][tuple(onehel)] = i + 1
            elif hasattr(rw_me, 'set_madloop_path') and \
                 os.path.exists(os.path.join(self.target_dir, 'rwgt', self.onedir, 'SubProcesses', 'MadLoop5_resources', '%sHelConfigs.dat' % prefix.upper())):
                self.hel_dict[prefix] = {}
                for i,line in enumerate(open(os.path.join(self.target_dir, 'rwgt', self.onedir, 'SubProcesses', 'MadLoop5_resources', '%sHelConfigs.dat' % prefix.upper()))):
                    onehel = [int(h) for h in line.split()]
                    self.hel_dict[prefix][tuple(onehel)] = i+1

        self.setNinitsFromPdgList()
        self.sorted_pdgs = []
        for pdglist in self.all_pdgs:
            self.sorted_pdgs.append(self.SortPDGs(pdglist))

        print '>> StandaloneReweight class initialized'
        print '>> Accepted PDG lists:'
        for pdgs in self.all_pdgs:
            print '   - %s' % pdgs
        # print self.hel_dict
        # print self.all_pdgs
        # print self.sorted_pdgs

    def checkNLO(self):
        if os.path.isdir(os.path.join(self.target_dir, 'rwgt', "rw_me_second", 'SubProcesses')): #if nlo
            self.nlo = True
            self.onedir = "rw_me_second"
        else:
            self.nlo = False
            self.onedir = "rw_me"

    def setNinitsFromPdgList(self):
        """Get number of initial particles. Make a guess based upon the pdgs of the first two
        particles in a pdglist. If both are either quarks or gluons -> production process ->
        Ninits = 2. If not assume decay process -> Ninits = 1.
        Guess may be wrong so cross checks are made later on."""
        pdglist = self.all_pdgs[0]
        if (abs(pdglist[0])<9 or pdglist[0]==21) and (abs(pdglist[0])<9 or pdglist[0]==21):
            self.nInits = 2
        else:
            self.nInits = 1

    def InitModules(self):
        iwd = os.getcwd()

        subproc_dir = os.path.join(self.target_dir, 'rwgt', self.onedir, 'SubProcesses')
        sys.path.append(subproc_dir)
        self.mods = []

        if self.mode == 0:
            """
            if not os.path.isdir(os.path.join(subproc_dir, 'rwdir_0')):
                os.chdir(subproc_dir)
                for i in xrange(self.N):
                    os.mkdir('rwdir_%i' % i)
                    subprocess.check_call(['cp', 'allmatrix2py.so', 'rwdir_%i/allmatrix2py.so' % i])
                os.chdir(iwd)
            else:
                print '>> Reusing working directory %s' % self.target_dir
            """
            os.chdir(subproc_dir)
            for i in range(self.N):
                try:
                    os.mkdir('rwdir_%i' % i)
                except:
                    pass
                subprocess.check_call(['cp', 'allmatrix2py.so', 'rwdir_%i/allmatrix2py.so' % i])
            os.chdir(iwd)

            os.chdir(subproc_dir)

            for i in xrange(self.N):
                sys.path[-1] = '%s/rwdir_%i' % (subproc_dir, i)
                # print imp.find_module('allmatrix2py')
                self.mods.append(imp.load_module('allmatrix2py', *imp.find_module('allmatrix2py')))
                del sys.modules['allmatrix2py']
                self.mods[-1].initialise('%s/param_card_%i.dat' % (self.target_dir, i))
                if hasattr(self.mods[-1], 'set_madloop_path'):
                    self.mods[-1].set_madloop_path(os.path.join(subproc_dir, 'MadLoop5_resources'))

            os.chdir(iwd)
        elif self.mode == 1:
            os.chdir(subproc_dir)
            self.mods.append(imp.load_module('allmatrix2py', *imp.find_module('allmatrix2py')))
            mod = self.mods[0]
            self.references = {}

            for block in self.tocache:
                print '>>> %s' % block
                self.references[block] = []
                self.caches[block] = []
                fortran_dict = getattr(mod, block).__dict__
                for key, val in fortran_dict.iteritems():
                    self.references[block].append((key, val))
                # print self.references[block]

            for i in xrange(self.N):
                mod.initialise('%s/param_card_%i.dat' % (self.target_dir, i))
                for block in self.tocache:
                    cache = []
                    for key, val in self.references[block]:
                        cache.append(val.copy())
                    self.caches[block].append(cache)

                # for i in range(len(self.references[block])):
                #     vals = [X[i] for X in self.caches[block]]
                #     allequal = vals.count(vals[0]) == len(vals)
                #     print self.references[block][i], allequal
            # print self.caches
            # print self.references
            # print self.references['couplings']
            # for key, val in mod.couplings.__dict__.iteritems():
            #     cache.append((key, val, val.copy()))
            os.chdir(iwd)
            # sys.exit(0)

    def RestoreCache(self, index):
        for block in self.tocache:
            restore_to = self.references[block]
            restore_from = self.caches[block][index]
            for i in range(len(restore_to)):
                numpy.copyto(restore_to[i][1], restore_from[i])


    def SortPDGs(self, pdgs):
        return sorted(pdgs[:self.nInits]) + sorted(pdgs[self.nInits:])

    def invert_momenta(self, p):
            """ fortran/C-python do not order table in the same order"""
            new_p = []
            for i in range(len(p[0])):
                new_p.append([0] * len(p))
            for i, onep in enumerate(p):
                for j, x in enumerate(onep):
                    new_p[j][i] = x
            return new_p

    def zboost(self, part, pboost=[]):
            """Both momenta should be in the same frame.
               The boost perform correspond to the boost required to set pboost at
               rest (only z boost applied).
            """
            E = pboost[0]
            pz = pboost[3]

            #beta = pz/E
            gamma = E / math.sqrt(E**2-pz**2)
            gammabeta = pz  / math.sqrt(E**2-pz**2)

            out =  [gamma * part[0] - gammabeta * part[3],
                                part[1],
                                part[2],
                                gamma * part[3] - gammabeta * part[0]]

            if abs(out[3]) < 1e-6 * out[0]:
                out[3] = 0
            return out

    def rotZ(self, p, angle):
        p[1], p[2] = p[1]*math.cos(angle)-p[2]*math.sin(angle),  p[1]*math.sin(angle)+p[2]*math.cos(angle)
        return p

    def rotY(self, p, angle):
        p[1], p[3] = p[1]*math.cos(angle)+p[3]*math.sin(angle),  -p[1]*math.sin(angle)+p[3]*math.cos(angle)
        return p

    def allboost(self, p, pboost):
        """
        Strategy here is to rotate pboost such that it lies along the z axis. Then boost pboost 
        so that it is in its rest frame. Perform the same transformations to p, and then undo
        the rotations at the end.
        """
        p, pboost = copy.copy(p), copy.copy(pboost) #force pass by value

        #rotate around z axis such that there is no y component
        if pboost[1]!=0:
            z_rot_angle = math.atan2(pboost[2],pboost[1])
        elif pboost[2]>0:
            z_rot_angle = math.pi/2
        else:
            z_rot_angle = -math.pi/2

        p = self.rotZ(p, -z_rot_angle)
        pboost = self.rotZ(pboost, -z_rot_angle)

        #rotate around y axis so pboost lies along z axis
        r = math.sqrt(pboost[1]**2+pboost[2]**2+pboost[3]**2)
        y_rot_angle = math.acos(pboost[3]/r)

        p = self.rotY(p, -y_rot_angle)
        pboost = self.rotY(pboost, -y_rot_angle)

        #perform Lorentz boost
        p = self.zboost(p, pboost)
        pboost = self.zboost(pboost, pboost)

        #undo rotations
        p = self.rotY(p, y_rot_angle)
        pboost = self.rotY(pboost, y_rot_angle)
        p = self.rotZ(p, z_rot_angle)
        pboost = self.rotZ(pboost, z_rot_angle)
    
        if abs(p[1]) < 1e-6 * p[0]:
            p[1] = 0
        if abs(p[2]) < 1e-6 * p[0]:
            p[2] = 0
        if abs(p[3]) < 1e-6 * p[0]:
            p[3] = 0
        if abs(pboost[1]) < 1e-6 * pboost[0]:
            pboost[1] = 0
        if abs(pboost[2]) < 1e-6 * pboost[0]:
            pboost[2] = 0
        if abs(pboost[3]) < 1e-6 * pboost[0]:
            pboost[3] = 0

        #check that transformations put pboost in rest frame
        assert pboost[1]==pboost[2]==pboost[3]==0

        return p

    def ComputeWeights(self, parts, pdgs, hels, stats, alphas, dohelicity=True, verb=False):
        assert len(parts) == len(pdgs) == len(hels) == len(stats)
        if self.no_match_behaviour=='return False':
            res = False
        else:
            res = [1.0] * self.N

        init_pdg_dict = defaultdict(list)
        fnal_pdg_dict = defaultdict(list)

        nParts = len(parts)
        nInits = 0 #count number of incoming particles
        selected_pdgs = []
        for ip in xrange(nParts):
            if stats[ip] not in [-1, 1]:
                continue
            selected_pdgs.append(pdgs[ip])
            if stats[ip] == -1:
                nInits += 1
                init_pdg_dict[pdgs[ip]].append(ip)
            if stats[ip] == +1:
                fnal_pdg_dict[pdgs[ip]].append(ip)

        assert nInits==self.nInits #check that nInits guess from earlier was correct

        evt_sorted_pdgs = self.SortPDGs(selected_pdgs)

        try:
            idx = self.sorted_pdgs.index(evt_sorted_pdgs)
        except ValueError:
            print '>> Event with PDGs %s does not match any known process' % pdgs
            return res

        target_pdgs = self.all_pdgs[idx]

        reorder_pids = []
        for ip in xrange(len(target_pdgs)):
            target = target_pdgs[ip]
            if ip < nInits:
                reorder_pids.append(init_pdg_dict[target].pop(0))
            else:
                reorder_pids.append(fnal_pdg_dict[target].pop(0))
        if verb:
            print '>> Event layout is %s, matching target layout %s => ordering is %s' % (selected_pdgs, target_pdgs, reorder_pids)

        final_pdgs = []
        final_parts = []
        final_hels = []
        for ip in reorder_pids:
            final_parts.append(parts[ip])
            final_pdgs.append(pdgs[ip])
            final_hels.append(hels[ip])
        # print final_pdgs

        com_final_parts = []
        if nInits == 1:
            pboost = [final_parts[0][i] for i in xrange(4)]
        elif nInits == 2:
            pboost = [final_parts[0][i] + final_parts[1][i] for i in range(4)]
        else:
            raise Exception("More than two initial particles.")

        for part in final_parts:
            if (pboost[1]!=0) or (pboost[2]!=0): #if non-zero pt boost do boost in all directions
                com_final_parts.append(self.allboost(part, pboost))
            else: #otherwise just boost along z
                com_final_parts.append(self.zboost(part, pboost))
            

        final_parts_i = self.invert_momenta(com_final_parts)

        nhel = -1  # means sum over all helicity

        if dohelicity:
            hel_dict = self.hel_dict[self.all_prefix[idx]]
            t_final_hels = tuple(final_hels)
            if t_final_hels in hel_dict:
                nhel = hel_dict[t_final_hels]
                if verb:
                    print '>> Selected nhel=%i, from dict %s' % (nhel, self.all_prefix[idx])
            else:
                print '>> Helicity configuration %s was not found in dict, using -1' % final_hels
        scale2 = 0.
        val_ref = 1.0
        for iw in xrange(self.N):
            if self.mode == 0:
                with stdchannel_redirected(sys.stdout, os.devnull): #prevent MadLoop output
                    val = self.mods[iw].smatrixhel(final_pdgs, final_parts_i, alphas, scale2, nhel)
            elif self.mode == 1:
                self.RestoreCache(iw)
                val = self.mods[0].smatrixhel(final_pdgs, final_parts_i, alphas, scale2, nhel)
            if self.nlo:
                val = val[0]
            if iw == 0:
                val_ref = val
            res[iw] = val / val_ref
        return res

    def TransformWeights(self, raw_weights):
        N = len(raw_weights)
        verb = 0
        if verb > 0:
            print "-- Have %i weights" % N
        out = [0.] * len(raw_weights)
        out_unscaled = [0.] * len(raw_weights)
        Npars = self.Npars
        for i in xrange(N):
            if verb > 0:
                print " - %f" % raw_weights[i]
            out[i] = raw_weights[i]
            out_unscaled[i] = raw_weights[i]

        for ip in xrange(Npars):
            s0 = raw_weights[0]
            s1 = raw_weights[ip * 2 + 1]
            s2 = raw_weights[ip * 2 + 2]
            if verb > 0:
                print " -- Doing %i" % ip
                print "%f\t%f\t%f" % (s0, s1, s2)
            s1 -= s0
            s2 -= s0
            if verb > 0:
                print " - subtract s0: %f\t%f" % (s1, s2)
            Ai = 4. * s1 - s2
            Bii = s2 - Ai
            if verb > 0:
                print " - Result: %f\t%f" % (Ai, Bii)
            out[ip * 2 + 1] = Ai
            out[ip * 2 + 2] = Bii
            out_unscaled[ip * 2 + 1] = (Ai / self.parVals[ip])
            out_unscaled[ip * 2 + 2] = (Bii / (self.parVals[ip] * self.parVals[ip]))
        crossed_offset = 1 + 2 * Npars
        c_counter = 0
        for ix in xrange(0, Npars):
            for iy in xrange(ix + 1, Npars):
                if verb > 0:
                    print " -- Doing %i\t%i\t[%i]" % (ix, iy, crossed_offset + c_counter)
                s = raw_weights[crossed_offset + c_counter]
                sm = raw_weights[0]
                sx = out[ix * 2 + 1]
                sy = out[iy * 2 + 1]
                sxx = out[ix * 2 + 2]
                syy = out[iy * 2 + 2]
                s -= (sm + sx + sy + sxx + syy)
                out[crossed_offset + c_counter] = s
                out_unscaled[crossed_offset + c_counter] = s / (self.parVals[ix] * self.parVals[iy])
                if verb > 0:
                    print " - Result: %f" % s
                c_counter += 1

        return out_unscaled

    def CalculateWeight(self, transformed_weights, **kwargs):
        # print kwargs
        wt = transformed_weights[0]
        for i in xrange(self.Npars):
            par = self.pars[i]
            if par in kwargs:
                # print transformed_weights[i * 2 + 1], transformed_weights[i * 2 + 2]
                wt += transformed_weights[i * 2 + 1] * kwargs[par]
                wt += transformed_weights[i * 2 + 2] * kwargs[par] * kwargs[par]
        crossed_offset = 1 + 2 * self.Npars
        c_counter = 0
        for ix in xrange(0, self.Npars):
            for iy in xrange(ix + 1, self.Npars):
                if self.pars[ix] in kwargs and self.pars[iy] in kwargs:
                    # print transformed_weights[crossed_offset + c_counter] 
                    wt += transformed_weights[crossed_offset + c_counter] * kwargs[self.pars[ix]] * kwargs[self.pars[iy]]
                c_counter += 1
        return wt

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--module', default='.')
    # parser.add_argument('--cards', default='rw_config')
    # parser.add_argument('--config', default='test.json')
    parser.add_argument('--helicity', type=int, default=1)
    parser.add_argument('-i', '--input', default='input.lhe')
    parser.add_argument('-o', '--output', default='output.lhe')
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()

    iwd = os.getcwd()


    ROOT.gROOT.ProcessLine('#include "LHEF.h"')

    # // Create Reader and Writer object
    reader = ROOT.LHEF.Reader(args.input)
    writer = ROOT.LHEF.Writer(args.output)
    rw = StandaloneReweight(args.module)
    # # // Copy header and init blocks and write them out.
    # //  if ( reader.outsideBlock.length() ) std::cerr << reader.outsideBlock;
    # print reader.headerBlock

    writer.headerBlock().write(str(reader.headerBlock), len(str(reader.headerBlock)))
    writer.initComments().write(str(reader.initComments), len(str(reader.initComments)))
    writer.heprup = reader.heprup
    writer.heprup.weightgroup.clear()
    writer.heprup.weightinfo.clear()

    weightgroup = ROOT.LHEF.WeightGroup()
    # weightgroup.attributes['name'] ="mg_reweighting"
    # weightgroup.attributes['weight_name_strategy'] = "includeIdInWeightName"
    writer.heprup.weightgroup.push_back(weightgroup)

    for iw in xrange(rw.N):
        weightinfo = ROOT.LHEF.WeightInfo()
        weightinfo.name = 'rw%.4i' % iw
        weightinfo.inGroup = 0
        weightinfo.isrwgt = True
        weightinfo.contents = 'from param_card_%i.dat' % iw
        writer.heprup.weightinfo.push_back(weightinfo)


    writer.init()
    neve = 0
    # // Read each event and write them out again.
    while reader.readEvent():
        ++neve
        # if reader.outsideBlock.length() ) std::cout << reader.outsideBlock;
        writer.eventComments().write(str(reader.eventComments), len(str(reader.eventComments)))
        writer.hepeup = reader.hepeup
        existing = []
        if args.validate:
            print '>> Reading %i existing weights' % (writer.hepeup.weights.size() - 1)
            # The first weight is the original weight - we should skip it
            for iorig in xrange(1, writer.hepeup.weights.size()):
                existing.append(writer.hepeup.weights[iorig].first)
        writer.hepeup.namedweights.clear()
        writer.hepeup.weights.clear()

        parts = []
        pdgs = []
        hels = []
        stats = []
        nParts = writer.hepeup.NUP
        for ip in xrange(nParts):
            # Put in EPxPyPz format
            parts.append([writer.hepeup.PUP[ip][3], writer.hepeup.PUP[ip][0], writer.hepeup.PUP[ip][1], writer.hepeup.PUP[ip][2]])
            pdgs.append(int(writer.hepeup.IDUP[ip]))
            stats.append(int(writer.hepeup.ISTUP[ip]))
            hels.append(round(writer.hepeup.SPINUP[ip]))
        # print hels

        res = rw.ComputeWeights(parts, pdgs, hels, stats, writer.hepeup.AQCDUP, bool(args.helicity))

        trans_res = rw.TransformWeights(res)

        # print rw.CalculateWeight(trans_res, ca=0.01, c3w=0.01)

        if args.validate:
            for iw in xrange(min(len(existing), len(res))):
                print '%-10f %-10f %-10f | %-10f' % (existing[iw] / existing[0], res[iw], res[iw] / (existing[iw] / existing[0]), trans_res[iw])

        for iw, wt in enumerate(res):
            weight = ROOT.LHEF.Weight()
            weight.name = 'rw%.4i' % iw
            weight.iswgt = True
            weight.weights.push_back(wt * writer.hepeup.XWGTUP)
            writer.hepeup.namedweights.push_back(weight)

        writer.hepeup.heprup = writer.heprup
        writer.writeEvent()
