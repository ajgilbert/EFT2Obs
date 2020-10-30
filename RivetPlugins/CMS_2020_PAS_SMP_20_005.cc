// -*- C++ -*-
#include "Rivet/Analysis.hh"
#include "Rivet/Event.hh"
#include "Rivet/Particle.fhh"
#include "Rivet/Particle.hh"
#include "Rivet/Math/LorentzTrans.hh"
#include "Rivet/Projections/ChargedLeptons.hh"
#include "Rivet/Projections/DressedLeptons.hh"
#include "Rivet/Projections/FastJets.hh"
#include "Rivet/Projections/FinalState.hh"
#include "Rivet/Projections/IdentifiedFinalState.hh"
#include "Rivet/Projections/JetAlg.hh"
#include "Rivet/Projections/MissingMomentum.hh"
#include "Rivet/Projections/NonPromptFinalState.hh"
#include "Rivet/Projections/PromptFinalState.hh"
#include "Rivet/Projections/VetoedFinalState.hh"
#include "CMS_2020_PAS_SMP_20_005.h"

WGammaRivetVariables::WGammaRivetVariables() {
  resetVars();
}

void WGammaRivetVariables::resetVars() {
  is_wg_gen = false;
  l0_pt = 0.;
  l0_eta = 0.;
  l0_phi = 0.;
  l0_M = 0.;
  l0_q = 0;
  l0_abs_pdgid = 0;
  p0_pt = 0.;
  p0_eta = 0.;
  p0_phi = 0.;
  p0_M = 0.;
  p0_frixione = false;
  n0_pt = 0.;
  n0_eta = 0.;
  n0_phi = 0.;
  n0_M = 0.;
  met_pt = 0.;
  met_phi = 0.;
  true_phi = 0.;
  true_phi_f = 0.;
  l0p0_dr = 0.;
  mt_cluster = 0.;
  n_jets = 0;
}

namespace Rivet {

/// Book histograms and initialise projections before the run
void CMS_2020_PAS_SMP_20_005::init() {
  vars_.resetVars();

  FinalState fs;

  // Jets - all final state particles excluding neutrinos
  VetoedFinalState vfs;
  vfs.vetoNeutrinos();
  FastJets fastjets(vfs, FastJets::ANTIKT, 0.4);
  declare(fastjets, "Jets");

  // Non-prompt particles for photon isolation
  NonPromptFinalState nonprompt(fs);
  declare(nonprompt, "NonPrompt");

  // Dressed leptons
  ChargedLeptons charged_leptons(fs);
  IdentifiedFinalState photons(fs);
  photons.acceptIdPair(PID::PHOTON);

  PromptFinalState prompt_leptons(charged_leptons);
  declare(prompt_leptons, "PromptLeptons");

  PromptFinalState prompt_photons(photons);
  prompt_photons.acceptMuonDecays(true);
  prompt_photons.acceptTauDecays(true);

  // useDecayPhotons=true allows for photons with tau ancestor,
  // photons from hadrons are vetoed by the PromptFinalState;
  // will be default DressedLeptons behaviour for Rivet >= 2.5.4
  DressedLeptons dressed_leptons(prompt_photons, prompt_leptons, dressed_lepton_cone_, Cuts::open(),
                                 /*useDecayPhotons*/ true);
  declare(dressed_leptons, "DressedLeptons");

  // Photons
  // We remove the photons used up for lepton dressing in this case
  VetoedFinalState vetoed_prompt_photons(prompt_photons);
  if (use_dressed_leptons_) {
    vetoed_prompt_photons.addVetoOnThisFinalState(dressed_leptons);
  }
  declare(vetoed_prompt_photons, "Photons");

  // Neutrinos
  IdentifiedFinalState neutrinos(fs);
  neutrinos.acceptNeutrinos();
  PromptFinalState prompt_neutrinos(neutrinos);
  prompt_neutrinos.acceptMuonDecays(true);
  prompt_neutrinos.acceptTauDecays(true);
  declare(prompt_neutrinos, "Neutrinos");

  // MET
  declare(MissingMomentum(fs), "MET");

  // Booking of histograms
  std::vector<double> eft_pt_binning = {150., 200., 300., 500., 800., 1200.};
  std::vector<double> eft_phi_binning = {0., PI / 6., PI / 3., PI / 2.};
  book(_h["baseline_photon_pt"], "baseline_photon_pt", std::vector<double>{30., 50., 70., 100., 150., 200., 300., 500., 800., 1200.});
  // book(_h2d["eft_main_p_photon_pt_phi"], "eft_main_p_photon_pt_phi", eft_pt_binning, eft_phi_binning);
  // book(_h2d["eft_main_n_photon_pt_phi"], "eft_main_n_photon_pt_phi", eft_pt_binning, eft_phi_binning);
  book(_h2d["eft_main_x_photon_pt_phi"], "eft_main_x_photon_pt_phi", eft_pt_binning, eft_phi_binning);
  // book(_h2d["eft_main_p_photon_pt_phi_jveto"], "eft_main_p_photon_pt_phi_jveto", eft_pt_binning, eft_phi_binning);
  // book(_h2d["eft_main_n_photon_pt_phi_jveto"], "eft_main_n_photon_pt_phi_jveto", eft_pt_binning, eft_phi_binning);
  book(_h2d["eft_main_x_photon_pt_phi_jveto"], "eft_main_x_photon_pt_phi_jveto", eft_pt_binning, eft_phi_binning);
  // book(_h2d["eft_met1_p_photon_pt_phi"], "eft_met1_p_photon_pt_phi", eft_pt_binning, eft_phi_binning);
  // book(_h2d["eft_met1_n_photon_pt_phi"], "eft_met1_n_photon_pt_phi", eft_pt_binning, eft_phi_binning);
  book(_h2d["eft_met1_x_photon_pt_phi"], "eft_met1_x_photon_pt_phi", eft_pt_binning, eft_phi_binning);
  // book(_h2d["eft_met1_p_photon_pt_phi_jveto"], "eft_met1_p_photon_pt_phi_jveto", eft_pt_binning, eft_phi_binning);
  // book(_h2d["eft_met1_n_photon_pt_phi_jveto"], "eft_met1_n_photon_pt_phi_jveto", eft_pt_binning, eft_phi_binning);
  book(_h2d["eft_met1_x_photon_pt_phi_jveto"], "eft_met1_x_photon_pt_phi_jveto", eft_pt_binning, eft_phi_binning);

  book(_h2d["baseline_main_x_photon_pt_phi"], "baseline_main_x_photon_pt_phi", eft_pt_binning, eft_phi_binning);
  book(_h2d["baseline_main_x_photon_pt_phi_jveto"], "baseline_main_x_photon_pt_phi_jveto", eft_pt_binning, eft_phi_binning);
  book(_h2d["baseline_met1_x_photon_pt_phi"], "baseline_met1_x_photon_pt_phi", eft_pt_binning, eft_phi_binning);
  book(_h2d["baseline_met1_x_photon_pt_phi_jveto"], "baseline_met1_x_photon_pt_phi_jveto", eft_pt_binning, eft_phi_binning);

}

/// Perform the per-event analysis
void CMS_2020_PAS_SMP_20_005::analyze(const Event& event) {
  vars_.resetVars();

  std::vector<Particle> outgoing_partons;
  Particle lhe_photon;
  for (unsigned i = 0; i < event.allParticles().size(); ++i) {
    auto const& part = event.allParticles()[i];
    int apdgid = std::abs(part.pid());
    // std::cout << i << "\t" << part.momentum() << "\t" << part.pid() << "\t" << part.genParticle()->status() << "\n";
    if (part.genParticle()->status() == 23 && ((apdgid >= 1 && apdgid <= 6) || apdgid == 21)) {
      outgoing_partons.push_back(part);
    }
  }

  const Particles leptons = applyProjection<FinalState>(event, use_dressed_leptons_ ? "DressedLeptons" : "PromptLeptons").particlesByPt();

  if (leptons.size() == 0) {
    vetoEvent;
  }
  auto l0 = leptons.at(0);

  const Particles photons = applyProjection<FinalState>(event, "Photons").particlesByPt(DeltaRGtr(l0, lepton_photon_dr_cut_));
  if (photons.size() == 0) {
    vetoEvent;
  }
  auto p0 = photons.at(0);

  // bool found_tau = false;
  const Particles neutrinos = applyProjection<FinalState>(event, "Neutrinos").particlesByPt();
  // for (unsigned i = 0; i < neutrinos.size(); ++i) {
  //   if (std::abs(neutrinos[i].pid()) == 16) found_tau = true;
  // }

  if (neutrinos.size() == 0) {
    vetoEvent;
  }

  auto n0 = neutrinos.at(0);

  FourMomentum met = applyProjection<MissingMomentum>(event, "MET").missingMomentum();

  // Redefine the MET
  met = FourMomentum(met.pt(), met.px(), met.py(), 0.);

  // Filter jets on pT, eta and DR with lepton and photon
  const Jets jets = applyProjection<FastJets>(event, "Jets").jetsByPt([&](Jet const& j) {
    return j.pt() > jet_pt_cut_ && std::abs(j.eta()) < jet_abs_eta_cut_ && deltaR(j, l0) > jet_dr_cut_ && deltaR(j, p0) > jet_dr_cut_;
  });

  if (leptons.size() >= 1 && photons.size() >= 1 && neutrinos.size() >= 1) {
    // Populate variables
    vars_.is_wg_gen = true;

    vars_.l0_pt = l0.pt();
    vars_.l0_eta = l0.eta();
    vars_.l0_phi = l0.phi(PhiMapping::MINUSPI_PLUSPI);
    vars_.l0_M = l0.mass();
    vars_.l0_q = l0.charge3() / 3;
    vars_.l0_abs_pdgid = std::abs(l0.pid());

    vars_.p0_pt = p0.pt();
    vars_.p0_eta = p0.eta();
    vars_.p0_phi = p0.phi(PhiMapping::MINUSPI_PLUSPI);
    vars_.p0_M = p0.mass();

    vars_.n_jets = jets.size();

    vars_.p0_frixione = true;
    double frixione_sum = 0.;
    // Apply Frixione isolation to the photon:
    Particles parts = applyProjection<FinalState>(event, "NonPrompt")
                                .particles(DeltaRLess(p0, photon_iso_dr_),
                                           [&](Particle const& part1, Particle const& part2) {
                                             return deltaR(part1, p0) < deltaR(part2, p0);
                                           });
    if (use_parton_isolation_) {
      parts = sortBy(outgoing_partons, [&](Particle const& part1, Particle const& part2) {
                                             return deltaR(part1, p0) < deltaR(part2, p0);
                                           });
    }
    for (auto const& ip : parts) {
      double dr = deltaR(ip, p0);
      if (dr >= photon_iso_dr_) {
        break;
      }
      frixione_sum += ip.pt();
      if (frixione_sum > (p0.pt() * ((1. - std::cos(dr)) / (1. - std::cos(photon_iso_dr_))))) {
        vars_.p0_frixione = false;
      }
    }

    vars_.l0p0_dr = deltaR(l0, p0);

    vars_.n0_pt = n0.pt();
    vars_.n0_eta = n0.eta();
    vars_.n0_phi = n0.phi(PhiMapping::MINUSPI_PLUSPI);
    vars_.n0_M = n0.mass();

    vars_.met_pt = met.pt();
    vars_.met_phi = met.phi(PhiMapping::MINUSPI_PLUSPI);

    auto wg_system = WGSystem(l0, n0, p0, false);

    vars_.true_phi = wg_system.Phi();
    vars_.true_phi_f = wg_system.SymPhi();

    auto cand1 = l0.momentum() + p0.momentum();
    auto full_system = cand1 + met;
    double mTcluster2 = std::pow(std::sqrt(cand1.mass2() + cand1.pt2()) + met.pt(), 2) - full_system.pt2();
    if (mTcluster2 > 0) {
      vars_.mt_cluster = std::sqrt(mTcluster2);
    } else {
      vars_.mt_cluster = 0.;
    }

    if (vars_.l0_pt > lepton_pt_cut_ && std::abs(vars_.l0_eta) < lepton_abs_eta_cut_ &&
        vars_.p0_pt > photon_pt_cut_ && std::abs(vars_.p0_eta) < photon_abs_eta_cut_ && vars_.p0_frixione &&
        vars_.l0p0_dr > lepton_photon_dr_cut_ && vars_.met_pt > missing_pt_cut_) {
      // if (found_tau) {
      //   std::cout << "Found tau event in fiducial volume!\n";
      // }
      _h["baseline_photon_pt"]->fill(vars_.p0_pt / GeV);
    }



    if (vars_.l0_pt > lepton_pt_cut_ && std::abs(vars_.l0_eta) < lepton_abs_eta_cut_ &&
        vars_.p0_pt > photon_pt_cut_ && std::abs(vars_.p0_eta) < photon_abs_eta_cut_ && vars_.p0_frixione &&
        vars_.l0p0_dr > lepton_photon_dr_cut_ && vars_.met_pt > 0.) {

      if (vars_.met_pt <= missing_pt_cut_) {
        _h2d["baseline_met1_x_photon_pt_phi"]->fill(vars_.p0_pt / GeV, vars_.true_phi_f);
        if (vars_.n_jets == 0) {
          _h2d["baseline_met1_x_photon_pt_phi_jveto"]->fill(vars_.p0_pt / GeV, vars_.true_phi_f);
        }
      }

      if (vars_.met_pt > missing_pt_cut_) {
        _h2d["baseline_main_x_photon_pt_phi"]->fill(vars_.p0_pt / GeV, vars_.true_phi_f);
        if (vars_.n_jets == 0) {
          _h2d["baseline_main_x_photon_pt_phi_jveto"]->fill(vars_.p0_pt / GeV, vars_.true_phi_f);
        }
      }
    }

    if (vars_.l0_pt > eft_lepton_pt_cut_ && std::abs(vars_.l0_eta) < lepton_abs_eta_cut_ &&
        vars_.p0_pt > eft_photon_pt_cut_ && std::abs(vars_.p0_eta) < photon_abs_eta_cut_ && vars_.p0_frixione &&
        vars_.l0p0_dr > eft_lepton_photon_dr_cut_ && vars_.met_pt > eft_missing_pt_met1_cut_) {

      // std::string chg = vars_.l0_q == +1 ? "p" : "n";

      if (vars_.met_pt <= eft_missing_pt_cut_) {
        // _h2d["eft_met1_" + chg + "_photon_pt_phi"]->fill(vars_.p0_pt / GeV, vars_.true_phi_f);
        _h2d["eft_met1_x_photon_pt_phi"]->fill(vars_.p0_pt / GeV, vars_.true_phi_f);
        if (vars_.n_jets == 0) {
          // _h2d["eft_met1_" + chg + "_photon_pt_phi_jveto"]->fill(vars_.p0_pt / GeV, vars_.true_phi_f);
          _h2d["eft_met1_x_photon_pt_phi_jveto"]->fill(vars_.p0_pt / GeV, vars_.true_phi_f);
        }
      }

      if (vars_.met_pt > eft_missing_pt_cut_) {
        // _h2d["eft_main_" + chg + "_photon_pt_phi"]->fill(vars_.p0_pt / GeV, vars_.true_phi_f);
        _h2d["eft_main_x_photon_pt_phi"]->fill(vars_.p0_pt / GeV, vars_.true_phi_f);
        if (vars_.n_jets == 0) {
          // _h2d["eft_main_" + chg + "_photon_pt_phi_jveto"]->fill(vars_.p0_pt / GeV, vars_.true_phi_f);
          _h2d["eft_main_x_photon_pt_phi_jveto"]->fill(vars_.p0_pt / GeV, vars_.true_phi_f);
        }
      }

    }
  }
}

/// Normalise histograms etc., after the run
void CMS_2020_PAS_SMP_20_005::finalize() {
  // Scale according to cross section
  scale(_h["baseline_photon_pt"], crossSection() / picobarn / sumOfWeights());
  for (std::string const& x :
       {
        // "eft_main_p_photon_pt_phi",
        // "eft_main_n_photon_pt_phi",
        "eft_main_x_photon_pt_phi",
        // "eft_main_p_photon_pt_phi_jveto",
        // "eft_main_n_photon_pt_phi_jveto",
        "eft_main_x_photon_pt_phi_jveto",
        // "eft_met1_p_photon_pt_phi",
        // "eft_met1_n_photon_pt_phi",
        "eft_met1_x_photon_pt_phi",
        // "eft_met1_p_photon_pt_phi_jveto",
        // "eft_met1_n_photon_pt_phi_jveto",
        "eft_met1_x_photon_pt_phi_jveto",
        "baseline_main_x_photon_pt_phi",
        "baseline_main_x_photon_pt_phi_jveto",
        "baseline_met1_x_photon_pt_phi",
        "baseline_met1_x_photon_pt_phi_jveto"
      }) {
    scale(_h2d[x], crossSection() / picobarn / sumOfWeights());
  }
}

CMS_2020_PAS_SMP_20_005::WGSystem::WGSystem(Particle const& lep, Particle const& neu, Particle const& pho, bool verbose) {
  lepton_charge = lep.charge3() / 3;
  wg_system += lep.momentum();
  wg_system += neu.momentum();
  wg_system += pho.momentum();

  if (verbose) {
    std::cout << "> charge:    " << lepton_charge << "\n";
    std::cout << "> wg_system: " << wg_system << "\n";
    std::cout << "> lepton   : " << lep.momentum() << "\n";
    std::cout << "> neutrino : " << neu.momentum() << "\n";
    std::cout << "> photon   : " << pho.momentum() << "\n";
  }

  auto boost = LorentzTransform::mkFrameTransformFromBeta(wg_system.betaVec());

  c_charged_lepton = boost.transform(lep);
  c_neutrino = boost.transform(neu);
  c_photon = boost.transform(pho);

  if (verbose) {
    std::cout << "> c_lepton   : " << c_charged_lepton << "\n";
    std::cout << "> c_neutrino : " << c_neutrino << "\n";
    std::cout << "> c_photon   : " << c_photon << "\n";
  }

  FourMomentum c_w_boson;
  c_w_boson += c_charged_lepton;
  c_w_boson += c_neutrino;

  auto r_uvec = wg_system.vector3().unit();

  if (verbose) {
    std::cout << "> c_w_boson : " << c_w_boson << "\n";
    std::cout << "> r_uvec   : " << r_uvec << "\n";
  }

  auto z_uvec = c_w_boson.vector3().unit();
  auto y_uvec = z_uvec.cross(r_uvec).unit();
  auto x_uvec = y_uvec.cross(z_uvec).unit();

  if (verbose) {
    std::cout << "> x_uvec   : " << x_uvec << "\n";
    std::cout << "> y_uvec   : " << y_uvec << "\n";
    std::cout << "> z_uvec   : " << z_uvec << "\n";
  }

  Matrix3 rot_matrix;
  rot_matrix.setRow(0, x_uvec).setRow(1, y_uvec).setRow(2, z_uvec);
  auto rotator = LorentzTransform();
  rotator = rotator.postMult(rot_matrix);
  if (verbose) {
    std::cout << "> rotator   : " << rotator << "\n";
  }

  r_w_boson = rotator.transform(c_w_boson);
  r_charged_lepton = rotator.transform(c_charged_lepton);
  r_neutrino = rotator.transform(c_neutrino);
  r_photon = rotator.transform(c_photon);

  if (verbose) {
    std::cout << "> r_lepton   : " << r_charged_lepton << "\n";
    std::cout << "> r_neutrino : " << r_neutrino << "\n";
    std::cout << "> r_photon   : " << r_photon << "\n";
    std::cout << "> r_w_boson  : " << r_w_boson << "\n";
  }
}

double CMS_2020_PAS_SMP_20_005::WGSystem::Phi() {
  double lep_phi = r_charged_lepton.phi(PhiMapping::MINUSPI_PLUSPI);
  return mapAngleMPiToPi(lepton_charge > 0 ? (lep_phi) : (lep_phi + PI));
}

double CMS_2020_PAS_SMP_20_005::WGSystem::SymPhi() {
  double lep_phi = Phi();
  if (lep_phi > PI / 2.) {
    return PI - lep_phi;
  } else if (lep_phi < -1. * (PI / 2.)) {
    return -1. * (PI + lep_phi);
  } else {
    return lep_phi;
  }
}

// The hook for the plugin system
DECLARE_RIVET_PLUGIN(CMS_2020_PAS_SMP_20_005);

}  // namespace Rivet
