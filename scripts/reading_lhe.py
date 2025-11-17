import awkward as ak
import vector
from lhereader import LHEReader
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import awkward as ak
import numpy as np
import mplhep
import hist
from hist import Hist
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep

mpl.rcParams['figure.dpi'] = 300

def printProgressBar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    if iteration == total: 
        print()

def lhe_to_awkward(filename):
    reader = LHEReader(filename, weight_mode='dict')

    # Build the event structure as an awkward array
    events = ak.Array([
        {
            "px": [p.px for p in e.particles],
            "py": [p.py for p in e.particles],
            "pz": [p.pz for p in e.particles],
            "E":  [p.energy for p in e.particles],
            "pdgid": [p.pdgid for p in e.particles],
            "status": [p.status for p in e.particles],
            "mass": [p.mass for p in e.particles],
            "weights": e.weights
        }
        for e in reader
    ])

    # Adding a a new field "p4", the 4-vector of the particle in the list events as an awkward array
    vector.register_awkward()
    events = ak.with_field(
        events,
        ak.zip(
            {"px": events.px, "py": events.py, "pz": events.pz, "E": events.E},
            with_name="Momentum4D",
        ),
        "p4"
    )
    
    #Adding a new field with the event number
    events = ak.with_field(events, ak.local_index(events.pdgid, axis=0), "event_id")

    return events

def abs_delta_phi(phi1, phi2):
    dphi = np.abs(phi1 - phi2)
    dphi = ak.where(dphi > np.pi, 2 * np.pi - dphi, dphi)
    return dphi

def delta_phi(phi1, phi2):
    dphi = phi1 - phi2
    dphi = ak.where(dphi > np.pi, 2 * np.pi - dphi, dphi)
    return dphi

def calcDeltaR(part1_eta, part2_eta, part1_phi, part2_phi):

    deta = np.abs (part1_eta - part2_eta)
    dphi = delta_phi(part1_phi, part2_phi)

    deltaR = np.sqrt(deta**2 + dphi**2)
    return deltaR


def plot_awkward_hist_ratio_histlib(
    data,
    weights_dataset,
    bins=50,
    range_=(0, 10),
    xlabel="",
    ylabel="Ratio",
    alpha=1,
    figsize=(10, 10),
    log=False,
):
    
    flat_data = np.asarray(ak.flatten(data, axis=-1))
    hep.style.use("CMS")

    h_template = (
        Hist.new
        .Reg(bins, *range_, name="x", label=xlabel, underflow=False, overflow=False)
        .Weight()
    )

    #Filling histograms to plot
    histograms = []

    for i, (label, weights, color) in enumerate(weights_dataset):
        h = h_template.copy()
        h.fill(x=flat_data, weight=weights)
        histograms.append((label, color, h))

    ref_label, ref_color, h_ref = histograms[0]
    bin_edges = h_ref.axes[0].edges

    #Creating figures

    fig, (ax, ax_ratio) = plt.subplots(
        2, 1,
        sharex=True,
        figsize=figsize,
        gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.05}
    )
    mplhep.cms.label('Private Work', data=False, ax=ax)


    # Plot all histograms on main axis
    for label, color, h in histograms:
        hep.histplot(
                h,
                histtype="step",
                label=f"{label}",
                ax=ax,
                color=color,
                alpha=alpha,
                linewidth=2,
            )
    

    ax.set_ylabel("Events")
    ax.legend(fontsize=18)
    ax.set_xlabel("")
    ax.grid(linestyle=':')
    if log:
        ax.set_yscale("log")

    for label, color, h in histograms[1:]:

        # The method "sqrt" is used giving the Poisson standard deviation (symmetric uncertainties) derived from the variance stored in the histogram object
        # Since this object is a from the Hist library that has been initialized using .Weight(), the variance stored is the (sum of weights)^2
        ratio, err_up, err_down = hep.get_comparison(
                h,
                h_ref,
                comparison="ratio",
                h1_w2method="sqrt",
            )


        hep.histplot(
                ratio,
                bins=bin_edges,
                yerr=err_up,
                histtype="errorbar",
                label=f"{label}/{ref_label}",
                ax=ax_ratio,
                alpha=alpha,
                color=color,
            )


    ax_ratio.axhline(1.0, color="black", linestyle="--", linewidth=1)
    ax_ratio.set_ylabel(ylabel)
    ax_ratio.set_xlabel(xlabel)
    ax_ratio.grid(linestyle=':')

    # plt.tight_layout()

#To plot without wrror bars just the histogram, to add them, the hostogram should be defined using Hist library (in order to account for the weights)

def plot_awkward_hist(data, weights_dataset ,bins=50, range=[0,10], xlabel="", ylabel="Events", alpha=1, figsize=(10,10), log=False):

    # Flatten in case data is jagged
    flat_data = ak.flatten(data, axis=-1)
    flat_data = np.asarray(flat_data)

    plt.figure(figsize=figsize, dpi=300)

    for label, weights, color in weights_dataset:
        plt.hist(flat_data, bins=bins, range=range, color=color, alpha=alpha,label=label, weights=weights, histtype='step', linewidth=2.5)
        mplhep.cms.label('Private Work', data=False, com = None)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(loc='best')
    if log:
        plt.yscale("log")
    plt.grid(linestyle=':')
    plt.tight_layout()