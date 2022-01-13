// -*- C++ -*-
#include "Rivet/Analysis.hh"
#include "Rivet/Projections/FinalState.hh"
#include "Rivet/Projections/FastJets.hh"
#include "Rivet/Projections/ChargedLeptons.hh"
#include "Rivet/Projections/DressedLeptons.hh"
#include "Rivet/Projections/MissingMomentum.hh"
#include "Rivet/Projections/PromptFinalState.hh"
#include "Rivet/Projections/VetoedFinalState.hh"
#include "Rivet/Projections/PartonicTops.hh"

namespace Rivet {


  /// Differential cross sections and charge ratios for 13 TeV t-channel single top-quark production
  class CMS_2019_I1744604 : public Analysis {
  public:

    /// Constructor
    DEFAULT_RIVET_ANALYSIS_CTOR(CMS_2019_I1744604);


    /// @brief Book histograms and initialise projections before the run
    void init() override {

      // final state of all stable particles
      Cut particle_cut = (Cuts::abseta < 5.0) and (Cuts::pT > 0.*MeV);
      FinalState fs(particle_cut);

      // select charged leptons
      ChargedLeptons charged_leptons(fs);
      // select final state photons for dressed lepton clustering
      IdentifiedFinalState photons(fs);
      photons.acceptIdPair(PID::PHOTON);

      // select final state prompt charged leptons
      PromptFinalState prompt_leptons(charged_leptons);
      prompt_leptons.acceptMuonDecays(true);
      prompt_leptons.acceptTauDecays(true);
      // select final state prompt photons
      PromptFinalState prompt_photons(photons);
      prompt_photons.acceptMuonDecays(true);
      prompt_photons.acceptTauDecays(true);

      // Dressed leptons from selected prompt charged leptons and photons
      Cut lepton_cut   = (Cuts::abseta < 2.4) and (Cuts::pT > 26.*GeV);
      DressedLeptons dressed_leptons(
        prompt_photons, prompt_leptons, 0.1,
        lepton_cut, true
      );
      declare(dressed_leptons, "DressedLeptons");

      // Jets
      VetoedFinalState fsForJets(fs);
      fsForJets.addVetoOnThisFinalState(dressed_leptons);
      declare(
        // excludes all neutrinos by default
        FastJets(fsForJets, FastJets::ANTIKT, 0.4),
        "Jets"
      );

      // Neutrinos
      IdentifiedFinalState neutrinos(fs);
      neutrinos.acceptNeutrinos();
      PromptFinalState prompt_neutrinos(neutrinos);
      prompt_neutrinos.acceptMuonDecays(true);
      prompt_neutrinos.acceptTauDecays(true);
      declare(prompt_neutrinos, "Neutrinos");

      // Partonic top for differentiating between t and tbar events
      declare(PartonicTops(),"TopQuarks");


      // book top quark pt histograms
      book(_hist_abs_top_pt, "d13-x01-y01"); // absolute cross section
      book(_hist_norm_top_pt, "d37-x01-y01");  // normalized cross section
      book(_hist_ratio_top_pt, "d59-x01-y01"); // charge ratio
      // temporary histograms of absolute top quark and antiquark cross sections
      book(_hist_t_top_pt, "t_top_pt", refData(13, 1, 1));
      book(_hist_tbar_top_pt, "tbar_top_pt", refData(13, 1, 1));


      // book top quark rapidity histograms
      book(_hist_abs_top_y, "d15-x01-y01"); // absolute cross section
      book(_hist_norm_top_y, "d39-x01-y01"); // normalized cross section
      book(_hist_ratio_top_y, "d61-x01-y01"); // charge ratio
      // temporary histograms of absolute top quark and antiquark cross sections
      book(_hist_t_top_y, "t_top_y", refData(15, 1, 1));
      book(_hist_tbar_top_y, "tbar_top_y", refData(15, 1, 1));


      // book charged lepton pt histograms
      book(_hist_abs_lepton_pt,"d17-x01-y01"); // absolute cross section
      book(_hist_norm_lepton_pt,"d41-x01-y01"); // normalized cross section
      book(_hist_ratio_lepton_pt,"d63-x01-y01");  // charge ratio
      // temporary histograms of absolute top quark and antiquark cross sections
      book(_hist_t_lepton_pt,"t_lepton_pt",refData(17, 1, 1));
      book(_hist_tbar_lepton_pt,"tbar_lepton_pt",refData(17, 1, 1));


      // book charged lepton rapidity histograms
      book(_hist_abs_lepton_y, "d19-x01-y01"); // absolute cross section
      book(_hist_norm_lepton_y, "d43-x01-y01"); // normalized cross section
      book(_hist_ratio_lepton_y, "d65-x01-y01"); // charge ratio
      // temporary histograms of absolute top quark and antiquark cross sections
      book(_hist_t_lepton_y, "t_lepton_y", refData(19, 1, 1));
      book(_hist_tbar_lepton_y, "tbar_lepton_y", refData(19, 1, 1));


      // book W boson pt histograms
      book(_hist_abs_w_pt, "d21-x01-y01"); // absolute cross section
      book(_hist_norm_w_pt, "d45-x01-y01"); // normalized cross section
      book(_hist_ratio_w_pt, "d67-x01-y01"); // charge ratio
      // temporary histograms of absolute top quark and antiquark cross sections
      book(_hist_t_w_pt, "t_w_pt", refData(21, 1, 1));
      book(_hist_tbar_w_pt, "tbar_w_pt", refData(21, 1, 1));


      // book top quark polarization angle histograms
      book(_hist_abs_top_cos, "d23-x01-y01"); // absolute cross section
      book(_hist_norm_top_cos, "d47-x01-y01"); // normalized cross section
      // temporary histograms of absolute top quark and antiquark cross sections
      book(_hist_t_top_cos, "t_top_cos", refData(23, 1, 1));
      book(_hist_tbar_top_cos, "tbar_top_cos", refData(23, 1, 1));

    }


    /// @brief Perform the per-event analysis
    void analyze(const Event& event) override {
      vector<Particle> topQuarks = applyProjection<PartonicTops>(
        event,
        "TopQuarks"
      ).tops();


      // skip events with no partonic top quark
      if (topQuarks.size() != 1) {
        return;
      }

      vector<DressedLepton> dressedLeptons = applyProjection<DressedLeptons>(
        event,
        "DressedLeptons"
      ).dressedLeptons();

      // only analyze events with one dressed lepton (muon or electron)
      if (dressedLeptons.size()!=1) {
        return;
      }

      Cut jet_cut((Cuts::abseta < 4.7) and (Cuts::pT > 40.*GeV));
      vector<Jet> jets = apply<FastJets>(
        event,
        "Jets"
      ).jets(jet_cut);

      // ignore jets that overlap with dressed leptons within dR<0.4
      Jets cleanedJets;
      DeltaRLess dRFct(dressedLeptons[0], 0.4);
      for (const Jet& jet: jets) {
        if (not dRFct(jet)) cleanedJets.push_back(jet);
      }

      // select events with exactly two jets
      if (cleanedJets.size() != 2) {
        return;
      }

      Particles neutrinos = apply<PromptFinalState>(event, "Neutrinos").particles();
      // construct missing transverse momentum by summing over all prompt neutrinos
      FourMomentum met;
      for (const Particle& neutrino: neutrinos) {
        met += neutrino.momentum();
      }

      /* find unknown pz component of missing transverse momentum by imposing
         a W boson mass constraint */
      std::pair<FourMomentum,FourMomentum> nuMomentum = NuMomentum(
        dressedLeptons[0].px(), dressedLeptons[0].py(), dressedLeptons[0].pz(),
        dressedLeptons[0].E(), met.px(), met.py()
      );

      // define the W boson momentum as the sum of the dressed lepton + neutrino
      FourMomentum wboson = nuMomentum.first + dressedLeptons[0].momentum();

      /** construct the pseudo top quark momentum by summing the W boson and
       *  the jet that yields a top quark mass closest to TOPMASS
       */
      FourMomentum topQuark(0, 0, 0, 0);
      int bjetIndex = -1;
      for (size_t i = 0; i < cleanedJets.size(); ++i) {
        const auto& jet = cleanedJets[i];
        FourMomentum topCandidate = jet.momentum() + wboson;
        if (fabs(topQuark.mass() - TOPMASS) > fabs(topCandidate.mass() - TOPMASS)) {
          bjetIndex = i;
          topQuark = topCandidate;
        }
      }

      if (bjetIndex < 0) {
        return;
      }

      // define the jet used to construct the pseudo top quark as the b jet
      Jet bjet = cleanedJets[bjetIndex];

      // define the other jet as the spectator jet
      Jet lightjet = cleanedJets[(bjetIndex + 1) % 2];

      // calculate the cosine of the polarization angle that is defined as the
      //   angle between the charged lepton and the spectator jet in the top
      //   quark rest frame
      LorentzTransform boostToTopFrame = LorentzTransform::mkFrameTransform(topQuark);
      Vector3 ljetInTopFrame = boostToTopFrame.transform(lightjet.momentum()).vector3().unit();
      Vector3 leptonInTopFrame = boostToTopFrame.transform(dressedLeptons[0].momentum()).vector3().unit();
      double polarizationAngle = ljetInTopFrame.dot(leptonInTopFrame);

      // fill the histograms depending on the partonic top quark charge
      if (topQuarks[0].charge() > 0) {
        _hist_t_top_pt->fill(topQuark.pt() / GeV);
        _hist_t_top_y->fill(topQuark.absrapidity());
        _hist_t_lepton_pt->fill(dressedLeptons[0].pt() / GeV);
        _hist_t_lepton_y->fill(dressedLeptons[0].absrapidity());
        _hist_t_w_pt->fill(wboson.pt() / GeV);
        _hist_t_top_cos->fill(polarizationAngle);

      } else {
        _hist_tbar_top_pt->fill(topQuark.pt() / GeV);
        _hist_tbar_top_y->fill(topQuark.absrapidity());
        _hist_tbar_lepton_pt->fill(dressedLeptons[0].pt() / GeV);
        _hist_tbar_lepton_y->fill(dressedLeptons[0].absrapidity());
        _hist_tbar_w_pt->fill(wboson.pt() / GeV);
        _hist_tbar_top_cos->fill(polarizationAngle);
      }
    }


    /// @brief Normalise histograms etc., after the run
    void finalize() override {

      // multiply by 0.5 to average electron/muon decay channels
      scale(_hist_t_top_pt, 0.5 * crossSection() / picobarn / sumOfWeights());
      scale(_hist_t_top_y, 0.5 * crossSection() / picobarn / sumOfWeights());
      scale(_hist_t_lepton_pt, 0.5 * crossSection() / picobarn / sumOfWeights());
      scale(_hist_t_lepton_y, 0.5 * crossSection() / picobarn / sumOfWeights());
      scale(_hist_t_w_pt,0.5 * crossSection() / picobarn / sumOfWeights());
      scale(_hist_t_top_cos, 0.5 * crossSection() / picobarn / sumOfWeights());

      scale(_hist_tbar_top_pt, 0.5 * crossSection() / picobarn / sumOfWeights());
      scale(_hist_tbar_top_y, 0.5 * crossSection() / picobarn / sumOfWeights());
      scale(_hist_tbar_lepton_pt,0.5 * crossSection() / picobarn / sumOfWeights());
      scale(_hist_tbar_lepton_y, 0.5 * crossSection() / picobarn / sumOfWeights());
      scale(_hist_tbar_w_pt, 0.5 * crossSection() / picobarn / sumOfWeights());
      scale(_hist_tbar_top_cos, 0.5 * crossSection() /picobarn / sumOfWeights());

      // populate absolute, normalized, and ratio histograms once top quark and
      // antiquark histograms have been populated
      if (_hist_t_top_pt->numEntries() > 0 and _hist_tbar_top_pt->numEntries() > 0) {
        fillAbsHist(_hist_abs_top_pt, _hist_t_top_pt, _hist_tbar_top_pt);
        fillNormHist(_hist_norm_top_pt, _hist_t_top_pt, _hist_tbar_top_pt);
        divide(_hist_t_top_pt, _hist_abs_top_pt, _hist_ratio_top_pt);

        fillAbsHist(_hist_abs_top_y, _hist_t_top_y, _hist_tbar_top_y);
        fillNormHist(_hist_norm_top_y, _hist_t_top_y, _hist_tbar_top_y);
        divide(_hist_t_top_y, _hist_abs_top_y, _hist_ratio_top_y);

        fillAbsHist(_hist_abs_lepton_pt, _hist_t_lepton_pt, _hist_tbar_lepton_pt);
        fillNormHist(_hist_norm_lepton_pt, _hist_t_lepton_pt, _hist_tbar_lepton_pt);
        divide(_hist_t_lepton_pt, _hist_abs_lepton_pt, _hist_ratio_lepton_pt);

        fillAbsHist(_hist_abs_lepton_y, _hist_t_lepton_y, _hist_tbar_lepton_y);
        fillNormHist(_hist_norm_lepton_y, _hist_t_lepton_y, _hist_tbar_lepton_y);
        divide(_hist_t_lepton_y, _hist_abs_lepton_y, _hist_ratio_lepton_y);

        fillAbsHist(_hist_abs_w_pt, _hist_t_w_pt, _hist_tbar_w_pt);
        fillNormHist(_hist_norm_w_pt, _hist_t_w_pt, _hist_tbar_w_pt);
        divide(_hist_t_w_pt, _hist_abs_w_pt, _hist_ratio_w_pt);

        fillAbsHist(_hist_abs_top_cos, _hist_t_top_cos, _hist_tbar_top_cos);
        fillNormHist(_hist_norm_top_cos, _hist_t_top_cos, _hist_tbar_top_cos);
      }
    }

    //@}


  private:

    // for reconstruction only
    const double WMASS = 80.399;
    const double TOPMASS = 172.5;

    // Top quark pt histograms and ratio
    Histo1DPtr _hist_abs_top_pt;
    Histo1DPtr _hist_norm_top_pt;
    Scatter2DPtr _hist_ratio_top_pt;
    Histo1DPtr _hist_t_top_pt;
    Histo1DPtr _hist_tbar_top_pt;

    // Top quark rapidity histograms and ratio
    Histo1DPtr _hist_abs_top_y;
    Histo1DPtr _hist_norm_top_y;
    Scatter2DPtr _hist_ratio_top_y;
    Histo1DPtr _hist_t_top_y;
    Histo1DPtr _hist_tbar_top_y;

    // Charged lepton pt histograms and ratio
    Histo1DPtr _hist_abs_lepton_pt;
    Histo1DPtr _hist_norm_lepton_pt;
    Scatter2DPtr _hist_ratio_lepton_pt;
    Histo1DPtr _hist_t_lepton_pt;
    Histo1DPtr _hist_tbar_lepton_pt;

    // Charged lepton rapidity histograms and ratio
    Histo1DPtr _hist_abs_lepton_y;
    Histo1DPtr _hist_norm_lepton_y;
    Scatter2DPtr _hist_ratio_lepton_y;
    Histo1DPtr _hist_t_lepton_y;
    Histo1DPtr _hist_tbar_lepton_y;

    // W boson pt histograms and ratio
    Histo1DPtr _hist_abs_w_pt;
    Histo1DPtr _hist_norm_w_pt;
    Scatter2DPtr _hist_ratio_w_pt;
    Histo1DPtr _hist_t_w_pt;
    Histo1DPtr _hist_tbar_w_pt;

    // Top quark polarization angle histograms
    Histo1DPtr _hist_abs_top_cos;
    Histo1DPtr _hist_norm_top_cos;
    Histo1DPtr _hist_t_top_cos;
    Histo1DPtr _hist_tbar_top_cos;


    /// @brief helper function to fill absolute cross section histograms
    void fillAbsHist(
      Histo1DPtr& hist_abs, const Histo1DPtr& hist_t,
      const Histo1DPtr& hist_tbar
    ) {
      (*hist_abs) += (*hist_t);
      (*hist_abs) += (*hist_tbar);
    }

    /// @brief helper function to fill normalized cross section histograms
    void fillNormHist(
      Histo1DPtr& hist_norm, const Histo1DPtr& hist_t,
      const Histo1DPtr& hist_tbar
    ) {
      (*hist_norm) += (*hist_t);
      (*hist_norm) += (*hist_tbar);
      hist_norm->normalize();
    }


    /** @brief helper function to solve for the unknown neutrino pz momentum
     *  using a W boson mass constraint
     */
    std::pair<FourMomentum,FourMomentum> NuMomentum(
      double pxlep, double pylep, double pzlep,
      double elep, double metpx, double metpy
    ) {

      FourMomentum result(0, 0, 0, 0);
      FourMomentum result2(0, 0, 0, 0);

      double misET2 = (metpx * metpx + metpy * metpy);
      double mu = (WMASS * WMASS) / 2 + metpx * pxlep + metpy * pylep;
      double a  = (mu * pzlep) / (elep * elep - pzlep * pzlep);
      double a2 = std::pow(a, 2);

      double b  = (std::pow(elep, 2.) * (misET2) - std::pow(mu, 2.))
                  / (std::pow(elep, 2) - std::pow(pzlep, 2));

      double pz1(0), pz2(0), pznu(0), pznu2(0);

      FourMomentum p4W_rec;
      FourMomentum p4b_rec;
      FourMomentum p4Top_rec;
      FourMomentum p4lep_rec;

      p4lep_rec.setXYZE(pxlep, pylep, pzlep, elep);

      FourMomentum p40_rec(0, 0, 0, 0);

      // there are two real solutions
      if (a2 - b > 0 ) {
        double root = sqrt(a2 - b);
        pz1 = a + root;
        pz2 = a - root;

        pznu = pz1;
        pznu2 = pz2;

        // first solution is the one with the smallest |pz|
        if (fabs(pz1) > fabs(pz2)) {
          pznu = pz2;
          pznu2 = pz1;
        }

        double Enu = sqrt(misET2 + pznu * pznu);
        double Enu2 = sqrt(misET2 + pznu2 * pznu2);

        result.setXYZE(metpx, metpy, pznu, Enu);
        result2.setXYZE(metpx, metpy, pznu2, Enu2);

      } else {

        // there are only complex solutions; set pz=0 and vary px/py such
        // that mT=mW while keeping px^2+py^2 close to the original pT^2
        double ptlep = sqrt(pxlep * pxlep + pylep * pylep);

        double EquationA = 1;
        double EquationB = -3 * pylep * WMASS / (ptlep);

        double EquationC = WMASS * WMASS * (2 * pylep * pylep) / (ptlep * ptlep)
                           + WMASS * WMASS
                           - 4 * pxlep * pxlep * pxlep * metpx / (ptlep * ptlep)
                           - 4 * pxlep * pxlep * pylep * metpy / (ptlep * ptlep);

        double EquationD = 4 * pxlep * pxlep * WMASS * metpy / (ptlep)
                           - pylep * WMASS * WMASS * WMASS / ptlep;

        vector<double> solutions = EquationSolve(EquationA, EquationB, EquationC, EquationD);

        vector<double> solutions2 = EquationSolve(EquationA, -EquationB, EquationC, -EquationD);

        double deltaMin = 14000 * 14000;
        double zeroValue = -WMASS * WMASS / (4 * pxlep);
        double minPx = 0;
        double minPy = 0;

        for ( size_t i = 0; i < solutions.size(); ++i) {
          if (solutions[i] < 0) continue;
          double p_x = (solutions[i] * solutions[i] - WMASS * WMASS) / (4 * pxlep);
          double p_y = (WMASS * WMASS * pylep
                        + 2 * pxlep * pylep * p_x
                        - WMASS * ptlep * solutions[i]
                        ) / (2 * pxlep * pxlep);
          double Delta2 = (p_x - metpx) * (p_x - metpx) + (p_y - metpy) * (p_y - metpy);

          if (Delta2 < deltaMin && Delta2 > 0) {
            deltaMin = Delta2;
            minPx = p_x;
            minPy = p_y;
          }

        }

        for ( size_t i = 0; i < solutions2.size(); ++i) {
          if (solutions2[i] < 0) continue;
          double p_x = (solutions2[i] * solutions2[i] - WMASS * WMASS) / (4 * pxlep);
          double p_y = (WMASS * WMASS * pylep
                        + 2 * pxlep * pylep * p_x
                        + WMASS * ptlep * solutions2[i]
                       ) / (2 * pxlep * pxlep);
          double Delta2 = (p_x - metpx) * (p_x - metpx) + (p_y - metpy) * (p_y - metpy);
          if (Delta2 < deltaMin && Delta2 > 0) {
            deltaMin = Delta2;
            minPx = p_x;
            minPy = p_y;
          }
        }

        double pyZeroValue = (WMASS * WMASS * pxlep + 2 * pxlep * pylep * zeroValue);
        double delta2ZeroValue = (zeroValue - metpx) * (zeroValue - metpx)
                                 + (pyZeroValue - metpy) * (pyZeroValue - metpy);

        if (deltaMin == 14000 * 14000) {
          return std::make_pair(result, result2);
        }

        if (delta2ZeroValue < deltaMin) {
          deltaMin = delta2ZeroValue;
          minPx = zeroValue;
          minPy = pyZeroValue;
        }


        double mu_Minimum = (WMASS * WMASS) / 2 + minPx * pxlep + minPy * pylep;
        double a_Minimum  = (mu_Minimum * pzlep) /
                            (elep * elep - pzlep * pzlep);
        pznu = a_Minimum;

        double Enu = sqrt(minPx * minPx + minPy * minPy + pznu * pznu);
        result.setXYZE(minPx, minPy, pznu , Enu);
      }
      return std::make_pair(result, result2);
    }


    /// @brief helper function find root of the cubic equation a*x^3 + b*x^2 + c*x + d = 0
    std::vector<double> EquationSolve(
      double a, double b,
      double c, double d
    ) {
      std::vector<double> result;

      std::complex<double> x1;
      std::complex<double> x2;
      std::complex<double> x3;

      double q = (3 * a * c - b * b) / (9 * a * a);
      double r = (9 * a * b * c - 27 * a * a * d - 2 * b * b * b
                 ) / (54 * a * a * a);
      double Delta = q * q * q + r * r;

      std::complex<double> s;
      std::complex<double> t;

      double rho = 0;
      double theta = 0;

      if (Delta <= 0) {
        rho = sqrt(-(q * q * q));

        theta = acos(r / rho);

        s = std::polar<double>(sqrt(-q), theta / 3.0);
        t = std::polar<double>(sqrt(-q), -theta / 3.0);
      }

      if (Delta > 0) {
        s = std::complex<double>(cbrt(r + sqrt(Delta)), 0);
        t = std::complex<double>(cbrt(r - sqrt(Delta)), 0);
      }

      std::complex<double> i(0, 1.0);


      x1 = s + t + std::complex<double>(-b / (3.0 * a), 0);

      x2 = (s + t) * std::complex<double>(-0.5, 0)
           - std::complex<double>(b / (3.0 * a), 0)
           + (s - t) * i * std::complex<double>(sqrt(3) / 2.0, 0);

      x3 = (s + t) * std::complex<double>(-0.5, 0)
           - std::complex<double>(b / (3.0 * a), 0)
           - (s - t) * i * std::complex<double>(sqrt(3) / 2.0, 0);

      if (fabs(x1.imag()) < 0.0001) result.push_back(x1.real());
      if (fabs(x2.imag()) < 0.0001) result.push_back(x2.real());
      if (fabs(x3.imag()) < 0.0001) result.push_back(x3.real());

      return result;
    }

  };


  DECLARE_RIVET_PLUGIN(CMS_2019_I1744604);

}
