import reading_lhe as lhe
import matplotlib.pyplot as plt
import numpy as np
import awkward as ak
from matplotlib.colors import ListedColormap
import mplhep
plt.style.use(mplhep.style.CMS)
import glob
import argparse
import os
import sys
import vector
vector.register_awkward()


my_colors = ["#df05a5", "#ec8d08", "#77c02a", "#18a1c0", "#9c28c0", "#fc0000"]  
my_cmap = ListedColormap(my_colors)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Plotting parameters')
    parser.add_argument('--parquet', action='store_true', help='Produce parquet file to plot')
    parser.add_argument('--file', type=str, default='plots', help='Parquet filename')
    parser.add_argument('--output', type=str, default='plots', help='Output name for plots')
    args = parser.parse_args()

    if args.parquet:
        filenames = glob.glob("/data_CMS/cms/amella/EFT2Obs/lhe_files/ggF-H-chg/events/events_*_nonp.lhe")
        total_files = len(filenames)

        print(f"Found {total_files} LHE files to process.")
        lhe.printProgressBar(0, total_files, prefix='Progress:', suffix='Complete', length=50)
        arrays = []
        for i, f in enumerate(filenames, start=1):
            events_ind = lhe.lhe_to_awkward(f)
            arrays.append(events_ind)
            lhe.printProgressBar(i, total_files, prefix='Progress:', suffix='Complete', length=50)
        events = ak.concatenate(arrays)

        # events = ak.concatenate([lhe.lhe_to_awkward(f) for f in filenames])

        output_dir = "/data_CMS/cms/amella/EFT2Obs/parquet_files/" 
        os.makedirs(output_dir, exist_ok=True)

        ak.to_parquet(events, os.path.join(output_dir, args.file+"events.parquet"))

    parquet_dir = "/data_CMS/cms/amella/EFT2Obs/parquet_files/" 
    if os.path.exists(parquet_dir):
     print("Opening", parquet_dir+args.file+"events.parquet")
     events=ak.from_parquet(parquet_dir+args.file+"events.parquet") 
     events = ak.with_field(
        events,
        ak.zip(
            {"px": events.p4.px, "py": events.p4.py, "pz": events.p4.pz, "E": events.p4.E},
            with_name="Momentum4D",
        ),
        "p4"
    )

    plot_dir= "/home/llr/cms/amella/EFT2Obs/"+args.output+"/plots/"
    os.makedirs(plot_dir, exist_ok=True)
    events_weights = events.weights

    weight_dataset= [
        ('chg= 0', events_weights[:]['rw0000'], my_cmap(0)),
        ('chg= 0.005', events_weights[:]['rw0001'], my_cmap(1)),
        ('chg= 0.01', events_weights[:]['rw0002'], my_cmap(2)),
        ('chg= 0.015', events_weights[:]['rw0003'], my_cmap(3)),
        ('chg= 0.02', events_weights[:]['rw0004'], my_cmap(4)),
    ]


    # weight_dataset= [
    #     ('chg= 0', events_weights[:]['rw0000'], my_cmap(0)),
    #     ('chg= 0.005', events_weights[:]['rw0001'], my_cmap(1)),
    #     ('chg= 0.01', events_weights[:]['rw0002'], my_cmap(2)),
    #     ('chg= 0.015', events_weights[:]['rw0003'], my_cmap(3)),
    #     ('chg= 0.02', events_weights[:]['rw0004'], my_cmap(4)),
    #     ('No weights', None, my_cmap(5)),
    #     ]

    ylabel="chg/chg=0"
    ## Plotting the pt of the the particles in the event
    higgs_mask= events.pdgid == 25
    higgs_pt = events.p4.pt[higgs_mask]
    lhe.plot_awkward_hist_ratio_histlib(higgs_pt, weight_dataset, bins=20, range_=(0, 1000), xlabel=r"$ p_T (H) $", ylabel=ylabel, log=True)
    plt.savefig(plot_dir +"higgs_pt.png")
    plt.savefig(plot_dir +"higgs_pt.pdf")
    print("Saved Figure: "+ plot_dir +"higgs_pt.png")

    particle_mask= (events.pdgid != 25) & (events.status == 1)
    particles_pt = events.p4.pt[particle_mask]
    #Sorting the particles by descending pt
    sort_indices = ak.argsort(particles_pt, ascending=False)
    # print(particles_pt)
    sorted_particles_pt = particles_pt[sort_indices]
    # print(sorted_particles_pt)
    lhe.plot_awkward_hist_ratio_histlib(sorted_particles_pt[:,0], weight_dataset, bins=20, range_=(0, 400), xlabel=r"$ p_T (jet0) $", ylabel=ylabel,log= True)
    plt.savefig(plot_dir +"jet0_pt.png")
    plt.savefig(plot_dir +"jet0_pt.pdf")
    print("Saved Figure: "+ plot_dir +"jet0_pt.png")
    lhe.plot_awkward_hist_ratio_histlib(sorted_particles_pt[:,1], weight_dataset, bins=20, range_=(0, 400), xlabel=r"$ p_T (jet1) $", ylabel=ylabel,log= True)
    plt.savefig(plot_dir +"jet1_pt.png")
    plt.savefig(plot_dir +"jet1_pt.pdf")
    print("Saved Figure: "+ plot_dir +"jet1_pt.png")

    combined_p4_jets = ak.sum(events.p4[particle_mask], axis=1)

    lhe.plot_awkward_hist_ratio_histlib(combined_p4_jets.mass, weight_dataset, bins=20, range_=(0, 1000), xlabel=r"$ M (jet0, jet1) $",ylabel=ylabel, log= True)
    plt.savefig(plot_dir +"mass_jets.png")
    plt.savefig(plot_dir +"mass_jets.pdf")
    print("Saved Figure: "+ plot_dir +"mass_jets.png")

    #Computing deltaeta, deltaphi and deltaR between the 2 jets
    phi = events.p4.phi[particle_mask]
    eta = events.p4.eta[particle_mask]

    jets_ordered= phi[sort_indices]
    delta_phi = lhe.delta_phi(jets_ordered[:,0], jets_ordered[:,1])
    lhe.plot_awkward_hist_ratio_histlib(delta_phi, weight_dataset, bins=20, range_=(-np.pi, np.pi), xlabel=r"$ \Delta \phi (jet0-jet1) $", ylabel=ylabel,log=True)
    plt.savefig(plot_dir +"dphi_jets.png")
    plt.savefig(plot_dir +"dphi_jets.pdf")
    print("Saved Figure: "+ plot_dir +"dphi_jets.png")

    deta = np.abs (eta[:,0] - eta[:,1])
    abs_dphi= lhe.abs_delta_phi(phi[:,0], phi[:,1])
    dR = lhe.calcDeltaR(eta[:,0], eta[:,1], phi[:,0], phi[:,1])
    events_weights = events.weights

    lhe.plot_awkward_hist_ratio_histlib(abs_dphi, weight_dataset, bins=20, range_=(0, np.pi), xlabel=r"$ | \Delta \phi (jet0-jet1) |$",ylabel=ylabel, log=True)
    plt.savefig(plot_dir +"dphi_abs_jets.png")
    plt.savefig(plot_dir +"dphi_abs_jets.pdf")
    print("Saved Figure: "+ plot_dir +"dphi_abs_jets.png")
    lhe.plot_awkward_hist_ratio_histlib(deta, weight_dataset, bins=20, range_=(ak.min(deta), ak.max(deta)), xlabel=r"$ | \Delta \eta (jet0-jet1) |$", ylabel=ylabel,log=True)
    plt.savefig(plot_dir +"deta_jets.png")
    plt.savefig(plot_dir +"deta_jets.pdf")
    print("Saved Figure: "+ plot_dir +"deta_jets.png")
    lhe.plot_awkward_hist_ratio_histlib(dR, weight_dataset, bins=20, range_=(ak.min(dR), ak.max(dR)), xlabel=r"$ \Delta R (jet0-jet1) $",ylabel=ylabel, log=True)
    plt.savefig(plot_dir +"dR_jets.png")
    plt.savefig(plot_dir +"dR_jets.pdf")
    print("Saved Figure: "+ plot_dir +"dR_jets.png")