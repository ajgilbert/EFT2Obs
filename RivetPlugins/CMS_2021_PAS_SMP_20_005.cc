
// This is not the offical Rivet plugin working on the official Rivet 3.1.2 release, but a modified version of it that works with Rivet 4 and includes the modifications made for additional 3D histogram in pT x |phi_f| x theta bins.
// It also includes theta variable. 
// -*- C++ -*-
#include "Rivet/Analysis.hh"
#include "Rivet/Event.hh"
#include "Rivet/Math/LorentzTrans.hh"
#include "Rivet/Particle.hh"
#include "Rivet/Projections/ChargedLeptons.hh"
#include "Rivet/Projections/LeptonFinder.hh"  
#include "Rivet/Projections/FastJets.hh"
#include "Rivet/Projections/FinalState.hh"
#include "Rivet/Projections/IdentifiedFinalState.hh"
#include "Rivet/Projections/MissingMomentum.hh"
#include "Rivet/Projections/PromptFinalState.hh"
#include "Rivet/Projections/VetoedFinalState.hh"
#include <cmath>

namespace Rivet {

class CMS_2021_PAS_SMP_20_005 : public Analysis {
 public:
  struct WGammaRivetVariables {
    bool is_wg_gen;

    double l0_pt;
    double l0_eta;
    double l0_phi;
    double l0_M;
    int l0_q;
    unsigned l0_abs_pdgid;

    double p0_pt;
    double p0_eta;
    double p0_phi;
    double p0_M;
    bool p0_frixione;
    double p0_frixione_sum;

    double l0p0_dr;
    double mt_cluster;

    double n0_pt;
    double n0_eta;
    double n0_phi;
    double n0_M;

    double met_pt;
    double met_phi;

    double true_phi;
    double true_phi_f;

    double true_theta; 
    double true_costheta; 

    int n_jets;

    WGammaRivetVariables() { resetVars(); }
    void resetVars() {
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
      p0_frixione_sum = 0.;
      n0_pt = 0.;
      n0_eta = 0.;
      n0_phi = 0.;
      n0_M = 0.;
      met_pt = 0.;
      met_phi = 0.;
      true_phi = 0.;
      true_phi_f = 0.;
      true_theta = 0.; 
      true_costheta = 0.; 
      l0p0_dr = 0.;
      mt_cluster = 0.;
      n_jets = 0;
    }
  };

  struct WGSystem {
    int lepton_charge;

    FourMomentum wg_system;

    FourMomentum c_w_boson;
    FourMomentum c_charged_lepton;
    FourMomentum c_neutrino;
    FourMomentum c_photon;

    FourMomentum r_w_boson;
    FourMomentum r_charged_lepton;
    FourMomentum r_neutrino;
    FourMomentum r_photon;

    WGSystem(Particle const& lep, Particle const& neu, Particle const& pho, bool verbose);

    double Phi();
    double SymPhi();
    double Theta(); 
    double CosTheta(); 
  };

  double photon_iso_dr_ = 0.4;
  double lepton_pt_cut_ = 30.;
  double lepton_abs_eta_cut_ = 2.5;
  double photon_pt_cut_ = 30.;
  double photon_abs_eta_cut_ = 2.5;
  double missing_pt_cut_ = 40.;
  double lepton_photon_dr_cut_ = 0.7;
  double dressed_lepton_cone_ = 0.1;

  double eft_lepton_pt_cut_ = 80.;
  double eft_photon_pt_cut_ = 150.;

  double jet_pt_cut_ = 30.;
  double jet_abs_eta_cut_ = 2.5;
  double jet_dr_cut_ = 0.4;

  WGammaRivetVariables vars_;
  map<string, Histo1DPtr> _h;
  map<string, Histo2DPtr> _h2;

  // 3D histogram: (pT) x (|phi_f|) x (theta)
  // x: pT   {150,200,300,500,800,1500} GeV, y: |phi_f| {0, pi/6, pi/3, pi/2}, z: theta   {0, pi/3, 2pi/3, pi}
  Histo3DPtr _h3_pt_phi_theta;

  RIVET_DEFAULT_ANALYSIS_CTOR(CMS_2021_PAS_SMP_20_005);

  static int phiBin3(double absphi) {
    if (absphi > 0. && absphi <= (PI / 6.)) return 0;
    if (absphi > (PI / 6.) && absphi <= (PI / 3.)) return 1;
    if (absphi > (PI / 3.) && absphi <= (PI / 2.)) return 2;
    return -1;
  }

  static int thetaBin3(double theta) {
    if (theta >= 0. && theta <= (PI / 3.)) return 0;
    if (theta > (PI / 3.) && theta <= (2. * PI / 3.)) return 1;
    if (theta > (2. * PI / 3.) && theta <= PI) return 2;
    return -1;
  }

  void init() {
    vars_.resetVars();

    FinalState fs;
    declare(fs, "FinalState");

    // Jets - all final state particles excluding neutrinos
    VetoedFinalState vfs;
    vfs.vetoNeutrinos();
    FastJets fastjets(vfs, fastjet::antikt_algorithm, fastjet::E_scheme, 0.4);
    declare(fastjets, "Jets");

    // Dressed leptons
    ChargedLeptons charged_leptons(fs);
    PromptFinalState prompt_leptons(charged_leptons);
    declare(prompt_leptons, "PromptLeptons");

    IdentifiedFinalState photons(fs);
    photons.acceptIdPair(PID::PHOTON);
    PromptFinalState prompt_photons(photons);
    prompt_photons.acceptMuonDecays(true);
    prompt_photons.acceptTauDecays(true);

    // Rivet 4: LeptonFinder replaces DressedLeptons; arg order swapped
    LeptonFinder dressed_leptons(prompt_leptons, prompt_photons, dressed_lepton_cone_,
                                 Cuts::open());
    declare(dressed_leptons, "DressedLeptons");

    // Photons
    VetoedFinalState vetoed_prompt_photons(prompt_photons);
    vetoed_prompt_photons.addVetoOnThisFinalState(dressed_leptons);
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
    book(_h["baseline_photon_pt"], 1, 1, 1);
    book(_h["baseline_photon_eta"], 8, 1, 1);
    book(_h["baseline_leppho_dr"], 15, 1, 1);
    book(_h["baseline_leppho_deta"], 22, 1, 1);
    book(_h["baseline_mt_cluster"], 29, 1, 1);
    book(_h["baseline_njet"], 36, 1, 1);
    book(_h["raz_leppho_deta"], 40, 1, 1);

    book(_h["eft_photon_pt_phi_0"], 54, 1, 1);
    book(_h["eft_photon_pt_phi_1"], 55, 1, 1);
    book(_h["eft_photon_pt_phi_2"], 56, 1, 1);

    book(_h["eft_ext_photon_pt_phi_0"], "eft_ext_photon_pt_phi_0",
         {150., 200., 300., 500., 800., 1500.});
    book(_h["eft_ext_photon_pt_phi_1"], "eft_ext_photon_pt_phi_1",
         {150., 200., 300., 500., 800., 1500.});
    book(_h["eft_ext_photon_pt_phi_2"], "eft_ext_photon_pt_phi_2",
         {150., 200., 300., 500., 800., 1500.});

    // New 3x3 pT histograms binned in phi and theta
    book(_h["eft_ext_photon_pt_phi_0_theta_0"], "eft_ext_photon_pt_phi_0_theta_0",
         {150., 200., 300., 500., 800., 1500.});
    book(_h["eft_ext_photon_pt_phi_0_theta_1"], "eft_ext_photon_pt_phi_0_theta_1",
         {150., 200., 300., 500., 800., 1500.});
    book(_h["eft_ext_photon_pt_phi_0_theta_2"], "eft_ext_photon_pt_phi_0_theta_2",
         {150., 200., 300., 500., 800., 1500.});
    book(_h["eft_ext_photon_pt_phi_1_theta_0"], "eft_ext_photon_pt_phi_1_theta_0",
         {150., 200., 300., 500., 800., 1500.});
    book(_h["eft_ext_photon_pt_phi_1_theta_1"], "eft_ext_photon_pt_phi_1_theta_1",
         {150., 200., 300., 500., 800., 1500.});
    book(_h["eft_ext_photon_pt_phi_1_theta_2"], "eft_ext_photon_pt_phi_1_theta_2",
         {150., 200., 300., 500., 800., 1500.});
    book(_h["eft_ext_photon_pt_phi_2_theta_0"], "eft_ext_photon_pt_phi_2_theta_0",
         {150., 200., 300., 500., 800., 1500.});
    book(_h["eft_ext_photon_pt_phi_2_theta_1"], "eft_ext_photon_pt_phi_2_theta_1",
         {150., 200., 300., 500., 800., 1500.});
    book(_h["eft_ext_photon_pt_phi_2_theta_2"], "eft_ext_photon_pt_phi_2_theta_2",
         {150., 200., 300., 500., 800., 1500.});

    book(_h["eft_phi"], "eft_phi", 10, -PI/2., PI/2.); 
    book(_h["eft_costheta"], "eft_costheta", 10, -1.0, 1.0); 
    book(_h["eft_costheta_phi_0"], "eft_costheta_phi_0", 10, -1.0, 1.0); 
    book(_h["eft_costheta_phi_1"], "eft_costheta_phi_1", 10, -1.0, 1.0); 
    book(_h["eft_costheta_phi_2"], "eft_costheta_phi_2", 10, -1.0, 1.0); 
    book(_h["eft_theta"], "eft_theta", 10, 0.0, PI); 
    book(_h["eft_theta_phi_0"], "eft_theta_phi_0", 10, 0.0, PI); 
    book(_h["eft_theta_phi_1"], "eft_theta_phi_1", 10, 0.0, PI);
    book(_h["eft_theta_phi_2"], "eft_theta_phi_2", 10, 0.0, PI); 

    book(_h2["eft_phi_theta"], "eft_phi_theta", 10, 0.0, PI/2., 10, 0.0, PI); 

    // 3D histogram with 3 theta bins 
    const std::vector<double> pt3d_edges = {150., 200., 300., 500., 800., 1500.};
    const std::vector<double> phi3d_edges = {0., PI/6., PI/3., PI/2.};
    const std::vector<double> theta3d_edges = {0., PI/3., 2. * PI / 3., PI};
    book(_h3_pt_phi_theta, "eft_pt_phi_theta_3d", pt3d_edges, phi3d_edges, theta3d_edges);
  }

  // Perform the per-event analysis
  void analyze(const Event& event) {
    vars_.resetVars();

    const Particles leptons = apply<LeptonFinder>(event, "DressedLeptons").particlesByPt();

    if (leptons.size() == 0) {
      vetoEvent;
    }
    auto l0 = leptons.at(0);

    const Particles photons = apply<FinalState>(event, "Photons")
                                  .particlesByPt(DeltaRGtr(l0, lepton_photon_dr_cut_));
    if (photons.size() == 0) {
      vetoEvent;
    }
    auto p0 = photons.at(0);

    const Particles neutrinos = apply<FinalState>(event, "Neutrinos").particlesByPt();
    if (neutrinos.size() == 0) {
      vetoEvent;
    }
    auto n0 = neutrinos.at(0);

    FourMomentum met = apply<MissingMomentum>(event, "MET").missingMomentum();
    met = FourMomentum(met.pt(), met.px(), met.py(), 0.);

    // Filter jets on pT, eta and DR with lepton and photon
    const Jets jets = apply<FastJets>(event, "Jets").jetsByPt([&](Jet const& j) {
      return j.pt() > jet_pt_cut_ && std::abs(j.eta()) < jet_abs_eta_cut_ &&
             deltaR(j, l0) > jet_dr_cut_ && deltaR(j, p0) > jet_dr_cut_;
    });

    if (leptons.size() >= 1 && photons.size() >= 1 && neutrinos.size() >= 1) {
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
      vars_.l0p0_dr = deltaR(l0, p0);
      vars_.n0_pt = n0.pt();
      vars_.n0_eta = n0.eta();
      vars_.n0_phi = n0.phi(PhiMapping::MINUSPI_PLUSPI);
      vars_.n0_M = n0.mass();
      vars_.met_pt = met.pt();
      vars_.met_phi = met.phi(PhiMapping::MINUSPI_PLUSPI);

      Particles finalparts_iso = apply<FinalState>(event, "FinalState").particles();
      Particles filtered_iso;
      for (Particle const& p : finalparts_iso) {
        if (p.genParticle() == l0.genParticle() || p.genParticle() == p0.genParticle() ||
            p.genParticle() == n0.genParticle() || p.fromTau()) {
          continue;
        }
        filtered_iso.push_back(p);
      }
      auto proj = get<FastJets>("Jets");
      proj.reset();
      proj.calc(filtered_iso);
      auto jets_iso = proj.jets();

      vars_.p0_frixione = true;
      double frixione_sum = 0.;

      auto jparts = sortBy(jets_iso, [&](Jet const& part1, Jet const& part2) {
        return deltaR(part1, p0) < deltaR(part2, p0);
      });

      for (auto const& ip : jparts) {
        double dr = deltaR(ip, p0);
        if (dr >= photon_iso_dr_) {
          break;
        }
        frixione_sum += ip.pt();
        if (frixione_sum > (p0.pt() * ((1. - std::cos(dr)) / (1. - std::cos(photon_iso_dr_))))) {
          vars_.p0_frixione = false;
        }
      }
      vars_.p0_frixione_sum = frixione_sum;

      auto wg_system = WGSystem(l0, n0, p0, false);

      vars_.true_phi = wg_system.Phi();
      vars_.true_phi_f = wg_system.SymPhi();
      vars_.true_theta = wg_system.Theta();
      vars_.true_costheta = wg_system.CosTheta();

      auto cand1 = l0.momentum() + p0.momentum();
      auto full_system = cand1 + met;
      double mTcluster2 =
          std::pow(std::sqrt(cand1.mass2() + cand1.pt2()) + met.pt(), 2) - full_system.pt2();
      if (mTcluster2 > 0) {
        vars_.mt_cluster = std::sqrt(mTcluster2);
      } else {
        vars_.mt_cluster = 0.;
      }

      if (vars_.l0_pt > lepton_pt_cut_ && std::abs(vars_.l0_eta) < lepton_abs_eta_cut_ &&
          vars_.p0_pt > photon_pt_cut_ && std::abs(vars_.p0_eta) < photon_abs_eta_cut_ &&
          vars_.p0_frixione && vars_.l0p0_dr > lepton_photon_dr_cut_ &&
          vars_.met_pt > missing_pt_cut_) {
        _h["baseline_photon_pt"]->fill(vars_.p0_pt / GeV);
        _h["baseline_photon_eta"]->fill(vars_.p0_eta);
        _h["baseline_leppho_dr"]->fill(vars_.l0p0_dr);
        _h["baseline_leppho_deta"]->fill(vars_.l0_eta - vars_.p0_eta);
        _h["baseline_mt_cluster"]->fill(vars_.mt_cluster / GeV);
        double fill_n_jets = vars_.n_jets >= 2 ? 2. : double(vars_.n_jets);
        _h["baseline_njet"]->fill(fill_n_jets);
        if (vars_.n_jets == 0 && vars_.mt_cluster > 150.) {
          _h["raz_leppho_deta"]->fill(vars_.l0_eta - vars_.p0_eta);
        }
      }

      if (vars_.l0_pt > eft_lepton_pt_cut_ && std::abs(vars_.l0_eta) < lepton_abs_eta_cut_ &&
          vars_.p0_pt > eft_photon_pt_cut_ && std::abs(vars_.p0_eta) < photon_abs_eta_cut_ &&
          vars_.p0_frixione && vars_.l0p0_dr > lepton_photon_dr_cut_ &&
          vars_.met_pt > missing_pt_cut_ && vars_.n_jets == 0) {

        _h2["eft_phi_theta"]->fill(std::abs(vars_.true_phi_f), vars_.true_theta);

        _h["eft_phi"]->fill(vars_.true_phi_f);
        _h["eft_costheta"]->fill(vars_.true_costheta);
        _h["eft_theta"]->fill(vars_.true_theta);

        double absphi = std::abs(vars_.true_phi_f);
        double pt_gev = vars_.p0_pt / GeV;

        // Fill 3D histogram
        _h3_pt_phi_theta->fill(pt_gev, absphi, vars_.true_theta);

        int iphi = phiBin3(absphi);
        int itheta = thetaBin3(vars_.true_theta);

        if (absphi > 0. && absphi <= (PI / 6.)) {
          _h["eft_photon_pt_phi_0"]->fill(pt_gev);
          _h["eft_ext_photon_pt_phi_0"]->fill(pt_gev);
          _h["eft_costheta_phi_0"]->fill(vars_.true_costheta);
          _h["eft_theta_phi_0"]->fill(vars_.true_theta);
        } else if (absphi > (PI / 6.) && absphi <= (PI / 3.)) {
          _h["eft_photon_pt_phi_1"]->fill(pt_gev);
          _h["eft_ext_photon_pt_phi_1"]->fill(pt_gev);
          _h["eft_costheta_phi_1"]->fill(vars_.true_costheta);
          _h["eft_theta_phi_1"]->fill(vars_.true_theta);
        } else if (absphi > (PI / 3.) && absphi <= (PI / 2.)) {
          _h["eft_photon_pt_phi_2"]->fill(pt_gev);
          _h["eft_ext_photon_pt_phi_2"]->fill(pt_gev);
          _h["eft_costheta_phi_2"]->fill(vars_.true_costheta);
          _h["eft_theta_phi_2"]->fill(vars_.true_theta);
        }

        // Fill 3x3 pT histograms
        if (iphi == 0 && itheta == 0) _h["eft_ext_photon_pt_phi_0_theta_0"]->fill(pt_gev);
        if (iphi == 0 && itheta == 1) _h["eft_ext_photon_pt_phi_0_theta_1"]->fill(pt_gev);
        if (iphi == 0 && itheta == 2) _h["eft_ext_photon_pt_phi_0_theta_2"]->fill(pt_gev);

        if (iphi == 1 && itheta == 0) _h["eft_ext_photon_pt_phi_1_theta_0"]->fill(pt_gev);
        if (iphi == 1 && itheta == 1) _h["eft_ext_photon_pt_phi_1_theta_1"]->fill(pt_gev);
        if (iphi == 1 && itheta == 2) _h["eft_ext_photon_pt_phi_1_theta_2"]->fill(pt_gev);

        if (iphi == 2 && itheta == 0) _h["eft_ext_photon_pt_phi_2_theta_0"]->fill(pt_gev);
        if (iphi == 2 && itheta == 1) _h["eft_ext_photon_pt_phi_2_theta_1"]->fill(pt_gev);
        if (iphi == 2 && itheta == 2) _h["eft_ext_photon_pt_phi_2_theta_2"]->fill(pt_gev);
      }
    }
  }

  void finalize() {
    double flavor_factor = 3. / 2.;

    for (std::string const x :
         {"baseline_photon_pt", "baseline_photon_eta", "baseline_leppho_dr", "baseline_leppho_deta",
          "baseline_mt_cluster", "baseline_njet", "raz_leppho_deta",
          "eft_photon_pt_phi_0", "eft_photon_pt_phi_1", "eft_photon_pt_phi_2",
          "eft_ext_photon_pt_phi_0", "eft_ext_photon_pt_phi_1", "eft_ext_photon_pt_phi_2",
          "eft_ext_photon_pt_phi_0_theta_0", "eft_ext_photon_pt_phi_0_theta_1",
          "eft_ext_photon_pt_phi_0_theta_2", "eft_ext_photon_pt_phi_1_theta_0",
          "eft_ext_photon_pt_phi_1_theta_1", "eft_ext_photon_pt_phi_1_theta_2",
          "eft_ext_photon_pt_phi_2_theta_0", "eft_ext_photon_pt_phi_2_theta_1",
          "eft_ext_photon_pt_phi_2_theta_2",
          "eft_phi", "eft_costheta", "eft_theta",
          "eft_costheta_phi_0", "eft_costheta_phi_1", "eft_costheta_phi_2",
          "eft_theta_phi_0", "eft_theta_phi_1", "eft_theta_phi_2"}) {
      if (crossSection() < 0.) {
        scale(_h[x], flavor_factor / femtobarn / numEvents());
      } else {
        scale(_h[x], flavor_factor * crossSection() / femtobarn / sumOfWeights());
      }
    }

    for (const auto& kv : _h2) {
      Histo2DPtr h2 = kv.second;
      if (!h2) continue;
      if (crossSection() < 0.) {
        scale(h2, flavor_factor / femtobarn / numEvents());
      } else {
        scale(h2, flavor_factor * crossSection() / femtobarn / sumOfWeights());
      }
    }

    if (crossSection() < 0.) {
      scale(_h3_pt_phi_theta, flavor_factor / femtobarn / numEvents());
    } else {
      scale(_h3_pt_phi_theta, flavor_factor * crossSection() / femtobarn / sumOfWeights());
    }

    // Since these are really 2D, divide by the phi-bin width
    for (std::string const x :
         {"eft_photon_pt_phi_0", "eft_photon_pt_phi_1", "eft_photon_pt_phi_2",
          "eft_ext_photon_pt_phi_0", "eft_ext_photon_pt_phi_1", "eft_ext_photon_pt_phi_2",
          "eft_ext_photon_pt_phi_0_theta_0", "eft_ext_photon_pt_phi_0_theta_1",
          "eft_ext_photon_pt_phi_0_theta_2", "eft_ext_photon_pt_phi_1_theta_0",
          "eft_ext_photon_pt_phi_1_theta_1", "eft_ext_photon_pt_phi_1_theta_2",
          "eft_ext_photon_pt_phi_2_theta_0", "eft_ext_photon_pt_phi_2_theta_1",
          "eft_ext_photon_pt_phi_2_theta_2"}) {
      scale(_h[x], 1. / (PI / 6.));
    }

    // Also divide the 3x3 histograms by theta-bin width 
    for (std::string const x :
         {"eft_ext_photon_pt_phi_0_theta_0", "eft_ext_photon_pt_phi_0_theta_1",
          "eft_ext_photon_pt_phi_0_theta_2", "eft_ext_photon_pt_phi_1_theta_0",
          "eft_ext_photon_pt_phi_1_theta_1", "eft_ext_photon_pt_phi_1_theta_2",
          "eft_ext_photon_pt_phi_2_theta_0", "eft_ext_photon_pt_phi_2_theta_1",
          "eft_ext_photon_pt_phi_2_theta_2"}) {
      scale(_h[x], 1. / (PI / 3.));
    }
  }
};

CMS_2021_PAS_SMP_20_005::WGSystem::WGSystem(Particle const& lep, Particle const& neu,
                                            Particle const& pho, bool verbose) {
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

double CMS_2021_PAS_SMP_20_005::WGSystem::Phi() {
  double lep_phi = r_charged_lepton.phi(PhiMapping::MINUSPI_PLUSPI);
  return mapAngleMPiToPi(lepton_charge > 0 ? lep_phi : (lep_phi + PI));
}

double CMS_2021_PAS_SMP_20_005::WGSystem::SymPhi() {
  double lep_phi = Phi();
  if (lep_phi > PI / 2.) {
    return PI - lep_phi;
  } else if (lep_phi < -1. * (PI / 2.)) {
    return -1. * (PI + lep_phi);
  } else {
    return lep_phi;
  }
}

double CMS_2021_PAS_SMP_20_005::WGSystem::CosTheta() {
  const double eta_plus = (lepton_charge > 0) ? r_charged_lepton.eta() : r_neutrino.eta();
  const double eta_minus = (lepton_charge > 0) ? r_neutrino.eta() : r_charged_lepton.eta();
  double c = std::tanh((eta_plus - eta_minus) / 2.);

  if (c > 1.) c = 1.;
  if (c < -1.) c = -1.;
  return c;
}

double CMS_2021_PAS_SMP_20_005::WGSystem::Theta() {
  return std::acos(CosTheta());
}

RIVET_DECLARE_PLUGIN(CMS_2021_PAS_SMP_20_005);

}  // namespace Rivet