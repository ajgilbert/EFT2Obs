// -*- C++ -*-
#include "Rivet/Analysis.hh"
#include "Rivet/Projections/FastJets.hh"
#include "Rivet/Projections/FinalState.hh"
#include "Rivet/Projections/MissingMomentum.hh"
#include "Rivet/Projections/PromptFinalState.hh"
#include "Rivet/Projections/DressedLeptons.hh"
#include "Rivet/Projections/VetoedFinalState.hh"

namespace Rivet {


  /// @brief WW production at 13 TeV
  class ATLAS_2019_I1734263 : public Analysis {
  public:

    /// Constructor
    DEFAULT_RIVET_ANALYSIS_CTOR(ATLAS_2019_I1734263);


    /// @name Analysis methods
    //@{

    /// Book histograms and initialise projections before the run
    void init() {

      const FinalState fs(Cuts::abseta < 5.);

      // Project photons for dressing
      FinalState photon_id(Cuts::abspid == PID::PHOTON);

      // Cuts for leptons
      Cut lepton_cuts = (Cuts::abseta < 2.5) && (Cuts::pT > 27*GeV);
      // Lepton for simplified phase space (e.g. for comparison with CMS)
      Cut lepton_cuts_simpl = (Cuts::abseta < 2.5) && (Cuts::pT > 25*GeV);

      // Project dressed leptons (e/mu not from tau) with pT > 27 GeV and |eta| < 2.5
      // Both for normal and simplified phase space
      PromptFinalState lep_bare(Cuts::abspid == PID::MUON || Cuts::abspid == PID::ELECTRON);
      DressedLeptons lep_dressed(photon_id, lep_bare, 0.1, lepton_cuts, true);
      declare(lep_dressed,"lep_dressed");
      DressedLeptons lep_dressed_simpl(photon_id, lep_bare, 0.1, lepton_cuts_simpl, true);
      declare(lep_dressed_simpl,"lep_dressed_simpl");

      // Get MET
      MissingMomentum mm(fs);
      declare(mm, "met");

      // Define hadrons as everything but dressed leptons (for jet clustering)
      VetoedFinalState hadrons(fs);
      hadrons.addVetoOnThisFinalState(lep_dressed);
      declare(hadrons, "hadrons");
      VetoedFinalState hadrons_simpl(fs);
      hadrons_simpl.addVetoOnThisFinalState(lep_dressed_simpl);
      declare(hadrons_simpl, "hadrons_simpl");

      // Project jets
      FastJets jets(hadrons, FastJets::ANTIKT, 0.4, JetAlg::Muons::ALL, JetAlg::Invisibles::NONE);
      declare(jets, "jets");
      FastJets jets_simpl(hadrons_simpl, FastJets::ANTIKT, 0.4, JetAlg::Muons::ALL, JetAlg::Invisibles::NONE);
      declare(jets_simpl, "jets_simpl");


      // Book histograms
      // fiducial differential cross section as a function of the jet-veto pt cut
      book(_h["jetveto"], 1, 1, 1);

      // fiducial differential cross section (leading lepton pt)
      book(_h["ptlead"], 4, 1, 1);
      book(_h["ptlead_norm"], 22, 1, 1);
      book(_h["ptlead_simpl"], 41, 1, 1);

      // fiducial differential cross section (dilepton-system mll)
      book(_h["mll"], 7, 1, 1);
      book(_h["mll_norm"], 25, 1, 1);
      book(_h["mll_simpl"], 42, 1, 1);

      // fiducial differential cross section (dilepton-system ptll)
      book(_h["ptll"], 10, 1, 1);
      book(_h["ptll_norm"], 28, 1, 1);
      book(_h["ptll_simpl"], 43, 1, 1);

      // fiducial differential cross section (absolute rapidity of dilepton-system y_ll)
      book(_h["yll"], 13, 1, 1);
      book(_h["yll_norm"], 31, 1, 1);

      // fiducial differential cross section (dilepton-system delta_phi_ll)
      book(_h["dphill"], 16, 1, 1);
      book(_h["dphill_norm"], 34, 1, 1);


      // fiducial differential cross section (absolute costheta* of dilepton-system costhetastar_ll)
      book(_h["costhetastarll"], 19, 1, 1);
      book(_h["costhetastarll_norm"], 37, 1, 1);

    }


    /// Perform the per-event analysis
    void analyze(const Event& event) {

      // Get met and find leptons
      const MissingMomentum& met = apply<MissingMomentum>(event, "met");
      const vector<DressedLepton> &leptons       = apply<DressedLeptons>(event, "lep_dressed").dressedLeptons();
      const vector<DressedLepton> &leptons_simpl = apply<DressedLeptons>(event, "lep_dressed_simpl").dressedLeptons();

      // Find jets and jets for simplified phase space (for the latter slightly different leptons are excluded from clustering)
      const Jets& jets30     = apply<FastJets>(event, "jets").jetsByPt(Cuts::abseta < 4.5 && Cuts::pT > 30*GeV);
      const Jets& jets_simpl = apply<FastJets>(event, "jets_simpl").jetsByPt(Cuts::abseta < 4.5 && Cuts::pT > 30*GeV);

      // Define observables
      const FourMomentum dilep  = leptons.size()>1 ? leptons[0].momentum() + leptons[1].momentum() : FourMomentum(0,0,0,0);
      const double ptll         = leptons.size()>1 ? dilep.pT()/GeV : -1;
      const double Mll          = leptons.size()>1 ? dilep.mass()/GeV : -1;
      const double Yll          = leptons.size()>1 ? dilep.absrap() : -5;
      const double DPhill       = leptons.size()>1 ? fabs(deltaPhi(leptons[0], leptons[1])) : -1.;
      const double costhetastar = leptons.size()>1 ? fabs(tanh((leptons[0].eta() - leptons[1].eta()) / 2)) : -0.2;

      // Define observables for simplified PS
      const FourMomentum dilep_simpl = leptons_simpl.size()>1 ? leptons_simpl[0].momentum() + leptons_simpl[1].momentum() : FourMomentum(0,0,0,0);
      const double ptll_simpl        = leptons_simpl.size()>1 ? dilep_simpl.pT()/GeV : -1;
      const double Mll_simpl         = leptons_simpl.size()>1 ? dilep_simpl.mass()/GeV : -1;

      // Cuts for simplified PS
      bool veto_simpl = false;
      // Remove events that do not contain 2 good leptons (either muons or electrons)
      if ( leptons_simpl.size() != 2 ) veto_simpl = true;
      // Veto same-flavour events
      else if ( leptons_simpl[0].abspid() == leptons_simpl[1].abspid()) veto_simpl = true;
      // Veto same-charge events
      else if ( leptons_simpl[0].pid()*leptons_simpl[1].pid()>0) veto_simpl = true;
      // MET (pt-MET) cut
      else if (met.missingPt() <= 20*GeV)  veto_simpl = true;
      // jetveto
      else if ( !jets_simpl.empty() ) veto_simpl = true;

      // Fill histos for simplified phase space
      if ( !veto_simpl ){
        _h["ptlead_simpl"]->fill(leptons_simpl[0].pT()/GeV);
        _h["ptll_simpl"]->fill(ptll_simpl);
        _h["mll_simpl"]->fill(Mll_simpl);
      }


      // Event selection for proper fiducial phase space
      // Remove events that do not contain 2 good leptons (either muons or electrons)
      if ( leptons.size() != 2)  vetoEvent;
      // Veto same-flavour events
      if ( leptons[0].abspid() == leptons[1].abspid())  vetoEvent;
      // Veto same-charge events
      if ( leptons[0].pid()*leptons[1].pid()>0)  vetoEvent;
      // MET (pt-MET) cut
      if (met.missingPt() <= 20*GeV)  vetoEvent;
      // m_ll cut
      if (dilep.mass() <= 55*GeV)  vetoEvent;
      // pt_ll cut
      if (dilep.pT() <= 30*GeV)  vetoEvent;

      // Fill cross section as function of veto-jet pt before applying jet veto
      if (jets30.empty() || jets30[0].pT()/GeV < 30.) _h["jetveto"]->fillBin(0);
      if (jets30.empty() || jets30[0].pT()/GeV < 35.) _h["jetveto"]->fillBin(1);
      if (jets30.empty() || jets30[0].pT()/GeV < 40.) _h["jetveto"]->fillBin(2);
      if (jets30.empty() || jets30[0].pT()/GeV < 45.) _h["jetveto"]->fillBin(3);
      if (jets30.empty() || jets30[0].pT()/GeV < 50.) _h["jetveto"]->fillBin(4);
      if (jets30.empty() || jets30[0].pT()/GeV < 55.) _h["jetveto"]->fillBin(5);
      if (jets30.empty() || jets30[0].pT()/GeV < 60.) _h["jetveto"]->fillBin(6);
      // Jet veto at 35 GeV is the default
      if (!jets30.empty() && jets30[0].pT()/GeV > 35.)  vetoEvent;

      // fill histograms
      _h["ptlead"]->fill(leptons[0].pT()/GeV);
      _h["ptlead_norm"]->fill(leptons[0].pT()/GeV);

      _h["ptll"]->fill(ptll);
      _h["ptll_norm"]->fill(ptll);

      _h["mll"]->fill(Mll);
      _h["mll_norm"]->fill(Mll);

      _h["yll"]->fill(Yll);
      _h["yll_norm"]->fill(Yll);

      _h["dphill"]->fill(DPhill);
      _h["dphill_norm"]->fill(DPhill);

      _h["costhetastarll"]->fill(costhetastar);
      _h["costhetastarll_norm"]->fill(costhetastar);

    }


    /// Normalise histograms etc., after the run
    void finalize() {
      const double sf(crossSection()/femtobarn/sumOfWeights());
      // scale histogram by binwidth, as bin content is actually a integrated fiducial cross section
      // @todo revisit when new YODA binned-object type drops
      scale(_h["jetveto"], 5.);
      // scale to cross section
      for (auto& hist : _h) {
        scale(hist.second, sf);
        if (hist.first.find("norm") != string::npos) normalize(hist.second);
      }
    }

    //@}

  private:

    /// @name Histograms
    //@{
    map<string, Histo1DPtr> _h;
    //@}

  };


  // The hook for the plugin system
  DECLARE_RIVET_PLUGIN(ATLAS_2019_I1734263);

}
