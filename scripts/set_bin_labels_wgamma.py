import json

# Binning used in CMS_2021_PAS_SMP_20_005.cc
n_phi_bins = 3
n_theta3d_bins = 3
n_pt_ext_bins = 5
n_costheta_bins = 10
n_theta_bins = 10
n_phi_1d_bins = 10

base_paths = [
    '/CMS_2021_PAS_SMP_20_005',
]

bin_labels = {}


def add_labels(hist_name, labels):
    for base in base_paths:
        bin_labels['{}/{}'.format(base, hist_name)] = list(labels)


# 1D histograms
add_labels('eft_phi', ['phi_{}'.format(i) for i in range(n_phi_1d_bins)])
add_labels('eft_costheta', ['costheta_{}'.format(i) for i in range(n_costheta_bins)])
add_labels('eft_theta', ['theta_{}'.format(i) for i in range(n_theta_bins)])

# 1D slices in phi
for i_phi in range(n_phi_bins):
    add_labels(
        'eft_costheta_phi_{}'.format(i_phi),
        ['costheta_{}_phi_{}'.format(i, i_phi) for i in range(n_costheta_bins)]
    )
    add_labels(
        'eft_theta_phi_{}'.format(i_phi),
        ['theta_{}_phi_{}'.format(i, i_phi) for i in range(n_theta_bins)]
    )

# 1D pT histograms split in phi
for i_phi in range(n_phi_bins):
    add_labels(
        'eft_ext_photon_pt_phi_{}'.format(i_phi),
        ['photon_pt_{}_phi_{}'.format(i_pt, i_phi) for i_pt in range(n_pt_ext_bins)]
    )

# 1D pT histograms split in (phi, theta)
for i_theta in range(n_theta3d_bins):
    for i_phi in range(n_phi_bins):
        add_labels(
            'eft_ext_photon_pt_phi_{}_theta_{}'.format(i_phi, i_theta),
            [
                'photon_pt_{}_phi_{}_theta_{}'.format(i_pt, i_phi, i_theta)
                for i_pt in range(n_pt_ext_bins)
            ]
        )

# 3D histogram (flattened ordering in JSON / YODA bins):
labels_3d = []
for i_theta in range(n_theta3d_bins):
    for i_phi in range(n_phi_bins):
        for i_pt in range(n_pt_ext_bins):
            labels_3d.append(
                'photon_pt_{}_phi_{}_theta_{}'.format(i_pt, i_phi, i_theta)
            )
add_labels('eft_pt_phi_theta_3d', labels_3d)

with open('./bin_labels_wgamma.json', 'w') as json_file:
    json.dump(bin_labels, json_file, indent=4)

print('Created bin_labels_wgamma.json with {} histograms'.format(len(bin_labels)))
print('Total labeled bins: {}'.format(sum(len(v) for v in bin_labels.values())))
