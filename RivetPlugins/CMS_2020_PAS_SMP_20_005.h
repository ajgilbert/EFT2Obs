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

  int n_jets;

  WGammaRivetVariables();
  void resetVars();
};



namespace Rivet {

/// @brief Add a short analysis description here
class CMS_2020_PAS_SMP_20_005 : public Analysis {
 public:
  /// Constructor
  DEFAULT_RIVET_ANALYSIS_CTOR(CMS_2020_PAS_SMP_20_005);

// This is a hack to make the code compile with rivet 2.X.Y.
// We rely on the fact that RIVET_VERSION is not defined in
// rivet 3.X.Y.
#ifdef RIVET_VERSION
 private:
  template <typename ...Args>
  void book(Histo1DPtr &ptr, Args&&... args) {
   ptr = this->bookHisto1D(std::forward<Args>(args)...);
  }

  template <typename ...Args>
  void book(Histo2DPtr &ptr, Args&&... args) {
   ptr = this->bookHisto2D(std::forward<Args>(args)...);
  }
#endif

  bool use_dressed_leptons_ = true;
  bool use_parton_isolation_ = false;
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
  double eft_missing_pt_cut_ = 80.;
  double eft_missing_pt_met1_cut_ = 40.;
  double eft_lepton_photon_dr_cut_ = 3.0;

  double jet_pt_cut_ = 30.;
  double jet_abs_eta_cut_ = 2.5;
  double jet_dr_cut_ = 0.4;

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
  };

 public:

  WGammaRivetVariables vars_;

  /// @name Analysis methods
  //@{

  /// Book histograms and initialise projections before the run
  void init();

  /// Perform the per-event analysis
  void analyze(const Event& event);

  /// Normalise histograms etc., after the run
  void finalize();
  //@}

  /// @name Histograms
  //@{
  map<string, Histo1DPtr> _h;
  map<string, Histo2DPtr> _h2d;
  //@}
};
}  // namespace Rivet
