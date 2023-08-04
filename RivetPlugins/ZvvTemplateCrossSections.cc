// -*- C++ -*-
#include "Rivet/Analysis.hh"
#include "Rivet/Projections/FinalState.hh"
#include "Rivet/Projections/FastJets.hh"
#include "Rivet/Projections/DressedLeptons.hh"
#include "Rivet/Projections/MissingMomentum.hh"
#include "Rivet/Projections/PromptFinalState.hh"
#include "Rivet/Projections/ZFinder.hh"
#include "Rivet/Projections/IdentifiedFinalState.hh"

namespace Rivet {


  /// Measurements of differential Z-boson -> ll and vv production cross-sections in 13 TeV pp collisions
  class ZvvTemplateCrossSections : public Analysis {
  public:

    /// Constructor
    DEFAULT_RIVET_ANALYSIS_CTOR(ZvvTemplateCrossSections);


    /// @name Analysis methods
    /// @{

    /// Book histograms and initialise projections before the run
    void init() {

      // FinalState fs;
      // declare(fs, "FinalState");

      // Initialise and register projections
      ZFinder zmmFind(FinalState(), Cuts::pT > 0*GeV, PID::MUON, 76.1876*GeV, 106.1876*GeV, 0.1,
                      ZFinder::ChargedLeptons::PROMPT, ZFinder::ClusterPhotons::NODECAY, ZFinder::AddPhotons::YES );
      declare(zmmFind, "ZmmFind");

      // Invisibles
      // vector<PdgId> ids = {12,14,16,-12,-14,-16};
      // std::cout << 22222 << typeid(ids).name() << '\n';
      // IdentifiedFinalState invisibles(fs, ids);
      IdentifiedFinalState nu_id;
      nu_id.acceptNeutrinos();
      // InvisibleFinalState invisibles(true, true, true);
      declare(nu_id, "Invisibles");

      // Book histograms
      book(hist_pT_Z,       "pT_Z",80,200,1000);
      book(_h_Z_pt,"h_Z_pt",      refData(12, 1, 1));
      book(_h_Z_pt_norm,"h_Z_pt_norm", refData(13, 1, 1));

    }


    /// Perform the per-event analysis
    void analyze(const Event& event) {

      // const Particles& zmms = apply<ZFinder>(event, "ZmmFind").bosons();

      const Particles invisibles = apply<IdentifiedFinalState>(event, "Invisibles").particlesByPt();
      FourMomentum n0;
      for (auto const& inv : invisibles) {
        n0 += inv.momentum();
      }

      // Need to match analysis, can't tell how many neutrinos we have, 
      // so not writing: invisibles.size() > 1
      if (n0.pT() > 200*GeV) {
        _h_Z_pt     ->fill(min(n0.pT()/GeV, 1499.999));
        _h_Z_pt_norm->fill(min(n0.pT()/GeV, 1499.999));
        hist_pT_Z->fill(min(n0.pT()/GeV, 1499.999));
      }

    }


    /// @todo Replace with barchart()
    void normalizeToSum(Histo1DPtr hist) {
      //double sum = 0.;
      for (size_t i = 0; i < hist->numBins(); ++i) {
        //sum += hist->bin(i).height();
        double width = hist->bin(i).width();
        hist->bin(i).scaleW(width != 0 ? width : 1.);
      }
      if (hist->integral() > 0) scale(hist, 1./hist->integral());
    }


    /// Normalise histograms etc., after the run
    void finalize() {

      double norm = (sumOfWeights() != 0) ? crossSection()/femtobarn/sumOfWeights() : 1.0;

      scale(_h_Z_pt, norm);
      scale(hist_pT_Z, norm);

      normalizeToSum(_h_Z_pt_norm);

    }

    /// @}


    /// @name Histograms
    /// @{
    Histo1DPtr _h_Z_pt, _h_Z_pt_norm;
    Histo1DPtr hist_pT_Z;
    /// @}


  };


  DECLARE_RIVET_PLUGIN(ZvvTemplateCrossSections);

}
